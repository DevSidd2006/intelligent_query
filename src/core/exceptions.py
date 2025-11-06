"""
Custom exception hierarchy for Intelligent Query system.
Provides structured error handling and reporting.
"""

from typing import Optional, Dict, Any


class IntelliQueryException(Exception):
    """Base exception for all Intelligent Query errors"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response"""
        return {
            'error': self.error_code,
            'message': self.message,
            'details': self.details
        }


class ConfigurationError(IntelliQueryException):
    """Configuration or setup error"""
    pass


class ValidationError(IntelliQueryException):
    """Input validation error"""
    pass


# PDF Processing Errors
class PDFProcessingError(IntelliQueryException):
    """Base class for PDF processing errors"""
    pass


class PDFExtractionError(PDFProcessingError):
    """PDF text extraction failed"""
    pass


class PDFValidationError(PDFProcessingError):
    """PDF validation failed"""
    pass


class UnsupportedFileFormatError(PDFProcessingError):
    """Unsupported file format"""
    pass


class FileSizeExceededError(PDFProcessingError):
    """File size exceeds maximum allowed"""
    pass


# Embedding Errors
class EmbeddingError(IntelliQueryException):
    """Base class for embedding errors"""
    pass


class EmbeddingCreationError(EmbeddingError):
    """Failed to create embeddings"""
    pass


class ModelLoadError(EmbeddingError):
    """Failed to load embedding model"""
    pass


class SemanticSearchError(EmbeddingError):
    """Semantic search operation failed"""
    pass


# LLM Errors
class LLMError(IntelliQueryException):
    """Base class for LLM errors"""
    pass


class APIKeyError(LLMError):
    """API key missing or invalid"""
    pass


class RateLimitError(LLMError):
    """Rate limit exceeded"""
    pass


class TokenLimitError(LLMError):
    """Token limit exceeded"""
    pass


class LLMResponseError(LLMError):
    """Invalid response from LLM"""
    pass


class APIConnectionError(LLMError):
    """Failed to connect to API"""
    pass


# Cache Errors
class CacheError(IntelliQueryException):
    """Base class for cache errors"""
    pass


class CacheNotFoundError(CacheError):
    """Item not found in cache"""
    pass


class CacheCorruptedError(CacheError):
    """Cache data is corrupted"""
    pass


# Repository Errors
class RepositoryError(IntelliQueryException):
    """Base class for repository errors"""
    pass


class DocumentNotFoundError(RepositoryError):
    """Document not found"""
    pass


class SessionNotFoundError(RepositoryError):
    """Session not found"""
    pass


class RepositoryAccessError(RepositoryError):
    """Failed to access repository"""
    pass


# API Errors
class APIError(IntelliQueryException):
    """Base class for API errors"""
    pass


class AuthenticationError(APIError):
    """Authentication failed"""
    pass


class AuthorizationError(APIError):
    """Authorization failed"""
    pass


class BadRequestError(APIError):
    """Bad request"""
    pass


class NotFoundError(APIError):
    """Resource not found"""
    pass


class ConflictError(APIError):
    """Resource conflict"""
    pass


class InternalServerError(APIError):
    """Internal server error"""
    pass


# Utility functions
def get_error_response(exception: Exception) -> Dict[str, Any]:
    """
    Convert an exception to an API error response.
    """
    if isinstance(exception, IntelliQueryException):
        return exception.to_dict()
    
    return {
        'error': 'InternalServerError',
        'message': str(exception),
        'details': {}
    }


def http_status_code(exception: Exception) -> int:
    """
    Map exceptions to HTTP status codes.
    """
    if isinstance(exception, ValidationError):
        return 400
    elif isinstance(exception, AuthenticationError):
        return 401
    elif isinstance(exception, AuthorizationError):
        return 403
    elif isinstance(exception, DocumentNotFoundError):
        return 404
    elif isinstance(exception, SessionNotFoundError):
        return 404
    elif isinstance(exception, NotFoundError):
        return 404
    elif isinstance(exception, FileSizeExceededError):
        return 413
    elif isinstance(exception, RateLimitError):
        return 429
    elif isinstance(exception, ConflictError):
        return 409
    elif isinstance(exception, (PDFProcessingError, EmbeddingError, LLMError)):
        return 500
    else:
        return 500
