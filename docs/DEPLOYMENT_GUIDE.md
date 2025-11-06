# 🚀 Deployment Guide - Intelligent Query System

This comprehensive guide covers various deployment options for the Intelligent Query PDF Q&A System, from local development to production cloud deployment.

## 📋 Prerequisites

### System Requirements
- **CPU**: 2+ cores recommended (4+ for production)
- **RAM**: 4GB minimum, 8GB+ recommended
- **Storage**: 10GB+ available space
- **Network**: Stable internet connection for AI API calls

### Software Requirements
- **Python**: 3.11 or higher
- **Docker**: 20.10+ (for containerized deployment)
- **Git**: For source code management
- **Node.js**: 16+ (for some deployment platforms)

### API Keys Required
- **Groq API Key**: [Get from Groq Console](https://console.groq.com/keys)
- **Bearer Token**: Generate a secure token for API authentication

## 🏠 Local Development Deployment

### 1. Quick Setup
```bash
# Clone repository
git clone https://github.com/your-username/intelligent-query.git
cd intelligent-query

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run application
python run_flask.py
```

### 2. Development Server Options

#### Flask Web Interface (Port 5000)
```bash
python run_flask.py
# Access: http://localhost:5000
```

#### FastAPI Server (Port 3000)
```bash
uvicorn src.app:app --host 0.0.0.0 --port 3000 --reload
# Access: http://localhost:3000
# API Docs: http://localhost:3000/docs
```

### 3. Development Configuration
```bash
# .env for development
DEBUG=True
FLASK_ENV=development
LOG_LEVEL=DEBUG
GROQ_API_KEY=your_groq_api_key
SECRET_KEY=dev_secret_key
HACKRX_BEARER_TOKEN=dev_bearer_token
```

## 🐳 Docker Deployment

### 1. Docker Compose (Recommended)

#### Quick Start
```bash
# Build and start
docker-compose up --build -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

#### Production Docker Compose
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  intelligent-query:
    build: .
    container_name: intelligent-query-prod
    restart: unless-stopped
    ports:
      - "80:5000"
    environment:
      - FLASK_ENV=production
      - DEBUG=False
    env_file:
      - .env.production
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    container_name: nginx-proxy
    restart: unless-stopped
    ports:
      - "443:443"
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - intelligent-query
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
```

### 2. Manual Docker Build

#### Build Image
```bash
# Build production image
docker build -t intelligent-query:latest .

# Build with specific tag
docker build -t intelligent-query:v1.0.0 .

# Build for different architecture
docker buildx build --platform linux/amd64,linux/arm64 -t intelligent-query:latest .
```

#### Run Container
```bash
# Basic run
docker run -d \
  --name intelligent-query-app \
  -p 5000:5000 \
  --env-file .env \
  -v $(pwd)/uploads:/app/uploads \
  intelligent-query:latest

# Production run with resource limits
docker run -d \
  --name intelligent-query-prod \
  -p 80:5000 \
  --env-file .env.production \
  --memory=4g \
  --cpus=2 \
  --restart=unless-stopped \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/logs:/app/logs \
  intelligent-query:latest
```

### 3. Docker Optimization

#### Multi-stage Dockerfile
```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

# Copy installed packages
COPY --from=builder /root/.local /root/.local

# Set environment
ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app/src:/app
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY src/ ./src/
COPY .env.example .env

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 5000
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

CMD ["python", "src/web_app.py"]
```

## ☁️ Cloud Platform Deployment

### 1. Railway.app Deployment

#### Setup
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and initialize
railway login
railway init

# Set environment variables
railway variables set GROQ_API_KEY=your_key
railway variables set SECRET_KEY=your_secret
railway variables set HACKRX_BEARER_TOKEN=your_token

# Deploy
railway up
```

#### Railway Configuration
```json
{
  "build": {
    "builder": "DOCKERFILE"
  },
  "deploy": {
    "startCommand": "python src/web_app.py",
    "healthcheckPath": "/health"
  }
}
```

### 2. Heroku Deployment

#### Setup
```bash
# Install Heroku CLI
# Create Heroku app
heroku create your-app-name

# Set environment variables
heroku config:set GROQ_API_KEY=your_key
heroku config:set SECRET_KEY=your_secret
heroku config:set HACKRX_BEARER_TOKEN=your_token

# Deploy
git push heroku main
```

#### Procfile
```
web: python src/web_app.py
worker: python src/app.py
```

#### Heroku Configuration
```json
{
  "stack": "heroku-22",
  "buildpacks": [
    {
      "url": "heroku/python"
    }
  ],
  "formation": {
    "web": {
      "quantity": 1,
      "size": "standard-1x"
    }
  },
  "addons": [
    {
      "plan": "heroku-redis:mini"
    }
  ]
}
```

### 3. AWS Deployment

#### ECS with Fargate
```yaml
# task-definition.json
{
  "family": "intelligent-query",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "containerDefinitions": [
    {
      "name": "intelligent-query",
      "image": "your-account.dkr.ecr.region.amazonaws.com/intelligent-query:latest",
      "portMappings": [
        {
          "containerPort": 5000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "FLASK_ENV",
          "value": "production"
        }
      ],
      "secrets": [
        {
          "name": "GROQ_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:groq-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/intelligent-query",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Deploy to ECS
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account.dkr.ecr.us-east-1.amazonaws.com

docker build -t intelligent-query .
docker tag intelligent-query:latest your-account.dkr.ecr.us-east-1.amazonaws.com/intelligent-query:latest
docker push your-account.dkr.ecr.us-east-1.amazonaws.com/intelligent-query:latest

# Create ECS service
aws ecs create-service \
  --cluster your-cluster \
  --service-name intelligent-query \
  --task-definition intelligent-query:1 \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-12345],securityGroups=[sg-12345],assignPublicIp=ENABLED}"
```

### 4. Google Cloud Platform

#### Cloud Run Deployment
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/intelligent-query
gcloud run deploy --image gcr.io/PROJECT-ID/intelligent-query --platform managed

# Set environment variables
gcloud run services update intelligent-query \
  --set-env-vars GROQ_API_KEY=your_key,SECRET_KEY=your_secret
```

#### Cloud Run Configuration
```yaml
# cloudrun.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: intelligent-query
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/maxScale: "10"
        run.googleapis.com/memory: "4Gi"
        run.googleapis.com/cpu: "2"
    spec:
      containers:
      - image: gcr.io/PROJECT-ID/intelligent-query
        ports:
        - containerPort: 5000
        env:
        - name: FLASK_ENV
          value: "production"
        resources:
          limits:
            memory: "4Gi"
            cpu: "2"
```

### 5. Azure Deployment

#### Container Instances
```bash
# Create resource group
az group create --name intelligent-query-rg --location eastus

# Deploy container
az container create \
  --resource-group intelligent-query-rg \
  --name intelligent-query \
  --image your-registry/intelligent-query:latest \
  --dns-name-label intelligent-query-app \
  --ports 5000 \
  --environment-variables FLASK_ENV=production \
  --secure-environment-variables GROQ_API_KEY=your_key SECRET_KEY=your_secret
```

## 🔧 Production Configuration

### 1. Environment Variables

#### Production .env
```bash
# Application
FLASK_ENV=production
DEBUG=False
SECRET_KEY=your_very_secure_secret_key_here
PORT=5000

# API Configuration
GROQ_API_KEY=your_production_groq_api_key
HACKRX_BEARER_TOKEN=your_secure_bearer_token

# Performance
MAX_FILE_SIZE=209715200  # 200MB
CACHE_TTL=3600
MAX_CACHE_SIZE=20

# Security
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
CORS_ORIGINS=https://your-domain.com

# Logging
LOG_LEVEL=INFO
LOG_FILE=/app/logs/app.log
```

### 2. Nginx Configuration

#### nginx.conf
```nginx
events {
    worker_connections 1024;
}

http {
    upstream app {
        server intelligent-query:5000;
    }

    server {
        listen 80;
        server_name your-domain.com www.your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name your-domain.com www.your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        client_max_body_size 200M;

        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_read_timeout 300s;
            proxy_connect_timeout 75s;
        }

        location /health {
            proxy_pass http://app/health;
            access_log off;
        }
    }
}
```

### 3. SSL/TLS Configuration

#### Let's Encrypt with Certbot
```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 4. Monitoring Setup

#### Health Check Script
```bash
#!/bin/bash
# health-check.sh

URL="https://your-domain.com/health"
EXPECTED_STATUS="healthy"

response=$(curl -s "$URL")
status=$(echo "$response" | jq -r '.status')

if [ "$status" = "$EXPECTED_STATUS" ]; then
    echo "✅ Health check passed"
    exit 0
else
    echo "❌ Health check failed: $response"
    exit 1
fi
```

#### Monitoring with Prometheus
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'intelligent-query'
    static_configs:
      - targets: ['intelligent-query:5000']
    metrics_path: '/metrics'
    scrape_interval: 30s
```

## 🔒 Security Configuration

### 1. Firewall Rules
```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# Deny direct access to application port
sudo ufw deny 5000/tcp
```

### 2. Docker Security
```dockerfile
# Use non-root user
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Read-only filesystem
docker run --read-only --tmpfs /tmp --tmpfs /var/run intelligent-query

# Security options
docker run --security-opt=no-new-privileges:true intelligent-query
```

### 3. Environment Security
```bash
# Secure environment file permissions
chmod 600 .env
chown root:root .env

# Use secrets management
# AWS Secrets Manager
# Azure Key Vault
# Google Secret Manager
```

## 📊 Performance Optimization

### 1. Application Tuning
```python
# gunicorn.conf.py
bind = "0.0.0.0:5000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 300
keepalive = 2
```

### 2. Database Optimization (Future)
```python
# Redis caching configuration
REDIS_URL = "redis://redis:6379/0"
CACHE_DEFAULT_TIMEOUT = 3600
CACHE_KEY_PREFIX = "iq_"
```

### 3. CDN Configuration
```nginx
# Static file caching
location /static/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}

# API response caching
location /api/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_key "$request_uri";
}
```

## 🔄 CI/CD Pipeline

### 1. GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python test_setup.py

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to Railway
        run: |
          npm install -g @railway/cli
          railway login --token ${{ secrets.RAILWAY_TOKEN }}
          railway up
```

### 2. GitLab CI/CD
```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - deploy

test:
  stage: test
  image: python:3.11
  script:
    - pip install -r requirements.txt
    - python test_setup.py

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA

deploy:
  stage: deploy
  script:
    - kubectl set image deployment/intelligent-query app=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
```

## 🚨 Troubleshooting

### Common Deployment Issues

#### 1. Memory Issues
```bash
# Check memory usage
docker stats

# Increase container memory
docker run --memory=4g intelligent-query

# Monitor application memory
htop
```

#### 2. Port Conflicts
```bash
# Find process using port
netstat -tulpn | grep :5000
lsof -i :5000

# Kill process
sudo kill -9 PID
```

#### 3. SSL Certificate Issues
```bash
# Check certificate
openssl x509 -in cert.pem -text -noout

# Test SSL
curl -I https://your-domain.com
```

#### 4. API Connection Issues
```bash
# Test API connectivity
curl -H "Authorization: Bearer token" http://localhost:3000/health

# Check logs
docker logs intelligent-query-app
```

### Performance Issues

#### 1. Slow Response Times
- Increase worker processes
- Add Redis caching
- Optimize document processing
- Use CDN for static assets

#### 2. High Memory Usage
- Reduce cache size
- Use smaller ML models
- Implement garbage collection
- Monitor memory leaks

#### 3. Database Bottlenecks
- Add connection pooling
- Implement read replicas
- Use database caching
- Optimize queries

## 📈 Scaling Strategies

### 1. Horizontal Scaling
```yaml
# Kubernetes deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: intelligent-query
spec:
  replicas: 3
  selector:
    matchLabels:
      app: intelligent-query
  template:
    metadata:
      labels:
        app: intelligent-query
    spec:
      containers:
      - name: app
        image: intelligent-query:latest
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
```

### 2. Load Balancing
```nginx
upstream app_servers {
    server app1:5000 weight=3;
    server app2:5000 weight=2;
    server app3:5000 weight=1;
}
```

### 3. Auto-scaling
```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: intelligent-query-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: intelligent-query
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## 📞 Support

For deployment support:
- **Documentation**: [Deployment Docs](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Community**: [Discord Server](https://discord.gg/your-server)

---

*Last updated: November 2024*