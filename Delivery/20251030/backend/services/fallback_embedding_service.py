"""
Fallback Embedding Service - Combines free and paid embeddings.

This service automatically tries free embeddings first, then falls back to paid
embeddings if there's an error or if free embeddings are not available.
"""
import logging
from typing import List, Dict, Any, Optional
from backend.services.free_embedding_service import FreeEmbeddingService

logger = logging.getLogger(__name__)

class FallbackEmbeddingService:
    """
    Embedding service with automatic fallback between free and paid options.

    This service provides a unified interface for embeddings and automatically
    switches between free (local) and paid (API) embedding services based on
    availability and preference.
    """

    def __init__(self, preferred_provider: str = "free", gemini_model: str = "models/embedding-001"):
        """
        Initialize fallback embedding service.

        Args:
            preferred_provider: "free" (default) or "paid" - Only "free" is supported now
            gemini_model: Gemini model name for paid embeddings (not used)
        """
        self.preferred_provider = "free"  # Force free provider only
        self.gemini_model = gemini_model

        # Initialize services
        self.free_service = None
        self.paid_service = None

        # Try to import and initialize services
        self._initialize_services()

        # Set primary service (always free now)
        self._setup_primary_service()

    def _initialize_services(self):
        """Initialize only free service."""
        # Initialize free service (Sentence Transformers) with 768-dimensions model
        try:
            self.free_service = FreeEmbeddingService(model_name="PORTULAN/serafim-100m-portuguese-pt-sentence-encoder-ir")
            logger.info("✅ Free embedding service (Sentence Transformers) ready with 768-dimensional model")
        except Exception as e:
            logger.error(f"Free embedding service failed to initialize: {e}")
            logger.info("💡 Install with: pip install sentence-transformers torch")
            raise RuntimeError("Free embedding service is required but failed to initialize")

        # Don't initialize paid service anymore
        logger.info("📝 Paid embedding service (Gemini) disabled - using only free embeddings")

    def _setup_primary_service(self):
        """Set up primary service (only free service available now)."""
        if self.free_service:
            self.primary_service = self.free_service
            self.fallback_service = None  # No fallback needed
            logger.info("🚀 Primary: Free embeddings (Sentence Transformers) - No fallback available")
        else:
            logger.error("❌ No embedding service available!")
            raise RuntimeError("No embedding service could be initialized")

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding using only free service.

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding vector

        Raises:
            RuntimeError: If service fails
        """
        if self.primary_service:
            try:
                logger.debug("Using free embedding service (Sentence Transformers)")
                return self.primary_service.generate_embedding(text)
            except Exception as e:
                error_msg = f"Free embedding service failed: {str(e)}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
        else:
            raise RuntimeError("No embedding service available")

    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate query embedding using only free service.

        Same logic as generate_embedding, but optimized for search queries.

        Args:
            query: Search query text

        Returns:
            Query embedding vector
        """
        return self.generate_embedding(query)  # Same implementation

    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about available services.

        Returns:
            Dictionary with service status and configuration
        """
        return {
            'preferred_provider': self.preferred_provider,
            'primary_service': 'free',  # Always free now
            'fallback_service': None,   # No fallback
            'free_available': self.free_service is not None,
            'paid_available': False,    # Always false now
            'total_services': 1 if self.free_service else 0,
            'gemini_model': None        # Not used anymore
        }

    def switch_to_free(self):
        """Switch primary service to free embeddings."""
        # Always using free service now
        logger.info("🔄 Already using free embeddings as primary")

    def switch_to_paid(self):
        """Switch primary service to paid embeddings."""
        logger.warning("❌ Paid embeddings are not available - only free embeddings are supported")
        logger.info("💡 Install sentence-transformers for free local embeddings")

    def is_free_available(self) -> bool:
        """Check if free embeddings are available."""
        return self.free_service is not None

    def is_paid_available(self) -> bool:
        """Check if paid embeddings are available."""
        return False  # Paid service is not available anymore

    def get_embedding_dimension(self) -> int:
        """
        Get embedding dimension from primary service.

        Returns:
            Embedding dimension or 0 if no service available
        """
        if self.primary_service:
            if hasattr(self.primary_service, 'embedding_dimension'):
                return self.primary_service.embedding_dimension
            elif hasattr(self.primary_service, 'get_model_info'):
                return self.primary_service.get_model_info().get('embedding_dimension', 0)

    def process_document_for_embedding(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process document for embedding using only free service.

        Args:
            document: Fiscal document data

        Returns:
            List of chunks with embeddings ready for database storage

        Raises:
            RuntimeError: If service fails
        """
        if self.primary_service:
            try:
                logger.debug("Using free embedding service for document processing (Sentence Transformers)")
                return self.primary_service.process_document_for_embedding(document)
            except Exception as e:
                error_msg = f"Free embedding service failed: {str(e)}"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
        else:
            raise RuntimeError("No embedding service available")
