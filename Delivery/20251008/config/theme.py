import streamlit as st
import os

def load_css():
    """Carrega os estilos CSS personalizados."""
    try:
        css_path = os.path.join(os.path.dirname(__file__), "..", "assets", "style.css")
        with open(css_path, encoding='utf-8') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Erro ao carregar estilos: {e}")

def set_theme():
    """Configura o tema personalizado do Streamlit."""
    st.markdown("""
    <style>
        /* Corrige o padding do conteúdo principal */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        /* Melhora a aparência das abas */
        .stTabs [data-baseweb="tab"] {
            margin: 0 0.25rem;
        }
        /* Melhora a aparência dos inputs */
        .stTextInput>div>div>input, 
        .stSelectbox>div>div {
            box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        }
        /* Estilo para mensagens de erro */
        .stAlert {
            border-radius: 0.5rem;
            margin: 1rem 0;
        }
        /* Espaçamento entre elementos */
        .stButton>button {
            margin: 0.25rem 0;
        }
    </style>
    """, unsafe_allow_html=True)

def init_ui():
    """Inicializa a interface do usuário com tema e estilos."""
    # Configuração da página
    # Desenvolvido por Ernani Fantinatti
    st.set_page_config(
        layout="wide",
        page_title="InsightAgent EDA - Ernani Fantinatti",
        page_icon="📊",
        initial_sidebar_state="expanded"
    )
    
    # Carrega estilos e tema
    load_css()
    set_theme()
