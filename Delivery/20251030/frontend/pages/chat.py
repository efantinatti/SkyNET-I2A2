"""
Chat page with LLM integration for document and CSV analysis.

This page provides an intelligent chat interface that can:
- Answer questions about processed documents
- Analyze CSV data and provide insights
- Cache responses to save tokens
- Maintain conversation context
"""
import streamlit as st
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List
import asyncio
import logging

# Import the chat coordinator
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from backend.agents.chat_coordinator import ChatCoordinator

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize chat coordinator
@st.cache_resource
def get_chat_coordinator():
    """Get or create chat coordinator instance."""
    try:
        from backend.database import storage_manager
        # Use storage directly instead of supabase_client
        return ChatCoordinator(storage_manager.storage)
    except Exception as e:
        st.error(f"Erro ao inicializar chat: {e}")
        return None

def render():
    """Render the chat page."""

    st.title("💬 Chat Inteligente")
    st.markdown("### Assistente IA para Análise de Documentos Fiscais")

    # Initialize chat coordinator
    chat_coordinator = get_chat_coordinator()
    if not chat_coordinator:
        st.error("Não foi possível inicializar o sistema de chat.")
        return

    # Initialize session state
    if 'chat_session_id' not in st.session_state:
        st.session_state.chat_session_id = None
    if 'chat_messages' not in st.session_state:
        st.session_state.chat_messages = []
    if 'chat_initialized' not in st.session_state:
        st.session_state.chat_initialized = False

    # Sidebar for session management
    with st.sidebar:
        st.header("🔧 Gerenciar Sessão")

        # Session name input
        session_name = st.text_input(
            "Nome da Sessão",
            value=st.session_state.get('chat_session_name', ''),
            help="Dê um nome descritivo para sua sessão de chat"
        )

        # New session button
        if st.button("🆕 Nova Sessão", type="primary"):
            try:
                session_id = asyncio.run(chat_coordinator.initialize_session(session_name or None))
                st.session_state.chat_session_id = session_id
                st.session_state.chat_session_name = session_name
                st.session_state.chat_messages = []
                st.session_state.chat_initialized = True
                st.success("Nova sessão criada!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao criar sessão: {e}")

        # Session info
        if st.session_state.chat_session_id:
            st.info(f"📝 Sessão: {st.session_state.get('chat_session_name', 'Sem nome')}")
            st.info(f"🆔 ID: {st.session_state.chat_session_id[:8]}...")

            # Load chat history
            if st.button("📚 Carregar Histórico"):
                try:
                    messages = asyncio.run(chat_coordinator.get_session_history(st.session_state.chat_session_id))
                    st.session_state.chat_messages = messages
                    st.success("Histórico carregado!")
                except Exception as e:
                    st.error(f"Erro ao carregar histórico: {e}")

        # Session list
        st.markdown("---")
        st.subheader("📋 Sessões Recentes")

        try:
            sessions = asyncio.run(chat_coordinator.get_chat_sessions())
            if sessions:
                for session in sessions[:5]:  # Show last 5 sessions
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.text(f"{session['title']}")
                        created_at = session['created_at']
                        # Handle datetime object or string
                        if hasattr(created_at, 'strftime'):
                            # It's a datetime object
                            date_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            # It's already a string
                            date_str = str(created_at)[:19]
                        st.caption(date_str)
                    with col2:
                        if st.button("🔄", key=f"load_{session['id']}", help="Carregar esta sessão"):
                            st.session_state.chat_session_id = session['id']
                            st.session_state.chat_session_name = session['title']
                            messages = asyncio.run(chat_coordinator.get_session_history(session['id']))
                            st.session_state.chat_messages = messages
                            st.success("Sessão carregada!")
                            st.rerun()
            else:
                st.info("Nenhuma sessão encontrada")
        except Exception as e:
            st.error(f"Erro ao carregar sessões: {e}")

    # Main chat interface
    if not st.session_state.chat_session_id:
        st.info("👋 Crie uma nova sessão para começar a conversar!")
        return

    # Chat messages display
    st.subheader("💬 Conversa")

    # Display chat messages
    chat_container = st.container()
    with chat_container:
        if not st.session_state.chat_messages:
            st.info("Esta é uma nova sessão. Faça sua primeira pergunta!")
        else:
            for message in st.session_state.chat_messages:
                if isinstance(message, dict):
                    msg_type = message.get('message_type', 'user')
                    if msg_type == 'user':
                        with st.chat_message("user"):
                            st.write(message.get('content', ''))
                    elif msg_type == 'assistant':
                        with st.chat_message("assistant"):
                            st.write(message.get('content', ''))

    # Chat input
    st.markdown("---")

    # Default context for all queries
    context = {
        'query_type': 'geral',
        'limit': 10
    }

    # Chat input
    if prompt := st.chat_input("Digite sua pergunta..."):
        # Add user message to display
        with st.chat_message("user"):
            st.write(prompt)

        # Update session state with user message
        try:
            # The message will be saved by process_query
            st.session_state.chat_messages = asyncio.run(chat_coordinator.get_session_history(st.session_state.chat_session_id))
            
        except Exception as e:
            st.error(f"Erro ao salvar mensagem: {e}")
            return

        # Show loading
        with st.chat_message("assistant"):
            with st.spinner("Pensando..."):
                try:
                    # Process query
                    response = asyncio.run(chat_coordinator.process_query(
                        session_id=st.session_state.chat_session_id,
                        query=prompt,
                        context=context
                    ))

                    if response.get('success'):
                        # Display response
                        st.write(response['response'])

                        # Update session state with assistant response
                        try:
                            # The response is already saved by process_query
                            st.session_state.chat_messages = asyncio.run(chat_coordinator.get_session_history(st.session_state.chat_session_id))
                            
                        except Exception as e:
                            st.error(f"Erro ao salvar resposta do assistente: {e}")

                    else:
                        st.error(f"Erro: {response.get('error', 'Erro desconhecido')}")

                except Exception as e:
                    st.error(f"Erro ao processar pergunta: {e}")
                    logger.error(f"Chat error: {e}")

    # Footer - Apenas uma dica será exibida
    st.markdown("---")
    if not st.session_state.get('dica_exibida', False):
        st.caption("💡 Dica: Faça perguntas sobre documentos fiscais para obter informações detalhadas.")
        st.session_state.dica_exibida = True
