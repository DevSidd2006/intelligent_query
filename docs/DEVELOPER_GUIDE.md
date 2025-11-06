# 🛠️ Developer Guide - Intelligent Query System

This guide provides comprehensive information for developers who want to understand, modify, extend, or contribute to the Intelligent Query PDF Q&A System.

## 🏗️ Architecture Overview

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Client Layer                             │
├─────────────────────┬───────────────────────────────────────┤
│   Web Interface     │           API Clients                 │
│   (Flask + HTML)    │      (REST API consumers)             │
└─────────────────────┴───────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                 Application Layer                           │
├─────────────────────┬───────────────────────────────────────┤
│   Flask Web App     │         FastAPI Server               │
│   (web_app.py)      │           (app.py)                    │
└─────────────────────┴───────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Core Engine                               │
├─────────────────────┬─────────────────┬─────────────────────┤
│  Document Parser    │  Embedding      │   AI Integration    │
│  - PDF Extraction   │  - Chunking     │   - Groq API        │
│  - Text Processing  │  - Vectorization│   - Response Gen    │
│  - Format Detection │  - FAISS Index  │   - Context Mgmt    │
└─────────────────────┴─────────────────┴─────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                External Services                            │
├─────────────────────┬─────────────────┬─────────────────────┤
│     Groq API        │  HuggingFace    │    File Storage     │
│  (LLM Inference)    │   (Models)      │   (Temporary)       │
└─────────────────────┴─────────────────┴─────────────────────┘
```

### Core Components

#### 1. Document Processing Pipeline
```python
# Document ingestion flow
Document Upload → Format Detection → Text Extraction → 
Text Cleaning → Chunking → Embedding Generation → 
Vector Index Creation → Ready for Queries
```

#### 2. Query Processing Pipeline
```python
# Query processing flow
User Question → Query Parsing → Semantic Search → 
Context Retrieval → Prompt Construction → 
LLM Inference → Response Formatting → User Response
```

#### 3. Caching System
```python
# Multi-level caching
Model Cache (Singleton) → Document Cache (LRU + TTL) → 
Response Cache (Future) → Static Asset Cache
```

## 📁 Project Structure

### Directory Layout
```
intelligent-query/
├── src/                          # Source code
│   ├── app.py                   # FastAPI application (main)
│   ├── web_app.py               # Flask web interface
│   ├── new_app.py               # Optimized FastAPI version
│   └── __init__.py              # Package initialization
├── scripts/                     # Utility scripts
│   ├── setup-docker.bat        # Docker setup (Windows)
│   ├── start-server.bat        # Server startup (Windows)
│   ├── test_*.py               # Test scripts
│   └── benchmark.py            # Performance benchmarks
├── docs/                        # Documentation
│   ├── API_DOCUMENTATION.md    # API reference
│   ├── DEPLOYMENT_GUIDE.md     # Deployment instructions
│   ├── USER_GUIDE.md           # User manual
│   └── DEVELOPER_GUIDE.md      # This file
├── test/                        # Test files
│   ├── test_script.py          # Integration tests
│   └── benchmark.py            # Performance tests
├── uploads/                     # File upload directory
├── logs/                        # Application logs
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container configuration
├── docker-compose.yml          # Multi-container setup
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
└── README.md                   # Project overview
```

### Key Files Explained

#### `src/app.py` - Main FastAPI Application
- **Purpose**: Primary API server with optimized performance
- **Features**: Document processing, Q&A endpoints, caching
- **Framework**: FastAPI with async support
- **Port**: 3000 (default)

#### `src/web_app.py` - Flask Web Interface
- **Purpose**: User-friendly web interface
- **Features**: File upload, chat interface, session management
- **Framework**: Flask with Jinja2 templates
- **Port**: 5000 (default)

#### `src/new_app.py` - Optimized FastAPI Version
- **Purpose**: Enhanced version with advanced optimizations
- **Features**: Better caching, async processing, performance monitoring
- **Status**: Development/experimental

## 🔧 Core Technologies

### Backend Technologies

#### Python Frameworks
```python
# FastAPI - Modern, fast web framework
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse

