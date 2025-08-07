from flask import Flask, request, jsonify, render_template_string, flash, redirect, url_for
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
    Get API key with fallback mechanism for backward compatibility
    Supports both OPENROUTER_API_KEY and OPENAI_API_KEY
    """
    # Primary: OpenRouter API key (preferred)
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if api_key:
        return api_key, 'OPENROUTER_API_KEY'
    
    # Fallback: OpenAI API key (for backward compatibility)
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key:
        logger.warning("Using OPENAI_API_KEY. Consider renaming to OPENROUTER_API_KEY")
        return api_key, 'OPENAI_API_KEY'
    
    return None, None

def validate_api_configuration():
    """Validate API configuration at startup"""
    api_key, key_source = get_api_key()
    
    if not api_key:
        logger.error("No API key found!")
        logger.info("Please set one of the following environment variables:")
        logger.info("- OPENROUTER_API_KEY (recommended)")
        logger.info("- OPENAI_API_KEY (for backward compatibility)")
        logger.info("Check your .env file or environment variables")
        return False
    
    logger.info(f"API key found: {key_source}")
    
    # Validate key format
    if not api_key.startswith(('sk-', 'or-')):
        logger.warning("API key format unusual (should start with 'sk-' or 'or-')")
    
    return True

import secrets

# Validate API configuration at startup
if not validate_api_configuration():
    logger.warning("API configuration validation failed")
    logger.info("HINT: Create a .env file with:")
    logger.info("OPENROUTER_API_KEY=your_actual_api_key_here")
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
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB max file size

app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Global variables to store processed document data
current_document = {
    'chunks': None,
    'embeddings': None,
    'index': None,
    'model_st': None,
    'filename': None,
    'upload_time': None,
    'chunk_count': 0
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# HTML Template as string (for better performance)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI PDF Chat</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .app-container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1);
            width: 100%;
            max-width: 800px;
            overflow: hidden;
            animation: slideUp 0.6s ease-out;
        }
        
        @keyframes slideUp {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }
        
        .header::before {
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: pulse 3s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 0.5; }
            50% { transform: scale(1.1); opacity: 0.8; }
        }
        
        .header h1 {
            font-size: 2.5rem;
            font-weight: 600;
            margin: 0;
            position: relative;
            z-index: 2;
        }
        
        .header p {
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-weight: 300;
            position: relative;
            z-index: 2;
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
    <div class="app-container">
        <div class="header">
            <h1>🤖 AI PDF Chat</h1>
            <p>Upload your PDF and chat with it using AI</p>
        </div>

        <div class="content">
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    {% for message in messages %}
                        <div class="flash-message">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}

            {% if not document_loaded %}
            <div class="upload-section">
                <div class="upload-tabs">
                    <button class="upload-tab active" onclick="switchTab('file')">Upload PDF</button>
                    <button class="upload-tab" onclick="switchTab('url')">PDF URL</button>
                </div>
                
                <form action="/upload" method="post" enctype="multipart/form-data" id="file-content" class="upload-content active">
                    <div class="upload-area" onclick="document.getElementById('fileInput').click()">
                        <div class="upload-icon">📄</div>
                        <div class="upload-text">Drop your PDF here or click to browse</div>
                        <div class="upload-subtext">Maximum file size: 16MB</div>
                        <input type="file" name="file" accept=".pdf" class="file-input" id="fileInput" required>
                    </div>
                    <button type="submit" class="btn">✨ Upload & Analyze</button>
                </form>
                
                <form action="/upload-url" method="post" id="url-content" class="upload-content">
                    <div class="url-input-container">
                        <div class="upload-icon">🔗</div>
                        <div class="upload-text">Enter PDF URL</div>
                        <input type="url" name="pdf_url" class="url-input" id="pdfUrlInput" placeholder="https://example.com/document.pdf" required>
                    </div>
                    <button type="submit" class="btn">🌐 Fetch & Analyze</button>
                </form>
            </div>
            {% endif %}

            {% if document_loaded %}
            <div class="chat-section">
                <div class="document-info">
                    <div class="doc-details">
                        <h3><span class="status-dot"></span>{{ filename }}</h3>
                        <p>Uploaded at {{ upload_time }} • {{ chunk_count }} sections processed</p>
                    </div>
                    <button class="new-doc-btn" onclick="clearDocument()">📎 New Document</button>
                </div>

                <div class="chat-container" id="chatContainer">
                    <div class="empty-state">
                        <div class="empty-icon">💬</div>
                        <h3>Ready to chat!</h3>
                        <p>Ask me anything about your PDF document</p>
                    </div>
                </div>

                <div id="loading" class="loading" style="display: none;">
                    <div class="spinner"></div>
                    <p>AI is thinking...</p>
                </div>

                <div class="input-section">
                    <div class="input-container">
                        <input type="text" id="questionInput" class="question-input" 
                               placeholder="Ask anything about your document..." 
                               onkeypress="handleKeyPress(event)">
                        <button class="send-btn" onclick="askQuestion()">➤</button>
                    </div>
                    
                    <div class="suggestions">
                        <button class="suggestion" onclick="askSampleQuestion('What is this document about?')">
                            📋 What's this about?
                        </button>
                        <button class="suggestion" onclick="askSampleQuestion('Summarize the key points')">
                            📝 Key points
                        </button>
                        <button class="suggestion" onclick="askSampleQuestion('Any important dates or deadlines?')">
                            📅 Important dates
                        </button>
                    </div>
                </div>
            </div>
            {% endif %}
        </div>
    </div>

    <script>
        function switchTab(tabId) {
            // Hide all content sections
            document.querySelectorAll('.upload-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Deactivate all tabs
            document.querySelectorAll('.upload-tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Activate selected tab and content
            document.querySelector(`.upload-tab[onclick="switchTab('${tabId}')"]`).classList.add('active');
            document.getElementById(`${tabId}-content`).classList.add('active');
        }

        function handleKeyPress(event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                askQuestion();
            }
        }

        function askSampleQuestion(question) {
            document.getElementById('questionInput').value = question;
            askQuestion();
        }

        function askQuestion() {
            const questionInput = document.getElementById('questionInput');
            const question = questionInput.value.trim();
            
            if (!question) {
                showNotification('Please enter a question', 'warning');
                return;
            }

            addMessageToChat(question, 'user');
            questionInput.value = '';
            document.getElementById('loading').style.display = 'block';
            questionInput.disabled = true;

            fetch('/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: question })
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('loading').style.display = 'none';
                questionInput.disabled = false;
                questionInput.focus();
                
                if (data.success) {
                    addResponseToChat(data.response);
                } else {
                    addErrorToChat(data.error);
                }
            })
            .catch(error => {
                document.getElementById('loading').style.display = 'none';
                questionInput.disabled = false;
                questionInput.focus();
                addErrorToChat('Network error: ' + error.message);
            });
        }

        function addMessageToChat(message, sender) {
            const chatContainer = document.getElementById('chatContainer');
            
            if (chatContainer.querySelector('.empty-state')) {
                chatContainer.innerHTML = '';
            }
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}-message`;
            
            if (sender === 'user') {
                messageDiv.innerHTML = `<div class="user-bubble">${message}</div>`;
            }
            
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function addResponseToChat(response) {
            const chatContainer = document.getElementById('chatContainer');
            
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message bot-message';
            
            const decision = response.decision ? response.decision : '';
            const justification = response.justification || 'No explanation provided.';
            
            let badgeClass = '';
            if (decision.toLowerCase().includes('covered') && !decision.toLowerCase().includes('not')) {
                badgeClass = decision.toLowerCase().includes('partially') ? 'partial' : 'covered';
            } else if (decision.toLowerCase().includes('not covered')) {
                badgeClass = 'not-covered';
            }
            
            let responseHtml = `
                <div class="bot-bubble">
                    ${decision ? `<div class="decision-badge ${badgeClass}">${decision}</div>` : ''}
                    <div>${justification}</div>
                </div>
            `;
            
            messageDiv.innerHTML = responseHtml;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function addErrorToChat(error) {
            const chatContainer = document.getElementById('chatContainer');
            
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message bot-message';
            messageDiv.innerHTML = `
                <div class="bot-bubble" style="border-left: 4px solid #ef4444;">
                    <div style="color: #ef4444; font-weight: 600; margin-bottom: 10px;">❌ Error</div>
                    <div>${error}</div>
                </div>
            `;
            
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }

        function clearDocument() {
            if (confirm('Upload a new document? This will clear the current conversation.')) {
                fetch('/clear', { method: 'POST', headers: { 'Content-Type': 'application/json' } })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        showNotification('Document cleared!', 'success');
                        setTimeout(() => location.reload(), 1000);
                    } else {
                        showNotification('Error: ' + data.error, 'error');
                    }
                })
                .catch(error => showNotification('Error: ' + error.message, 'error'));
            }
        }

        function showNotification(message, type) {
            const notification = document.createElement('div');
            notification.className = `notification ${type}`;
            notification.textContent = message;
            
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.style.animation = 'slideIn 0.3s ease-out reverse';
                setTimeout(() => notification.remove(), 300);
            }, 3000);
        }

        // File upload handling
        document.addEventListener('DOMContentLoaded', function() {
            const fileInput = document.getElementById('fileInput');
            const fileForm = document.getElementById('file-content');
            const urlForm = document.getElementById('url-content');
            
            if (fileInput) {
                fileInput.addEventListener('change', function() {
                    const file = this.files[0];
                    if (file) {
                        if (file.type !== 'application/pdf') {
                            showNotification('Please select a PDF file', 'warning');
                            this.value = '';
                            return;
                        }
                        if (file.size > 16 * 1024 * 1024) {
                            showNotification('File size must be less than 16MB', 'warning');
                            this.value = '';
                            return;
                        }
                        
                        // Show file selected feedback
                        const uploadArea = document.querySelector('.upload-area');
                        const uploadText = document.querySelector('.upload-text');
                        uploadText.textContent = `Selected: ${file.name}`;
                        uploadArea.style.borderColor = '#10b981';
                        uploadArea.style.background = 'linear-gradient(145deg, #dcfce7 0%, #bbf7d0 100%)';
                    }
                });
                
                fileForm.addEventListener('submit', function() {
                    const submitBtn = this.querySelector('.btn');
                    submitBtn.innerHTML = '⏳ Processing...';
                    submitBtn.disabled = true;
                });
            }
            
            if (urlForm) {
                urlForm.addEventListener('submit', function() {
                    const submitBtn = this.querySelector('.btn');
                    submitBtn.innerHTML = '⏳ Processing...';
                    submitBtn.disabled = true;
                });
            }
            
            // Focus on question input if document is loaded
            const questionInput = document.getElementById('questionInput');
            if (questionInput) {
                questionInput.focus();
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    # Add cache-busting headers
    response = app.response_class(
        render_template_string(HTML_TEMPLATE, 
                              document_loaded=current_document['chunks'] is not None,
                              filename=current_document['filename'],
                              upload_time=current_document.get('upload_time', 'Unknown'),
                              chunk_count=current_document.get('chunk_count', 0))
    )
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            flash('No file selected')
            return redirect(url_for('index'))
        
        file = request.files['file']
        if file.filename == '' or not allowed_file(file.filename):
            flash('Please upload a valid PDF file')
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
            
            flash(f'✅ PDF "{file.filename}" uploaded and processed successfully! Ready for AI analysis with {len(chunks)} text sections.')
            return redirect(url_for('index'))
            
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
        flash(f'❌ Error processing file: {str(e)}')
        logger.error(f"Upload error: {traceback.format_exc()}")
        return redirect(url_for('index'))

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
                'error': 'No API key configured. Please set OPENROUTER_API_KEY in your .env file.'
            }), 500
        
        logger.info(f"Answering question for PDF: {current_document['filename']}")
        logger.debug(f"Question: {question}")
        logger.debug(f"Using {len(current_document['chunks'])} chunks from document")
        logger.debug(f"API Key source: {key_source}")
        
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
            # Add document info to response for debugging
            response_data['_debug_info'] = {
                'document': current_document['filename'],
                'chunks_count': len(current_document['chunks']),
                'api_key_source': key_source
            }
            return jsonify({'success': True, 'response': response_data})
        except json.JSONDecodeError:
            return jsonify({
                'success': True,
                'response': {
                    'decision': '',
                    'justification': response,
                    '_debug_info': {
                        'document': current_document['filename'],
                        'chunks_count': len(current_document['chunks']),
                        'api_key_source': key_source
                    }
                }
            })
            
    except Exception as e:
        error_msg = str(e).lower()
        
        # Provide specific error messages for common API issues
        if 'api' in error_msg and 'key' in error_msg:
            return jsonify({
                'error': 'API key error. Please check your OPENROUTER_API_KEY in the .env file.'
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

@app.route('/clear', methods=['POST'])
def clear_document():
    try:
        current_document.update({
            'chunks': None, 'embeddings': None, 'index': None, 
            'model_st': None, 'filename': None, 'upload_time': None, 'chunk_count': 0
        })
        return jsonify({'success': True, 'message': 'Document cleared successfully'})
    except Exception as e:
        return jsonify({'error': f'Error clearing document: {str(e)}'}), 500

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
                'help': 'Set OPENROUTER_API_KEY in your .env file'
            }), 400
        
        # Basic format validation
        valid_format = api_key.startswith(('sk-', 'or-'))
        
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
    app.run(host='0.0.0.0', port=port, debug=False)
