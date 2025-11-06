# 📚 API Documentation - Intelligent Query System

## Overview

The Intelligent Query API provides programmatic access to AI-powered document analysis capabilities. Built with FastAPI, it offers high-performance document processing and question-answering services.

## Base URL

```
Production: https://your-domain.com/api/v1
Development: http://localhost:3000
```

## Authentication

All API requests require Bearer token authentication:

```http
Authorization: Bearer YOUR_API_TOKEN
```

### Getting an API Token

Set the `HACKRX_BEARER_TOKEN` environment variable in your `.env` file:
```bash
HACKRX_BEARER_TOKEN=your_secure_token_here
```

## Endpoints

### Health Check

Check the API service status and configuration.

**Endpoint:** `GET /health`

**Headers:**
- None required

**Response:**
```json
{
  "status": "healthy",
  "service": "Intelligent Query PDF Q&A System",
  "version": "1.0.0",
  "api_configured": true,
  "cache_size": 5,
  "uptime": 1635789123.456
}
```

**Status Codes:**
- `200`: Service is healthy
- `503`: Service is unhealthy

**Example:**
```bash
curl -X GET "http://localhost:3000/health"
```

---

### Document Analysis

Process a document and answer questions about its content.

**Endpoint:** `POST /hackrx/run`

**Headers:**
```http
Authorization: Bearer YOUR_TOKEN
Content-Type: application/json
```

**Request Body:**
```json
{
  "documents": "string",
  "questions": ["string"]
}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `documents` | string | ✅ | URL to the document (PDF, DOCX, or email) |
| `questions` | array[string] | ✅ | List of questions to ask about the document |

**Response:**
```json
{
  "answers": [
    "string"
  ]
}
```

**Status Codes:**
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `401`: Unauthorized (invalid token)
- `429`: Rate Limit Exceeded
- `500`: Internal Server Error

**Example Request:**
```bash
curl -X POST "http://localhost:3000/hackrx/run" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "documents": "https://example.com/sample.pdf",
       "questions": [
         "What is the main topic of this document?",
         "What are the key findings?",
         "Who are the authors?"
       ]
     }'
```

**Example Response:**
```json
{
  "answers": [
    "The main topic of this document is artificial intelligence applications in healthcare, specifically focusing on diagnostic imaging and patient care optimization.",
    "The key findings include a 25% improvement in diagnostic accuracy, 40% reduction in processing time, and enhanced patient satisfaction scores.",
    "The authors are Dr. Jane Smith from MIT, Dr. John Doe from Stanford University, and Dr. Sarah Johnson from Johns Hopkins."
  ]
}
```

---

## Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "success": false,
  "error": "Error description",
  "details": "Additional error details (optional)"
}
```

### Common Error Codes

#### 400 Bad Request
```json
{
  "success": false,
  "error": "Missing 'documents' parameter. Please provide a URL to the document."
}
```

#### 401 Unauthorized
```json
{
  "success": false,
  "error": "Invalid Bearer token."
}
```

#### 429 Rate Limit Exceeded
```json
{
  "success": false,
  "error": "Rate limit exceeded. Please try again later."
}
```

#### 500 Internal Server Error
```json
{
  "success": false,
  "error": "Failed to process document",
  "details": "Specific error message"
}
```

---

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Limit**: 20 requests per minute per IP address
- **Window**: 60 seconds (sliding window)
- **Headers**: Rate limit information is included in response headers

**Rate Limit Headers:**
```http
X-RateLimit-Limit: 20
X-RateLimit-Remaining: 15
X-RateLimit-Reset: 1635789183
```

---

## Supported Document Formats

### PDF Documents
- **Max Size**: 200MB
- **Formats**: PDF 1.0 - 2.0
- **Features**: Text extraction, table detection, image descriptions

### Microsoft Word Documents
- **Max Size**: 200MB
- **Formats**: .docx (Office 2007+)
- **Features**: Text extraction, formatting preservation

### Email Files
- **Max Size**: 50MB
- **Formats**: .eml, .msg
- **Features**: Header extraction, body text, attachments list

---

## Performance Considerations

### Response Times
- **Document Processing**: 30-120 seconds (depending on size)
- **Question Answering**: 2-10 seconds per question
- **Cached Documents**: <1 second for subsequent questions

### Optimization Tips

1. **Document Size**: Smaller documents process faster
2. **Question Batching**: Ask multiple questions in one request
3. **Caching**: Repeated questions on the same document are cached
4. **Concurrent Requests**: Limit to 5 concurrent requests per client

---

## SDK Examples

### Python SDK

```python
import requests
import json

class IntelligentQueryClient:
    def __init__(self, base_url, api_token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
    
    def analyze_document(self, document_url, questions):
        """Analyze a document and get answers to questions."""
        payload = {
            'documents': document_url,
            'questions': questions
        }
        
        response = requests.post(
            f'{self.base_url}/hackrx/run',
            headers=self.headers,
            json=payload
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f'API Error: {response.status_code} - {response.text}')
    
    def health_check(self):
        """Check API health status."""
        response = requests.get(f'{self.base_url}/health')
        return response.json()

# Usage example
client = IntelligentQueryClient(
    base_url='http://localhost:3000',
    api_token='your_token_here'
)

# Analyze document
result = client.analyze_document(
    document_url='https://example.com/document.pdf',
    questions=[
        'What is the main topic?',
        'Who are the key stakeholders?'
    ]
)

print(result['answers'])
```

