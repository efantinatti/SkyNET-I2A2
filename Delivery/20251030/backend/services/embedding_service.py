"""
Gemini Embedding Service for RAG system.

This module provides embedding generation using Google Gemini API for semantic search
and retrieval-augmented generation in fiscal documents.
"""
import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from config import GOOGLE_API_KEY

logger = logging.getLogger(__name__)

# Conditional import for google.generativeai
try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    logger.warning("Google Generative AI not available. Consider installing: pip install google-generativeai")


class GeminiEmbeddingService:
    """
    Service for generating embeddings using Google Gemini API.

    This service handles text preprocessing, chunking, and embedding generation
    specifically optimized for fiscal documents.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: str = "models/embedding-001"):
        """
        Initialize the Gemini embedding service.

        Args:
            api_key: Google API key (uses config.GOOGLE_API_KEY if not provided)
            model_name: Gemini model name for embeddings
        """
        self.api_key = api_key or GOOGLE_API_KEY
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY is required for Gemini embeddings")

        if not GOOGLE_AVAILABLE:
            raise ImportError("Google Generative AI is not available. Install with: pip install google-generativeai")

        genai.configure(api_key=self.api_key)
        self.model_name = model_name
        self.embedding_dimension = 768  # Gemini embedding-001 produces 768-dimensional vectors

        logger.info(f"GeminiEmbeddingService initialized with model: {model_name}")

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for the given text using Gemini.

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding vector

        Raises:
            Exception: If embedding generation fails
        """
        try:
            # Validate input text
            if not text or not text.strip():
                raise ValueError("Input text cannot be empty")

            # Truncate text if too long (Gemini has limits)
            text = self._truncate_text(text, max_length=8000)

            # Generate embedding using Gemini
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_document"
            )

            embedding = result['embedding']

            # Validate embedding dimensions
            if len(embedding) != self.embedding_dimension:
                logger.warning(f"Unexpected embedding dimension: {len(embedding)}, expected: {self.embedding_dimension}")

            logger.debug(f"Generated embedding for text (length: {len(text)}) with {len(embedding)} dimensions")
            return embedding

        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise

    def split_document(self, document_content: Dict[str, Any], chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """
        Split document content into chunks for better semantic search.

        Args:
            document_content: Document data including extracted text and metadata
            chunk_size: Maximum characters per chunk
            overlap: Number of overlapping characters between chunks

        Returns:
            List of chunks with metadata
        """
        try:
            # Extract text content from document
            text_content = self._extract_text_content(document_content)
            if not text_content:
                logger.warning("No text content found in document")
                return []

            # Clean and prepare text
            cleaned_text = self._clean_text(text_content)

            # Split into chunks
            chunks = self._create_chunks(cleaned_text, chunk_size, overlap)

            # Add metadata to each chunk
            result_chunks = []
            for i, chunk_text in enumerate(chunks):
                chunk_metadata = {
                    'content_text': chunk_text,
                    'metadata': {
                        'chunk_number': i,
                        'document_id': document_content.get('id', ''),
                        'document_type': document_content.get('document_type', ''),
                        'file_name': document_content.get('file_name', ''),
                        'issuer_cnpj': document_content.get('issuer_cnpj', ''),
                        'document_number': document_content.get('document_number', ''),
                        'chunk_size': len(chunk_text),
                        'total_chunks': len(chunks)
                    }
                }
                result_chunks.append(chunk_metadata)

            logger.info(f"Split document into {len(result_chunks)} chunks")
            return result_chunks

        except Exception as e:
            logger.error(f"Error splitting document: {str(e)}")
            raise

    def process_document_for_embedding(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Complete pipeline: split document and generate embeddings for each chunk.

        Args:
            document: Fiscal document data

        Returns:
            List of chunks with embeddings ready for database storage
        """
        try:
            # Split document into chunks
            chunks = self.split_document(document)
            if not chunks:
                return []

            logger.info(f"Processing {len(chunks)} chunks for embeddings")

            # Generate embeddings for each chunk
            for chunk in chunks:
                try:
                    embedding = self.generate_embedding(chunk['content_text'])
                    chunk['embedding'] = embedding
                    logger.debug(f"Generated embedding for chunk {chunk['metadata']['chunk_number']}")
                except Exception as e:
                    logger.error(f"Failed to generate embedding for chunk {chunk['metadata']['chunk_number']}: {str(e)}")
                    chunk['embedding'] = None

            # Filter out chunks without embeddings
            successful_chunks = [chunk for chunk in chunks if chunk.get('embedding') is not None]

            logger.info(f"Successfully processed {len(successful_chunks)}/{len(chunks)} chunks")
            return successful_chunks

        except Exception as e:
            logger.error(f"Error processing document for embedding: {str(e)}")
            raise

    def _extract_text_content(self, document: Dict[str, Any]) -> str:
        """
        Extract relevant text content from fiscal document.

        Args:
            document: Document data

        Returns:
            Combined text content for embedding
        """
        text_parts = []

        # Add document metadata
        if document.get('document_type'):
            text_parts.append(f"Tipo: {document['document_type']}")

        if document.get('document_number'):
            text_parts.append(f"Número: {document['document_number']}")

        # Add issuer information
        if document.get('issuer_cnpj'):
            text_parts.append(f"CNPJ Emissor: {document['issuer_cnpj']}")

        # Add extracted data if available
        extracted_data = document.get('extracted_data', {})
        if isinstance(extracted_data, dict):
            # Add key-value pairs from extracted data
            for key, value in extracted_data.items():
                if value and isinstance(value, (str, int, float)):
                    text_parts.append(f"{key}: {str(value)}")

        # Add raw text content if available
        if document.get('raw_text'):
            text_parts.append(document['raw_text'])

        # Add OCR content if available
        if document.get('ocr_text'):
            text_parts.append(document['ocr_text'])

        return ' '.join(text_parts)

    def _clean_text(self, text: str) -> str:
        """
        Clean and normalize text for better embedding quality.

        Args:
            text: Raw text to clean

        Returns:
            Cleaned text
        """
        # Remove extra whitespace and normalize
        cleaned = re.sub(r'\s+', ' ', text.strip())

        # Remove special characters but keep important punctuation
        cleaned = re.sub(r'[^\w\s\-.,;:()/%R$]', '', cleaned)

        # Normalize common fiscal terms
        fiscal_terms = {
            'nota fiscal': 'nota fiscal',
            'nf-e': 'nota fiscal eletrônica',
            'nfe': 'nota fiscal eletrônica',
            'cnpj': 'CNPJ',
            'cpf': 'CPF',
            'icms': 'ICMS',
            'ipi': 'IPI',
            'pis': 'PIS',
            'cofins': 'COFINS'
        }

        for term, replacement in fiscal_terms.items():
            cleaned = cleaned.replace(term.lower(), replacement)

        return cleaned.strip()

    def _truncate_text(self, text: str, max_length: int = 8000) -> str:
        """
        Truncate text to fit within Gemini's limits while preserving meaning.

        Args:
            text: Text to truncate
            max_length: Maximum character length

        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text

        # Try to truncate at sentence boundary
        sentences = re.split(r'[.!?]+', text)
        result = ""

        for sentence in sentences:
            if len(result + sentence) > max_length:
                break
            result += sentence + "."

        return result.strip()

    def _create_chunks(self, text: str, chunk_size: int, overlap: int) -> List[str]:
        """
        Create overlapping text chunks.

        Args:
            text: Text to split
            chunk_size: Maximum characters per chunk
            overlap: Overlap between chunks

        Returns:
            List of text chunks
        """
        if not text or len(text) <= chunk_size:
            return [text] if text else []

        chunks = []
        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))

            # If we're not at the end, try to end at a sentence boundary
            if end < len(text):
                # Look for sentence endings within the last 100 characters
                for i in range(min(end, start + chunk_size - 100), end):
                    if text[i] in '.!?' and (i + 1 >= len(text) or text[i + 1] in ' \n'):
                        end = i + 1
                        break

            chunk = text[start:end].strip()
            if chunk:  # Only add non-empty chunks
                chunks.append(chunk)

            # Move start position with overlap
            start = end - overlap if end < len(text) else end

            # Prevent infinite loops
            if start >= end:
                start = end

        return chunks

    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a search query.

        Args:
            query: Search query text

        Returns:
            Query embedding vector
        """
        # Clean and enhance the query for better search results
        enhanced_query = self._enhance_query(query)
        return self.generate_embedding(enhanced_query)

    def _enhance_query(self, query: str) -> str:
        """
        Enhance search query with fiscal document context.

        Args:
            query: Original query

        Returns:
            Enhanced query for better search results
        """
        # Add fiscal document context to improve search relevance
        fiscal_keywords = [
            'documento fiscal', 'nota fiscal', 'cupom fiscal',
            'fatura', 'recibo', 'comprovante', 'extrato'
        ]

        enhanced = query

        # Add fiscal context if query seems related to documents
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in ['documento', 'nota', 'fatura', 'comprovante']):
            enhanced = f"contexto fiscal: {query}"

        return enhanced


# Rate limiting implementation
"""
Rate-limited version of Gemini Embedding Service.