# Flask - Traditional web framework
from flask import Flask, request, jsonify, render_template
```

#### AI/ML Libraries
```python
# Sentence Transformers - Text embeddings
from sentence_transformers import SentenceTransformer

# FAISS - Vector similarity search
import faiss

# Transformers - NLP models
from transformers import pipeline

# OpenAI Client - LLM API integration
from openai import OpenAI
```

#### Document Processing
```python
# PyMuPDF - Fast PDF processing
import fitz

# PDFPlumber - Alternative PDF processor
import pdfplumber

# Python-docx - Word document processing
from docx import Document
```

### Frontend Technologies

#### Web Interface
- **HTML5**: Semantic markup
- **CSS3**: Modern styling with CSS Grid/Flexbox
- **JavaScript**: Vanilla JS for interactivity
- **Bootstrap**: Responsive design framework

#### API Interface
- **OpenAPI/Swagger**: Automatic API documentation
- **JSON**: Data exchange format
- **REST**: API design pattern

## 🚀 Development Setup

### Prerequisites
```bash
# Python 3.11+
python --version

# Git
git --version

# Docker (optional)
docker --version
```

### Environment Setup
```bash
# Clone repository
git clone https://github.com/your-username/intelligent-query.git
cd intelligent-query

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest black flake8 mypy

# Setup pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

### Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
# Add your API keys and settings
```

### Running in Development Mode
```bash
# Flask web interface (with auto-reload)
export FLASK_ENV=development
python src/web_app.py

# FastAPI server (with auto-reload)
uvicorn src.app:app --reload --host 0.0.0.0 --port 3000

