# Project Structure Guide

## Directory Organization

```
intelligent_query/
├── src/                          # Main application source code
│   ├── __init__.py
│   ├── app.py                    # Core PDF processing and LLM logic
│   ├── web_app.py                # Flask web application (2183 lines)
│   ├── run_flask.py              # Flask entry point
│   │
│   ├── config/                   # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py           # Dataclass-based settings (Phase 1 ✓)
│   │
│   ├── core/                     # Core domain models and exceptions
│   │   ├── __init__.py
│   │   ├── models.py             # Type-safe data models (Phase 1 ✓)
│   │   └── exceptions.py         # Exception hierarchy (Phase 1 ✓)
│   │
│   ├── services/                 # Business logic services (Phase 2)
│   │   ├── __init__.py
│   │   ├── pdf_service.py        # PDF extraction (planned)
│   │   ├── embedding_service.py  # Vector embeddings (planned)
│   │   ├── llm_service.py        # LLM interactions (planned)
│   │   └── cache_service.py      # Caching logic (planned)
│   │
│   ├── repositories/             # Data persistence layer (Phase 3)
│   │   ├── __init__.py
│   │   ├── base.py               # Abstract base classes (planned)
│   │   ├── document_repo.py      # Document storage (planned)
│   │   └── session_repo.py       # Session storage (planned)
│   │
│   ├── api/                      # API routes and handlers (Phase 4)
│   │   ├── __init__.py
│   │   ├── flask_app.py          # Flask blueprints (planned)
│   │   └── fastapi_app.py        # FastAPI routers (planned)
│   │
│   ├── utils/                    # Utility functions
│   │   ├── __init__.py
│   │   ├── file_utils.py         # File handling (planned)
│   │   ├── logging_utils.py      # Logging setup (planned)
│   │   └── time_utils.py         # Time utilities (planned)
│   │
│   └── templates/                # HTML/Jinja2 templates
│       └── landing.html          # Main UI template
│
├── scripts/                      # Utility scripts
│   ├── check-api-config.py       # API configuration checker
│   ├── docker-entrypoint.sh      # Docker startup script
│   ├── setup-docker.bat          # Docker setup script
│   ├── start-server.bat          # Server startup script
│   ├── test_openrouter.py        # OpenRouter API test
│   └── push_to_docker_hub.ps1    # Docker Hub push script
│
├── docs/                         # Documentation
│   ├── API_DOCUMENTATION.md      # API endpoint documentation
│   ├── DEPLOYMENT_GUIDE.md       # Deployment instructions
│   ├── DEVELOPER_GUIDE.md        # Developer setup guide
│   ├── USER_GUIDE.md             # User manual
│   ├── DOCKER_DEPLOYMENT.md      # Docker deployment guide
│   ├── DOCKER_README.md          # Docker usage guide
│   ├── README-DOCKERHUB.md       # Docker Hub guide
│   ├── ARCHITECTURE_IMPROVEMENTS.md # Architecture refactoring plan
│   ├── PHASE_1_COMPLETE.md       # Phase 1 completion summary
│   └── QUICK_REFERENCE.md        # Developer quick reference
│
├── uploads/                      # User uploaded files (runtime)
├── logs/                         # Application logs (runtime)
├── venv/                         # Python virtual environment (local dev)
│
├── .env                          # Environment variables (local dev)
├── .env.example                  # Example environment file
├── .dockerignore                 # Docker build exclusions
├── .gitignore                    # Git exclusions
├── .gitattributes                # Git attributes
├── .git/                         # Git repository
├── .vscode/                      # VS Code settings
│
├── Dockerfile                    # Docker image definition
├── docker-compose.yml            # Multi-container orchestration
├── requirements.txt              # Python dependencies
├── runtime.txt                   # Python runtime version
├── Procfile                      # Heroku process definition
│
├── README.md                     # Project overview
├── CHANGELOG.md                  # Version history
├── CONTRIBUTING.md              # Contribution guidelines
├── DIFFERENTIATORS.md            # Key differentiators
└── PROJECT_STRUCTURE.md          # Previous structure (deprecated)
```

## Core Architecture (Phase 1 Complete ✓)

### Configuration Layer (`src/config/settings.py`)
- **PDFConfig**: PDF processing settings (chunk_size, overlap, max_file_size)
- **EmbeddingConfig**: Embedding model configuration
- **CacheConfig**: Caching strategy (TTL, max_size)
- **LLMConfig**: LLM provider settings (model, temperature, max_tokens)
- **APIConfig**: API settings (host, port, debug mode)
- **LoggingConfig**: Logging configuration
- **Settings**: Master configuration class

