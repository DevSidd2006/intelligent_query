# 🤖 Intelligent Query - AI-Powered PDF Q&A System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-green.svg)](https://fastapi.tiangolo.com/)
[![Flask](https://img.shields.io/badge/Flask-3.1.2-red.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A sophisticated AI-powered document analysis system that enables users to upload PDF documents and ask intelligent questions about their content. Built with modern AI technologies including Groq's ultra-fast inference, semantic search, and advanced document processing.

## 🌟 Key Features

### � **Advanced Document Processing**
- **Multi-format Support**: PDF, DOCX, and email files (.eml)
- **Large File Handling**: Support for documents up to 200MB
- **Fast Extraction**: PyMuPDF with pdfplumber fallback for optimal performance
- **Smart Chunking**: Intelligent text segmentation preserving context

### 🧠 **AI-Powered Intelligence**
- **Groq Integration**: Ultra-fast inference with Llama 3.1 8B Instant model
- **Semantic Search**: FAISS-powered vector similarity search
- **Context-Aware Responses**: Maintains document context across conversations
- **Multiple AI Models**: Support for various embedding models

### 🚀 **Performance & Scalability**
- **Intelligent Caching**: Document and model caching with TTL
- **Async Processing**: Concurrent request handling
- **Rate Limiting**: Built-in protection against abuse
- **Memory Optimization**: Efficient resource management

### 🔒 **Enterprise-Ready Security**
- **Bearer Token Authentication**: Secure API access
- **Input Validation**: Comprehensive security checks
- **Non-root Execution**: Docker security best practices
- **Environment Isolation**: Secure configuration management

### 🌐 **Dual Interface Options**
- **Web Interface**: Modern, responsive chat-based UI
- **REST API**: Full programmatic access with OpenAPI documentation
- **Docker Support**: Containerized deployment ready

## 📚 Documentation

**Complete documentation is available in the `docs/` directory:**

- **[Project Structure](docs/PROJECT_STRUCTURE.md)** - Detailed module and directory organization
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - For developers setting up the project
- **[Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Production deployment instructions
- **[User Guide](docs/USER_GUIDE.md)** - End-user documentation
- **[API Documentation](docs/API_DOCUMENTATION.md)** - Complete API reference
- **[Docker Deployment](docs/DOCKER_DEPLOYMENT.md)** - Docker setup and management
- **[Docker Hub Guide](docs/README-DOCKERHUB.md)** - Docker Hub integration
- **[Architecture Improvements](docs/ARCHITECTURE_IMPROVEMENTS.md)** - Refactoring roadmap
- **[Phase 1 Complete](docs/PHASE_1_COMPLETE.md)** - Architecture foundation summary
- **[Codebase Organization](docs/CODEBASE_ORGANIZATION.md)** - Current cleanup status
- **[Quick Reference](docs/QUICK_REFERENCE.md)** - Developer quick reference

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Interface │    │    REST API      │    │   Docker        │
│   (Flask)       │    │   (FastAPI)      │    │   Container     │
└─────────┬───────┘    └────────┬─────────┘    └─────────┬───────┘
          │                     │                        │
          └─────────────────────┼────────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   Core Engine         │
                    │   - Document Parser   │
                    │   - Embedding Engine  │
                    │   - Vector Search     │
                    │   - AI Integration    │
                    └───────────┬───────────┘
                                │
          ┌─────────────────────┼─────────────────────┐
          │                     │                     │
    ┌─────▼─────┐    ┌─────────▼────────┐    ┌──────▼──────┐
    │  PyMuPDF  │    │ SentenceTransf.  │    │   Groq API  │
    │ PDFPlumber│    │     FAISS        │    │ Llama 3.1   │
    └───────────┘    └──────────────────┘    └─────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- Git
- Groq API key ([Get one here](https://console.groq.com/keys))

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/intelligent-query.git
cd intelligent-query
```

### 2. Set Up Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
.\venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
# Copy environment template
cp .env.example .env

# Edit .env file and add your Groq API key
# GROQ_API_KEY=your_groq_api_key_here
```

### 5. Run the Application

#### Option A: Web Interface (Recommended for beginners)
```bash
python run_flask.py
```
Open your browser and go to: http://localhost:5000

#### Option B: API Server (For developers)
```bash
python -c "import uvicorn; uvicorn.run('src.app:app', host='0.0.0.0', port=3000)"
```
API Documentation: http://localhost:3000/docs

### 6. Test the Setup
```bash
python test_setup.py
```

## 📖 Usage Guide

### Web Interface Usage

1. **Upload Document**: Drag and drop a PDF file or click to browse
2. **Wait for Processing**: The system will extract and index the document
3. **Ask Questions**: Type your questions in the chat interface
4. **Get Answers**: Receive AI-powered responses based on document content

### API Usage

#### Authentication
All API requests require a Bearer token:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     http://localhost:3000/health
```

#### Process Document and Ask Questions
```bash
curl -X POST "http://localhost:3000/hackrx/run" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "documents": "https://example.com/document.pdf",
       "questions": [
         "What is the main topic of this document?",
         "What are the key findings?"
       ]
     }'
```

#### Response Format
```json
{
  "answers": [
    "The main topic of this document is artificial intelligence and machine learning applications in healthcare.",
    "The key findings include improved diagnostic accuracy and reduced processing time."
  ]
}
```

## 🐳 Docker Deployment

### Quick Docker Setup
```bash
# Build and run with Docker Compose
docker-compose up --build -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### Manual Docker Commands
```bash
# Build image
docker build -t intelligent-query .

# Run container
docker run -d \
  --name intelligent-query-app \
  -p 5000:5000 \
  --env-file .env \
  -v $(pwd)/uploads:/app/uploads \
  intelligent-query
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GROQ_API_KEY` | Groq API key for AI inference | - | ✅ |
| `SECRET_KEY` | Flask secret key | Generated | ✅ |
| `PORT` | Application port | 3000 | ❌ |
| `MAX_FILE_SIZE` | Maximum upload size (bytes) | 16777216 | ❌ |
| `DEBUG` | Enable debug mode | False | ❌ |
| `HACKRX_BEARER_TOKEN` | API authentication token | - | ✅ |

### Advanced Configuration

#### Model Selection
```python
# In src/app.py, modify get_sentence_transformer()
model = SentenceTransformer('all-MiniLM-L6-v2')  # Fast
model = SentenceTransformer('all-mpnet-base-v2')  # Balanced
model = SentenceTransformer('BAAI/bge-large-en-v1.5')  # Accurate
```

#### Cache Settings
```python
# Document cache configuration
MAX_CACHE_SIZE = 10  # Number of documents to cache
CACHE_TTL = 3600     # Cache time-to-live in seconds
```

## 📊 Performance Benchmarks

### Processing Speed
- **Document Processing**: ~30-60 seconds for 100-page PDF
- **Question Answering**: ~2-5 seconds per question
- **Concurrent Users**: Supports 10+ simultaneous users

### Resource Usage
- **Memory**: ~2-4GB RAM for optimal performance
- **Storage**: ~1GB for models and cache
- **CPU**: Multi-core recommended for concurrent processing

### Optimization Tips
1. **Use SSD storage** for faster model loading
2. **Increase RAM** for larger document caches
3. **Enable GPU** for faster embedding generation (optional)
4. **Use CDN** for static assets in production

## 🧪 Testing

### Run All Tests
```bash
# Environment setup test
python test_setup.py

# API client test
python test_openai_client.py

# Import tests
python test_web_app_imports.py

# Performance benchmark
python test/benchmark.py
```

### API Testing
```bash
# Test health endpoint
curl http://localhost:3000/health

# Test with sample document
python scripts/test_openrouter.py
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Import Errors
**Problem**: `ModuleNotFoundError` or import issues
**Solution**:
```bash
# Ensure virtual environment is activated
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Reinstall dependencies
pip install -r requirements.txt
```

#### 2. API Key Issues
**Problem**: "API key not configured" error
**Solution**:
```bash
# Check .env file exists and contains valid key
cat .env | grep GROQ_API_KEY

# Test API key
python test_openai_client.py
```

#### 3. Memory Issues
**Problem**: Out of memory errors
**Solution**:
- Reduce `MAX_CACHE_SIZE` in configuration
- Use smaller embedding models
- Process smaller documents
- Increase system RAM

#### 4. Port Conflicts
**Problem**: "Port already in use" error
**Solution**:
```bash
# Find process using port
netstat -ano | findstr :5000  # Windows
lsof -i :5000                 # macOS/Linux

# Kill process or change port in .env
```

### Debug Mode
Enable debug logging:
```bash
# Set environment variable
export DEBUG=True  # Linux/macOS
set DEBUG=True     # Windows

# Or modify .env file
DEBUG=True
```

## 🛠️ Development

### Project Structure
```
intelligent-query/
├── src/                    # Source code
│   ├── app.py             # FastAPI application
│   ├── web_app.py         # Flask web interface
│   └── new_app.py         # Optimized FastAPI version
├── scripts/               # Utility scripts
│   ├── setup-docker.bat   # Docker setup (Windows)
│   └── test_*.py          # Test scripts
├── docs/                  # Documentation
├── test/                  # Test files
├── uploads/               # File upload directory
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Multi-container setup
└── .env.example          # Environment template
```

### Adding New Features

#### 1. New Document Format Support
```python
# In src/app.py, add new extraction function
def extract_text_from_new_format(file_path):
    # Implementation here
    pass

# Update download_and_extract_text function
elif ext in ['.new_ext']:
    return extract_text_from_new_format(tmp_path)
```

#### 2. Custom AI Models
```python
# Add new model in get_sentence_transformer()
def get_custom_model():
    return SentenceTransformer('your-custom-model')
```

#### 3. New API Endpoints
```python
# In src/app.py
@app.post("/new-endpoint")
async def new_endpoint():
    # Implementation here
    pass
```

### Code Style Guidelines
- Follow PEP 8 for Python code
- Use type hints where possible
- Add docstrings for functions
- Keep functions focused and small
- Use meaningful variable names

## 🚀 Deployment

### Production Deployment

#### 1. Environment Setup
```bash
# Production environment variables
FLASK_ENV=production
DEBUG=False
SECRET_KEY=your_strong_secret_key
GROQ_API_KEY=your_api_key
```

#### 2. Docker Production
```yaml
# docker-compose.prod.yml
services:
  app:
    build: .
    restart: always
    ports:
      - "80:5000"
    environment:
      - FLASK_ENV=production
    volumes:
      - ./uploads:/app/uploads
```

#### 3. Cloud Deployment Options

**Railway.app**:
```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway init
railway up
```

**Heroku**:
```bash
# Create Heroku app
heroku create your-app-name

# Set environment variables
heroku config:set GROQ_API_KEY=your_key

# Deploy
git push heroku main
```

**AWS/GCP/Azure**:
- Use Docker container deployment
- Configure load balancer for scaling
- Set up persistent storage for uploads
- Configure environment variables securely

### Scaling Considerations
1. **Load Balancing**: Use nginx or cloud load balancers
2. **Database**: Consider PostgreSQL for persistent storage
3. **Caching**: Redis for distributed caching
4. **Monitoring**: Implement health checks and logging
5. **Security**: HTTPS, rate limiting, input validation

## 📈 Monitoring & Analytics

### Health Monitoring
```bash
# Check application health
curl http://localhost:3000/health

# Monitor Docker containers
docker-compose ps
docker-compose logs -f
```

### Performance Metrics
- Response time per request
- Document processing time
- Cache hit/miss ratios
- Memory and CPU usage
- API error rates

### Logging
Logs are written to:
- Console output
- `app.log` (FastAPI)
- `web_app.log` (Flask)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Reporting Issues
Please include:
- Environment details (OS, Python version)
- Steps to reproduce
- Expected vs actual behavior
- Error messages and logs

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Groq** for ultra-fast AI inference
- **Hugging Face** for transformer models
- **FAISS** for efficient similarity search
- **PyMuPDF** for fast PDF processing
- **FastAPI** and **Flask** for web frameworks

## 📚 Documentation

### Complete Documentation Suite
- **📖 [User Guide](docs/USER_GUIDE.md)** - Complete user manual with best practices
- **🔌 [API Documentation](docs/API_DOCUMENTATION.md)** - Comprehensive API reference
- **🚀 [Deployment Guide](docs/DEPLOYMENT_GUIDE.md)** - Deploy to any platform
- **🛠️ [Developer Guide](docs/DEVELOPER_GUIDE.md)** - Architecture and development
- **🤝 [Contributing Guidelines](CONTRIBUTING.md)** - How to contribute
- **📝 [Changelog](CHANGELOG.md)** - Version history and updates

### Quick Links
- **🎯 [Getting Started](#-quick-start)** - Set up in 5 minutes
- **💡 [Usage Examples](#-usage-guide)** - Common use cases
- **🐳 [Docker Deployment](#-docker-deployment)** - Containerized setup
- **🔧 [Configuration](#-configuration)** - Environment setup
- **🧪 [Testing](#-testing)** - Quality assurance

## 📞 Support

- **📖 Documentation**: [Complete Documentation Suite](docs/)
- **🐛 Issues**: [GitHub Issues](https://github.com/your-username/intelligent-query/issues)
- **💬 Discussions**: [GitHub Discussions](https://github.com/your-username/intelligent-query/discussions)
- **📧 Email**: support@your-domain.com

## 🗺️ Roadmap

### Version 2.0 (Planned)
- [ ] Multi-document comparison
- [ ] Document summarization
- [ ] Custom model fine-tuning
- [ ] Real-time collaboration
- [ ] Advanced analytics dashboard

### Version 2.1 (Future)
- [ ] Multi-modal analysis (text + images)
- [ ] Voice interaction
- [ ] Mobile app
- [ ] Enterprise SSO integration

---

**Made with ❤️ by the Intelligent Query Team**

*Transform your documents into intelligent conversations!*