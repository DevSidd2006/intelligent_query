# System Architecture Improvements

## Current Issues Identified

### 1. **Code Duplication**
- **Problem**: Same logic exists in `app.py`, `web_app.py`, and `new_app.py`
  - PDF extraction repeated
  - Embedding creation duplicated
  - Cache management redefined
  - Model initialization scattered

### 2. **Poor Layer Separation**
- **Problem**: Business logic mixed with HTTP handlers
  - PDF processing logic inside Flask routes
  - Model management scattered across files
  - No clear service layer

### 3. **Missing Abstraction**
- **Problem**: Direct calls to external libraries
  - PyMuPDF/pdfplumber coupling in routes
  - SentenceTransformer management inline
  - FAISS operations in HTTP handlers

### 4. **Configuration Issues**
- **Problem**: Hard-coded values and environment-dependent logic
  - Magic numbers scattered (chunk sizes, batch sizes, timeouts)
  - Model selection logic repeated
  - Cache sizes defined multiple times

### 5. **Import Hell**
- **Problem**: Complex, fragile import system
  - 4-method fallback import mechanism (lines 28-61 in web_app.py)
  - Circular dependencies possible
  - No clear dependency graph

### 6. **Session/State Management**
- **Problem**: Global dictionaries for state
  - `current_document` dictionary in Flask
  - `chat_sessions` dictionary
  - No persistence layer
  - Thread-safety concerns

### 7. **Error Handling**
- **Problem**: Inconsistent error handling
  - Generic try/catch blocks
  - Mixed logging strategies
  - No structured error responses

### 8. **Testing Challenges**
- **Problem**: Difficult to test due to tight coupling
  - Can't test business logic independently
  - Must mock entire Flask/FastAPI stack
  - No service interfaces for dependency injection

## Proposed New Architecture

```
intelligent_query/
├── src/
│   ├── __init__.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py          # Centralized configuration
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py            # Data models and DTOs
│   │   ├── exceptions.py        # Custom exceptions
│   │   └── types.py             # Type definitions
│   ├── services/
│   │   ├── __init__.py
│   │   ├── pdf_service.py       # PDF extraction
│   │   ├── embedding_service.py # Embeddings and vectors
│   │   ├── retrieval_service.py # Semantic search
│   │   ├── llm_service.py       # LLM interactions
│   │   └── cache_service.py     # Document caching
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── document_repo.py     # Document storage/retrieval
│   │   └── session_repo.py      # Session management
│   ├── api/
│   │   ├── __init__.py
│   │   ├── flask_app.py         # Flask application
│   │   ├── fastapi_app.py       # FastAPI application
│   │   └── routes/
│   │       ├── __init__.py
│   │       ├── documents.py     # Document endpoints
│   │       ├── chat.py          # Chat endpoints
│   │       └── health.py        # Health check endpoints
│   ├── ui/
│   │   ├── __init__.py
│   │   └── templates.py         # UI templates
│   └── utils/
│       ├── __init__.py
│       ├── logging.py           # Logging utilities
│       ├── validation.py        # Input validation
│       └── helpers.py           # Helper functions
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_pdf_service.py
│   │   ├── test_embedding_service.py
│   │   └── test_retrieval_service.py
│   ├── integration/
│   │   └── test_api.py
│   └── fixtures/
│       └── test_data.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Key Improvements

### 1. **Service Layer Architecture**
```python
# Services handle all business logic
class PDFService:
    """Handles PDF extraction with strategy pattern"""
    - extract_text(file_path)
    - validate_file(file_path)
    
class EmbeddingService:
    """Manages embeddings and FAISS indices"""
    - create_embeddings(text)
    - retrieve_similar(query, top_k)
    
class LLMService:
    """Manages LLM interactions"""
    - generate_response(query, context)
    - validate_token(token)
    
class CacheService:
    """Manages document caching with TTL"""
    - get_document(key)
    - cache_document(key, data)
    - clear_cache()
```

### 2. **Dependency Injection**
```python
# Instead of global imports
from services import PDFService, EmbeddingService

class DocumentProcessor:
    def __init__(self, 
                 pdf_service: PDFService,
                 embedding_service: EmbeddingService,
                 cache_service: CacheService):
        self.pdf = pdf_service
        self.embeddings = embedding_service
        self.cache = cache_service
