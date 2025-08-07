# Project Structure for Intelligent_Query

## Folders
- `src/` : Main Python source code (FastAPI, Flask, utilities)
- `scripts/` : Utility, test, and deployment scripts
- `docs/` : Documentation (Docker, API, usage)
- `uploads/` : User-uploaded files (PDFs, DOCX, etc.)

## Root Files
- `requirements.txt` : Python dependencies
- `Dockerfile`, `Dockerfile.new` : Docker setup
- `docker-compose.yml` : Multi-container setup
- `README.md` : Project overview and instructions
- `.gitignore` : Ignore files for Git
- `CONTRIBUTING.md` : Contribution guidelines
- `OPTIMIZATION.md`, `PROJECT_STRUCTURE.md`, `PYMUPDF_OPTIMIZATION.md`, `FIXES_IMPLEMENTED.md` : Technical notes

## Example Tree
```
Intelligent_Query/
├── src/
├── scripts/
├── docs/
├── uploads/
├── requirements.txt
├── Dockerfile
├── Dockerfile.new
├── docker-compose.yml
├── README.md
├── .gitignore
├── CONTRIBUTING.md
├── OPTIMIZATION.md
├── PROJECT_STRUCTURE.md
├── PYMUPDF_OPTIMIZATION.md
├── FIXES_IMPLEMENTED.md
```

## Best Practices
- Keep code, scripts, docs, and uploads separate
- Use `.gitignore` to avoid pushing logs, cache, uploads, and secrets
- Document API endpoints and setup in `README.md`
- Use Docker for reproducible deployment
# Project Structure

```
pdf-qa-system/
├── src/                          # Source code
│   ├── __init__.py              # Package initialization
│   ├── app.py                   # Core AI/PDF processing logic
│   └── web_app.py               # Flask web application
├── scripts/                     # Utility scripts
│   ├── setup-docker.bat        # Docker setup (Windows)
│   ├── setup-ngrok.bat         # Ngrok setup (Windows)
│   ├── start-ngrok.bat         # Start ngrok tunnel
│   ├── start-server.bat        # Start server (Windows)
├── docs/                        # Documentation
│   ├── DOCKER_README.md        # Docker setup guide
│   ├── NGROK-SETUP.md          # Ngrok setup guide
│   └── README-DOCKERHUB.md     # Docker Hub deployment guide
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── .gitattributes              # Git attributes for line endings
├── .dockerignore               # Docker ignore rules
├── Dockerfile                   # Docker container definition
├── docker-compose.yml          # Docker Compose configuration
├── requirements.txt             # Python dependencies
└── README.md                    # Main project documentation
```

## Key Files

### Source Code (`src/`)
- **app.py**: Core AI and PDF processing functionality
- **web_app.py**: Flask web application with UI

### Configuration
- **.env.example**: Template for environment variables
- **requirements.txt**: Python package dependencies
- **Dockerfile**: Container configuration
- **docker-compose.yml**: Multi-container setup

### Documentation (`docs/`)
- Deployment guides
- Setup instructions
- API documentation
