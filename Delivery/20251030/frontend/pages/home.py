"""Home page of the SkyNET-I2A2 Fiscal Processing System."""
import streamlit as st
from backend.database import storage_manager

# Try to import streamlit_extras, but make it optional
HAS_STREAMLIT_EXTRAS = False
if 'streamlit_extras_imported' not in st.session_state:
    try:
        from streamlit_extras.metric_cards import style_metric_cards
        HAS_STREAMLIT_EXTRAS = True
        st.session_state.streamlit_extras_imported = True
    except ImportError:
        st.session_state.streamlit_extras_imported = False
        # Mostra o aviso apenas uma vez
        if 'show_streamlit_extras_warning' not in st.session_state:
            st.warning(
                "⚠️ O pacote 'streamlit-extras' não está instalado. "
                "Alguns recursos visuais podem estar limitados.\n\n"
                "Para instalar, execute no terminal:\n"
                "```\n"
                "pip install streamlit-extras\n"
                "```"
            )
            st.session_state.show_streamlit_extras_warning = True
else:
    HAS_STREAMLIT_EXTRAS = st.session_state.streamlit_extras_imported


def render():
    """Render the home page with system overview and features."""
    # Session state initialization if needed
    if 'page_initialized' not in st.session_state:
        st.session_state.page_initialized = True
    
    # Header with logo and title
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image("https://img.icons8.com/color/96/000000/invoice.png", width=80)
    with col2:
        st.title("SkyNET-I2A2")
        st.markdown("### Sistema Inteligente de Processamento Fiscal")
    
    st.markdown("---")
    
    # Key Features Section
    st.markdown("## 🚀 Funcionalidades Principais")
    
    # Feature cards
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container(border=True, height=200):
            st.markdown("### 📄 Extração Inteligente")
            st.markdown("""
            - Suporte a múltiplos formatos (XML, PDF, Imagens)
            - OCR avançado com Tesseract
            - Parser XML para NFe/NFCe/CTe/MDFe
            """)
    
    with col2:
        with st.container(border=True, height=200):
            st.markdown("### ✅ Validação Fiscal")
            st.markdown("""
            - Validação de CNPJ/CPF
            - Cálculo automático de impostos
            - Verificação de inconsistências
            - Classificação automática
            """)
    
    with col3:
        with st.container(border=True, height=200):
            st.markdown("### 🔍 IA & RAG Conversacional")
            st.markdown("""
            - Busca semântica com pgvector
            - Chat com memória conversacional
            - Contexto fiscal enriquecido automaticamente
            - Respostas consultivas em português
            """)
    
    # Getting Started Section
    st.markdown("## 🏁 Começando")
    
    tab1, tab2, tab3 = st.tabs(["📤 Upload de Documento", "💬 Chat IA & RAG", "📂 Histórico"])
    
    with tab1:
        st.markdown("""
        ### Processe documentos fiscais
        1. Acesse a aba **Upload Documento**
        2. Selecione um arquivo (XML, PDF ou imagem)
        3. Visualize os dados extraídos
        4. Verifique as validações fiscais
        """)
    
    with tab2:
        st.markdown("""
        ### Converse com a IA
        1. Acesse a aba **Chat IA**
        2. Faça perguntas sobre documentos ou processos fiscais
        3. Utilize o contexto sugerido pelo RAG quando disponível
        4. Exporte as conversas para compartilhar com a equipe
        """)
    
    with tab3:
        st.markdown("""
        ### Histórico e Busca
        1. Acesse a aba **Histórico**
        2. Visualize documentos processados
        3. Filtre por data, tipo ou status
        4. Consulte revisões e documentos previamente processados
        """)
    
    # Storage Status Section
    st.markdown("## 💾 Status do Armazenamento")
    
    # Storage Status Card
    status_container = st.container(border=True)
    with status_container:
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown("### Configuração Atual")
            # Get status from storage manager
            status = storage_manager.status
            status_type = storage_manager.status_type
            
            # Status badge
            status_emoji = ""
            if status_type == "success":
                status_emoji = "✅"
                status_color = "green"
            elif status_type == "warning":
                status_emoji = "⚠️"
                status_color = "orange"
            elif status_type == "error":
                status_emoji = "❌"
                status_color = "red"
            else:
                status_emoji = "ℹ️"
                status_color = "blue"
                
            st.markdown(f"""
            <div style='background-color:#f0f2f6; padding:15px; border-radius:10px;'>
                <h3 style='color:{status_color};'>{status_emoji} {status}</h3>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if "Supabase" in status:
                st.markdown("""
                ### Banco de Dados Remoto
                - **Tipo**: Supabase (PostgreSQL)
                - **Status**: Conectado e sincronizado
                - **Tabelas**: 
                    - `fiscal_documents` - Armazena documentos fiscais processados
                    - `document_analyses` - Análises e validações realizadas
                    - `sessions` - Histórico de sessões do usuário
                - **Vantagens**: 
                    - Dados persistentes entre sessões
                    - Backup automático
                    - Acesso de múltiplos dispositivos
                """)
            else:
                st.markdown("""
                ### Armazenamento Local
                - **Tipo**: Sistema de arquivos (JSON)
                - **Status**: Ativo (Modo de demonstração)
                - **Localização**: Pasta local do aplicativo
                - **Limitações**:
                    - Dados temporários (apenas na sessão atual)
                    - Sem backup automático
                    - Apenas um usuário por vez
                - **Recomendação**: Configure o Supabase para uso em produção
                
                *Para configurar o Supabase, adicione as credenciais no arquivo `.env`*
                """)
    
    # Call to Action
    st.markdown("---")
    st.markdown("""
    ## Pronto para começar?
    
    Acesse o menu lateral para explorar as funcionalidades do sistema ou consulte nossa documentação para mais informações.
    
    **Equipe SkyNET-I2A2**  
    *Soluções Inteligentes em Processamento Fiscal*
    """)