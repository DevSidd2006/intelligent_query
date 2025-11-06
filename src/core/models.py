"""
Core data models and type definitions for Intelligent Query system.
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
import numpy as np
from enum import Enum


class MessageSender(str, Enum):
    """Message sender types"""
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class Document:
    """Document data model"""
    id: str
    filename: str
    chunks: List[str]
    embeddings: np.ndarray
    created_at: float
    updated_at: float
    file_size: int = 0
    format: str = "pdf"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary (excludes embeddings)"""
        return {
            'id': self.id,
            'filename': self.filename,
            'chunk_count': len(self.chunks),
            'created_at': datetime.fromtimestamp(self.created_at).isoformat(),
            'updated_at': datetime.fromtimestamp(self.updated_at).isoformat(),
            'file_size': self.file_size,
            'format': self.format,
            'metadata': self.metadata
        }


@dataclass
class ChatMessage:
    """Chat message data model"""
    id: str
    session_id: str
    sender: MessageSender
    content: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'sender': self.sender.value,
            'content': self.content,
            'timestamp': datetime.fromtimestamp(self.timestamp).isoformat(),
            'metadata': self.metadata
        }


@dataclass
class ChatSession:
    """Chat session data model"""
    id: str
    document_id: str
    created_at: float
    updated_at: float
    messages: List[ChatMessage] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'created_at': datetime.fromtimestamp(self.created_at).isoformat(),
            'updated_at': datetime.fromtimestamp(self.updated_at).isoformat(),
            'message_count': len(self.messages),
            'metadata': self.metadata
        }


@dataclass
class RetrievalResult:
    """Result from semantic retrieval"""
    chunk: str
    chunk_index: int
    similarity_score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class QueryResponse:
    """Response from query processing"""
    answer: str
    confidence: float
    sources: List[RetrievalResult]
    tokens_used: int
    processing_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'answer': self.answer,
            'confidence': self.confidence,
            'sources': [s.to_dict() for s in self.sources],
            'tokens_used': self.tokens_used,
            'processing_time': self.processing_time,
            'metadata': self.metadata
        }


@dataclass
class FileUpload:
    """File upload data model"""
    filename: str
    content: bytes
    content_type: str
    size: int
    
    @property
    def extension(self) -> str:
        """Get file extension"""
        return self.filename.split('.')[-1].lower() if '.' in self.filename else ''


@dataclass
class APIResponse:
    """Standard API response format"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'success': self.success,
            'data': self.data,
            'error': self.error,
            'metadata': self.metadata
        }


@dataclass
class HealthStatus:
    """System health status"""
    status: str  # 'healthy', 'degraded', 'unhealthy'
    services: Dict[str, str] = field(default_factory=dict)
    version: str = "1.0.0"
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            'status': self.status,
            'services': self.services,
            'version': self.version,
            'timestamp': datetime.fromtimestamp(self.timestamp).isoformat()
        }
