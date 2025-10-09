# Arquivo: agents/visualization.py

import pandas as pd
from agents.agent_setup import get_llm, get_dataset_preview
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

PROMPT_TEMPLATE = """
Você é o "VisualizationAgent", um especialista em visualização de dados. Sua tarefa é gerar o código Python para criar um gráfico interativo usando a biblioteca Plotly.

**Contexto da Análise:**
{dataset_preview}

**Análise de Dados Recebida (se houver):**
{analysis_results}

**Pedido do Usuário:**
"{user_request}"

**Sua Tarefa:**
Gere um script Python que cria a visualização solicitada.
O seu código deve assumir que um DataFrame do pandas já existe e está disponível na variável `df`.

**REGRAS IMPORTANTES:**
1.  **NÃO inclua** a linha `df = pd.read_csv(...)` no seu código. O DataFrame `df` já está carregado na memória.
2.  O código deve incluir os imports necessários, como `import plotly.express as px`.
3.  O código do gráfico deve ser claro, com títulos e labels apropriados.
4.  O código deve criar uma figura e atribuí-la a uma variável chamada `fig`. Ex: `fig = px.histogram(...)`.
5.  **NÃO inclua** a linha `fig.show()`. A aplicação se encarregará de exibir o gráfico.

**IMPORTANTE:** Retorne APENAS o bloco de código Python. Não inclua nenhuma explicação ou texto adicional.

**Exemplo de Pedido:** "Crie um histograma da coluna 'idade'."
**Exemplo de Saída Esperada:**
```python
import plotly.express as px

# O DataFrame 'df' já existe.
# A coluna 'idade' foi identificada como numérica.

fig = px.histogram(df, x='idade', title='Distribuição da Idade', nbins=20)
fig.update_layout(bargap=0.1)
"""

def get_visualization_agent(api_key: str):
    llm = get_llm(api_key)
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    chain = prompt | llm | StrOutputParser()
    return chain

def run_visualization(api_key: str, df: pd.DataFrame, analysis_results: str, user_request: str):
    agent = get_visualization_agent(api_key)
    dataset_preview = get_dataset_preview(df)
    raw_code = agent.invoke({
        "dataset_preview": dataset_preview,
        "analysis_results": analysis_results,
        "user_request": user_request
    })

    if "```python" in raw_code:
        clean_code = raw_code.split("```python")[1].split("```")[0].strip()
    else:
        clean_code = raw_code.strip()
        
    return clean_code