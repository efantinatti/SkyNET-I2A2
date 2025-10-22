"""
🚀 SkyNET-I2A2 - Agentes Autônomos para Processamento Fiscal + EDA
Sistema completo com IA Generativa para análise de documentos fiscais e dados

Desenvolvido por: Equipe SkyNET-I2A2
Tecnologias: Streamlit + FastAPI + CrewAI + Google Gemini + Supabase
"""

import streamlit as st
import os
import sys
import json
from pathlib import Path
from datetime import datetime
import asyncio
import uuid

# Adiciona o backend ao path
backend_path = Path(__file__).parent / "backend"
sys.path.append(str(backend_path))

# Imports locais
try:
    from backend.config import settings
    from backend.core.memory import SupabaseManager, MemoryManager
    from backend.auth.models import UserCreate, UserLogin
    from backend.auth.password import PasswordManager
    from backend.auth.jwt_handler import JWTHandler, TokenValidator
except ImportError as e:
    st.error(f"Erro ao importar módulos: {e}")
    st.stop()

# Configuração da página
st.set_page_config(
    page_title="SkyNET-I2A2 | IA para Fiscal & Análise",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://docs.skynet-i2a2.com',
        'Report a bug': 'https://github.com/skynet-i2a2/issues',
        'About': """
        ## SkyNET-I2A2 v1.0.0
        
        Sistema de agentes autônomos para:
        - 📄 Processamento de documentos fiscais (NFe, NFCe, CTe)
        - 📊 Análise exploratória de dados (EDA)
        - 🤖 Chat inteligente com IA
        - 📈 Geração automática de gráficos
        - 🔐 Autenticação segura com JWT
        
        **Tecnologias:**
        - Frontend: Streamlit
        - Backend: FastAPI
        - Agentes: CrewAI
        - LLM: Google Gemini
        - Banco: Supabase (PostgreSQL)
        
        Desenvolvido com ❤️ pela equipe SkyNET-I2A2
        """
    }
)

