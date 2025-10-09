# Arquivo: agents/code_generator.py

from agents.agent_setup import get_llm, get_dataset_preview
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

PROMPT_TEMPLATE = """
Você é o "CodeGeneratorAgent", um especialista em gerar código Python limpo e reproduzível para análise de dados.

**Informações do Dataset:**
{dataset_info}

**Análise a ser Convertida em Código:**
{analysis_to_convert}

**Sua Tarefa:**
Gere um script Python que reproduza a análise solicitada. O código deve ser:
- **Completo e Executável**: Inclua todos os imports necessários no topo (`pandas`, `plotly`, etc.).
- **Bem Documentado**: Adicione comentários explicativos.
- **Profissional**: Use boas práticas de programação.
- **IMPORTANTE**: O DataFrame já está carregado na variável `df`. NÃO inclua código para carregar arquivos CSV.
- **Focado**: Retorne APENAS o bloco de código Python, sem nenhum texto ou explicação adicional.

**Exemplo de Análise:** "Cálculo da média da coluna 'price' e plotagem de um histograma."
**Exemplo de Saída Esperada:**
```python
import pandas as pd
import plotly.express as px

# O DataFrame 'df' já está carregado e disponível
# Não é necessário carregar o arquivo CSV

# --- Análise Estatística ---
# Calcula a média da coluna 'price'
media_price = df['price'].mean()
print(f"A média de 'price' é: {{media_price}}")

# --- Visualização ---
# Cria um histograma para a distribuição de 'price'
fig = px.histogram(df, x='price', title='Distribuição de Preços')
fig.update_layout(bargap=0.1)
# fig.show()  # Não necessário no Streamlit
```

**Exemplo de KNN Gaussiano:**
```python
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.neighbors import KernelDensity

# O DataFrame 'df' já está carregado e disponível
# Não é necessário carregar o arquivo CSV

# Selecionar colunas numéricas para análise KNN
numeric_cols = df.select_dtypes(include=[np.number]).columns
if len(numeric_cols) >= 2:
    # Usar as duas primeiras colunas numéricas
    col1, col2 = numeric_cols[0], numeric_cols[1]

    # Criar dados para o gráfico de densidade
    X = df[[col1, col2]].values

    # Estimar densidade usando Kernel Density Estimation
    kde = KernelDensity(kernel='gaussian', bandwidth=0.5)
    kde.fit(X)

    # Criar grade de pontos para visualização
    x_min, x_max = X[:, 0].min() - 1, X[:, 0].max() + 1
    y_min, y_max = X[:, 1].min() - 1, X[:, 1].max() + 1
    xx, yy = np.meshgrid(np.linspace(x_min, x_max, 100),
                         np.linspace(y_min, y_max, 100))

    # Calcular densidade na grade
    grid_points = np.c_[xx.ravel(), yy.ravel()]
    Z = np.exp(kde.score_samples(grid_points))
    Z = Z.reshape(xx.shape)

    # Criar gráfico de contorno usando plotly.graph_objects
    fig = go.Figure(data=go.Contour(
        x=xx.ravel(),
        y=yy.ravel(),
        z=Z.ravel(),
        colorscale='Viridis',
        contours=dict(showlabels=True, labelfont=dict(size=12, color='white'))
    ))

    fig.update_layout(
        title=f'KNN Gaussiano - Densidade {{col1}} vs {{col2}}',
        xaxis_title=col1,
        yaxis_title=col2
    )

    print(f"Gráfico KNN Gaussiano criado para {{col1}} vs {{col2}}")
else:
    print("Erro: São necessárias pelo menos 2 colunas numéricas para KNN Gaussiano")
    fig = None
```
Gere agora o código para a análise fornecida.
"""

def get_code_generator_agent(api_key: str):
    llm = get_llm(api_key)
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    chain = prompt | llm | StrOutputParser()
    return chain

def run_code_generator(api_key: str, dataset_info: str, analysis_to_convert: str):
    agent = get_code_generator_agent(api_key)
    raw_code = agent.invoke({
    "dataset_info": dataset_info,
    "analysis_to_convert": analysis_to_convert
    })

    # Melhorar a extração do código para evitar duplicatas
    if "```python" in raw_code:
        # Dividir por blocos de códigos e pegar apenas o primeiro
        code_blocks = raw_code.split("```python")
        if len(code_blocks) > 1:
            # Pegar o primeiro bloco de código
            first_block = code_blocks[1].split("```")[0].strip()

            # Verificar se há mais blocos de códigos
            remaining_text = "```".join(code_blocks[1].split("```")[1:])
            if "```python" in remaining_text:
                # Se há mais blocos, comparar se são idênticos
                second_block = remaining_text.split("```python")[1].split("```")[0].strip()
                if first_block == second_block:
                    # Se são idênticos, usar apenas o primeiro
                    clean_code = first_block
                    print("✅ Código duplicado detectado na resposta do LLM - usando apenas o primeiro bloco!")
                else:
                    # Se são diferentes, usar apenas o primeiro
                    clean_code = first_block
                    print("⚠️ Blocos diferentes detectados na resposta do LLM - usando apenas o primeiro!")
            else:
                clean_code = first_block
                print("✅ Apenas um bloco de código encontrado na resposta do LLM!")
        else:
            clean_code = raw_code.strip()
            print("❌ Nenhum bloco de código encontrado na resposta do LLM!")
    else:
        clean_code = raw_code.strip()
        print("❌ Formato inesperado - sem blocos de códigos na resposta do LLM!")

    # Remover linhas vazias extras no final
    lines = clean_code.split('\n')
    while lines and lines[-1].strip() == '':
        lines.pop()
    clean_code = '\n'.join(lines)

    # Verificação adicional: remover duplicatas se ainda existirem
    lines = clean_code.split('\n')
    if len(lines) > 1:
        # Verificar se as linhas são duplicadas
        half = len(lines) // 2
        first_half = '\n'.join(lines[:half])
        second_half = '\n'.join(lines[half:])
        if first_half.strip() == second_half.strip():
            clean_code = first_half.strip()
            print("✅ Duplicata detectada após parsing - removida!")

    return clean_code