```

### 3. **Configuration Management**
```python
# config/settings.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class PDFConfig:
    max_file_size: int = 200 * 1024 * 1024
    supported_formats: tuple = ('pdf', 'docx', 'eml')

@dataclass
class EmbeddingConfig:
    model_name: str = 'all-MiniLM-L6-v2'
    batch_size: int = 64
    chunk_size: int = 500

@dataclass
class Settings:
    pdf: PDFConfig
    embedding: EmbeddingConfig
    api_key: str
    debug: bool
    
    @classmethod
    def from_env(cls):
        return cls(...)
```

### 4. **Data Models**
```python
# core/models.py
from dataclasses import dataclass
from typing import List, Optional
import numpy as np

@dataclass
class Document:
    id: str
    filename: str
    chunks: List[str]
    embeddings: np.ndarray
    created_at: float
    
@dataclass
class ChatMessage:
    id: str
    session_id: str
    sender: str  # 'user' or 'assistant'
    content: str
    timestamp: float
    
@dataclass
class QueryResponse:
    answer: str
    confidence: float
    sources: List[str]
```

### 5. **Exception Hierarchy**
```python
# core/exceptions.py
class IntelliQueryException(Exception):
    """Base exception"""

class PDFProcessingError(IntelliQueryException):
    """PDF extraction failed"""

class EmbeddingError(IntelliQueryException):
    """Embedding creation failed"""

class APIError(IntelliQueryException):
    """API request failed"""
```

### 6. **Repository Pattern**
```python
# repositories/document_repo.py
from abc import ABC, abstractmethod

class DocumentRepository(ABC):
    @abstractmethod
    def save(self, document: Document) -> str:
        pass
    
    @abstractmethod
    def get(self, doc_id: str) -> Optional[Document]:
        pass
    
    @abstractmethod
    def list_recent(self, limit: int) -> List[Document]:
        pass

class InMemoryDocumentRepository(DocumentRepository):
    """Development/testing implementation"""
    
class RedisDocumentRepository(DocumentRepository):
    """Production implementation with Redis"""
```

### 7. **API Routes Refactoring**
```python
# api/routes/documents.py (Flask)
from flask import Blueprint, request
from services import PDFService

documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')

@documents_bp.route('/', methods=['POST'])
def upload_document(pdf_service: PDFService):
    """Upload and process a document"""
    file = request.files['file']
    doc = pdf_service.process_file(file)
    return jsonify(doc.to_dict())

@documents_bp.route('/<doc_id>', methods=['GET'])
def get_document(doc_id: str):
    """Retrieve document metadata"""
    doc = document_repo.get(doc_id)
    if not doc:
        raise NotFoundError(f"Document {doc_id} not found")
    return jsonify(doc.to_dict())
```

## Implementation Roadmap

### Phase 1: Core Services (2-3 hours)
1. Create `config/settings.py`
2. Create `core/models.py` and `core/exceptions.py`
3. Create `services/pdf_service.py`
4. Create `services/embedding_service.py`
5. Create `services/llm_service.py`
6. Create `services/cache_service.py`

### Phase 2: Repository Layer (1-2 hours)
1. Create `repositories/document_repo.py`
2. Create `repositories/session_repo.py`
3. Implement in-memory repositories

### Phase 3: API Refactoring (2-3 hours)
1. Refactor Flask routes to use services
2. Refactor FastAPI endpoints to use services
3. Add dependency injection

### Phase 4: Testing (2-3 hours)
1. Unit tests for services
2. Integration tests for API
3. Test coverage report

### Phase 5: Documentation (1 hour)
1. Update API documentation
2. Add service documentation
3. Create deployment guide

## Benefits

✅ **Maintainability**: Clear separation of concerns
✅ **Testability**: Easy to unit test services
✅ **Reusability**: Services can be used by multiple apps
✅ **Scalability**: Easy to swap implementations
✅ **Consistency**: Single source of truth for business logic
✅ **Debugging**: Clear error messages and logging
✅ **Onboarding**: New developers understand structure

## Migration Path

1. Create new structure alongside existing code
2. Gradually migrate endpoints to use services
3. Remove old code once all endpoints migrated
4. No downtime - both versions run simultaneously
5. Clean up and optimize after full migration

## Backward Compatibility

- Keep existing endpoints working during migration
- Versioned API endpoints (`/api/v1/`, `/api/v2/`)
- Gradual deprecation of old endpoints
- Client-side migration guides

---

**Next Steps**: Start with Phase 1 implementation