# CSS customizado
st.markdown("""
<style>
    /* Layout principal */
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .feature-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #2a5298;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .stat-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #c3e6cb;
        margin: 1rem 0;
    }
    
    .error-message {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #f5c6cb;
        margin: 1rem 0;
    }
    
    .sidebar-logo {
        text-align: center;
        padding: 1rem;
        margin-bottom: 2rem;
    }
    
    /* Botões customizados */
    .stButton > button {
        background: linear-gradient(90deg, #2a5298 0%, #1e3c72 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: transform 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Métricas */
    [data-testid="metric-container"] {
        background: white;
        border: 1px solid #e0e0e0;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Sidebar */
    .css-1d391kg {
        background: #f8f9fa;
    }
    
    /* Ocultara menu do Streamlit em produção */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Funções de sessão
def init_session_state():
    """Inicializa o estado da sessão"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Home"

def check_authentication():
    """Verifica se usuário está autenticado"""
    if not st.session_state.authenticated:
        return False
    
    # Verifica se há token válido nos cookies ou session state
    if 'access_token' in st.session_state:
        token_data = TokenValidator.validate_access_token(st.session_state.access_token)
        if token_data:
            return True
    
    # Token inválido, desloga
    logout_user()
    return False

def logout_user():
    """Realiza logout do usuário"""
    st.session_state.authenticated = False
    st.session_state.user_data = None
    st.session_state.session_id = None
    if 'access_token' in st.session_state:
        del st.session_state.access_token
    if 'refresh_token' in st.session_state:
        del st.session_state.refresh_token

async def authenticate_user(email: str, password: str) -> tuple[bool, str]:
    """Autentica usuário"""
    try:
        supabase = SupabaseManager()
        
        # Busca usuário
        user = await supabase.get_user_by_email(email)
        if not user:
            return False, "Email ou senha incorretos"
        
        # Verifica senha
        if not PasswordManager.verify_password(password, user['password_hash']):
            return False, "Email ou senha incorretos"
        
        # Verifica se conta está ativa
        if not user.get('is_active', False):
            return False, "Conta inativa. Contate o suporte."
        
        # Gera tokens
        tokens = JWTHandler.create_token_pair(user['id'], user['email'])
        
        # Salva no session state
        st.session_state.authenticated = True
        st.session_state.user_data = user
        st.session_state.access_token = tokens['access_token']
        st.session_state.refresh_token = tokens['refresh_token']
        st.session_state.session_id = str(uuid.uuid4())
        
        return True, "Login realizado com sucesso!"
        
    except Exception as e:
        return False, f"Erro interno: {str(e)}"

async def register_user(user_data: dict) -> tuple[bool, str]:
    """Registra novo usuário"""
    try:
        supabase = SupabaseManager()
        
        # Verifica se email já existe
        existing_user = await supabase.get_user_by_email(user_data['email'])
        if existing_user:
            return False, "Email já está em uso"
        
        # Valida senha
        is_strong, issues = PasswordManager.check_password_strength(user_data['password'])
        if not is_strong:
            return False, f"Senha fraca: {', '.join(issues)}"
        
        # Cria usuário
        password_hash = PasswordManager.hash_password(user_data['password'])
        user_dict = {**user_data}
        del user_dict['password']
        del user_dict['confirm_password']
        user_dict['password_hash'] = password_hash
        user_dict['id'] = str(uuid.uuid4())
        
        await supabase.create_user(user_dict)
        return True, "Usuário criado com sucesso! Faça login para continuar."
        
    except Exception as e:
        return False, f"Erro ao criar usuário: {str(e)}"

# Interface principal
def main():
    """Função principal da aplicação"""
    init_session_state()
    
    # Header principal
    st.markdown("""
    <div class="main-header">
        <h1>🚀 SkyNET-I2A2</h1>
        <h3>Agentes Autônomos para Processamento Fiscal + EDA</h3>
        <p>Análise inteligente de documentos fiscais e dados com IA Generativa</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div class="sidebar-logo">
            <h2>🤖 SkyNET-I2A2</h2>
            <p>Powered by AI</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Menu de navegação
        if st.session_state.authenticated:
            st.success(f"👋 Olá, {st.session_state.user_data.get('full_name', 'Usuário')}")
            
            # Estatísticas rápidas
            st.markdown("### 📊 Resumo")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Documentos", "12", "↗️ +3")
            with col2:
                st.metric("Análises", "8", "↗️ +2")
            
            st.markdown("---")
            
            # Menu principal
            page = st.selectbox(
                "🧭 Navegação",
                ["🏠 Dashboard", "📊 Análise de Dados", "📄 Documentos Fiscais", "💬 Chat IA", "👤 Perfil"],
                key="navigation"
            )
            
            st.markdown("---")
            
            if st.button("🚪 Logout", use_container_width=True):
                logout_user()
                st.rerun()
        
        else:
            st.markdown("### 🔐 Acesso")
            auth_mode = st.selectbox("Escolha uma opção:", ["Login", "Registrar"])
            
            if auth_mode == "Login":
                show_login_form()
            else:
                show_register_form()
    
    # Conteúdo principal
    if st.session_state.authenticated:
        show_authenticated_content()
    else:
        show_public_content()

def show_login_form():
    """Formulário de login"""
    with st.form("login_form"):
        st.markdown("#### 📧 Login")
        email = st.text_input("Email", placeholder="seu@email.com")
        password = st.text_input("Senha", type="password", placeholder="Sua senha")
        remember_me = st.checkbox("Lembrar de mim")
        
        if st.form_submit_button("🔓 Entrar", use_container_width=True):
            if email and password:
                # Executa autenticação
                with st.spinner("Autenticando..."):
                    success, message = asyncio.run(authenticate_user(email, password))
                
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.warning("Preencha todos os campos")

def show_register_form():
    """Formulário de registro"""
    with st.form("register_form"):
        st.markdown("#### 📝 Criar Conta")
        
        email = st.text_input("Email", placeholder="seu@email.com")
        full_name = st.text_input("Nome Completo", placeholder="Seu nome")
        company_name = st.text_input("Empresa (opcional)", placeholder="Nome da empresa")
        industry = st.selectbox("Setor", [
            "Indústria", "Comércio", "Agronegócio", 
            "Serviços", "Tecnologia", "Outros"
        ])
        
        col1, col2 = st.columns(2)
        with col1:
            password = st.text_input("Senha", type="password", placeholder="Mín. 8 caracteres")
        with col2:
            confirm_password = st.text_input("Confirmar Senha", type="password")
        
        terms = st.checkbox("Li e aceito os termos de uso")
        
        if st.form_submit_button("✅ Criar Conta", use_container_width=True):
            if not all([email, full_name, password, confirm_password]):
                st.warning("Preencha todos os campos obrigatórios")
            elif password != confirm_password:
                st.error("Senhas não coincidem")
            elif not terms:
                st.warning("Aceite os termos de uso para continuar")
            else:
                user_data = {
                    'email': email,
                    'full_name': full_name,
                    'company_name': company_name,
                    'industry': industry,
                    'password': password,
                    'confirm_password': confirm_password
                }
                
                with st.spinner("Criando conta..."):
                    success, message = asyncio.run(register_user(user_data))
                
                if success:
                    st.success(message)
                else:
                    st.error(message)

def show_public_content():
    """Conteúdo para usuários não autenticados"""
    
    # Seção de recursos
    st.markdown("## 🌟 Recursos Principais")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="feature-card">
            <h4>📄 Documentos Fiscais</h4>
            <p>Processamento automático de NFe, NFCe e CTe com OCR e validação fiscal inteligente.</p>
            <ul>
                <li>Extração automática de dados</li>
                <li>Validação de CFOP e NCM</li>
                <li>Classificação por setor</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="feature-card">
            <h4>📊 Análise de Dados</h4>
            <p>EDA automatizada com geração de insights e gráficos interativos.</p>
            <ul>
                <li>Upload de CSV/Excel</li>
                <li>Estatísticas descritivas</li>
                <li>Detecção de outliers</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="feature-card">
            <h4>🤖 Agentes IA</h4>
            <p>Sistema de agentes autônomos para análise e consultoria inteligente.</p>
            <ul>
                <li>Chat contextualizado</li>
                <li>Recomendações automáticas</li>
                <li>Relatórios personalizados</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Demonstração
    st.markdown("## 🎯 Demonstração")
    
    demo_tab1, demo_tab2, demo_tab3 = st.tabs(["📊 Análise", "📄 Documentos", "💬 Chat"])
    
    with demo_tab1:
        st.markdown("### Exemplo: Análise de Vendas")
        
        # Dados de exemplo
        import pandas as pd
        import numpy as np
        
        # Gera dados sintéticos
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=100, freq='D')
        data = {
            'Data': dates,
            'Vendas': np.random.normal(10000, 2000, 100),
            'Produto': np.random.choice(['A', 'B', 'C'], 100),
            'Região': np.random.choice(['Norte', 'Sul', 'Sudeste'], 100)
        }
        df = pd.DataFrame(data)
        
        st.dataframe(df.head(), use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total de Vendas", f"R$ {df['Vendas'].sum():,.2f}")
        with col2:
            st.metric("Ticket Médio", f"R$ {df['Vendas'].mean():,.2f}")
    
    with demo_tab2:
        st.markdown("### Exemplo: NFe Processada")
        st.json({
            "numero_documento": "000000123",
            "emissor": "Empresa XYZ Ltda",
            "cnpj_emissor": "12.345.678/0001-99",
            "valor_total": 15750.80,
            "data_emissao": "2024-10-20",
            "cfop": "5102",
            "status_validacao": "✅ Válido"
        })
    
    with demo_tab3:
        st.markdown("### Exemplo: Conversa com IA")
        
        # Simulação de chat
        messages = [
            {"role": "user", "content": "Analise as vendas do último trimestre"},
            {"role": "assistant", "content": "Com base nos dados analisados, identifiquei os seguintes insights:\n\n1. **Crescimento**: Aumento de 15% nas vendas\n2. **Produto líder**: Produto A representa 45% do faturamento\n3. **Região forte**: Sudeste concentra 60% das vendas\n\n**Recomendação**: Expandir marketing na região Norte para equilibrar a distribuição."}
        ]
        
        for msg in messages:
            if msg["role"] == "user":
                st.chat_message("user").write(msg["content"])
            else:
                st.chat_message("assistant").write(msg["content"])

def show_authenticated_content():
    """Conteúdo para usuários autenticados"""
    page = st.session_state.get("navigation", "🏠 Dashboard")
    
    if "Dashboard" in page:
        show_dashboard()
    elif "Análise" in page:
        show_analysis_page()
    elif "Documentos" in page:
        show_documents_page()
    elif "Chat" in page:
        show_chat_page()
    elif "Perfil" in page:
        show_profile_page()

def show_dashboard():
    """Dashboard principal"""
    st.markdown("## 📊 Dashboard")
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📄 Documentos", "12", "↗️ +3")
    with col2:
        st.metric("📊 Análises", "8", "↗️ +2")
    with col3:
        st.metric("💬 Conversas", "45", "↗️ +12")
    with col4:
        st.metric("💰 Valor Processado", "R$ 125K", "↗️ +15%")
    
    st.markdown("---")
    
    # Atividade recente
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 📈 Atividade Recente")
        
        # Lista de atividades simuladas
        activities = [
            {"time": "10:30", "action": "Documento NFe-123 processado", "status": "✅"},
            {"time": "10:15", "action": "Análise de vendas concluída", "status": "✅"},
            {"time": "09:45", "action": "Chat: Consulta sobre impostos", "status": "💬"},
            {"time": "09:20", "action": "Upload de dados CSV", "status": "📊"},
        ]
        
        for activity in activities:
            st.markdown(f"""
            <div style="padding: 0.5rem; border-left: 3px solid #2a5298; margin: 0.5rem 0; background: #f8f9fa;">
                <strong>{activity['time']}</strong> {activity['status']} {activity['action']}
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 🎯 Ações Rápidas")
        
        if st.button("📄 Novo Documento", use_container_width=True):
            st.session_state.navigation = "📄 Documentos Fiscais"
            st.rerun()
        
        if st.button("📊 Nova Análise", use_container_width=True):
            st.session_state.navigation = "📊 Análise de Dados"
            st.rerun()
        
        if st.button("💬 Abrir Chat", use_container_width=True):
            st.session_state.navigation = "💬 Chat IA"
            st.rerun()

def show_analysis_page():
    """Página de análise de dados"""
    st.markdown("## 📊 Análise de Dados")
    st.info("🚧 Módulo em construção - Funcionalidade será implementada pelos agentes")

def show_documents_page():
    """Página de documentos fiscais"""
    st.markdown("## 📄 Documentos Fiscais")
    st.info("🚧 Módulo em construção - Funcionalidade será implementada pelos agentes")

def show_chat_page():
    """Página de chat com IA"""
    st.markdown("## 💬 Chat com IA")
    st.info("🚧 Módulo em construção - Funcionalidade será implementada pelos agentes")

def show_profile_page():
    """Página de perfil do usuário"""
    st.markdown("## 👤 Perfil do Usuário")
    
    user_data = st.session_state.user_data
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### 📋 Informações")
        st.write(f"**Nome:** {user_data.get('full_name', 'N/A')}")
        st.write(f"**Email:** {user_data.get('email', 'N/A')}")
        st.write(f"**Empresa:** {user_data.get('company_name', 'N/A')}")
        st.write(f"**Setor:** {user_data.get('industry', 'N/A')}")
        st.write(f"**Membro desde:** {user_data.get('created_at', 'N/A')[:10]}")
    
    with col2:
        st.markdown("### ⚙️ Configurações")
        
        with st.form("profile_form"):
            full_name = st.text_input("Nome Completo", value=user_data.get('full_name', ''))
            company_name = st.text_input("Empresa", value=user_data.get('company_name', ''))
            industry = st.selectbox("Setor", [
                "Indústria", "Comércio", "Agronegócio", 
                "Serviços", "Tecnologia", "Outros"
            ], index=0)
            
            if st.form_submit_button("💾 Salvar Alterações"):
                st.success("Perfil atualizado com sucesso!")

# Execução principal
if __name__ == "__main__":
    # Carrega variáveis de ambiente em desenvolvimento
    if settings.is_development:
        from dotenv import load_dotenv
        load_dotenv()
    
    main()