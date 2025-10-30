"""
Free Embedding Service using Sentence Transformers.

This module provides completely free embeddings using local models,
no API keys or quotas required. Perfect alternative to paid embedding services.
"""
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import re
import os

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except (ImportError, ValueError):
    logger.warning("sentence-transformers not installed or misconfigured. Install with: pip install sentence-transformers torch")
    SentenceTransformer = None  # type: ignore
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class FreeEmbeddingService:
    """
    Free embedding service using Sentence Transformers.

    This service provides high-quality embeddings without any API costs or quotas.
    Uses pre-trained models that run locally on your machine.

    Supported models:
    - 'all-MiniLM-L6-v2': Fast, 384 dimensions (recommended for speed)
    - 'all-mpnet-base-v2': Higher quality, 768 dimensions (recommended for accuracy)
    - 'paraphrase-MiniLM-L3-v2': Very fast, 384 dimensions
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the free embedding service.

        Args:
            model_name: Name of the sentence transformer model to use
                       Options: 'all-MiniLM-L6-v2', 'all-mpnet-base-v2', 'paraphrase-MiniLM-L3-v2'
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers is required for free embeddings. "
                "Install with: pip install sentence-transformers torch"
            )

        self.model_name = model_name
        self.model = None
        self.embedding_dimension = self._get_model_dimensions(model_name)
        self._initialize_model()

        logger.info(f"FreeEmbeddingService initialized with model: {model_name}")
        logger.info(f"Embedding dimension: {self.embedding_dimension}")
        logger.info("✅ No API keys or quotas required!")

    def _get_model_dimensions(self, model_name: str) -> int:
        """Get embedding dimensions for different models."""
        dimensions = {
            'all-MiniLM-L6-v2': 384,
            'all-mpnet-base-v2': 768,
            'paraphrase-MiniLM-L3-v2': 384,
            'paraphrase-mpnet-base-v2': 768,
            'multi-qa-MiniLM-L6-cos-v1': 384,
            'multi-qa-mpnet-base-dot-v1': 768
        }
        return dimensions.get(model_name, 384)

    def _initialize_model(self):
        """Initialize the sentence transformer model."""
        try:
            logger.info(f"Loading model: {self.model_name}")

            # Use cache directory to avoid re-downloading
            cache_dir = Path.home() / '.cache' / 'sentence_transformers'
            cache_dir.mkdir(parents=True, exist_ok=True)

            self.model = SentenceTransformer(
                self.model_name,
                cache_folder=str(cache_dir)
            )

            logger.info(f"✅ Model loaded successfully: {self.model_name}")
            logger.info(f"   Model size: ~{self._get_model_size_mb():.1f} MB")
            logger.info(f"   Embedding dimensions: {self.embedding_dimension}")

        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")
            logger.info("💡 Try a smaller model like 'all-MiniLM-L6-v2'")
            raise

    def _get_model_size_mb(self) -> float:
        """Estimate model size in MB."""
        try:
            if hasattr(self.model, '_model_card'):
                # Try to estimate from model files
                model_path = Path.home() / '.cache' / 'sentence_transformers' / self.model_name
                if model_path.exists():
                    total_size = sum(f.stat().st_size for f in model_path.rglob('*') if f.is_file())
                    return total_size / (1024 * 1024)
            return 90  # Default estimate for MiniLM models
        except:
            return 90

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for the given text.

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

            # Truncate text if too long (most models handle up to 512 tokens)
            text = self._truncate_text(text, max_length=1000)

            # Generate embedding using the local model
            embedding = self.model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=True  # Normalize for better similarity search
            )

            # Convert to list for JSON serialization
            embedding_list = embedding.tolist()

            logger.debug(f"Generated embedding for text (length: {len(text)}) with {len(embedding_list)} dimensions")
            return embedding_list

        except Exception as e:
            logger.error(f"Error generating embedding: {str(e)}")
            raise

    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding for a search query with enhanced processing.

        Args:
            query: Search query text

        Returns:
            Query embedding vector optimized for search
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

    def _truncate_text(self, text: str, max_length: int = 1000) -> str:
        """
        Truncate text to fit within model's limits while preserving meaning.

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
            doc_type = document_content.get('document_type', '')
            issuer_cnpj = document_content.get('issuer_cnpj', '')

            for i, chunk_text in enumerate(chunks):
                # Prepend essential metadata to each chunk's content for better context
                metadata_header = f"[Tipo de Documento: {doc_type}, CNPJ Emissor: {issuer_cnpj}]\n"
                content_with_header = metadata_header + chunk_text

                chunk_metadata = {
                    'content_text': content_with_header,
                    'metadata': {
                        'chunk_number': i,
                        'document_id': document_content.get('id', ''),
                        'document_type': doc_type,
                        'file_name': document_content.get('file_name', ''),
                        'issuer_cnpj': issuer_cnpj,
                        'document_number': document_content.get('document_number', ''),
                        'chunk_size': len(content_with_header),
                        'total_chunks': len(chunks)
                    }
                }
                result_chunks.append(chunk_metadata)

            logger.info(f"Split document into {len(result_chunks)} chunks")
            logger.debug(f"Document ID used for chunks: {document_content.get('id', 'NO_ID')}")
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

        # Remove irrelevant special characters but keep a broader set for fiscal context
        cleaned = re.sub(r'[^\w\s\-.,;:()/%R$@+*<>_=\[\]]', '', cleaned)

        # Convert to lowercase to help normalization, but after specific term replacement
        cleaned = cleaned.lower()

        # Normalize common fiscal terms
        # Normalize common fiscal terms (case-insensitive)
        fiscal_terms = {
            r'\b(nf-e|nfe)\b': 'nota fiscal eletrônica',
            r'\b(nf|notafiscal)\b': 'nota fiscal',
            r'\b(cnpj|cadastro nacional da pessoa jurídica)\b': 'cnpj',
            r'\b(cpf|cadastro de pessoas físicas)\b': 'cpf',
            r'\b(icms|imposto sobre circulação de mercadorias e serviços)\b': 'icms',
            r'\b(ipi|imposto sobre produtos industrializados)\b': 'ipi',
            r'\b(pis|programa de integração social)\b': 'pis',
            r'\b(cofins|contribuição para o financiamento da seguridade social)\b': 'cofins',
            r'\b(rpa|recibo de pagamento autônomo)\b': 'rpa',
            r'\b(cte|conhecimento de transporte eletrônico)\b': 'cte',
            r'\b(mdfe|manifesto eletrônico de documentos fiscais)\b': 'mdfe'
        }

        for term, replacement in fiscal_terms.items():
            cleaned = re.sub(term, replacement, cleaned, flags=re.IGNORECASE)

        return cleaned.strip()

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
        if not text:
            return []

        # Use a more robust splitter, prioritizing more significant separators
        separators = ["\n\n", ". ", " "]
        
        # Start with the full text
        final_chunks = []
        initial_splits = [text]

        for sep in separators:
            new_splits = []
            for split in initial_splits:
                if len(split) > chunk_size:
                    new_splits.extend(split.split(sep))
                else:
                    new_splits.append(split)
            initial_splits = new_splits

        # Combine small splits and create final chunks with overlap
        current_chunk = ""
        for i, split in enumerate(initial_splits):
            if not current_chunk:
                current_chunk = split
            elif len(current_chunk) + len(split) + len(separators[-1]) <= chunk_size:
                current_chunk += separators[-1] + split
            else:
                final_chunks.append(current_chunk)
                # Create overlap by taking the end of the last chunk
                overlap_text = ' '.join(current_chunk.split(' ')[-int(overlap/5):]) # Simple word-based overlap
                current_chunk = overlap_text + ' ' + split
        
        if current_chunk:
            final_chunks.append(current_chunk)

        return [chunk for chunk in final_chunks if chunk.strip()]

        return chunks

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.

        Returns:
            Dictionary with model information
        """
        return {
            'model_name': self.model_name,
            'embedding_dimension': self.embedding_dimension,
            'estimated_size_mb': self._get_model_size_mb(),
            'is_free': True,
            'requires_api': False,
            'offline_capable': True
        }

    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score between 0 and 1 (1 = most similar)
        """
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)

            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)
            return float(similarity)

        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
