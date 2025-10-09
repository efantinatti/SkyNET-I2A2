# 🚀 Guia Rápido de Início - InsightAgent EDA (Ernani Fantinatti)

## ⚡ Início Rápido (5 minutos)

### 1️⃣ Instalação Expressa

```bash
# Clone ou navegue até a pasta do projeto
cd /caminho/para/rhein-ai-agent-challenge

# Crie o ambiente virtual
python -m venv .venv

# Ative o ambiente
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# Instale as dependências
pip install -r requirements.txt
```

### 2️⃣ Configuração Rápida

Crie um arquivo `.env` na raiz do projeto:

```env
# Chave da API do Google Gemini (OBRIGATÓRIA)
GOOGLE_API_KEY=sua_chave_aqui

# Supabase (OPCIONAL - apenas se quiser salvar histórico)
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua_chave_supabase_aqui
```

**🔑 Como obter a chave do Google Gemini:**
1. Acesse: https://makersuite.google.com/app/apikey
2. Clique em "Create API key"
3. Copie a chave gerada

### 3️⃣ Execute a Aplicação

```bash
streamlit run app.py
```

A aplicação abrirá automaticamente em: http://localhost:8501

## 📝 Primeiro Uso

### Passo 1: Upload do CSV
1. Clique em "Browse files" na barra lateral
2. Selecione um arquivo CSV do seu computador
3. Aguarde o carregamento

### Passo 2: Faça sua primeira pergunta
Exemplos de perguntas:
```
"Mostre as estatísticas descritivas"
"Qual é a distribuição da coluna X?"
"Existe correlação entre as colunas A e B?"
"Crie um gráfico de barras das categorias"
```

### Passo 3: Explore os recursos
- ✅ Use as **sugestões inteligentes** que aparecem
- ✅ Visualize os **gráficos interativos**
- ✅ Copie o **código Python** gerado
- ✅ Navegue pelas **abas de estatísticas**

## 🎯 Casos de Uso Rápidos

### Análise de Vendas
```
1. Carregue: vendas.csv
2. Pergunte: "Qual produto vendeu mais?"
3. Pergunte: "Mostre um gráfico de vendas por mês"
4. Pergunte: "Gere insights sobre o desempenho"
```

### Análise de RH
```
1. Carregue: funcionarios.csv
2. Pergunte: "Qual é a média salarial por departamento?"
3. Pergunte: "Crie um histograma das idades"
4. Pergunte: "Existe correlação entre tempo de casa e salário?"
```

### Análise de Marketing
```
1. Carregue: campanhas.csv
2. Pergunte: "Qual canal tem melhor ROI?"
3. Pergunte: "Mostre um scatter plot de investimento vs receita"
4. Pergunte: "Recomende em quais campanhas investir"
```

## 🔧 Solução Rápida de Problemas

### ❌ Erro: "Chave da API não configurada"
**Solução:** Crie o arquivo `.env` com a chave do Google Gemini

### ❌ Erro ao carregar CSV
**Solução:** 
- Verifique se o arquivo é CSV válido
- Certifique-se de que tem pelo menos uma linha de dados
- Tente com um arquivo menor primeiro

### ❌ Gráfico não aparece
**Solução:**
- Aguarde alguns segundos
- Reformule a pergunta
- Verifique se há dados suficientes

### ❌ Aplicação lenta
**Solução:**
- Use datasets menores (< 100MB)
- Faça perguntas mais específicas
- Aguarde entre perguntas

## 📊 Datasets de Exemplo

Não tem dados? Use estes datasets públicos para testar:

### 1. Titanic (Análise de sobreviventes)
```bash
wget https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv
```
**Perguntas sugeridas:**
- "Qual foi a taxa de sobrevivência por classe?"
- "Mostre a distribuição de idade dos passageiros"
- "Existe correlação entre idade e sobrevivência?"

### 2. Iris (Dados científicos)
```bash
wget https://raw.githubusercontent.com/uiuc-cse/data-fa14/gh-pages/data/iris.csv
```
**Perguntas sugeridas:**
- "Mostre a distribuição das espécies"
- "Crie um scatter plot de comprimento vs largura"
- "Qual é a correlação entre as medidas?"

## 🎨 Personalizações Rápidas

### Alterar cores do tema
Edite: `assets/style.css`
```css
:root {
    --primary: #4f46e5;  /* Sua cor aqui */
}
```

### Adicionar logo
Edite: `components/ui_components.py`
```python
st.sidebar.image("sua_logo.png", width=200)
```

### Customizar mensagens
Edite: `config/fantinatti_config.py`
```python
MESSAGES = {
    "welcome": "Sua mensagem aqui"
}
```

## 📱 Atalhos e Dicas

### Atalhos de Teclado
- `Ctrl/Cmd + R` - Recarregar aplicação
- `Ctrl/Cmd + K` - Abrir paleta de comandos
- `Ctrl/Cmd + /` - Ver atalhos disponíveis

### Dicas de Uso
1. **Seja específico**: Perguntas claras geram melhores respostas
2. **Use sugestões**: As sugestões são baseadas no contexto
3. **Explore as abas**: Navegue entre Dataset e Estatísticas
4. **Copie o código**: Use o código gerado em seus projetos

## 🔗 Links Úteis

- 📚 [Documentação Completa](README.md)
- 🎨 [Guia de Personalização](PERSONALIZACAO.md)
- 💻 [Código Fonte](https://github.com/efantinatti/SkyNET-I2A2)
- 🔑 [Obter API Key](https://makersuite.google.com/app/apikey)
- 🗄️ [Supabase (opcional)](https://supabase.com)

## 📞 Suporte

**Encontrou um problema?**
1. Verifique a seção de troubleshooting acima
2. Consulte a documentação completa
3. Verifique os logs no terminal
4. Entre em contato via GitHub

---

Desenvolvido por Ernani Fantinatti

[GitHub](https://github.com/efantinatti) | [Repositório](https://github.com/efantinatti/SkyNET-I2A2)

*Última atualização: Outubro 2025*