### JavaScript SDK

```javascript
class IntelligentQueryClient {
    constructor(baseUrl, apiToken) {
        this.baseUrl = baseUrl;
        this.headers = {
            'Authorization': `Bearer ${apiToken}`,
            'Content-Type': 'application/json'
        };
    }

    async analyzeDocument(documentUrl, questions) {
        const response = await fetch(`${this.baseUrl}/hackrx/run`, {
            method: 'POST',
            headers: this.headers,
            body: JSON.stringify({
                documents: documentUrl,
                questions: questions
            })
        });

        if (!response.ok) {
            throw new Error(`API Error: ${response.status} - ${await response.text()}`);
        }

        return await response.json();
    }

    async healthCheck() {
        const response = await fetch(`${this.baseUrl}/health`);
        return await response.json();
    }
}

// Usage example
const client = new IntelligentQueryClient(
    'http://localhost:3000',
    'your_token_here'
);

// Analyze document
client.analyzeDocument(
    'https://example.com/document.pdf',
    ['What is the main topic?', 'Who are the key stakeholders?']
).then(result => {
    console.log(result.answers);
}).catch(error => {
    console.error('Error:', error);
});
```

### cURL Examples

#### Basic Document Analysis
```bash
curl -X POST "http://localhost:3000/hackrx/run" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "documents": "https://example.com/research-paper.pdf",
       "questions": [
         "What is the research methodology used?",
         "What are the main conclusions?",
         "What future work is suggested?"
       ]
     }'
```

#### Health Check
```bash
curl -X GET "http://localhost:3000/health" \
     -H "Accept: application/json"
```

#### With Error Handling
```bash
#!/bin/bash

TOKEN="your_token_here"
DOCUMENT_URL="https://example.com/document.pdf"

response=$(curl -s -w "%{http_code}" -X POST "http://localhost:3000/hackrx/run" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d "{
       \"documents\": \"$DOCUMENT_URL\",
       \"questions\": [\"What is this document about?\"]
     }")

http_code="${response: -3}"
body="${response%???}"

if [ "$http_code" -eq 200 ]; then
    echo "Success: $body"
else
    echo "Error ($http_code): $body"
fi
```

---

## Webhooks (Future Feature)

### Webhook Configuration
```json
{
  "webhook_url": "https://your-app.com/webhook",
  "events": ["document.processed", "analysis.completed"],
  "secret": "webhook_secret_key"
}
```

### Webhook Payload
```json
{
  "event": "analysis.completed",
  "timestamp": "2023-11-01T12:00:00Z",
  "data": {
    "document_id": "doc_123",
    "status": "completed",
    "answers": ["Answer 1", "Answer 2"]
  }
}
```

---

## Testing

### Test Environment
```
Base URL: http://localhost:3000
Test Token: test_token_123
```

### Sample Test Document
```
URL: https://hackrx.blob.core.windows.net/assets/policy.pdf
Type: Insurance Policy Document
Size: ~2MB
Pages: 45
```

### Test Questions
```json
[
  "What is the grace period for premium payment?",
  "What is the waiting period for pre-existing diseases?",
  "Does this policy cover maternity expenses?",
  "What is the No Claim Discount offered?",
  "Are there any sub-limits on room rent?"
]
```

---

## Monitoring & Analytics

### Request Logging
All API requests are logged with:
- Timestamp
- Client IP
- Request method and path
- Response status
- Processing time
- Error details (if any)

### Metrics Available
- Request count per endpoint
- Average response time
- Error rate by status code
- Document processing time
- Cache hit/miss ratio

### Health Monitoring
```bash
# Check service health
curl http://localhost:3000/health

# Monitor response time
time curl -X POST "http://localhost:3000/hackrx/run" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"documents": "URL", "questions": ["test"]}'
```

---

## Best Practices

### 1. Authentication Security
- Store API tokens securely
- Rotate tokens regularly
- Use HTTPS in production
- Implement token expiration

### 2. Request Optimization
- Batch multiple questions in single request
- Use appropriate document URLs (direct links)
- Implement client-side caching
- Handle rate limits gracefully

### 3. Error Handling
- Always check response status codes
- Implement retry logic with exponential backoff
- Log errors for debugging
- Provide user-friendly error messages

### 4. Performance
- Monitor response times
- Implement request timeouts
- Use connection pooling
- Cache frequently accessed documents

---

## Changelog

### Version 1.0.0 (Current)
- Initial API release
- Document analysis endpoint
- Health check endpoint
- Bearer token authentication
- Rate limiting implementation

### Version 1.1.0 (Planned)
- Batch document processing
- Webhook support
- Enhanced error reporting
- Performance improvements

---

## Support

For API support and questions:
- **Documentation**: [API Docs](https://your-domain.com/docs)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Email**: api-support@your-domain.com

---

*Last updated: November 2024*