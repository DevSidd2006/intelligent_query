# PDF Question-Answer System

A web application that allows users to upload PDF documents and ask questions about their content using AI.

## Features

- 📄 **PDF Upload**: Drag & drop PDF files up to 16MB
- 🤖 **AI-Powered Q&A**: Ask questions and get intelligent answers
- 🎨 **Beautiful UI**: Modern, responsive web interface
- ⚡ **Fast Processing**: Quick document analysis and response generation
- 🔒 **Secure**: Files are processed temporarily and not stored permanently

## Technologies Used

- **Backend**: Flask, Python
- **AI**: OpenRouter API for accessing multiple AI models (Claude, GPT, etc.)
- **Document Processing**: PyMuPDF for PDF text extraction
- **Search**: FAISS for semantic similarity search
- **ML**: Sentence Transformers for embeddings
- **Frontend**: Bootstrap 5, vanilla JavaScript

## Project Structure

```
pdf-qa-system/
├── src/                    # Source code
│   ├── new_app.py             # Core AI/PDF processing
│   └── web_app.py         # Flask web application
├── scripts/               # Setup and utility scripts
├── docs/                  # Documentation
├── .github/workflows/     # CI/CD workflows
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
├── docker-compose.yml    # Multi-container setup
├── CONTRIBUTING.md       # Contribution guidelines

# Intelligent Query: PDF Q&A System

## Overview

Intelligent Query is a Dockerized Python application for secure, high-performance Q&A on PDF documents using advanced LLMs (Claude Sonnet 4 via OpenRouter). It supports both Flask and FastAPI backends, robust error handling, health checks, async model loading, and performance profiling.

## Features

- Upload PDF documents and ask questions
- Advanced prompt engineering for insurance/health Q&A
- Supports Claude Sonnet 4 (OpenRouter API)
- Dockerized for easy deployment
- Health check and performance endpoints
- Async model loading and caching
- Rate limiting and authentication
- Logging and monitoring

## Project Structure

```
.env.example
.gitignore
.dockerignore
.gitattributes
README.md
requirements.txt
docker-compose.yml
Dockerfile
CONTRIBUTING.md
PROJECT_STRUCTURE.md
OPTIMIZATION.md
PYMUPDF_OPTIMIZATION.md
FIXES_IMPLEMENTED.md
src/
    app.py
    web_app.py
    new_app.py
    final_app.py
    app.log
    web_app.log
scripts/
    setup-docker.bat
    start-server.bat
    test_hackrx_endpoint.py
    test_openai_docker.py
    test_openrouter.py
    test_local_performance.py
docs/
    DOCKER_DEPLOYMENT.md
    DOCKER_README.md
uploads/
```

## Quick Start

1. Clone the repository:
   ```powershell
   git clone <repo-url>
   cd Intelligent_Query
   ```
2. Copy `.env.example` to `.env` and set your API keys:
   ```powershell
   Copy-Item .env.example .env
   # Edit .env and set OPENROUTER_API_KEY
   ```
3. Build and run with Docker Compose:
   ```powershell
   docker-compose up --build
   ```
4. Access the web app at [http://localhost:3000](http://localhost:3000)

## Endpoints

### Flask (`src/web_app.py`)
- `/` : Main web interface for PDF upload and Q&A
- `/health` : Health check endpoint
- `/run` : Q&A API endpoint

### FastAPI (`src/new_app.py`, `src/final_app.py`)
- `/health` : Health check endpoint
- `/run` : Q&A API endpoint

## Documentation

- [Project Structure](PROJECT_STRUCTURE.md)
- [Docker Deployment Guide](docs/DOCKER_DEPLOYMENT.md)
- [Docker Usage](docs/DOCKER_README.md)
- [Optimization Notes](OPTIMIZATION.md)
- [Contributing](CONTRIBUTING.md)

## Testing & Performance

- Run test scripts in `scripts/` for endpoint and performance validation
- Example: `python scripts/test_openai_docker.py`

## License

Add your license here.

## Contact

For issues or contributions, open a GitHub issue or pull request.