Usage:
```python
from src.config import get_settings
settings = get_settings()
```

### Domain Models (`src/core/models.py`)
Type-safe dataclass models with automatic JSON serialization:
- **Document**: PDF document with chunks and embeddings
- **ChatMessage**: Individual chat message with sender info
- **ChatSession**: Collection of chat messages
- **RetrievalResult**: Vector search result
- **QueryResponse**: LLM response wrapper
- **FileUpload**: File upload metadata
- **APIResponse**: Generic API response wrapper
- **HealthStatus**: System health information

### Exception Hierarchy (`src/core/exceptions.py`)
Comprehensive exception system with HTTP status code mapping:
- **ConfigurationError**: Settings/configuration issues
- **ValidationError**: Input validation failures
- **PDFProcessingError**: PDF extraction failures
- **EmbeddingError**: Embedding generation failures
- **LLMError**: LLM provider errors
- **CacheError**: Caching operation failures
- **RepositoryError**: Data persistence failures
- **APIError**: API-level errors

All exceptions include:
- Custom error codes
- Detailed error messages
- Automatic HTTP status code mapping (400, 401, 403, 404, 413, 429, 500)
- to_dict() serialization for API responses

## Implementation Phases

### Phase 0: Cleanup (COMPLETE ✓)
- Removed duplicate app files (new_app.py)
- Removed outdated startup scripts
- Removed test files from root
- Organized documentation and scripts
- Established directory structure

### Phase 1: Foundation (COMPLETE ✓)
- Created configuration management module
- Created type-safe data models
- Created exception hierarchy
- Established module structure
- Generated comprehensive documentation

### Phase 2: Services (TODO)
Implement business logic services:
- **PDFService**: Encapsulate PDF extraction logic from app.py
- **EmbeddingService**: Vector embeddings and FAISS operations
- **LLMService**: Groq API interactions
- **CacheService**: Document caching with TTL
- Estimated: 2-3 hours

### Phase 3: Repositories (TODO)
Implement data persistence layer:
- Abstract base repositories
- In-memory implementations
- File-based implementations
- Database-backed implementations (optional)
- Estimated: 1-2 hours

### Phase 4: API Refactoring (TODO)
Integrate services into API layer:
- Refactor Flask app to use services
- Refactor/phase out FastAPI app
- Add dependency injection
- Simplify route handlers
- Estimated: 2-3 hours

### Phase 5: Testing & Docs (TODO)
Complete testing and documentation:
- Unit tests for all services
- Integration tests for API
- Update API documentation
- Service documentation
- Estimated: 2-3 hours

## Key Technologies

- **Framework**: Flask 3.1.2 (primary), FastAPI 0.110.0 (secondary)
- **Python**: 3.11 (slim Docker image, 12.9GB)
- **PDF Processing**: PyMuPDF + pdfplumber (fallback strategy)
- **AI/ML**: SentenceTransformers (embeddings) + FAISS (vector search)
- **LLM**: Groq API (Llama 3.1 8B Instant model)
- **Containerization**: Docker + Docker Compose
- **Dependency Management**: pip with requirements.txt

## Port Configuration

- **Development**: Port 3000 (Flask)
- **Docker**: Port 3000 (mapped from 5000 internally)
- **Health Check**: GET /status (every 30 seconds)

## File Deployment

Current entry point: `run_flask.py`
```bash
python run_flask.py      # Development
docker-compose up -d     # Production with Docker
```

Docker Compose:
- Service: `intelligent-query-app`
- Image: `intelligent-query:latest`
- Port: `3000:5000`
- Health Check: `curl -f http://localhost:5000/status || exit 1`
- Logs Volume: `/app/logs` (persisted)

## Development Workflow

1. **Local Development**:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python run_flask.py
   ```

2. **Docker Development**:
   ```bash
   docker-compose up --build -d
   docker-compose logs -f
   docker-compose down
   ```

3. **Testing**:
   ```bash
   python -m pytest test/  # When tests are added in Phase 5
   ```

## Next Steps

1. Review Phase 1 completion (see `docs/PHASE_1_COMPLETE.md`)
2. Begin Phase 2 service implementation
3. Add unit tests for services
4. Refactor Flask app to use services (Phase 4)
5. Push Docker image to Docker Hub

See `docs/QUICK_REFERENCE.md` for developer quick reference.
