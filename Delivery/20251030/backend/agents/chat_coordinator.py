"""
Chat Coordinator - Main interface for the chat system.

This module provides a high-level interface for the chat functionality,
integrating all the chat components and providing a simple API for the frontend.
"""
import asyncio
from typing import Dict, Any, List, Optional
import logging

from backend.agents.chat_agent import ChatAgent, ChatResponse
from backend.tools.chat_tools import DocumentAnalysisTool, CSVAnalysisTool, InsightGenerator

logger = logging.getLogger(__name__)


class ChatCoordinator:
    """Main coordinator for chat system."""

    def __init__(self, storage):
        self.storage = storage
        self.chat_agent = ChatAgent(storage)
        self.document_tool = DocumentAnalysisTool(storage)
        self.csv_tool = CSVAnalysisTool(storage)
        self.insight_generator = InsightGenerator(self.document_tool, self.csv_tool)

    async def initialize_session(self, session_name: str = None) -> str:
        """Initialize a new chat session."""
        return await self.chat_agent.create_session(session_name)

    async def process_query(
        self,
        session_id: str,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a user query and return response."""

        try:
            # Save user message
            await self.chat_agent.save_message(session_id, 'user', query)

            # Determine query type and prepare context
            enhanced_context = await self._enhance_context(query, context)

            # Generate response
            response = await self.chat_agent.generate_response(
                session_id=session_id,
                query=query,
                context=enhanced_context
            )

            return {
                'success': True,
                'response': response.content,
                'metadata': response.metadata,
                'cached': response.cached,
                'tokens_used': response.tokens_used
            }

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            error_str = str(e)
            if '429' in error_str or 'ResourceExhausted' in error_str or 'Resource exhausted' in error_str:
                user_msg = (
                    '⚠️ O sistema atingiu o limite de uso da API de IA no momento. '
                    'Por favor, tente novamente em alguns minutos. Caso o problema persista, contate o suporte. '
                    'Mais detalhes: https://cloud.google.com/vertex-ai/generative-ai/docs/error-code-429'
                )
            else:
                user_msg = 'Desculpe, ocorreu um erro ao processar sua pergunta.'
            return {
                'success': False,
                'error': error_str,
                'response': user_msg,
                'metadata': {'error': True}
            }

    async def save_message(
        self,
        session_id: str,
        message_type: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Save a message to the chat session.
        
        Args:
            session_id: The ID of the chat session
            message_type: Type of message ('user' or 'assistant')
            content: The message content
            metadata: Optional metadata for the message
        """
        try:
            await self.chat_agent.save_message(
                session_id=session_id,
                message_type=message_type,
                content=content,
                metadata=metadata or {}
            )
            logger.info(f"Message saved - Session: {session_id}, Type: {message_type}")
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            raise
            
    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get chat history for a session."""
        try:
            # Get messages from storage
            messages = await self.chat_agent.get_conversation_history(session_id)
            logger.info(f"Retrieved {len(messages)} messages for session {session_id}")
            return messages
            
        except Exception as e:
            logger.error(f"Error getting session history: {e}")
            return []

    async def _enhance_context(
        self,
        query: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Enhance context based on query content."""

        enhanced_context = context or {}
        query_lower = query.lower()

        # Detect query type based on keywords
        if any(word in query_lower for word in ['documento', 'nota', 'nfe', 'nfce', 'cte', 'fiscal']):
            enhanced_context['query_type'] = 'document_analysis'
            enhanced_context['document_types'] = ['NFe', 'NFCe', 'CTe']

        elif any(word in query_lower for word in ['csv', 'planilha', 'dados', 'análise', 'estatística']):
            enhanced_context['query_type'] = 'csv_analysis'

        elif any(word in query_lower for word in ['financeiro', 'valor', 'total', 'imposto', 'receita', 'despesa']):
            enhanced_context['query_type'] = 'financial_analysis'

        elif any(word in query_lower for word in ['validação', 'erro', 'inconsistência', 'problema']):
            enhanced_context['query_type'] = 'validation_analysis'

        else:
            enhanced_context['query_type'] = 'general'

        # Set default limits
        enhanced_context.setdefault('limit', 10)

        return enhanced_context

    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get chat history for a session."""

        try:
            return self.storage.get_chat_messages(session_id, limit=50)

        except Exception as e:
            logger.error(f"Error getting session history: {e}")
            return []

    async def get_document_analysis(self, document_ids: List[str]) -> Dict[str, Any]:
        """Get detailed analysis for specific documents."""

        try:
            documents = []
            for doc_id in document_ids:
                summary = self.document_tool.get_document_summary(doc_id)
                if summary:
                    documents.append(summary)

            if not documents:
                return {'error': 'Nenhum documento encontrado'}

            # Generate insights
            insights = self.insight_generator.generate_financial_insights(
                [doc['document'] for doc in documents]
            )

            return {
                'documents': documents,
                'insights': insights,
                'summary': {
                    'total_documents': len(documents),
                    'document_types': list(set(doc['document'].get('document_type', 'Unknown')
                                             for doc in documents))
                }
            }

        except Exception as e:
            logger.error(f"Error getting document analysis: {e}")
            return {'error': str(e)}

    async def analyze_csv_data(self, csv_data: str) -> Dict[str, Any]:
        """Analyze CSV data and return insights."""

        try:
            analysis = self.csv_tool.analyze_csv_data(csv_data)

            if 'error' in analysis:
                return analysis

            # Generate insights
            insights = self.insight_generator.generate_csv_insights(analysis)

            return {
                'analysis': analysis,
                'insights': insights
            }

        except Exception as e:
            logger.error(f"Error analyzing CSV data: {e}")
            return {'error': str(e)}

    async def search_documents(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search documents based on query and filters."""

        try:
            criteria = filters or {}

            # Add text search to criteria
            if query:
                # Use storage to search documents
                all_docs = await self.storage.get_fiscal_documents(page=1, page_size=1000)

                # Filter documents containing the query
                filtered_docs = []
                for doc in all_docs.items:
                    if self._document_matches_query(doc, query):
                        filtered_docs.append(doc)

                return {
                    'documents': filtered_docs[:20],  # Limit results
                    'total': len(filtered_docs),
                    'query': query
                }

            else:
                # Use criteria-based search
                documents = self.document_tool.get_documents_by_criteria(criteria, limit=20)
                return {
                    'documents': documents,
                    'total': len(documents),
                    'query': query
                }

        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return {'error': str(e), 'documents': [], 'total': 0}

    def _document_matches_query(self, document: Dict[str, Any], query: str) -> bool:
        """Check if document matches the search query."""

        query_lower = query.lower()
        extracted_data = document.get('extracted_data', {})

        # Search in various fields
        search_fields = [
            extracted_data.get('emitente', {}).get('razao_social', ''),
            extracted_data.get('emitente', {}).get('cnpj', ''),
            extracted_data.get('destinatario', {}).get('razao_social', ''),
            extracted_data.get('destinatario', {}).get('cnpj', ''),
            document.get('file_name', ''),
            document.get('document_number', ''),
            str(extracted_data)
        ]

        return any(query_lower in str(field).lower() for field in search_fields)

    async def get_chat_sessions(self, user_id: str = None) -> List[Dict[str, Any]]:
        """Get list of chat sessions."""

        try:
            sessions = self.storage.get_chat_sessions(limit=20)

            # Filter by user_id if provided (not implemented in storage yet)
            if user_id:
                sessions = [s for s in sessions if s.get('user_id') == user_id]

            return sessions

        except Exception as e:
            logger.error(f"Error getting chat sessions: {e}")
            return []

    async def delete_session(self, session_id: str) -> bool:
        """Delete a chat session and all its messages."""

        try:
            return self.storage.delete_chat_session(session_id)

        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False
