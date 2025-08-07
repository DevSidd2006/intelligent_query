FROM python:3.11-slim

# Set metadata
LABEL maintainer="Devsidd2006"
LABEL description="Intelligent Query PDF Q&A System - AI-powered document analysis with advanced optimization"
LABEL version="1.1.0"
LABEL features="Model caching, Parallel processing, GPU acceleration, Memory-efficient streaming, Document-level caching"

# Accept build arguments for configuring which service to run
ARG SERVICE_TYPE=web_app
ARG PORT=3000
ARG ENABLE_GPU=false
ARG ENABLE_PARALLEL=true
ARG CACHE_LEVEL=aggressive

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    curl \
    wget \
    htop \
    python3-dev \
    libblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies with optimizations
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    # Install additional optimization packages
    pip install --no-cache-dir \
    torch-optimizer \
    huggingface_hub[cli] \
    joblib \
    ujson \
    psutil \
    ray[default] \
    msgpack \
    lz4


# Copy application code
COPY src/ ./src/

# Create directories with proper permissions
RUN mkdir -p uploads && \
    mkdir -p logs && \
    mkdir -p cache/models && \
    mkdir -p cache/documents && \
    mkdir -p cache/embeddings && \
    mkdir -p cache/responses && \
    chmod 755 uploads logs cache


# Set environment variables with proper Python path
ENV PYTHONPATH="/app/src:/app"
ENV PYTHONUNBUFFERED=1
ENV SERVICE_TYPE=${SERVICE_TYPE}
ENV PORT=${PORT}
ENV TRANSFORMERS_CACHE="/app/cache/models"
ENV HF_HOME="/app/cache/models"
ENV TORCH_HOME="/app/cache/models"
ENV ENABLE_PARALLEL=${ENABLE_PARALLEL}
ENV CACHE_LEVEL=${CACHE_LEVEL}
ENV SENTENCE_TRANSFORMERS_HOME="/app/cache/models"
ENV TOKENIZERS_PARALLELISM=true

# Create a health check endpoint for app.py
COPY scripts/create_health_endpoint.py ./scripts/

# Add startup script
COPY scripts/docker-entrypoint.sh ./scripts/
RUN chmod +x ./scripts/docker-entrypoint.sh

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose ports for both services
EXPOSE 3000 5000

# Dynamic health check based on the running service
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD if [ "$SERVICE_TYPE" = "web_app" ]; then \
            curl -f http://localhost:$PORT/status || exit 1; \
        else \
            curl -f http://localhost:$PORT/health || exit 1; \
        fi

# Use entrypoint script to start the appropriate service
ENTRYPOINT ["./scripts/docker-entrypoint.sh"]
