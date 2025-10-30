"""
Services module for the SkyNET-I2A2 application.

This module contains all service classes for business logic,
including embedding, vector search, and RAG functionality.
"""

# Import fallback embedding service first (with free embeddings)
try:
    from .fallback_embedding_service import FallbackEmbeddingService
    FALLBACK_AVAILABLE = True
except ImportError:
    FALLBACK_AVAILABLE = False

# Import Gemini service as fallback
try:
    from .embedding_service import GeminiEmbeddingService
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

from .vector_store_service import VectorStoreService
from .rag_service import RAGService

__all__ = [
    'FallbackEmbeddingService',
    'GeminiEmbeddingService',
    'VectorStoreService',
    'RAGService'
]
