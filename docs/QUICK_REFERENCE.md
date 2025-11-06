# Quick Reference - New Architecture

## 📋 Configuration

### Get Settings
```python
from src.config import get_settings

settings = get_settings()
```

### Available Settings
```python
# PDF Configuration
settings.pdf.max_file_size        # 200MB default
settings.pdf.chunk_size           # 500 chars default
settings.pdf.supported_formats    # ('pdf', 'docx', 'eml')

# Embedding Configuration
settings.embedding.model_name     # 'all-MiniLM-L6-v2'
settings.embedding.batch_size     # 64 default

# Cache Configuration
settings.cache.enabled            # True
settings.cache.max_documents      # 10 default
settings.cache.ttl_seconds        # 3600 (1 hour)

# LLM Configuration
settings.llm.api_provider         # 'groq'
settings.llm.model_name           # 'llama-3.1-8b-instant'
settings.llm.temperature          # 0.7

# API Configuration
settings.api.port                 # 3000
settings.api.debug                # False
settings.api.enable_authentication # True

# API Keys
settings.groq_api_key             # From GROQ_API_KEY env var
settings.openai_api_key           # From OPENAI_API_KEY env var
settings.bearer_token             # From HACKRX_BEARER_TOKEN env var
```

### Validate Configuration
```python
is_valid, error_msg = settings.validate()
if not is_valid:
    print(f"Configuration error: {error_msg}")
```

### Export for Logging (Safe - No Secrets)
```python
config_dict = settings.to_dict()
# Returns: API port, model names, cache size, etc (no API keys!)
```

---

## 🎯 Data Models

### Document Model
```python
from src.core.models import Document
import numpy as np

doc = Document(
    id="doc_123",
    filename="research.pdf",
    chunks=["chunk1", "chunk2", ...],
    embeddings=np.array([[0.1, 0.2, ...], ...]),
    created_at=time.time(),
    updated_at=time.time(),
    file_size=1024000,
    format="pdf",
    metadata={"source": "user_upload"}
)

# Convert to dictionary (for JSON/API responses)
doc_dict = doc.to_dict()
# Returns: id, filename, chunk_count, timestamps, size, format
```

### ChatMessage Model
```python
from src.core.models import ChatMessage, MessageSender

msg = ChatMessage(
    id="msg_456",
    session_id="sess_123",
    sender=MessageSender.USER,  # or MessageSender.ASSISTANT
    content="What is this document about?",
    timestamp=time.time(),
    metadata={"source": "web_ui"}
)

msg_dict = msg.to_dict()
```

### QueryResponse Model
```python
from src.core.models import QueryResponse, RetrievalResult

response = QueryResponse(
    answer="The document discusses machine learning...",
    confidence=0.95,
    sources=[
        RetrievalResult(chunk="ML is...", chunk_index=0, similarity_score=0.98),
        RetrievalResult(chunk="Deep learning...", chunk_index=5, similarity_score=0.92)
    ],
    tokens_used=150,
    processing_time=1.23,
    metadata={"model": "llama-3.1"}
)

response_dict = response.to_dict()
```

### API Response Model
```python
from src.core.models import APIResponse

response = APIResponse(
    success=True,
    data={"document_id": "doc_123", "chunks": 45},
    metadata={"processing_time": 1.5}
)

# For errors
error_response = APIResponse(
    success=False,
    error="PDF extraction failed",
    metadata={"error_code": "PDF_INVALID"}
)
```

---

## ⚠️ Exception Hierarchy

### Common Exceptions
```python
from src.core.exceptions import (
    PDFExtractionError,      # PDF text extraction failed
    EmbeddingError,          # Embedding creation failed
    APIKeyError,             # API key missing/invalid
    DocumentNotFoundError,   # Document not found
    RateLimitError,          # Rate limit exceeded
    ValidationError,         # Input validation failed
)

# Raise with context
raise PDFExtractionError(
    message="Failed to extract text",
    error_code="PDF_CORRUPT",
    details={"filename": "doc.pdf"}
)
```

### Error Response Mapping
```python
from src.core.exceptions import get_error_response, http_status_code

try:
    process_pdf()
except PDFExtractionError as e:
    error_dict = get_error_response(e)
    status = http_status_code(e)  # Returns 500
    return error_dict, status
```

