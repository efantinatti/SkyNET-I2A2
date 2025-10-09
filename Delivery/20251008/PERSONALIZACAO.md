# Personalização - Ernani Fantinatti

## 🎯 Sobre Esta Versão

Esta é uma versão personalizada do **InsightAgent EDA** desenvolvida por **Ernani Fantinatti** como parte do projeto **SkyNET-I2A2**.

### 📝 Informações do Desenvolvedor

- **Nome:** Ernani Fantinatti
- **GitHub:** [@efantinatti](https://github.com/efantinatti)
- **Repositório:** [SkyNET-I2A2](https://github.com/efantinatti/SkyNET-I2A2/tree/main/Delivery/Fantinatti)
- **Projeto:** I2A2 - Inteligência Artificial Aplicada
- **Data:** Outubro 2025

## 🔄 Modificações Realizadas

### 1. **Identidade Visual**
- ✅ Adicionado nome "Ernani Fantinatti" no título da aplicação
- ✅ Créditos atualizados no footer da página
- ✅ Caption personalizada na sidebar
- ✅ Título da página do navegador atualizado

### 2. **Documentação**
- ✅ README.md atualizado com créditos ao Ernani
- ✅ Link para o repositório SkyNET-I2A2 adicionado
- ✅ Informações de contato incluídas

### 3. **Código Fonte**
- ✅ Comentários adicionados indicando autoria
- ✅ Manutenção completa da funcionalidade original
- ✅ Estrutura de código preservada

## 🚀 Como Executar Esta Versão

### Pré-requisitos
```bash
# 1. Python 3.8 ou superior instalado
python --version

# 2. Clone o repositório
git clone https://github.com/efantinatti/SkyNET-I2A2.git
cd SkyNET-I2A2/Delivery/Fantinatti
```

### Instalação
```bash
# 1. Crie um ambiente virtual
python -m venv .venv

# 2. Ative o ambiente virtual
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt
```

### Configuração
```bash
# 1. Copie o arquivo de exemplo
cp .env.example .env

# 2. Edite o .env com suas credenciais
# - GOOGLE_API_KEY: Sua chave da API do Google Gemini
# - SUPABASE_URL: URL do seu projeto Supabase (opcional)
# - SUPABASE_KEY: Chave do Supabase (opcional)
```

### Execução
```bash
# Execute a aplicação
streamlit run app.py

# A aplicação estará disponível em:
# http://localhost:8501
```

## 📊 Funcionalidades

Todas as funcionalidades originais foram mantidas:

### **5 Agentes Especializados**
1. **CoordinatorAgent** 🎯 - Roteia perguntas para o agente correto
2. **DataAnalystAgent** 📈 - Análises estatísticas detalhadas
3. **VisualizationAgent** 📊 - Gráficos interativos com Plotly
4. **ConsultantAgent** 💡 - Insights de negócio e recomendações
5. **CodeGeneratorAgent** ⚙️ - Geração de código Python

### **Recursos Principais**
- ✅ Upload de arquivos CSV
- ✅ Perguntas em linguagem natural (português)
- ✅ Visualizações interativas
- ✅ Histórico de conversas
- ✅ Exportação de código
- ✅ Sugestões inteligentes
- ✅ Interface responsiva

## 🛠️ Stack Tecnológica

| Tecnologia | Versão | Propósito |
|-----------|--------|-----------|
| Python | 3.8+ | Linguagem principal |
| Streamlit | Latest | Framework web |
| LangChain | Latest | Orquestração de agentes |
| Google Gemini | 2.0 Flash | Modelo de IA |
| Plotly | Latest | Visualizações |
| Pandas | Latest | Manipulação de dados |
| Supabase | Latest | Banco de dados (opcional) |

## 🎨 Customizações Adicionais Possíveis

Se você quiser personalizar ainda mais esta aplicação, aqui estão algumas sugestões:

### **1. Cores e Tema**
Edite o arquivo `assets/style.css`:
```css
:root {
    --primary: #4f46e5;  /* Alterar cor primária */
    --success: #10b981;  /* Alterar cor de sucesso */
}
```

### **2. Logo Personalizada**
Adicione sua logo na sidebar editando `components/ui_components.py`:
```python
st.sidebar.image("caminho/para/sua/logo.png", width=200)
```

### **3. Mensagens Customizadas**
Edite as mensagens de boas-vindas em `app.py`:
```python
st.title("🤖 Seu Título Personalizado")
```

## 📈 Estatísticas de Uso

Esta versão inclui as mesmas capacidades de análise:

- **Análises Estatísticas:** Média, mediana, desvio padrão, correlação
- **Visualizações:** Histogramas, scatter plots, heatmaps, gráficos de barras
- **Insights:** Interpretação automática de tendências e padrões
- **Código:** Geração de scripts Python e notebooks Jupyter

## 🤝 Suporte e Contato

### **Desenvolvedor**
- **Ernani Fantinatti**
- 📧 Email: [Entre em contato via GitHub](https://github.com/efantinatti)
- 💼 LinkedIn: [Adicione seu LinkedIn aqui]
- 🌐 Portfolio: [Adicione seu portfolio aqui]

## 📝 Notas de Versão

### **v1.0.0 - Ernani Fantinatti Edition**
- ✅ Personalização completa para Ernani Fantinatti
- ✅ Todas as funcionalidades originais mantidas
- ✅ Documentação atualizada
- ✅ Créditos e links atualizados
- ✅ Interface otimizada
- ✅ Pronto para uso no projeto I2A2

## 🔒 Licença

Este projeto mantém a licença MIT original. Veja o arquivo `LICENSE` para detalhes.

## 🙏 Agradecimentos

- **Google Gemini** - API de Inteligência Artificial
- **Streamlit** - Framework de desenvolvimento
- **Projeto I2A2** - Oportunidade de desenvolvimento
- **Comunidade Open Source** - Bibliotecas e ferramentas

---

Desenvolvido por Ernani Fantinatti

[GitHub](https://github.com/efantinatti) | [Documentação Completa](README.md)
