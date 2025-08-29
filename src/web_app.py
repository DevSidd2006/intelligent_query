from flask import Flask, request, jsonify, render_template_string, render_template, flash, redirect, url_for
from werkzeug.utils import secure_filename
import os
import json
import sys
import tempfile
import traceback
import time
import gc
import secrets
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('web_app.log')
    ]
)
logger = logging.getLogger(__name__)

# Smart import handling for different deployment scenarios
def import_app_module():
    """Dynamic import handler for app.py that works in all environments"""
    try:
        # Method 1: Try relative import (when running as package)
        from .app import extract_text_from_pdf, create_document_embeddings, generate_response
        return extract_text_from_pdf, create_document_embeddings, generate_response
    except (ImportError, ValueError):
        try:
            # Method 2: Try direct import (when running standalone)
            from app import extract_text_from_pdf, create_document_embeddings, generate_response
            return extract_text_from_pdf, create_document_embeddings, generate_response
        except ImportError:
            try:
                # Method 3: Add current directory to path and import
                current_dir = os.path.dirname(os.path.abspath(__file__))
                if current_dir not in sys.path:
                    sys.path.insert(0, current_dir)
                from app import extract_text_from_pdf, create_document_embeddings, generate_response
                return extract_text_from_pdf, create_document_embeddings, generate_response
            except ImportError:
                # Method 4: Absolute path import (fallback)
                import importlib.util
                app_file = os.path.join(os.path.dirname(__file__), 'app.py')
                if not os.path.exists(app_file):
                    raise ImportError(f"Could not find app.py at {app_file}")
                
                spec = importlib.util.spec_from_file_location("app_module", app_file)
                app_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(app_module)
                
                return (app_module.extract_text_from_pdf, 
                       app_module.create_document_embeddings, 
                       app_module.generate_response)

# Import the required functions
try:
    extract_text_from_pdf, create_document_embeddings, generate_response = import_app_module()
    logger.info("Successfully imported app module functions")
except Exception as import_error:
    logger.error(f"Failed to import app module: {import_error}")
    logger.error("Please ensure app.py is in the same directory as web_app.py")
    sys.exit(1)

def get_api_key():
    """
    Get Groq API key
    """
    # Groq API key
    api_key = os.environ.get('GROQ_API_KEY')
    if api_key:
        return api_key, 'GROQ_API_KEY'
    
    return None, None

def validate_api_configuration():
    """Validate API configuration at startup"""
    api_key, key_source = get_api_key()
    
    if not api_key:
        logger.error("No API key found!")
        logger.info("Please set GROQ_API_KEY environment variable")
        logger.info("Check your .env file or environment variables")
        return False
    
    logger.info(f"API key found: {key_source}")
    
    # Validate key format
    if not api_key.startswith('gsk_'):
        logger.warning("API key format unusual (should start with 'gsk_')")
    
    return True

import secrets

# Validate API configuration at startup
if not validate_api_configuration():
    logger.warning("API configuration validation failed")
    logger.info("HINT: Create a .env file with:")
    logger.info("GROQ_API_KEY=your_actual_groq_api_key_here")
    logger.info("Application will continue but AI features may not work")

app = Flask(__name__)

# Secure secret key handling
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    # Generate a random secret key for development
    secret_key = secrets.token_hex(32)
    logger.warning("Using generated secret key. Set SECRET_KEY environment variable for production.")

app.secret_key = secret_key

# Configuration
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB max file size

app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Global variables to store processed document data and chat history
current_document = {
    'chunks': None,
    'embeddings': None,
    'index': None,
    'model_st': None,
    'filename': None,
    'upload_time': None,
    'chunk_count': 0
}

# Chat history storage
chat_sessions = {}
current_session_id = None

def get_or_create_session():
    global current_session_id
    if current_session_id is None:
        current_session_id = str(int(time.time()))
        chat_sessions[current_session_id] = {
            'messages': [],
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'document': current_document['filename']
        }
    return current_session_id

