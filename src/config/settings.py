"""
Centralized configuration management for Intelligent Query system.
Provides environment-based settings with validation and defaults.
"""

import os
from dataclasses import dataclass
from typing import Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class PDFConfig:
    """PDF processing configuration"""
    max_file_size: int = 200 * 1024 * 1024  # 200MB
    supported_formats: Tuple[str, ...] = ('pdf', 'docx', 'eml')
    chunk_size: int = 500
    chunk_overlap: int = 50
    min_chunk_size: int = 80


@dataclass
class EmbeddingConfig:
    """Embedding and vector search configuration"""
    model_name: str = 'all-MiniLM-L6-v2'
    batch_size: int = 64
    normalize_embeddings: bool = True
    embedding_dim: int = 384  # For default model


@dataclass
class CacheConfig:
    """Document caching configuration"""
    enabled: bool = True
    max_documents: int = 10
    ttl_seconds: int = 3600  # 1 hour


@dataclass
class LLMConfig:
    """Language Model configuration"""
    api_provider: str = 'groq'  # 'groq' or 'openai'
    model_name: str = 'llama-3.1-8b-instant'
    temperature: float = 0.7
    max_tokens: int = 1024
    request_timeout: int = 30


@dataclass
class APIConfig:
    """API configuration"""
    host: str = '0.0.0.0'
    port: int = 3000
    debug: bool = False
    workers: int = 4
    enable_cors: bool = True
    enable_authentication: bool = True


@dataclass
class LoggingConfig:
    """Logging configuration"""
    level: str = 'INFO'
    format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    file_path: str = 'app.log'
    max_bytes: int = 10485760  # 10MB
    backup_count: int = 5


@dataclass
class Settings:
    """Main configuration container"""
    
    # Sub-configurations
    pdf: PDFConfig
    embedding: EmbeddingConfig
    cache: CacheConfig
    llm: LLMConfig
    api: APIConfig
    logging: LoggingConfig
    
    # API keys and secrets
    groq_api_key: Optional[str]
    openai_api_key: Optional[str]
    bearer_token: Optional[str]
    secret_key: str
    
    # Environment
    environment: str  # 'development', 'staging', 'production'
    
    @classmethod
    def from_env(cls) -> 'Settings':
        """Create settings from environment variables"""
        
        # Get environment
        environment = os.getenv('ENVIRONMENT', 'development')
        
        # API Keys
        groq_api_key = os.getenv('GROQ_API_KEY')
        openai_api_key = os.getenv('OPENAI_API_KEY')
        bearer_token = os.getenv('HACKRX_BEARER_TOKEN')
        secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
        
        # Port configuration
        port = int(os.getenv('PORT', 3000))
        debug = os.getenv('DEBUG', 'False').lower() == 'true'
        
        # Create sub-configs with environment overrides
        pdf_config = PDFConfig(
            chunk_size=int(os.getenv('CHUNK_SIZE', 500)),
            max_file_size=int(os.getenv('MAX_FILE_SIZE', 200 * 1024 * 1024))
        )
        
        embedding_config = EmbeddingConfig(
            model_name=os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2'),
            batch_size=int(os.getenv('BATCH_SIZE', 64))
        )
        
        cache_config = CacheConfig(
            enabled=os.getenv('CACHE_ENABLED', 'True').lower() == 'true',
            max_documents=int(os.getenv('CACHE_SIZE', 10)),
            ttl_seconds=int(os.getenv('CACHE_TTL', 3600))
        )
        
        llm_config = LLMConfig(
            api_provider=os.getenv('LLM_PROVIDER', 'groq'),
            model_name=os.getenv('LLM_MODEL', 'llama-3.1-8b-instant'),
            temperature=float(os.getenv('LLM_TEMPERATURE', 0.7))
        )
        
        api_config = APIConfig(
            port=port,
            debug=debug,
            workers=int(os.getenv('WORKERS', 4)),
            enable_authentication=os.getenv('ENABLE_AUTH', 'True').lower() == 'true'
        )
        
        logging_config = LoggingConfig(
            level=os.getenv('LOG_LEVEL', 'INFO'),
            file_path=os.getenv('LOG_FILE', 'app.log')
        )
        
        return cls(
            pdf=pdf_config,
            embedding=embedding_config,
            cache=cache_config,
            llm=llm_config,
            api=api_config,
            logging=logging_config,
            groq_api_key=groq_api_key,
            openai_api_key=openai_api_key,
            bearer_token=bearer_token,
            secret_key=secret_key,
            environment=environment
        )
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        """Validate configuration"""
        
        # Check API keys based on provider
        if self.llm.api_provider == 'groq':
            if not self.groq_api_key:
                return False, "GROQ_API_KEY not configured"
        elif self.llm.api_provider == 'openai':
            if not self.openai_api_key:
                return False, "OPENAI_API_KEY not configured"
        else:
            return False, f"Unknown LLM provider: {self.llm.api_provider}"
        
        # Check PDF configuration
        if self.pdf.chunk_size < 100:
            return False, "PDF chunk_size must be >= 100"
        
        # Check embedding configuration
        if self.embedding.batch_size < 1:
            return False, "Embedding batch_size must be >= 1"
        
        # Check port
        if not (1 <= self.api.port <= 65535):
            return False, "API port must be between 1 and 65535"
        
        return True, None
    
    def to_dict(self) -> dict:
        """Convert settings to dictionary (safe, no secrets)"""
        return {
            'environment': self.environment,
            'api': {
                'port': self.api.port,
                'debug': self.api.debug,
                'workers': self.api.workers,
            },
            'pdf': {
                'chunk_size': self.pdf.chunk_size,
                'max_file_size': self.pdf.max_file_size,
            },
            'embedding': {
                'model': self.embedding.model_name,
                'batch_size': self.embedding.batch_size,
            },
            'cache': {
                'enabled': self.cache.enabled,
                'max_documents': self.cache.max_documents,
            },
            'llm': {
                'provider': self.llm.api_provider,
                'model': self.llm.model_name,
            }
        }


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get global settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings.from_env()
        is_valid, error_msg = _settings.validate()
        if not is_valid:
            raise RuntimeError(f"Configuration Error: {error_msg}")
    return _settings


def reset_settings() -> None:
    """Reset global settings (for testing)"""
    global _settings
    _settings = None
