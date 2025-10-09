"""
Configurações personalizadas para Ernani Fantinatti
InsightAgent EDA - Versão I2A2
"""

# Informações do Desenvolvedor
DEVELOPER_INFO = {
    "name": "Ernani Fantinatti",
    "github": "efantinatti",
    "repository": "https://github.com/efantinatti/SkyNET-I2A2",
    "project": "SkyNET-I2A2 - Delivery/Fantinatti",
    "version": "1.0.0-fantinatti",
    "year": "2025"
}

# Configurações da Aplicação
APP_CONFIG = {
    "title": "InsightAgent EDA - Ernani Fantinatti",
    "subtitle": "Seu Assistente de Análise de Dados com IA",
    "icon": "📊",
    "description": "Desenvolvido por Ernani Fantinatti para o projeto I2A2"
}

# Mensagens Personalizadas
MESSAGES = {
    "welcome": f"""
    # 👋 Bem-vindo ao InsightAgent EDA!
    
    Desenvolvido por **{DEVELOPER_INFO['name']}** como parte do projeto **{DEVELOPER_INFO['project']}**.
    
    ## 🚀 Como começar:
    1. Faça upload de um arquivo CSV na barra lateral
    2. Faça perguntas sobre seus dados em linguagem natural
    3. Explore visualizações e insights gerados automaticamente
    
    ## 💡 Dica:
    Use as sugestões inteligentes que aparecem após cada análise!
    """,
    
    "no_data": """
    ### 📂 Nenhum arquivo carregado
    
    Para começar, faça o upload de um arquivo CSV usando o menu lateral.
    
    **Exemplo de perguntas que você poderá fazer:**
    - "Mostre a distribuição de vendas por região"
    - "Existe correlação entre preço e quantidade?"
    - "Crie um gráfico de tendência temporal"
    """,
    
    "footer": f"""
    Desenvolvido por {DEVELOPER_INFO['name']}
    [{DEVELOPER_INFO['repository']}]({DEVELOPER_INFO['repository']})
    """
}

# Temas e Cores Personalizadas
THEME = {
    "primary_color": "#4f46e5",
    "background_color": "#ffffff",
    "secondary_background": "#f8fafc",
    "text_color": "#1f2937",
    "font": "sans serif"
}

# Configurações de Visualização
VISUALIZATION_CONFIG = {
    "default_chart_height": 500,
    "default_chart_width": 800,
    "color_scheme": "plotly",
    "template": "plotly_white"
}

# Links e Referências
LINKS = {
    "github_profile": f"https://github.com/{DEVELOPER_INFO['github']}",
    "repository": DEVELOPER_INFO['repository'],
    "documentation": "README.md",
    "customization_guide": "PERSONALIZACAO.md"
}

def get_developer_info():
    """Retorna informações do desenvolvedor"""
    return DEVELOPER_INFO

def get_app_config():
    """Retorna configurações da aplicação"""
    return APP_CONFIG

def get_welcome_message():
    """Retorna mensagem de boas-vindas personalizada"""
    return MESSAGES["welcome"]

def get_theme():
    """Retorna configurações de tema"""
    return THEME