This module adds rate limiting to prevent quota exhaustion.
"""
import time
import functools
from typing import Any, Callable


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""
    pass


def rate_limit(calls_per_minute: int = 30, calls_per_hour: int = 500):
    """
    Decorator to implement rate limiting for API calls.

    Args:
        calls_per_minute: Maximum calls per minute
        calls_per_hour: Maximum calls per hour
    """
    min_interval_minute = 60.0 / calls_per_minute if calls_per_minute > 0 else 0
    min_interval_hour = 3600.0 / calls_per_hour if calls_per_hour > 0 else 0

    last_calls = []

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()

            # Clean old calls (older than 1 hour)
            last_calls[:] = [call_time for call_time in last_calls
                           if current_time - call_time < 3600]

            # Check minute limit
            recent_calls_minute = [call_time for call_time in last_calls
                                 if current_time - call_time < 60]
            if len(recent_calls_minute) >= calls_per_minute:
                wait_time = 60 - (current_time - recent_calls_minute[0])
                raise RateLimitError(
                    f"Rate limit exceeded (minute): {calls_per_minute} calls/min. "
                    f"Wait {wait_time:.1f} seconds or use a different API key."
                )

            # Check hour limit
            if len(last_calls) >= calls_per_hour:
                wait_time = 3600 - (current_time - last_calls[0])
                raise RateLimitError(
                    f"Rate limit exceeded (hour): {calls_per_hour} calls/hour. "
                    f"Wait {wait_time:.1f} seconds or use a different API key."
                )

            # Execute the function
            try:
                result = func(*args, **kwargs)
                last_calls.append(current_time)
                return result
            except Exception as e:
                # Even if the call fails, count it towards rate limit
                last_calls.append(current_time)
                raise

        return wrapper
    return decorator


# Apply rate limiting to embedding generation with conservative limits
def apply_rate_limiting():
    """Apply rate limiting to embedding service methods."""
    try:
        # Rate limit for embedding generation (conservative limits)
        GeminiEmbeddingService.generate_embedding = rate_limit(
            calls_per_minute=20,  # Conservative: 20 calls per minute
            calls_per_hour=300    # Conservative: 300 calls per hour
        )(GeminiEmbeddingService.generate_embedding)

        # Rate limit for query embeddings (less restrictive)
        GeminiEmbeddingService.generate_query_embedding = rate_limit(
            calls_per_minute=30,
            calls_per_hour=400
        )(GeminiEmbeddingService.generate_query_embedding)

        logger.info("✅ Rate limiting applied to embedding service")
        logger.info("   - generate_embedding: 20 calls/min, 300 calls/hour")
        logger.info("   - generate_query_embedding: 30 calls/min, 400 calls/hour")

    except Exception as e:
        logger.error(f"Failed to apply rate limiting: {e}")


# Apply rate limiting when module is imported
apply_rate_limiting()