# Run tests
python -m pytest test/
```

## 🧩 Core Components Deep Dive

### 1. Document Processing Engine

#### Text Extraction
```python
def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract text from PDF using PyMuPDF with fallback to pdfplumber
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        Extracted text content
        
    Raises:
        Exception: If extraction fails with both methods
    """
    try:
        # Primary: PyMuPDF (fast)
        return extract_text_from_pdf_fast(pdf_path)
    except Exception:
        # Fallback: pdfplumber (reliable)
        return extract_text_from_pdf_fallback(pdf_path)
```

#### Text Chunking Strategy
```python
def create_optimized_chunks(text: str) -> List[str]:
    """
    Create optimized text chunks for embedding
    
    Strategy:
    1. Split by paragraphs (double newlines)
    2. Target chunk size: 400-500 characters
    3. Preserve sentence boundaries
    4. Filter out very short chunks (<80 chars)
    
    Args:
        text: Input text to chunk
        
    Returns:
        List of text chunks
    """
    chunks = []
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    
    for paragraph in paragraphs:
        if len(paragraph) <= 500:
            if len(paragraph) >= 80:
                chunks.append(paragraph)
        else:
            # Split long paragraphs by sentences
            sentences = SENTENCE_SPLIT_PATTERN.split(paragraph)
            current_chunk = ""
            
            for sentence in sentences:
                test_chunk = current_chunk + (" " if current_chunk else "") + sentence
                if len(test_chunk) <= 500:
                    current_chunk = test_chunk
                else:
                    if current_chunk and len(current_chunk) >= 80:
                        chunks.append(current_chunk)
                    current_chunk = sentence
            
            if current_chunk and len(current_chunk) >= 80:
                chunks.append(current_chunk)
    
    return chunks
```

### 2. Embedding and Vector Search

#### Embedding Generation
```python
def create_document_embeddings(text: str) -> Tuple[List[str], np.ndarray, faiss.Index, SentenceTransformer]:
    """
    Create document embeddings and FAISS index
    
    Process:
    1. Load pre-trained sentence transformer model
    2. Create optimized text chunks
    3. Generate embeddings in batches
    4. Create FAISS index for similarity search
    
    Args:
        text: Document text content
        
    Returns:
        Tuple of (chunks, embeddings, faiss_index, model)
    """
    model = get_sentence_transformer()
    chunks = create_optimized_chunks(text)
    
    # Batch processing for efficiency
    batch_size = 64
    all_embeddings = []
    
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        batch_embeddings = model.encode(
            batch, 
            show_progress_bar=False,
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        all_embeddings.append(batch_embeddings)
    
    embeddings = np.vstack(all_embeddings) if len(all_embeddings) > 1 else all_embeddings[0]
    
    # Create FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner product for normalized embeddings
    index.add(embeddings.astype('float32'))
    
    return chunks, embeddings, index, model
```

#### Semantic Search
```python
def retrieve_relevant_chunks(query: str, chunks: List[str], embeddings: np.ndarray, 
                           index: faiss.Index, model: SentenceTransformer, k: int = 3) -> List[str]:
    """
    Retrieve most relevant chunks for a query using semantic search
    
    Args:
        query: User question
        chunks: Document text chunks
        embeddings: Precomputed chunk embeddings
        index: FAISS search index
        model: Sentence transformer model
        k: Number of chunks to retrieve
        
    Returns:
        List of most relevant text chunks
    """
    # Encode query with same settings as chunks
    query_embedding = model.encode([query], normalize_embeddings=True, convert_to_numpy=True)
    
    # Search for similar chunks
    scores, indices = index.search(query_embedding.astype('float32'), k)
    
    # Return relevant chunks with size limits
    relevant_chunks = []
    for i in indices[0]:
        if i < len(chunks):
            chunk = chunks[i]
            if len(chunk) > 400:
                chunk = chunk[:400] + "..."
            relevant_chunks.append(chunk)
    
    return relevant_chunks
```

### 3. AI Integration and Response Generation

#### LLM Integration
```python
def generate_response(query: str, chunks: List[str], embeddings: np.ndarray = None, 
                     index: faiss.Index = None, model_st: SentenceTransformer = None, 
                     llm_model: str = "llama-3.1-8b-instant") -> str:
    """
    Generate AI response using Groq API
    
    Process:
    1. Initialize OpenAI client with Groq endpoint
    2. Retrieve relevant document chunks
    3. Construct optimized prompt
    4. Call LLM API
    5. Parse and format response
    
    Args:
        query: User question
        chunks: Document chunks
        embeddings: Chunk embeddings
        index: FAISS index
        model_st: Sentence transformer model
        llm_model: LLM model name
        
    Returns:
        JSON-formatted response
    """
    from openai import OpenAI
    
    # Initialize Groq client
    client = OpenAI(
        api_key=get_api_key(),
        base_url="https://api.groq.com/openai/v1",
        timeout=15.0
    )
    
    # Get relevant context
    relevant_chunks = retrieve_relevant_chunks(query, chunks, embeddings, index, model_st)
    
    # Construct prompt
    prompt = f"""You are a knowledgeable document analyst. Provide clear, accurate answers based on the document content.

Question: {query}

Document Context:
{chr(10).join([f"{i+1}. {chunk}" for i, chunk in enumerate(relevant_chunks)])}

Instructions:
- Provide direct, factual answers based on the document content
- Include specific details, numbers, dates, and facts when available
- Use clear, professional language
- If information is not available, state this clearly

