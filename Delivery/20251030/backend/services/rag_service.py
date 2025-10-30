"""
RAG (Retrieval-Augmented Generation) Service.

This module orchestrates semantic search and response generation using Gemini
embeddings and vector search for intelligent Q&A on fiscal documents.
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
import asyncio
from datetime import datetime
import streamlit as st
from backend.services.vector_store_service import VectorStoreService

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False
    CrossEncoder = None # type: ignore


class RAGService:
    """
    Main RAG service that combines semantic search with Gemini response generation.

    This service handles the complete RAG pipeline:
    1. Query understanding and embedding
    2. Semantic search in document chunks
    3. Context retrieval and formatting
    4. Response generation using Gemini with context
    """

    def __init__(self, vector_store: VectorStoreService):
        """
        Initialize the RAG service with embedding and vector store services.
        """
        # Use fallback embedding service instead of direct Gemini
        self.vector_store = vector_store
        self.embedding_service = None
        self.cross_encoder = None
        self._initialize_embedding_service()
        self._initialize_cross_encoder()
        logger.info("RAGService initialized")
        
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the RAG system.
        
        Returns:
            Dict containing various statistics about the RAG system
        """
        stats = {
            'status': 'active',
            'last_updated': datetime.utcnow().isoformat(),
            'total_documents': 0,
            'total_embeddings': 0,
            'index_size_mb': 0,
            'documents_by_type': {},
            'embedding_stats': {
                'model': 'unknown',
                'dimensions': 0,
                'service': 'unknown'
            }
        }
        
        try:
            # Get vector store stats if available
            if hasattr(self.vector_store, 'get_stats'):
                vector_stats = self.vector_store.get_stats()
                if vector_stats:
                    stats['total_embeddings'] = vector_stats.get('total_vectors', 0)
                    stats['index_size_mb'] = vector_stats.get('index_size_mb', 0)
            
            # Get document type distribution if available
            if hasattr(self, 'document_service') and hasattr(self.document_service, 'get_document_type_distribution'):
                stats['documents_by_type'] = self.document_service.get_document_type_distribution()
                stats['total_documents'] = sum(stats['documents_by_type'].values())
            
            # Get embedding service info
            if self.embedding_service and hasattr(self.embedding_service, 'get_service_info'):
                service_info = self.embedding_service.get_service_info()
                stats['embedding_stats'].update({
                    'model': service_info.get('model', 'unknown'),
                    'dimensions': service_info.get('dimensions', 0),
                    'service': service_info.get('primary_service', 'unknown'),
                    'fallback_service': service_info.get('fallback_service', 'none')
                })
                
        except Exception as e:
            logger.error(f"Error getting RAG statistics: {str(e)}")
            stats['error'] = str(e)
            
        return stats

    def _initialize_embedding_service(self):
        """Initialize embedding service with fallback logic."""
        try:
            # Try to import and use fallback service with free embeddings first
            try:
                from .fallback_embedding_service import FallbackEmbeddingService

                # Prefer free embeddings first (Sentence Transformers)
                self.embedding_service = FallbackEmbeddingService(preferred_provider="free")

                service_info = self.embedding_service.get_service_info()
                logger.info(f"✅ RAG embedding service ready: {service_info['primary_service']} (fallback: {service_info['fallback_service']})")

            except ImportError:
                logger.warning("Fallback embedding service not available, trying Gemini...")
                # Fallback to Gemini service
                try:
                    from .embedding_service import GeminiEmbeddingService
                    self.embedding_service = GeminiEmbeddingService()
                    logger.info("✅ Using Gemini embedding service")
                except ImportError:
                    logger.error("No embedding service available")
                    raise ImportError("No embedding service available")

        except Exception as e:
            logger.error(f"Failed to initialize any embedding service: {e}")
            raise

    def _initialize_cross_encoder(self):
        """Initialize the Cross-Encoder model for re-ranking."""
        if CROSS_ENCODER_AVAILABLE:
            try:
                # Using a small, fast, and multilingual model
                model_name = 'mixedbread-ai/mxbai-rerank-xsmall-v1'
                self.cross_encoder = CrossEncoder(model_name)
                logger.info(f"✅ Cross-encoder model loaded: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load cross-encoder model: {e}")
                self.cross_encoder = None
        else:
            logger.warning("Cross-encoder not available. Install sentence-transformers.")
            self.cross_encoder = None

    async def _build_context_data(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        max_context_docs: int = 3
    ) -> Dict[str, Any]:
        """Internal helper to build context text and metadata."""

        try:
            query_embedding = self.embedding_service.generate_query_embedding(query)

            similar_chunks = self.vector_store.search_similar_chunks(
                query_embedding=query_embedding,
                similarity_threshold=0.65,
                max_results=10,
                filters=filters
            )

            if not similar_chunks:
                return {
                    'context': "Nenhum documento relevante encontrado para a sua pergunta.",
                    'documents': [],
                    'similar_chunks': [],
                    'query_embedding': query_embedding,
                    'status': 'no_matches'
                }

            if self.cross_encoder:
                cross_encoder_pairs = [[query, chunk['content_text']] for chunk in similar_chunks]
                scores = self.cross_encoder.predict(cross_encoder_pairs)
                for i, chunk in enumerate(similar_chunks):
                    chunk['rerank_score'] = scores[i]
                similar_chunks = sorted(similar_chunks, key=lambda x: x['rerank_score'], reverse=True)

            context_docs = self.vector_store.get_document_context(
                query_embedding=query_embedding,
                max_documents=max_context_docs,
                max_chunks_per_document=2
            )

            context_text = self._format_context_for_llm(context_docs, similar_chunks)

            return {
                'context': context_text,
                'documents': context_docs,
                'similar_chunks': similar_chunks,
                'query_embedding': query_embedding,
                'status': 'success'
            }

        except Exception as e:
            logger.error(f"Error getting context for query: {str(e)}")
            return {
                'context': f"Erro ao buscar contexto: {str(e)}",
                'documents': [],
                'similar_chunks': [],
                'query_embedding': None,
                'status': 'error',
                'error': str(e)
            }

    async def get_context_for_query(self, query: str, filters: Optional[Dict[str, Any]] = None, max_context_docs: int = 3) -> str:
        """Get formatted context for a query using RAG."""
        context_data = await self._build_context_data(query, filters=filters, max_context_docs=max_context_docs)
        return context_data['context']

    async def get_context_with_metadata(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        max_context_docs: int = 3
    ) -> Dict[str, Any]:
        """Return formatted context together with retrieved document metadata."""
        return await self._build_context_data(query, filters=filters, max_context_docs=max_context_docs)

    async def answer_query(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        max_context_docs: int = 3,
        response_temperature: float = 0.1
    ) -> Dict[str, Any]:
        """
        Answer a query using RAG with semantic search and Gemini generation.

        Args:
            query: User's question about fiscal documents
            filters: Optional filters for document search
            max_context_docs: Maximum number of context documents to use
            response_temperature: Temperature for Gemini response generation

        Returns:
            Dictionary with answer, context, and metadata
        """
        try:
            logger.info(f"Processing RAG query: {query[:100]}...")

            # Step 1: Generate embedding for the query
            query_embedding = self.embedding_service.generate_query_embedding(query)

            # Step 2: Search for relevant document chunks
            similar_chunks = self.vector_store.search_similar_chunks(
                query_embedding=query_embedding,
                similarity_threshold=0.65, # Adjusted from 0.6
                max_results=10,
                filters=filters
            )

            if not similar_chunks:
                logger.info("No similar chunks found - checking if any documents have embeddings")

                # Check if there are any documents with embeddings
                stats = self.vector_store.get_embedding_statistics()
                docs_with_embeddings = stats.get('documents_with_embeddings', 0)

                if docs_with_embeddings == 0:
                    logger.info("No documents with embeddings found")
                    return {
                        'answer': 'Nenhum documento foi processado para embeddings ainda. Use a aba "Processar Documento" para adicionar documentos ao sistema RAG.',
                        'context_docs': [],
                        'similar_chunks': [],
                        'total_chunks': 0,
                        'query_embedding_used': True,
                        'filters_applied': filters or {},
                        'status': 'no_documents'
                    }
                else:
                    logger.info(f"Found {docs_with_embeddings} documents with embeddings but no matches")
                    return {
                        'answer': f'Foram encontrados {docs_with_embeddings} documentos processados, mas nenhum relevante para sua consulta. Tente reformular a pergunta ou ajustar os filtros.',
                        'context_docs': [],
                        'similar_chunks': [],
                        'total_chunks': 0,
                        'query_embedding_used': True,
                        'filters_applied': filters or {},
                        'status': 'no_matches'
                    }

            # Step 3: Re-rank chunks using Cross-Encoder for better relevance
            if self.cross_encoder and similar_chunks:
                logger.info(f"Re-ranking {len(similar_chunks)} chunks with cross-encoder...")
                
                # Create pairs of [query, chunk_content]
                cross_encoder_pairs = [[query, chunk['content_text']] for chunk in similar_chunks]
                
                # Predict scores
                scores = self.cross_encoder.predict(cross_encoder_pairs)
                
                # Add scores to chunks and sort
                for i, chunk in enumerate(similar_chunks):
                    chunk['rerank_score'] = scores[i]
                
                similar_chunks = sorted(similar_chunks, key=lambda x: x['rerank_score'], reverse=True)
                logger.info(f"Top re-ranked chunk score: {similar_chunks[0]['rerank_score']:.4f}")

            # Step 4: Get document context for better responses
            context_docs = self.vector_store.get_document_context(
                query_embedding=query_embedding,
                max_documents=max_context_docs,
                max_chunks_per_document=2
            )

            # Step 4: Format context for the LLM
            context_text = self._format_context_for_llm(context_docs, similar_chunks)

            # Step 5: Generate response using Gemini with context
            answer = await self._generate_response_with_context(
                query=query,
                context=context_text,
                temperature=response_temperature
            )

            logger.info(f"RAG query completed successfully. Used {len(context_docs)} context documents")

            return {
                'answer': answer,
                'context_docs': context_docs,
                'similar_chunks': similar_chunks,
                'total_chunks': len(similar_chunks),
                'query_embedding_used': True,
                'filters_applied': filters or {},
                'status': 'success'
            }

        except Exception as e:
            logger.error(f"Error in RAG query processing: {str(e)}")
            return {
                'answer': f'Erro ao processar a consulta: {str(e)}. Tente novamente.',
                'context_docs': [],
                'similar_chunks': [],
                'total_chunks': 0,
                'query_embedding_used': False,
                'filters_applied': filters or {},
                'status': 'error',
                'error': str(e)
            }

    async def process_document_for_rag(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a fiscal document for RAG: split, embed, and store chunks.

        Args:
            document: Fiscal document data

        Returns:
            Processing result with statistics
        """
        try:
            logger.info(f"Processing document {document.get('id')} for RAG")
            logger.debug(f"Document data: {document}")

            # Process document: split and generate embeddings FIRST
            chunks_with_embeddings = self.embedding_service.process_document_for_embedding(document)

            if not chunks_with_embeddings:
                logger.error("No chunks generated from document")
                return {
                    'success': False,
                    'error': 'No chunks generated or embedding failed',
                    'chunks_processed': 0,
                    'document_id': document.get('id')
                }

            # Only update status AFTER chunks are ready to be saved
            logger.info(f"Generated {len(chunks_with_embeddings)} chunks, now updating status")
            update_success = self.vector_store.update_document_embedding_status(document['id'], 'processing')

            if not update_success:
                logger.warning(f"Failed to update document status to processing for {document['id']}")

            # Save chunks to database
            logger.info("Saving chunks to database...")
            saved_chunk_ids = self.vector_store.save_document_chunks(chunks_with_embeddings)

            # Update status to completed
            self.vector_store.update_document_embedding_status(document['id'], 'completed')

            logger.info(f"Document {document.get('id')} processed successfully: {len(saved_chunk_ids)} chunks saved")

            return {
                'success': True,
                'chunks_processed': len(saved_chunk_ids),
                'total_chunks': len(chunks_with_embeddings),
                'document_id': document['id'],
                'saved_chunk_ids': saved_chunk_ids
            }

        except Exception as e:
            logger.error(f"Error processing document for RAG: {str(e)}")
            logger.error(f"Document ID in error: {document.get('id', 'NO_ID')}")
            try:
                self.vector_store.update_document_embedding_status(document['id'], 'failed')
            except:
                logger.error("Failed to update status to failed")
            return {
                'success': False,
                'error': str(e),
                'chunks_processed': 0,
                'document_id': document.get('id')
            }

    def get_embedding_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the RAG system.

        Returns:
            Dictionary with system statistics
        """
        try:
            return self.vector_store.get_embedding_statistics()
        except Exception as e:
            logger.error(f"Error getting RAG statistics: {str(e)}")
            return {'error': str(e)}

    def _format_context_for_llm(self, context_docs: List[Dict[str, Any]], similar_chunks: List[Dict[str, Any]]) -> str:
        """
        Format document context for LLM consumption.

        Args:
            context_docs: Documents with relevant chunks
            similar_chunks: Individual similar chunks

        Returns:
            Formatted context string
        """
        if not context_docs and not similar_chunks:
            return "Nenhum documento relevante encontrado."

        context_parts = []

        # Add context from grouped documents
        if context_docs:
            context_parts.append("DOCUMENTOS RELEVANTES ENCONTRADOS:")
            context_parts.append("=" * 50)

            for i, doc in enumerate(context_docs, 1):
                context_parts.append(f"\nDOCUMENTO {i}:")
                context_parts.append(f"- Tipo: {doc.get('document_type', 'Não informado')}")
                context_parts.append(f"- CNPJ Emissor: {doc.get('issuer_cnpj', 'Não informado')}")
                context_parts.append(f"- Similaridade: {doc.get('total_similarity', 0):.3f}")
                context_parts.append(f"- Conteúdo Relevante: {doc.get('chunks_content', 'Sem conteúdo')[:500]}...")
                context_parts.append("-" * 30)

        # Add individual chunk details if needed
        if similar_chunks and len(similar_chunks) > len(context_docs):
            context_parts.append(f"\nTRECHOS ADICIONAIS ({len(similar_chunks) - len(context_docs)}):")
            for chunk in similar_chunks[len(context_docs):]:
                context_parts.append(f"- {chunk.get('content_text', '')[:200]}...")

        return "\n".join(context_parts)

    async def _generate_response_with_context(
        self,
        query: str,
        context: str,
        temperature: float = 0.1
    ) -> str:
        """
        Generate response using Gemini with RAG context.

        Args:
            query: Original user query
            context: Retrieved document context
            temperature: Response temperature for Gemini

        Returns:
            Generated response
        """
        try:
            import google.generativeai as genai
            from config import GOOGLE_API_KEY

            # Configure Gemini - tentar 2.0-flash primeiro, depois 1.5-flash
            genai.configure(api_key=GOOGLE_API_KEY)

            # Tentar modelo mais avançado primeiro
            model_name = 'gemini-2.0-flash-exp'
            try:
                model = genai.GenerativeModel(model_name)
                logger.info(f"✅ Using Gemini model: {model_name}")
            except Exception as e:
                logger.warning(f"Gemini 2.0-flash not available: {e}")
                # Fallback para 1.5-flash
                model_name = 'gemini-1.5-flash'
                try:
                    model = genai.GenerativeModel(model_name)
                    logger.info(f"✅ Using Gemini model: {model_name}")
                except Exception as e2:
                    logger.error(f"Gemini 1.5-flash also not available: {e2}")
                    # Último fallback para pro
                    model_name = 'gemini-pro'
                    model = genai.GenerativeModel(model_name)
                    logger.info(f"✅ Using fallback Gemini model: {model_name}")

            # Create RAG prompt
            rag_prompt = f"""
Responda à pergunta usando apenas o contexto abaixo dos documentos fiscais.
Se não encontrar a resposta, informe que não foi possível localizar no contexto.

Contexto:
{context}

Pergunta: {query}
Resposta:
"""

            # Generate response
            response = model.generate_content(
                rag_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=1000
                )
            )

            return response.text.strip()

        except Exception as e:
            logger.error(f"Error generating response with context: {str(e)}")
            return f"Erro ao gerar resposta: {str(e)}"

    async def validate_document_with_rag(
        self,
        document: Dict[str, Any],
        validation_rules: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Validate document fields using RAG context from similar documents.

        Args:
            document: Document to validate
            validation_rules: Specific validation rules to apply

        Returns:
            Validation results with insights
        """
        try:
            # Generate validation queries based on document type
            validation_queries = self._generate_validation_queries(document, validation_rules)

            validation_results = []

            for query in validation_queries:
                # Search for similar documents to validate against
                query_embedding = self.embedding_service.generate_query_embedding(query)

                similar_docs = self.vector_store.get_document_context(
                    query_embedding=query_embedding,
                    max_documents=5,
                    max_chunks_per_document=1
                )

                # Analyze validation based on similar documents
                validation_insight = self._analyze_validation(document, query, similar_docs)
                validation_results.append(validation_insight)

            # Save validation insights
            for insight in validation_results:
                if insight.get('confidence', 0) > 0.5:
                    self.vector_store.save_analysis_insight(
                        document_id=document['id'],
                        insight_type='validation',
                        insight_category='field_validation',
                        insight_text=insight['insight'],
                        confidence_score=insight['confidence'],
                        metadata=insight.get('metadata', {})
                    )

            return {
                'validation_results': validation_results,
                'document_id': document['id'],
                'validation_queries_used': len(validation_queries)
            }

        except Exception as e:
            logger.error(f"Error in document validation with RAG: {str(e)}")
            return {
                'validation_results': [],
                'document_id': document['id'],
                'error': str(e)
            }

    def _generate_validation_queries(self, document: Dict[str, Any], validation_rules: Optional[List[str]] = None) -> List[str]:
        """
        Generate validation queries based on document content.

        Args:
            document: Document to validate
            validation_rules: Specific rules to apply

        Returns:
            List of validation queries
        """
        queries = []

        # Default validation queries for fiscal documents
        if not validation_rules:
            validation_rules = [
                'document_format',
                'required_fields',
                'value_ranges',
                'issuer_validation'
            ]

        document_type = document.get('document_type', '')
        issuer_cnpj = document.get('issuer_cnpj', '')

        if 'document_format' in validation_rules:
            queries.append(f"Documentos do tipo {document_type} com formato correto")

        if 'required_fields' in validation_rules:
            queries.append(f"Campos obrigatórios para {document_type}")

        if 'value_ranges' in validation_rules and document.get('extracted_data'):
            total_value = document.get('extracted_data', {}).get('total', 0)
            queries.append(f"Valores típicos para documentos similares com valor próximo a {total_value}")

        if 'issuer_validation' in validation_rules and issuer_cnpj:
            queries.append(f"Documentos do emissor {issuer_cnpj} com padrões similares")

        return queries

    def _analyze_validation(
        self,
        document: Dict[str, Any],
        validation_query: str,
        similar_docs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze validation based on similar documents.

        Args:
            document: Document being validated
            validation_query: Validation query used
            similar_docs: Similar documents found

        Returns:
            Validation analysis result
        """
        if not similar_docs:
            return {
                'query': validation_query,
                'insight': 'Nenhum documento similar encontrado para validação',
                'confidence': 0.0,
                'metadata': {'similar_docs_count': 0}
            }

        # Analyze patterns in similar documents
        document_type = document.get('document_type', '')
        similar_types = [doc.get('document_type', '') for doc in similar_docs]
        type_consistency = similar_types.count(document_type) / len(similar_types) if similar_types else 0

        # Generate validation insight
        if type_consistency > 0.8:
            insight = f"Documento do tipo {document_type} é consistente com padrões encontrados em documentos similares."
        elif type_consistency > 0.5:
            insight = f"Documento do tipo {document_type} é parcialmente consistente. Verificar se o tipo está correto."
        else:
            insight = f"Documento do tipo {document_type} diverge dos padrões encontrados. Revisão recomendada."

        return {
            'query': validation_query,
            'insight': insight,
            'confidence': type_consistency,
            'metadata': {
                'similar_docs_count': len(similar_docs),
                'type_consistency': type_consistency,
                'similar_types': similar_types
            }
        }