def add_message_to_session(session_id, message, sender, response_data=None):
    if session_id not in chat_sessions:
        chat_sessions[session_id] = {'messages': [], 'created_at': time.strftime('%Y-%m-%d %H:%M:%S')}
    
    chat_sessions[session_id]['messages'].append({
        'message': message,
        'sender': sender,
        'timestamp': time.strftime('%H:%M:%S'),
        'response_data': response_data
    })

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Modern HTML Template with enhanced features
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>IntelliQuery - AI PDF Assistant</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {
            --primary: #2563eb;
            --primary-dark: #1d4ed8;
            --secondary: #64748b;
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
            --bg-primary: #ffffff;
            --bg-secondary: #f8fafc;
            --bg-tertiary: #f1f5f9;
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --border: #e2e8f0;
            --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            --shadow-lg: 0 20px 25px -5px rgba(0, 0, 0, 0.1);
        }
        
        [data-theme="dark"] {
            --primary: #3b82f6;
            --bg-primary: #1e293b;
            --bg-secondary: #0f172a;
            --bg-tertiary: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #cbd5e1;
            --border: #475569;
        }
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-secondary);
            color: var(--text-primary);
            line-height: 1.6;
            transition: all 0.3s ease;
        }
        
        .app-layout {
            display: flex;
            height: 100vh;
            overflow: hidden;
        }
        
        .sidebar {
            width: 320px;
            background: var(--bg-primary);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            transition: all 0.3s ease;
        }
        
        .sidebar-header {
            padding: 24px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
            font-weight: 700;
            font-size: 1.25rem;
            color: var(--primary);
        }
        
        .theme-toggle {
            background: none;
            border: none;
            padding: 8px;
            border-radius: 8px;
            cursor: pointer;
            color: var(--text-secondary);
            transition: all 0.2s ease;
        }
        
        .theme-toggle:hover {
            background: var(--bg-tertiary);
            color: var(--text-primary);
        }
        
        .new-chat-btn {
            margin: 16px 24px;
            padding: 12px 16px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 12px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
        }
        
        .new-chat-btn:hover {
            background: var(--primary-dark);
            transform: translateY(-1px);
        }
        
        .delete-history-btn {
            margin: 0 24px 16px 24px;
            padding: 8px 16px;
            background: var(--error);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
            font-size: 0.9rem;
        }
        
        .delete-history-btn:hover {
            background: #dc2626;
            transform: translateY(-1px);
        }
        
        .success-tick {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            width: 100px;
            height: 100px;
            background: var(--success);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 2000;
            animation: tickAnimation 1.5s ease-out;
        }
        
        .success-tick i {
            font-size: 3rem;
            color: white;
            animation: tickScale 0.6s ease-out 0.3s both;
        }
        
        @keyframes tickAnimation {
            0% {
                opacity: 0;
                transform: translate(-50%, -50%) scale(0.3);
            }
            50% {
                opacity: 1;
                transform: translate(-50%, -50%) scale(1.1);
            }
            100% {
                opacity: 1;
                transform: translate(-50%, -50%) scale(1);
            }
        }
        
        @keyframes tickScale {
            0% {
                transform: scale(0);
            }
            50% {
                transform: scale(1.2);
            }
            100% {
                transform: scale(1);
            }
        }
        
        .chat-history {
            flex: 1;
            overflow-y: auto;
            padding: 0 16px;
        }
        
        .chat-session {
            padding: 12px 16px;
            margin: 4px 0;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s ease;
            border: 1px solid transparent;
        }
        
        .chat-session:hover {
            background: var(--bg-tertiary);
        }
        
        .chat-session.active {
            background: var(--primary);
            color: white;
            border-color: var(--primary-dark);
        }
        
        .session-title {
            font-weight: 500;
            font-size: 0.9rem;
            margin-bottom: 4px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .session-meta {
            font-size: 0.75rem;
            opacity: 0.7;
        }
        
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            background: var(--bg-primary);
        }
        
        .main-header {
            padding: 20px 24px;
            border-bottom: 1px solid var(--border);
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: var(--bg-primary);
        }
        
        .document-status {
            display: flex;
            align-items: center;
            gap: 12px;
        }
        
        .status-indicator {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--success);
            animation: pulse 2s infinite;
        }
        
        .document-info h3 {
            font-size: 1rem;
            font-weight: 600;
            margin: 0;
        }
        
        .document-info p {
            font-size: 0.875rem;
            color: var(--text-secondary);
            margin: 2px 0 0 0;
        }
        
        .header-actions {
            display: flex;
            gap: 12px;
        }
        
        .btn-secondary {
            padding: 8px 16px;
            background: var(--bg-tertiary);
            color: var(--text-primary);
            border: 1px solid var(--border);
            border-radius: 8px;
            font-size: 0.875rem;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .btn-secondary:hover {
            background: var(--bg-secondary);
            transform: translateY(-1px);
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .chat-area {
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .messages-container {
            flex: 1;
            overflow-y: auto;
            padding: 24px;
            scroll-behavior: smooth;
        }
        
        .message {
            margin-bottom: 24px;
            animation: slideIn 0.3s ease-out;
        }
        
        .message-user {
            display: flex;
            justify-content: flex-end;
        }
        
        .message-assistant {
            display: flex;
            justify-content: flex-start;
        }
        
        .message-bubble {
            max-width: 70%;
            padding: 16px 20px;
            border-radius: 18px;
            position: relative;
        }
        
        .message-user .message-bubble {
            background: var(--primary);
            color: white;
            border-bottom-right-radius: 4px;
        }
        
        .message-assistant .message-bubble {
            background: var(--bg-tertiary);
            color: var(--text-primary);
            border-bottom-left-radius: 4px;
            border: 1px solid var(--border);
        }
        
        .message-time {
            font-size: 0.75rem;
            opacity: 0.7;
            margin-top: 8px;
            text-align: right;
        }
        
        .message-assistant .message-time {
            text-align: left;
        }
        
        .input-area {
            padding: 24px;
            border-top: 1px solid var(--border);
            background: var(--bg-primary);
        }
        
        .input-container {
            display: flex;
            gap: 12px;
            align-items: flex-end;
            max-width: 100%;
        }
        
        .message-input {
            flex: 1;
            min-height: 44px;
            max-height: 120px;
            padding: 12px 16px;
            border: 2px solid var(--border);
            border-radius: 22px;
            font-size: 0.95rem;
            resize: none;
            outline: none;
            transition: all 0.2s ease;
            font-family: inherit;
            background: var(--bg-primary);
            color: var(--text-primary);
        }
        
        .message-input:focus {
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
        }
        
        .send-button {
            width: 44px;
            height: 44px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s ease;
            flex-shrink: 0;
        }
        
        .send-button:hover:not(:disabled) {
            background: var(--primary-dark);
            transform: scale(1.05);
        }
        
        .send-button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .upload-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        
        .upload-modal {
            background: var(--bg-primary);
            border-radius: 16px;
            padding: 32px;
            max-width: 500px;
            width: 90%;
            box-shadow: var(--shadow-lg);
        }
        
        .upload-area {
            border: 2px dashed var(--border);
            border-radius: 12px;
            padding: 48px 24px;
            text-align: center;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .upload-area:hover {
            border-color: var(--primary);
            background: rgba(37, 99, 235, 0.05);
        }
        
        .upload-area.dragover {
            border-color: var(--primary);
            background: rgba(37, 99, 235, 0.1);
        }
        
        .upload-icon {
            font-size: 3rem;
            color: var(--primary);
            margin-bottom: 16px;
        }
        
        .upload-text {
            font-size: 1.1rem;
            font-weight: 500;
            margin-bottom: 8px;
        }
        
        .upload-subtext {
            color: var(--text-secondary);
            font-size: 0.9rem;
        }
        
        .file-input {
            display: none;
        }
        
        .modal-actions {
            display: flex;
            gap: 12px;
            margin-top: 24px;
            justify-content: flex-end;
        }
        
        .btn-primary {
            padding: 12px 24px;
            background: var(--primary);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        
        .btn-primary:hover {
            background: var(--primary-dark);
        }
        
        .empty-state {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100%;
            text-align: center;
            color: var(--text-secondary);
        }
        
        .empty-icon {
            font-size: 4rem;
            margin-bottom: 24px;
            opacity: 0.5;
        }
        
        .loading-indicator {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 16px;
            background: var(--bg-tertiary);
            border-radius: 12px;
            margin: 16px 0;
        }
        
        .spinner {
            width: 20px;
            height: 20px;
            border: 2px solid var(--border);
            border-top: 2px solid var(--primary);
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .notification {
            position: fixed;
            top: 24px;
            right: 24px;
            padding: 16px 20px;
            border-radius: 12px;
            color: white;
            font-weight: 500;
            z-index: 1001;
            animation: slideInRight 0.3s ease-out;
            max-width: 400px;
        }
        
        .notification.success { background: var(--success); }
        .notification.error { background: var(--error); }
        .notification.warning { background: var(--warning); }
        
        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        .sidebar-collapsed {
            width: 0;
            overflow: hidden;
        }
        
        .mobile-header {
            display: none;
            padding: 16px;
            background: var(--bg-primary);
            border-bottom: 1px solid var(--border);
            align-items: center;
            justify-content: space-between;
        }
        
        .menu-toggle {
            background: none;
            border: none;
            font-size: 1.25rem;
            cursor: pointer;
            color: var(--text-primary);
        }
        
        @media (max-width: 768px) {
            .sidebar {
                position: fixed;
                left: -320px;
                top: 0;
                height: 100vh;
                z-index: 999;
                transition: left 0.3s ease;
            }
            
            .sidebar.open {
                left: 0;
            }
            
            .mobile-header {
                display: flex;
            }
            
            .main-content {
                width: 100%;
            }
            
            .message-bubble {
                max-width: 85%;
            }
        }
        
        .hidden {
            display: none !important;
        }
        
        .fade-in {
            animation: fadeIn 0.3s ease-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        .content {
            padding: 0;
        }
        
        .upload-section {
            padding: 40px;
            text-align: center;
        }
        
        .upload-tabs {
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
        }
        
        .upload-tab {
            padding: 10px 20px;
            background: var(--bg-light);
            color: var(--text);
            border: none;
            cursor: pointer;
            transition: all 0.3s ease;
            border-bottom: 2px solid transparent;
            font-weight: 500;
        }
        
        .upload-tab.active {
            border-bottom: 2px solid var(--accent);
            color: var(--accent);
            background: rgba(245, 158, 11, 0.1);
        }
        
        .upload-tab:first-child {
            border-radius: 10px 0 0 10px;
        }
        
        .upload-tab:last-child {
            border-radius: 0 10px 10px 0;
        }
        
        .upload-content {
            display: none;
        }
        
        .upload-content.active {
            display: block;
            animation: fadeIn 0.5s ease-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .url-input-container {
            border: 3px dashed #e0e7ff;
            border-radius: 15px;
            padding: 40px 20px;
            transition: all 0.3s ease;
            position: relative;
            background: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 100%);
            margin-bottom: 20px;
        }
        
        .url-input-container:hover {
            border-color: #667eea;
            background: linear-gradient(145deg, #eef2ff 0%, #e0e7ff 100%);
        }
        
        .url-input {
            width: 100%;
            padding: 15px 20px;
            border: 2px solid #e0e7ff;
            border-radius: 10px;
            font-size: 1rem;
            margin-top: 20px;
            outline: none;
            transition: all 0.3s ease;
        }
        
        .url-input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .upload-area {
            border: 3px dashed #e0e7ff;
            border-radius: 15px;
            padding: 60px 20px;
            transition: all 0.3s ease;
            cursor: pointer;
            position: relative;
            background: linear-gradient(145deg, #f8fafc 0%, #f1f5f9 100%);
        }
        
        .upload-area:hover {
            border-color: #667eea;
            background: linear-gradient(145deg, #eef2ff 0%, #e0e7ff 100%);
            transform: translateY(-2px);
        }
        
        .upload-icon {
            font-size: 4rem;
            color: #667eea;
            margin-bottom: 20px;
            transition: all 0.3s ease;
        }
        
        .upload-area:hover .upload-icon {
            transform: scale(1.1);
            color: #764ba2;
        }
        
        .upload-text {
            font-size: 1.2rem;
            color: #4a5568;
            margin-bottom: 10px;
            font-weight: 500;
        }
        
        .upload-subtext {
            color: #718096;
            font-size: 0.9rem;
        }
        
        .file-input {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            opacity: 0;
            cursor: pointer;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 50px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 20px;
            font-size: 1rem;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        }
        
        .chat-section {
            height: 600px;
            display: flex;
            flex-direction: column;
        }
        
        .document-info {
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
            padding: 20px;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .doc-details h3 {
            color: #1e40af;
            margin: 0;
            font-size: 1.1rem;
            font-weight: 600;
        }
        
        .doc-details p {
            color: #64748b;
            margin: 5px 0 0 0;
            font-size: 0.9rem;
        }
        
        .status-dot {
            width: 8px;
            height: 8px;
            background: #10b981;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
            animation: blink 2s infinite;
        }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        
        .new-doc-btn {
            background: white;
            color: #667eea;
            border: 2px solid #667eea;
            padding: 8px 16px;
            border-radius: 25px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 0.9rem;
        }
        
        .new-doc-btn:hover {
            background: #667eea;
            color: white;
            transform: scale(1.05);
        }
        
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #fafafa;
        }
        
        .chat-container::-webkit-scrollbar {
            width: 6px;
        }
        
        .chat-container::-webkit-scrollbar-thumb {
            background: #cbd5e1;
            border-radius: 3px;
        }
        
        .message {
            margin-bottom: 20px;
            animation: messageSlide 0.4s ease-out;
        }
        
        @keyframes messageSlide {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .user-message {
            text-align: right;
        }
        
        .user-bubble {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 20px 20px 5px 20px;
            display: inline-block;
            max-width: 80%;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        }
        
        .bot-message {
            text-align: left;
        }
        
        .bot-bubble {
            background: white;
            color: #2d3748;
            padding: 20px;
            border-radius: 20px 20px 20px 5px;
            display: inline-block;
            max-width: 85%;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
            border: 1px solid #e2e8f0;
        }
        
        .decision-badge {
            padding: 6px 12px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-bottom: 10px;
            display: inline-block;
        }
        
        .covered { background: #dcfce7; color: #166534; }
        .not-covered { background: #fef2f2; color: #991b1b; }
        .partial { background: #fef3c7; color: #92400e; }
        
        .input-section {
            padding: 20px;
            background: white;
            border-top: 1px solid #e2e8f0;
        }
        
        .input-container {
            display: flex;
            gap: 10px;
            align-items: center;
        }
        
        .question-input {
            flex: 1;
            padding: 15px 20px;
            border: 2px solid #e2e8f0;
            border-radius: 25px;
            font-size: 1rem;
            outline: none;
            transition: all 0.3s ease;
        }
        
        .question-input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .send-btn {
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 50%;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.2rem;
        }
        
        .send-btn:hover {
            transform: scale(1.1);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        .suggestions {
            margin-top: 15px;
            text-align: center;
        }
        
        .suggestion {
            background: #f1f5f9;
            color: #475569;
            border: none;
            padding: 8px 16px;
            border-radius: 20px;
            margin: 5px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 0.9rem;
        }
        
        .suggestion:hover {
            background: #667eea;
            color: white;
            transform: translateY(-1px);
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            color: #64748b;
        }
        
        .spinner {
            width: 30px;
            height: 30px;
            border: 3px solid #e2e8f0;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #64748b;
        }
        
        .empty-icon {
            font-size: 3rem;
            margin-bottom: 20px;
            opacity: 0.5;
        }
        
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 10px;
            color: white;
            font-weight: 500;
            z-index: 1000;
            animation: slideIn 0.3s ease-out;
        }
        
        .notification.success { background: #10b981; }
        .notification.error { background: #ef4444; }
        .notification.warning { background: #f59e0b; }
        
        @keyframes slideIn {
            from { transform: translateX(100%); }
            to { transform: translateX(0); }
        }
        
        .flash-message {
            background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
            color: #1e40af;
            padding: 15px 20px;
            margin: 20px;
            border-radius: 10px;
            border-left: 4px solid #3b82f6;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .app-container { margin: 10px; }
            .header h1 { font-size: 2rem; }
            .upload-area { padding: 40px 20px; }
            .chat-section { height: 500px; }
            .user-bubble, .bot-bubble { max-width: 95%; }
        }
    </style>
</head>
<body>
    <div class="app-layout">
        <!-- Sidebar -->
        <div class="sidebar" id="sidebar">
            <div class="sidebar-header">
                <div class="logo">
                    <i class="fas fa-brain"></i>
                    <span>IntelliQuery</span>
                </div>
                <button class="theme-toggle" onclick="toggleTheme()" title="Toggle theme">
                    <i class="fas fa-moon" id="themeIcon"></i>
                </button>
            </div>
            
            <button class="new-chat-btn" onclick="startNewChat()">
                <i class="fas fa-plus"></i>
                New Chat
            </button>
            
            <button class="delete-history-btn" onclick="deleteHistory()">
                <i class="fas fa-trash"></i>
                Delete History
            </button>
            
            <div class="chat-history" id="chatHistory">
                {% for session_id, session in chat_sessions.items() %}
                <div class="chat-session {{ 'active' if session_id == current_session_id else '' }}" 
                     onclick="loadChatSession('{{ session_id }}')">
                    <div class="session-title">{{ session.get('document', 'New Chat') }}</div>
                    <div class="session-meta">{{ session.get('created_at', '') }}</div>
                </div>
                {% endfor %}
            </div>
        </div>
        
        <!-- Main Content -->
        <div class="main-content">
            <!-- Mobile Header -->
            <div class="mobile-header">
                <button class="menu-toggle" onclick="toggleSidebar()">
                    <i class="fas fa-bars"></i>
                </button>
                <div class="logo">
                    <i class="fas fa-brain"></i>
                    <span>IntelliQuery</span>
                </div>
                <button class="theme-toggle" onclick="toggleTheme()">
                    <i class="fas fa-moon" id="mobileThemeIcon"></i>
                </button>
            </div>
            
            <!-- Main Header -->
            {% if document_loaded %}
            <div class="main-header">
                <div class="document-status">
                    <div class="status-indicator"></div>
                    <div class="document-info">
                        <h3>{{ filename }}</h3>
                        <p>{{ chunk_count }} sections • Uploaded {{ upload_time }}</p>
                    </div>
                </div>
                <div class="header-actions">
                    <button class="btn-secondary" onclick="showUploadModal()">
                        <i class="fas fa-upload"></i> New Document
                    </button>
                    <button class="btn-secondary" onclick="exportChat()">
                        <i class="fas fa-download"></i> Export
                    </button>
                </div>
            </div>
            {% endif %}
            
            <!-- Chat Area -->
            <div class="chat-area">
                {% if document_loaded %}
                <div class="messages-container" id="messagesContainer">
                    {% if current_session_id and chat_sessions.get(current_session_id) %}
                        {% for msg in chat_sessions[current_session_id]['messages'] %}
                        <div class="message message-{{ msg.sender }}">
                            <div class="message-bubble">
                                {{ msg.message }}
                                {% if msg.response_data %}
                                    <div class="response-data">{{ msg.response_data.get('justification', '') }}</div>
                                {% endif %}
                            </div>
                            <div class="message-time">{{ msg.timestamp }}</div>
                        </div>
                        {% endfor %}
                    {% else %}
                    <div class="empty-state">
                        <div class="empty-icon">
                            <i class="fas fa-comments"></i>
                        </div>
                        <h3>Start a conversation</h3>
                        <p>Ask me anything about your PDF document</p>
                    </div>
                    {% endif %}
                </div>
                
                <div class="input-area">
                    <div class="input-container">
                        <textarea id="messageInput" class="message-input" 
                                placeholder="Ask anything about your document..." 
                                rows="1" onkeydown="handleKeyDown(event)"></textarea>
                        <button class="send-button" id="sendButton" onclick="sendMessage()">
                            <i class="fas fa-paper-plane"></i>
                        </button>
                    </div>
                </div>
                {% else %}
                <div class="empty-state">
                    <div class="empty-icon">
                        <i class="fas fa-file-pdf"></i>
                    </div>
                    <h3>Welcome to IntelliQuery</h3>
                    <p>Upload a PDF document to start chatting with AI</p>
                    <button class="btn-primary" onclick="showUploadModal()" style="margin-top: 24px;">
                        <i class="fas fa-upload"></i> Upload PDF
                    </button>
                </div>
                {% endif %}
            </div>
        </div>
    </div>
    
    <!-- Upload Modal -->
    <div class="upload-overlay hidden" id="uploadOverlay">
        <div class="upload-modal">
            <h2 style="margin-bottom: 24px; text-align: center;">Upload PDF Document</h2>
            
            <form id="uploadForm" enctype="multipart/form-data">
                <div class="upload-area" id="uploadArea" onclick="document.getElementById('fileInput').click()">
                    <div class="upload-icon">
                        <i class="fas fa-cloud-upload-alt"></i>
                    </div>
                    <div class="upload-text">Drop your PDF here or click to browse</div>
                    <div class="upload-subtext">Maximum file size: 200MB</div>
                    <input type="file" id="fileInput" class="file-input" accept=".pdf" required>
                </div>
            </form>
            
            <div class="modal-actions">
                <button class="btn-secondary" onclick="hideUploadModal()">Cancel</button>
                <button class="btn-primary" onclick="uploadFile()" id="uploadButton">Upload</button>
            </div>
        </div>
    </div>

    <!-- Loading Indicator -->
    <div class="loading-indicator hidden" id="loadingIndicator">
        <div class="spinner"></div>
        <span>AI is thinking...</span>
    </div>
    
    <script>
        // Global state
        let currentTheme = localStorage.getItem('theme') || 'light';
        let currentSessionId = '{{ current_session_id }}';
        let isUploading = false;
        
        // Initialize theme
        document.documentElement.setAttribute('data-theme', currentTheme);
        updateThemeIcon();
        
        function updateThemeIcon() {
            const icon = currentTheme === 'dark' ? 'fa-sun' : 'fa-moon';
            document.getElementById('themeIcon').className = `fas ${icon}`;
            const mobileIcon = document.getElementById('mobileThemeIcon');
            if (mobileIcon) mobileIcon.className = `fas ${icon}`;
        }
        
        function toggleTheme() {
            currentTheme = currentTheme === 'light' ? 'dark' : 'light';
            document.documentElement.setAttribute('data-theme', currentTheme);
            localStorage.setItem('theme', currentTheme);
            updateThemeIcon();
        }
        
        function toggleSidebar() {
            document.getElementById('sidebar').classList.toggle('open');
        }
        
        function showUploadModal() {
            document.getElementById('uploadOverlay').classList.remove('hidden');
        }
        
        function hideUploadModal() {
            document.getElementById('uploadOverlay').classList.add('hidden');
            document.getElementById('fileInput').value = '';
        }
        
        function startNewChat() {
            // Clear current document and show upload modal
            fetch('/clear', { method: 'POST' })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showUploadModal();
                    }
                });
        }
        
        function deleteHistory() {
            if (confirm('Are you sure you want to delete all chat history? This action cannot be undone.')) {
                fetch('/delete-history', { method: 'POST' })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            showNotification('Chat history deleted successfully', 'success');
                            location.reload();
                        } else {
                            showNotification('Failed to delete history', 'error');
                        }
                    })
                    .catch(error => {
                        showNotification('Error deleting history', 'error');
                    });
            }
        }
        
        function loadChatSession(sessionId) {
            fetch('/load-session', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: sessionId })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    location.reload();
                }
            });
        }
        
        function uploadFile() {
            const fileInput = document.getElementById('fileInput');
            const file = fileInput.files[0];
            
            if (!file) {
                showNotification('Please select a file', 'warning');
                return;
            }
            
            if (file.size > 200 * 1024 * 1024) {
                showNotification('File size must be less than 200MB', 'error');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            isUploading = true;
            document.getElementById('uploadButton').disabled = true;
            document.getElementById('uploadButton').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';
            
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showSuccessTick();
                    showNotification('File uploaded successfully!', 'success');
                    setTimeout(() => {
                        hideUploadModal();
                        location.reload();
                    }, 2000);
                } else {
                    showNotification(data.error || 'Upload failed', 'error');
                }
            })
            .catch(error => {
                showNotification('Upload failed: ' + error.message, 'error');
            })
            .finally(() => {
                isUploading = false;
                document.getElementById('uploadButton').disabled = false;
                document.getElementById('uploadButton').innerHTML = '<i class="fas fa-upload"></i> Upload';
            });
        }
        
        function handleKeyDown(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                sendMessage();
            }
        }
        
        function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message to chat
            addMessageToChat(message, 'user');
            input.value = '';
            
            // Show loading
            showLoading();
            
            // Send to server
            fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: message })
            })
            .then(response => response.json())
            .then(data => {
                hideLoading();
                if (data.success) {
                    addMessageToChat(data.response.justification || data.response, 'assistant');
                } else {
                    addMessageToChat('Error: ' + data.error, 'assistant');
                }
            })
            .catch(error => {
                hideLoading();
                addMessageToChat('Network error: ' + error.message, 'assistant');
            });
        }
        
        function addMessageToChat(message, sender) {
            const container = document.getElementById('messagesContainer');
            const emptyState = container.querySelector('.empty-state');
            
            if (emptyState) {
                emptyState.remove();
            }
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message message-${sender}`;
            
            const now = new Date();
            const time = now.toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            
            messageDiv.innerHTML = `
                <div class="message-bubble">${message}</div>
                <div class="message-time">${time}</div>
            `;
            
            container.appendChild(messageDiv);
            container.scrollTop = container.scrollHeight;
        }
        
        function showLoading() {
            const container = document.getElementById('messagesContainer');
            const loadingDiv = document.createElement('div');
            loadingDiv.id = 'tempLoading';
            loadingDiv.className = 'loading-indicator';
            loadingDiv.innerHTML = '<div class="spinner"></div><span>AI is thinking...</span>';
            container.appendChild(loadingDiv);
            container.scrollTop = container.scrollHeight;
        }
        
        function hideLoading() {
            const loading = document.getElementById('tempLoading');
            if (loading) loading.remove();
        }
        
        function showNotification(message, type) {
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.textContent = message;
            
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.style.animation = 'slideInRight 0.3s ease-out reverse';
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        }
        
        function showSuccessTick() {
            const tick = document.createElement('div');
            tick.className = 'success-tick';
            tick.innerHTML = '<i class="fas fa-check"></i>';
            
            document.body.appendChild(tick);
            
            setTimeout(() => {
                tick.remove();
            }, 1500);
        }
        
        function exportChat() {
            // Implementation for chat export
            showNotification('Export feature coming soon!', 'warning');
        }
        
        // Auto-resize textarea
        document.getElementById('messageInput')?.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 120) + 'px';
        });
        
        // Drag and drop for upload
        const uploadArea = document.getElementById('uploadArea');
        if (uploadArea) {
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                uploadArea.addEventListener(eventName, preventDefaults, false);
            });
            
            function preventDefaults(e) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            ['dragenter', 'dragover'].forEach(eventName => {
                uploadArea.addEventListener(eventName, () => uploadArea.classList.add('dragover'), false);
            });
            
            ['dragleave', 'drop'].forEach(eventName => {
                uploadArea.addEventListener(eventName, () => uploadArea.classList.remove('dragover'), false);
            });
            
            uploadArea.addEventListener('drop', handleDrop, false);
            
            function handleDrop(e) {
                const dt = e.dataTransfer;
                const files = dt.files;
                
                if (files.length > 0) {
                    document.getElementById('fileInput').files = files;
                }
            }
        }
        
        // Focus message input on load
        document.addEventListener('DOMContentLoaded', function() {
            const messageInput = document.getElementById('messageInput');
            if (messageInput) {
                messageInput.focus();
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/chat')
def index():
    global current_session_id
    if current_document['chunks'] is not None and current_session_id is None:
        get_or_create_session()
    
    response = app.response_class(
        render_template_string(HTML_TEMPLATE, 
                              document_loaded=current_document['chunks'] is not None,
                              filename=current_document['filename'],
                              upload_time=current_document.get('upload_time', 'Unknown'),
                              chunk_count=current_document.get('chunk_count', 0),
                              chat_sessions=chat_sessions,
                              current_session_id=current_session_id)
    )
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if request.is_json:
            return jsonify({'error': 'Use multipart/form-data for file uploads'}), 400
            
        if 'file' not in request.files:
            return jsonify({'error': 'No file selected'}), 400
        
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({'error': 'Please upload a valid PDF file'}), 400
        
        if file.content_length and file.content_length > MAX_FILE_SIZE:
            return jsonify({'error': 'File size exceeds 200MB limit'}), 400
        
        # Clear previous document first
        current_document.update({
            'chunks': None,
            'embeddings': None,
            'index': None,
            'model_st': None,
            'filename': None,
            'upload_time': None,
            'chunk_count': 0
        })
        
        # Save file to temporary location and process it
        temp_file_path = None
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file_path = temp_file.name
            
            # Save the uploaded file
            file.save(temp_file_path)
            temp_file.close()  # Explicitly close the file
            
            # Add a small delay to ensure file is released
            time.sleep(0.1)
            gc.collect()  # Force garbage collection
            
            logger.info(f"Processing new PDF: {file.filename}")
            
            # Process the PDF (file is now closed and released)
            text = extract_text_from_pdf(temp_file_path)
            chunks, embeddings, index, model_st = create_document_embeddings(text)
            
            # Store in global variables
            current_document.update({
                'chunks': chunks,
                'embeddings': embeddings,
                'index': index,
                'model_st': model_st,
                'filename': secure_filename(file.filename),
                'upload_time': time.strftime('%H:%M:%S'),
                'chunk_count': len(chunks)
            })
            
            logger.info(f"Successfully processed PDF: {file.filename} with {len(chunks)} chunks")
            
            # Create new chat session
            global current_session_id
            current_session_id = str(int(time.time()))
            chat_sessions[current_session_id] = {
                'messages': [],
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'document': secure_filename(file.filename)
            }
            
            logger.info(f"Successfully processed PDF: {file.filename} with {len(chunks)} chunks")
            return jsonify({
                'success': True, 
                'message': f'PDF "{file.filename}" uploaded successfully!',
                'chunks': len(chunks)
            })
            
        finally:
            # Clean up temp file safely with retry mechanism
            if temp_file_path and os.path.exists(temp_file_path):
                max_retries = 5
                for attempt in range(max_retries):
                    try:
                        time.sleep(0.1 * (attempt + 1))  # Increasing delay
                        os.unlink(temp_file_path)
                        break  # Success, exit retry loop
                    except PermissionError as e:
                        if attempt == max_retries - 1:
                            logger.warning(f"Could not delete temp file after {max_retries} attempts: {temp_file_path}")
                            # File will be cleaned up by system temp folder cleanup
                        else:
                            logger.debug(f"Retry {attempt + 1}/{max_retries} to delete temp file: {e}")
                            gc.collect()  # Force garbage collection between retries
                    except Exception as cleanup_error:
                        logger.warning(f"Unexpected error deleting temp file {temp_file_path}: {cleanup_error}")
                        break
        
    except Exception as e:
        logger.error(f"Upload error: {traceback.format_exc()}")
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/upload-url', methods=['POST'])
def upload_url():
    try:
        # Import the download function from app.py
        from app import download_and_extract_text
        
        pdf_url = request.form.get('pdf_url', '').strip()
        if not pdf_url:
            flash('Please enter a valid PDF URL')
            return redirect(url_for('index'))
        
        # Clear previous document first
        current_document.update({
            'chunks': None,
            'embeddings': None,
            'index': None,
            'model_st': None,
            'filename': None,
            'upload_time': None,
            'chunk_count': 0
        })
        
        logger.info(f"Processing PDF from URL: {pdf_url}")
        
        # Download and process the PDF from URL
        text = download_and_extract_text(pdf_url)
        chunks, embeddings, index, model_st = create_document_embeddings(text)
        
        # Extract filename from URL
        filename = pdf_url.split('/')[-1].split('?')[0]
        if not filename.endswith('.pdf'):
            filename = 'document.pdf'
        
        # Store in global variables
        current_document.update({
            'chunks': chunks,
            'embeddings': embeddings,
            'index': index,
            'model_st': model_st,
            'filename': secure_filename(filename),
            'upload_time': time.strftime('%H:%M:%S'),
            'chunk_count': len(chunks)
        })
        
        logger.info(f"Successfully processed PDF from URL with {len(chunks)} chunks")
        
        flash(f'✅ PDF "{filename}" downloaded and processed successfully! Ready for AI analysis with {len(chunks)} text sections.')
        return redirect(url_for('index'))
        
    except Exception as e:
        flash(f'❌ Error processing PDF from URL: {str(e)}')
        logger.error(f"URL upload error: {traceback.format_exc()}")
        return redirect(url_for('index'))

@app.route('/ask', methods=['POST'])
def ask_question():
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'error': 'Please enter a question'}), 400
        
        if current_document['chunks'] is None:
            return jsonify({'error': 'Please upload a PDF first'}), 400
        
        # Check API key before processing
        api_key, key_source = get_api_key()
        if not api_key:
            return jsonify({
                'error': 'No API key configured. Please set GROQ_API_KEY in your .env file.'
            }), 500
        
        # Get or create session
        session_id = get_or_create_session()
        
        logger.info(f"Answering question for PDF: {current_document['filename']}")
        logger.debug(f"Question: {question}")
        
        # Add user message to session
        add_message_to_session(session_id, question, 'user')
        
        # Generate response
        response = generate_response(
            question, 
            current_document['chunks'],
            current_document['embeddings'],
            current_document['index'],
            current_document['model_st']
        )
        
        # Parse the JSON response
        try:
            response_data = json.loads(response)
            # Add assistant message to session
            add_message_to_session(session_id, response_data.get('justification', response), 'assistant', response_data)
            return jsonify({'success': True, 'response': response_data})
        except json.JSONDecodeError:
            # Add assistant message to session
            add_message_to_session(session_id, response, 'assistant')
            return jsonify({
                'success': True,
                'response': {
                    'justification': response
                }
            })
            
    except Exception as e:
        error_msg = str(e).lower()
        
        # Provide specific error messages for common API issues
        if 'api' in error_msg and 'key' in error_msg:
            return jsonify({
                'error': 'API key error. Please check your GROQ_API_KEY in the .env file.'
            }), 500
        elif 'authentication' in error_msg or 'unauthorized' in error_msg:
            return jsonify({
                'error': 'Authentication failed. Please verify your API key is correct.'
            }), 500
        elif 'rate limit' in error_msg or 'quota' in error_msg:
            return jsonify({
                'error': 'API rate limit exceeded. Please try again later.'
            }), 500
        elif 'network' in error_msg or 'connection' in error_msg:
            return jsonify({
                'error': 'Network error. Please check your internet connection.'
            }), 500
        else:
            print(f"Question processing error: {traceback.format_exc()}")
            return jsonify({'error': f'Error processing question: {str(e)}'}), 500

@app.route('/new-chat', methods=['POST'])
def new_chat():
    try:
        global current_session_id
        if current_document['chunks'] is not None:
            current_session_id = str(int(time.time()))
            chat_sessions[current_session_id] = {
                'messages': [],
                'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
                'document': current_document['filename']
            }
        return jsonify({'success': True, 'session_id': current_session_id})
    except Exception as e:
        return jsonify({'error': f'Error creating new chat: {str(e)}'}), 500

@app.route('/load-session', methods=['POST'])
def load_session():
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if session_id in chat_sessions:
            global current_session_id
            current_session_id = session_id
            return jsonify({'success': True})
        else:
            return jsonify({'error': 'Session not found'}), 404
    except Exception as e:
        return jsonify({'error': f'Error loading session: {str(e)}'}), 500

@app.route('/clear', methods=['POST'])
def clear_document():
    try:
        global current_session_id
        current_document.update({
            'chunks': None, 'embeddings': None, 'index': None, 
            'model_st': None, 'filename': None, 'upload_time': None, 'chunk_count': 0
        })
        current_session_id = None
        return jsonify({'success': True, 'message': 'Document cleared successfully'})
    except Exception as e:
        return jsonify({'error': f'Error clearing document: {str(e)}'}), 500

@app.route('/delete-history', methods=['POST'])
def delete_history():
    try:
        global current_session_id
        chat_sessions.clear()
        current_session_id = None
        return jsonify({'success': True, 'message': 'Chat history deleted successfully'})
    except Exception as e:
        return jsonify({'error': f'Error deleting history: {str(e)}'}), 500

@app.route('/status')
def get_status():
    """Endpoint to check current document and API status"""
    api_key, key_source = get_api_key()
    
    return jsonify({
        'document_loaded': current_document['chunks'] is not None,
        'filename': current_document['filename'],
        'chunks_count': len(current_document['chunks']) if current_document['chunks'] else 0,
        'upload_time': current_document.get('upload_time', None),
        'model_ready': current_document['model_st'] is not None,
        'api_configured': api_key is not None,
        'api_key_source': key_source,
        'api_key_preview': f"{api_key[:8]}..." if api_key else None,
        'system_ready': api_key is not None and current_document['chunks'] is not None
    })

@app.route('/test-api')
def test_api():
    """Test API key configuration"""
    try:
        api_key, key_source = get_api_key()
        
        if not api_key:
            return jsonify({
                'success': False,
                'error': 'No API key configured',
                'help': 'Set GROQ_API_KEY in your .env file'
            }), 400
        
        # Basic format validation
        valid_format = api_key.startswith('gsk_')
        
        return jsonify({
            'success': True,
            'api_key_source': key_source,
            'api_key_preview': f"{api_key[:8]}..." if len(api_key) > 8 else "short_key",
            'valid_format': valid_format,
            'message': 'API key found and appears valid' if valid_format else 'API key found but format unusual'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error testing API: {str(e)}'
        }), 500

import io
import contextlib
# Implement verify_bearer_token in web_app.py
def verify_bearer_token(authorization: str):
    """
    Verifies Bearer token from Authorization header.
    Requires HACKRX_BEARER_TOKEN environment variable to be set.
    """
    required_token = os.environ.get('HACKRX_BEARER_TOKEN')
    if not required_token:
        return False, "HACKRX_BEARER_TOKEN environment variable is not configured."
    
    if not authorization or not authorization.startswith('Bearer '):
        return False, "Missing or invalid Authorization header."
    
    token = authorization.split('Bearer ')[-1].strip()
    if token != required_token:
        return False, "Invalid Bearer token."
    return True, None

# Implement rate limiting for web_app.py
RATE_LIMIT_WINDOW = 60  # 1 minute window
RATE_LIMIT_REQUESTS = 10  # 10 requests per window
request_counts = defaultdict(list)

def check_rate_limit(client_ip: str) -> bool:
    """Simple rate limiting - 10 requests per minute per IP"""
    now = time.time()
    # Clean old requests
    request_counts[client_ip] = [req_time for req_time in request_counts[client_ip] 
                               if now - req_time < RATE_LIMIT_WINDOW]
    
    if len(request_counts[client_ip]) >= RATE_LIMIT_REQUESTS:
        return False
    
    request_counts[client_ip].append(now)
    return True

@app.route('/hackrx/run', methods=['POST'])
def hackrx_run():
    """
    HackRx compliant endpoint for testing the system with standardized input/output.
    This is the main endpoint used for the hackathon submission testing.
    """
    try:
        # Get client IP for rate limiting
        client_ip = request.remote_addr
        if not check_rate_limit(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return jsonify({
                "success": False, 
                "error": "Rate limit exceeded. Please try again later."
            }), 429
        
        # Verify Bearer token
        authorization = request.headers.get('Authorization')
        ok, err = verify_bearer_token(authorization)
        if not ok:
            logger.warning(f"Bearer token verification failed: {err}")
            return jsonify({"success": False, "error": err}), 401

        # Get request data
        if not request.is_json:
            logger.warning("Request body is not JSON")
            return jsonify({
                "success": False, 
                "error": "Request body must be JSON."
            }), 400
            
        data = request.get_json()
        documents = data.get('documents')
        questions = data.get('questions')
        
        # Validate input parameters
        if not documents:
            logger.warning("Request missing documents parameter")
            return jsonify({
                "success": False, 
                "error": "Missing 'documents' parameter. Please provide a URL to the document."
            }), 400
        
        if not questions:
            logger.warning("Request missing questions parameter")
            return jsonify({
                "success": False, 
                "error": "Missing 'questions' parameter. Please provide a list of questions."
            }), 400
        
        if not isinstance(questions, list) or len(questions) == 0:
            logger.warning("Invalid questions format")
            return jsonify({
                "success": False, 
                "error": "Questions must be a non-empty list."
            }), 400
        
        # Validate URL format
        if not documents.startswith(('http://', 'https://')):
            logger.warning(f"Invalid document URL format: {documents}")
            return jsonify({
                "success": False, 
                "error": "Documents parameter must be a valid URL."
            }), 400

        # Download and extract text from the document URL
        logger.info(f"Processing document URL: {documents}")
        
        # Import the download function if needed
        from app import download_and_extract_text
        
        # Process document
        text = download_and_extract_text(documents)
        logger.info(f"Extracted {len(text)} characters from document")
        
        chunks, embeddings, index, model_st = create_document_embeddings(text)
        logger.info(f"Created {len(chunks)} chunks for processing")

        # Generate answers for each question
        answers = []
        for i, q in enumerate(questions):
            logger.info(f"Processing question {i+1}/{len(questions)}: {q[:50]}...")
            response = generate_response(q, chunks, embeddings, index, model_st)
            try:
                result = json.loads(response)
                # Extract the justification as the main answer
                answer = result.get('justification', '')
                if not answer:
                    # Fallback to decision + justification format
                    decision = result.get('decision', '')
                    justification = result.get('justification', '')
                    amount = result.get('amount', '')
                    
                    if amount and amount != 'null':
                        answer = f"{justification} Amount: {amount}"
                    else:
                        answer = justification or decision or str(result)
            except Exception:
                # If JSON parsing fails, use the raw response
                answer = response
            
            answers.append(answer)
            
            # Force garbage collection after each question to manage memory
            if i % 3 == 0:  # Every 3 questions
                gc.collect()
        
        # Return the final response
        return jsonify({
            "success": True,
            "answers": answers
        })
        
    except Exception as e:
        logger.error(f"Error in hackrx_run: {str(e)}\n{traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    # Production configuration
    app.run(
        host='0.0.0.0', 
        port=port, 
        debug=False,
        threaded=True
    )