Provide a clear, accurate answer based on the content."""

    # Generate response
    response = client.chat.completions.create(
        model=llm_model,
        messages=[
            {"role": "system", "content": "You are a document analysis expert. Provide direct, factual answers."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200,
        temperature=0.3
    )
    
    response_text = response.choices[0].message.content
    
    # Format as JSON
    try:
        parsed_response = json.loads(response_text)
        return json.dumps(parsed_response, separators=(',', ':'))
    except json.JSONDecodeError:
        return json.dumps({"justification": response_text}, separators=(',', ':'))
```

### 4. Caching System

#### Model Caching
```python
# Global model cache with thread safety
_model_cache = {
    'sentence_transformer': None,
    'ner_pipeline': None
}
_model_lock = threading.Lock()

@lru_cache(maxsize=1)
def get_sentence_transformer() -> SentenceTransformer:
    """Thread-safe singleton pattern for model loading"""
    with _model_lock:
        if _model_cache['sentence_transformer'] is None:
            _model_cache['sentence_transformer'] = SentenceTransformer('all-mpnet-base-v2')
        return _model_cache['sentence_transformer']
```

#### Document Caching
```python
# Document cache with TTL and LRU eviction
_document_cache = {}
_cache_timestamps = {}
MAX_CACHE_SIZE = 10
CACHE_TTL = 3600  # 1 hour

def cache_document(url: str, chunks: List[str], embeddings: np.ndarray, 
                  index: faiss.Index, model: SentenceTransformer):
    """Cache document processing results with TTL and LRU eviction"""
    cache_key = get_document_cache_key(url)
    
    with _cache_lock:
        # LRU eviction if at capacity
        if len(_document_cache) >= MAX_CACHE_SIZE:
            oldest_key = min(_cache_timestamps.keys(), key=_cache_timestamps.get)
            _document_cache.pop(oldest_key, None)
            _cache_timestamps.pop(oldest_key, None)
        
        _document_cache[cache_key] = {
            'chunks': chunks,
            'embeddings': embeddings,
            'index': index,
            'model': model
        }
        _cache_timestamps[cache_key] = time.time()
```

## 🔌 API Development

### FastAPI Endpoints

#### Health Check Endpoint
```python
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        api_key = get_api_key()
        return {
            "status": "healthy",
            "service": "Intelligent Query PDF Q&A System",
            "version": "1.0.0",
            "api_configured": bool(api_key),
            "cache_size": len(_document_cache),
            "uptime": time.time()
        }
    except Exception as e:
        return JSONResponse({
            "status": "unhealthy",
            "error": str(e)
        }, status_code=503)
```

#### Main Processing Endpoint
```python
@app.post("/hackrx/run")
async def hackrx_run(
    request: Request,
    authorization: str = Header(None),
    documents: Optional[str] = Body(None),
    questions: Optional[List[str]] = Body(None)
):
    """Main document analysis endpoint"""
    # Rate limiting
    client_ip = request.client.host
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Authentication
    ok, err = verify_bearer_token(authorization)
    if not ok:
        return JSONResponse({"success": False, "error": err}, status_code=401)
    
    # Input validation
    if not documents or not questions:
        return JSONResponse({
            "success": False,
            "error": "Missing required parameters"
        }, status_code=400)
    
    try:
        # Process document and generate answers
        # ... (implementation details)
        
        return JSONResponse({"answers": answers})
    
    except Exception as e:
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)
```

### Authentication and Security

#### Bearer Token Authentication
```python
def verify_bearer_token(authorization: str) -> Tuple[bool, Optional[str]]:
    """Verify Bearer token from Authorization header"""
    required_token = os.getenv('HACKRX_BEARER_TOKEN')
    if not required_token:
        return False, "Bearer token not configured"
    
    if not authorization or not authorization.startswith('Bearer '):
        return False, "Missing or invalid Authorization header"
    
    token = authorization[7:].strip()
    if token != required_token:
        return False, "Invalid Bearer token"
    
    return True, None
```

#### Rate Limiting
```python
class SlidingWindowRateLimit:
    """Sliding window rate limiter"""
    def __init__(self, max_requests: int = 20, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_ip: str) -> bool:
        now = time.time()
        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip] 
            if now - req_time < self.window_seconds
        ]
        
        if len(self.requests[client_ip]) >= self.max_requests:
            return False
        
        self.requests[client_ip].append(now)
        return True
```

## 🎨 Frontend Development

### Flask Templates

#### Base Template Structure
```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Intelligent Query{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="{{ url_for('static', filename='css/style.css') }}" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-brain"></i> Intelligent Query
            </a>
        </div>
    </nav>
    
    <main class="container mt-4">
        {% block content %}{% endblock %}
    </main>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script src="{{ url_for('static', filename='js/app.js') }}"></script>
</body>
</html>
```

#### JavaScript Integration
```javascript
// static/js/app.js
class IntelligentQueryApp {
    constructor() {
        this.initializeEventListeners();
        this.setupFileUpload();
        this.setupChat();
    }
    
    initializeEventListeners() {
        document.addEventListener('DOMContentLoaded', () => {
            this.setupDropZone();
            this.setupQuestionForm();
        });
    }
    
    setupDropZone() {
        const dropZone = document.getElementById('dropZone');
        
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });
        
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileUpload(files[0]);
            }
        });
    }
    
    async handleFileUpload(file) {
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showUploadSuccess();
                this.enableChat();
            } else {
                this.showError(result.error);
            }
        } catch (error) {
            this.showError('Upload failed: ' + error.message);
        }
    }
    
    async askQuestion(question) {
        const response = await fetch('/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question })
        });
        
        const result = await response.json();
        return result;
    }
}

// Initialize app
const app = new IntelligentQueryApp();
```

## 🧪 Testing

### Unit Tests
```python
# test/test_document_processing.py
import pytest
from src.app import extract_text_from_pdf, create_document_embeddings

class TestDocumentProcessing:
    def test_pdf_extraction(self):
        """Test PDF text extraction"""
        # Test with sample PDF
        text = extract_text_from_pdf('test/samples/sample.pdf')
        assert len(text) > 0
        assert isinstance(text, str)
    
    def test_embedding_creation(self):
        """Test document embedding creation"""
        sample_text = "This is a test document for embedding creation."
        chunks, embeddings, index, model = create_document_embeddings(sample_text)
        
        assert len(chunks) > 0
        assert embeddings.shape[0] == len(chunks)
        assert index.ntotal == len(chunks)
        assert model is not None

    def test_chunking_strategy(self):
        """Test text chunking strategy"""
        long_text = "This is a sentence. " * 100  # Create long text
        chunks, _, _, _ = create_document_embeddings(long_text)
        
        # Check chunk sizes are reasonable
        for chunk in chunks:
            assert 80 <= len(chunk) <= 500
```

### Integration Tests
```python
# test/test_api_endpoints.py
import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

class TestAPIEndpoints:
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_document_analysis_endpoint(self):
        """Test main document analysis endpoint"""
        headers = {"Authorization": "Bearer test_token"}
        payload = {
            "documents": "https://example.com/test.pdf",
            "questions": ["What is this document about?"]
        }
        
        response = client.post("/hackrx/run", json=payload, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "answers" in data
        assert len(data["answers"]) == 1
    
    def test_authentication_required(self):
        """Test that authentication is required"""
        payload = {
            "documents": "https://example.com/test.pdf",
            "questions": ["Test question"]
        }
        
        response = client.post("/hackrx/run", json=payload)
        assert response.status_code == 401
```

### Performance Tests
```python
# test/test_performance.py
import time
import pytest
from src.app import create_document_embeddings, generate_response

class TestPerformance:
    def test_embedding_performance(self):
        """Test embedding creation performance"""
        sample_text = "Sample text. " * 1000  # ~13KB text
        
        start_time = time.time()
        chunks, embeddings, index, model = create_document_embeddings(sample_text)
        end_time = time.time()
        
        processing_time = end_time - start_time
        assert processing_time < 60  # Should complete within 60 seconds
        
        print(f"Embedding creation took {processing_time:.2f} seconds")
        print(f"Created {len(chunks)} chunks")
    
    def test_response_generation_performance(self):
        """Test response generation performance"""
        sample_chunks = ["This is a test document about AI and machine learning."]
        
        start_time = time.time()
        response = generate_response("What is this about?", sample_chunks)
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response_time < 10  # Should respond within 10 seconds
        
        print(f"Response generation took {response_time:.2f} seconds")
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest test/test_document_processing.py

# Run with coverage
pytest --cov=src

# Run performance tests
pytest test/test_performance.py -v

# Run tests with detailed output
pytest -v -s
```

## 🔧 Configuration Management

### Environment Configuration
```python
# src/config.py
import os
from typing import Optional
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application settings with validation"""
    
    # API Configuration
    groq_api_key: str
    hackrx_bearer_token: str
    
    # Application Settings
    debug: bool = False
    port: int = 3000
    host: str = "0.0.0.0"
    
    # File Upload Settings
    max_file_size: int = 200 * 1024 * 1024  # 200MB
    upload_dir: str = "uploads"
    
    # Cache Settings
    max_cache_size: int = 10
    cache_ttl: int = 3600
    
    # Model Settings
    sentence_model: str = "all-mpnet-base-v2"
    llm_model: str = "llama-3.1-8b-instant"
    
    # Rate Limiting
    rate_limit_requests: int = 20
    rate_limit_window: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()
