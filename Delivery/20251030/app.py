import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

# Page configuration must be the first Streamlit command
st.set_page_config(
    page_title="SkyNET-I2A2",
    page_icon="🛰️",
    layout="wide"
)

# Import only basic modules here
from pathlib import Path
import json

# Initialize storage backend
try:
    from backend.database import storage_manager
    storage = storage_manager.storage
except Exception as e:
    st.error(f"Erro ao inicializar o armazenamento: {str(e)}")
    st.stop()

from frontend.components import document_renderer

st.title('SkyNET-I2A2 - Processamento Fiscal (MVP)')

menu = st.sidebar.selectbox('Navegação', ['Home', 'Importador', 'Chat IA', 'Histórico', 'RAG'])

# Initialize session state for RAG service
if 'rag_service' not in st.session_state:
    try:
        from backend.services import RAGService, VectorStoreService
        vector_store = VectorStoreService()
        st.session_state.rag_service = RAGService(vector_store=vector_store)
        st.sidebar.success("✅ Sistema RAG inicializado")
    except Exception as e:
        st.sidebar.error(f"❌ Erro no RAG: {str(e)[:50]}...")
        st.session_state.rag_service = None

# Display storage status in the sidebar
storage_manager.display_status()

# Initialize session state for processed documents
if 'processed_documents' not in st.session_state:
    st.session_state.processed_documents = []

# Load documents if not already loaded
if not st.session_state.processed_documents:
    try:
        result = storage.get_fiscal_documents(page=1, page_size=1000)
        st.session_state.processed_documents = result.items  # Acessando items diretamente do objeto PaginatedResponse
    except Exception as e:
        st.sidebar.error(f'Erro ao carregar documentos: {str(e)[:150]}')
        st.session_state.processed_documents = []

# Import and render the selected page
if menu == 'Home':
    from frontend.pages import home
    home.render()
elif menu == 'Importador':
    from frontend.pages import importador
    importador.render(storage)
elif menu == 'Chat IA':
    from frontend.pages import chat
    chat.render()
elif menu == 'Histórico':
    from frontend.pages import history
    history.render(storage)
elif menu == 'RAG':
    from frontend.pages import rag
    rag.main()