### Exception Tree
```
ValidationError         → HTTP 400
AuthenticationError     → HTTP 401
AuthorizationError      → HTTP 403
DocumentNotFoundError   → HTTP 404
FileSizeExceededError   → HTTP 413
RateLimitError          → HTTP 429
ConflictError           → HTTP 409
PDFProcessingError      → HTTP 500
EmbeddingError          → HTTP 500
LLMError                → HTTP 500
```

---

## 🔧 Using Multiple Features Together

### Example: Upload & Process Document
```python
from src.config import get_settings
from src.core.models import Document, APIResponse, FileUpload
from src.core.exceptions import (
    PDFExtractionError, 
    ValidationError,
    get_error_response,
    http_status_code
)

def handle_upload(file_bytes, filename):
    settings = get_settings()
    
    # Validate
    if len(file_bytes) > settings.pdf.max_file_size:
        raise ValidationError(
            f"File exceeds max size of {settings.pdf.max_file_size}",
            error_code="FILE_TOO_LARGE"
        )
    
    # Create model
    upload = FileUpload(
        filename=filename,
        content=file_bytes,
        content_type="application/pdf",
        size=len(file_bytes)
    )
    
    try:
        # Process (future: use PDFService)
        chunks = extract_pdf(upload.filename)
        
        # Create document model
        doc = Document(
            id=generate_id(),
            filename=filename,
            chunks=chunks,
            embeddings=embeddings_array,
            created_at=time.time(),
            updated_at=time.time(),
            file_size=upload.size
        )
        
        # Return success response
        response = APIResponse(
            success=True,
            data=doc.to_dict(),
            metadata={"chunk_count": len(chunks)}
        )
        return response.to_dict(), 200
        
    except PDFExtractionError as e:
        error = get_error_response(e)
        status = http_status_code(e)
        return error, status
```

---

## 🧪 Testing the New Architecture

```bash
# Test imports work
python -c "from src.config import get_settings; print('✓ Config OK')"
python -c "from src.core.models import Document; print('✓ Models OK')"
python -c "from src.core.exceptions import PDFExtractionError; print('✓ Exceptions OK')"

# Test configuration
python -c "from src.config import get_settings; s=get_settings(); print(s.to_dict())"

# Test models
python << 'EOF'
from src.core.models import ChatMessage, MessageSender
import json

msg = ChatMessage(
    id="1", session_id="s1", sender=MessageSender.USER,
    content="test", timestamp=1234567890
)
print(json.dumps(msg.to_dict(), indent=2))
EOF

# Test exceptions
python << 'EOF'
from src.core.exceptions import PDFExtractionError, http_status_code
try:
    raise PDFExtractionError("Test error", "TEST_CODE")
except Exception as e:
    print(f"Error: {e.to_dict()}")
    print(f"HTTP Status: {http_status_code(e)}")
EOF
```

---

## 📚 What's Next (Phase 2)

Create service layer files:
1. `src/services/pdf_service.py` - PDF extraction
2. `src/services/embedding_service.py` - Vector embeddings
3. `src/services/llm_service.py` - LLM interactions
4. `src/services/cache_service.py` - Document caching

Each service:
- Uses `get_settings()` for configuration
- Raises appropriate exceptions from `src.core.exceptions`
- Returns data models from `src.core.models`
- Is independently testable

Example:
```python
from src.config import get_settings
from src.core.exceptions import PDFExtractionError
from src.core.models import Document

class PDFService:
    def __init__(self):
        self.settings = get_settings()
    
    def extract_text(self, file_path: str) -> str:
        """Extract text from PDF, raise PDFExtractionError on failure"""
        if not self.settings.pdf.supported_formats:
            raise PDFExtractionError("No supported formats")
        # ... extraction logic ...
```

---

## 🎓 Best Practices

✅ Always use `get_settings()` for configuration  
✅ Raise specific exceptions (not generic Exception)  
✅ Use `to_dict()` before JSON serialization  
✅ Include error details in exceptions  
✅ Use type hints (models are type-safe)  
✅ Use `MessageSender.USER` enum (not string "user")  
✅ Set metadata for tracking and debugging  
✅ Validate configuration on startup  

❌ Don't hardcode configuration values  
❌ Don't catch generic Exception  
❌ Don't skip error details  
❌ Don't mix models with dictionaries  
❌ Don't access env vars directly in services  
❌ Don't use magic strings for message senders  

---

**Status**: Ready for Phase 2 Service Layer Implementation