```

### Feature Flags
```python
# src/features.py
class FeatureFlags:
    """Feature flags for enabling/disabling functionality"""
    
    # Document Processing Features
    ENABLE_PYMUPDF = True
    ENABLE_PDFPLUMBER_FALLBACK = True
    ENABLE_DOCX_SUPPORT = True
    ENABLE_EMAIL_SUPPORT = True
    
    # AI Features
    ENABLE_NER_PIPELINE = True
    ENABLE_QUERY_PARSING = True
    ENABLE_CONTEXT_ENHANCEMENT = True
    
    # Performance Features
    ENABLE_DOCUMENT_CACHING = True
    ENABLE_MODEL_CACHING = True
    ENABLE_RESPONSE_CACHING = False  # Future feature
    
    # Security Features
    ENABLE_RATE_LIMITING = True
    ENABLE_BEARER_AUTH = True
    ENABLE_INPUT_VALIDATION = True
    
    # Monitoring Features
    ENABLE_PERFORMANCE_LOGGING = True
    ENABLE_ERROR_TRACKING = True
    ENABLE_METRICS_COLLECTION = False  # Future feature

# Usage in code
if FeatureFlags.ENABLE_DOCUMENT_CACHING:
    cached_doc = get_cached_document(url)
```

## 📊 Monitoring and Logging

### Logging Configuration
```python
# src/logging_config.py
import logging
import sys
from pathlib import Path

def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Configure application logging"""
    
    # Create logs directory if it doesn't exist
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # File handler (if specified)
    handlers = [console_handler]
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        handlers=handlers,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Suppress noisy third-party loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('transformers').setLevel(logging.WARNING)
```

### Performance Monitoring
```python
# src/monitoring.py
import time
import functools
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Performance monitoring and metrics collection"""
    
    def __init__(self):
        self.metrics = {
            'request_count': 0,
            'total_processing_time': 0,
            'document_processing_times': [],
            'response_generation_times': [],
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def record_request(self):
        """Record a new request"""
        self.metrics['request_count'] += 1
    
    def record_processing_time(self, operation: str, duration: float):
        """Record processing time for an operation"""
        self.metrics['total_processing_time'] += duration
        
        if operation == 'document_processing':
            self.metrics['document_processing_times'].append(duration)
        elif operation == 'response_generation':
            self.metrics['response_generation_times'].append(duration)
    
    def record_cache_hit(self):
        """Record cache hit"""
        self.metrics['cache_hits'] += 1
    
    def record_cache_miss(self):
        """Record cache miss"""
        self.metrics['cache_misses'] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        cache_total = self.metrics['cache_hits'] + self.metrics['cache_misses']
        cache_hit_rate = self.metrics['cache_hits'] / cache_total if cache_total > 0 else 0
        
        return {
            **self.metrics,
            'cache_hit_rate': cache_hit_rate,
            'avg_processing_time': (
                self.metrics['total_processing_time'] / self.metrics['request_count']
                if self.metrics['request_count'] > 0 else 0
            )
        }

# Global monitor instance
monitor = PerformanceMonitor()

def track_performance(operation: str):
    """Decorator to track function performance"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                monitor.record_processing_time(operation, duration)
                logger.info(f"{operation} completed in {duration:.2f}s")
        return wrapper
    return decorator

# Usage
@track_performance('document_processing')
def process_document(text: str):
    # Processing logic here
    pass
```

## 🔄 Contributing Guidelines

### Code Style
```python
# Use Black for code formatting
black src/ test/

# Use flake8 for linting
flake8 src/ test/

# Use mypy for type checking
mypy src/

# Use isort for import sorting
isort src/ test/
```

### Pre-commit Configuration
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.950
    hooks:
      - id: mypy

  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort
```

### Development Workflow
1. **Create Feature Branch**: `git checkout -b feature/new-feature`
2. **Write Tests**: Add tests for new functionality
3. **Implement Feature**: Write clean, documented code
4. **Run Tests**: Ensure all tests pass
5. **Code Review**: Submit pull request for review
6. **Merge**: Merge after approval and CI passes

### Adding New Features

#### Example: Adding New Document Format Support
```python
# 1. Add extraction function
def extract_text_from_new_format(file_path: str) -> str:
    """Extract text from new document format"""
    # Implementation here
    pass

# 2. Update format detection
def detect_file_format(file_path: str) -> str:
    """Detect document format"""
    extension = Path(file_path).suffix.lower()
    
    format_map = {
        '.pdf': 'pdf',
        '.docx': 'docx',
        '.eml': 'email',
        '.new_ext': 'new_format'  # Add new format
    }
    
    return format_map.get(extension, 'unknown')

# 3. Update processing pipeline
def extract_text_from_document(file_path: str) -> str:
    """Extract text from any supported document format"""
    format_type = detect_file_format(file_path)
    
    extractors = {
        'pdf': extract_text_from_pdf,
        'docx': extract_text_from_docx,
        'email': extract_text_from_email,
        'new_format': extract_text_from_new_format  # Add new extractor
    }
    
    extractor = extractors.get(format_type)
    if not extractor:
        raise ValueError(f"Unsupported format: {format_type}")
    
    return extractor(file_path)

# 4. Add tests
def test_new_format_extraction():
    """Test new format text extraction"""
    text = extract_text_from_new_format('test/samples/sample.new_ext')
    assert len(text) > 0
    assert isinstance(text, str)
```

## 🚀 Deployment Considerations

### Production Optimizations
```python
# Production configuration
PRODUCTION_CONFIG = {
    'workers': 4,  # Number of worker processes
    'worker_class': 'uvicorn.workers.UvicornWorker',
    'max_requests': 1000,  # Restart workers after N requests
    'timeout': 300,  # Request timeout
    'keepalive': 2,  # Keep connections alive
    'preload_app': True,  # Preload application code
}

# Memory optimization
import gc

def optimize_memory():
    """Optimize memory usage"""
    # Force garbage collection
    gc.collect()
    
    # Clear model cache if memory usage is high
    if get_memory_usage() > MEMORY_THRESHOLD:
        clear_model_cache()
```

### Scaling Strategies
```python
# Horizontal scaling with load balancing
class LoadBalancer:
    """Simple load balancer for multiple instances"""
    
    def __init__(self, instances: List[str]):
        self.instances = instances
        self.current = 0
    
    def get_next_instance(self) -> str:
        """Round-robin load balancing"""
        instance = self.instances[self.current]
        self.current = (self.current + 1) % len(self.instances)
        return instance

# Database integration for persistent storage
class DocumentStore:
    """Document storage interface"""
    
    def store_document(self, doc_id: str, content: Dict[str, Any]):
        """Store document processing results"""
        pass
    
    def retrieve_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve stored document"""
        pass
    
    def delete_document(self, doc_id: str):
        """Delete stored document"""
        pass
```

---

## 📞 Developer Support

For development questions and support:

- **Documentation**: [Full Documentation](../README.md)
- **API Reference**: [API Documentation](API_DOCUMENTATION.md)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **Contributing**: [Contributing Guidelines](../CONTRIBUTING.md)

---

*Happy coding! 🚀*

*Last updated: November 2024*