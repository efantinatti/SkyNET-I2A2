import pandas as pd
from agents.agent_setup import get_llm, get_dataset_preview
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

PROMPT_TEMPLATE = """
Você é o "DataAnalystAgent", um especialista em análise de dados com PhD em Estatística. Sua tarefa é analisar o dataset fornecido e responder à pergunta do usuário de forma precisa e técnica.

**Contexto da Análise:**
{dataset_preview}

**Histórico da Conversa e Análises Anteriores:**
{analysis_context}

**Pergunta Específica para Você:**
"{specific_question}"

**Sua Resposta Deve Conter:**
1.  **Análise Direta**: Responda à pergunta com análises estatísticas detalhadas.
2.  **Métricas Relevantes**: Forneça números específicos (médias, medianas, desvios padrão, correlações, p-values, etc.).
3.  **Observações Técnicas**: Aponte padrões estatisticamente significativos, outliers (usando IQR ou Z-score), ou qualquer outra descoberta relevante.
4.  **Concisão**: Seja objetivo e foque nos dados. Não forneça conclusões de negócio, apenas os fatos analíticos.

Formate sua resposta usando Markdown para clareza.
"""

def get_data_analyst_agent(api_key: str):
    llm = get_llm(api_key)
    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    chain = prompt | llm | StrOutputParser()
    return chain

def run_data_analyst(api_key: str, df: pd.DataFrame, analysis_context: str, specific_question: str):
    try:
        # Verifica se o DataFrame está vazio
        if df.empty:
            return "Erro: O DataFrame está vazio. Não é possível realizar a análise."
            
        # Verifica se a pergunta específica foi fornecida
        if not specific_question or not specific_question.strip():
            return "Erro: Nenhuma pergunta específica foi fornecida para análise."
            
        # Obtém o agente e os dados
        agent = get_data_analyst_agent(api_key)
        dataset_preview = get_dataset_preview(df)
        
        # Verifica se o preview do dataset foi gerado corretamente
        if not dataset_preview:
            return "Erro: Não foi possível gerar o preview do dataset."
            
        # Executa a análise
        response = agent.invoke({
            "dataset_preview": dataset_preview,
            "analysis_context": analysis_context or "Nenhum contexto de análise anterior fornecido.",
            "specific_question": specific_question
        })
        
        # Verifica se a resposta é válida
        if not response or response.strip() == "undefined":
            return "Desculpe, não foi possível gerar uma análise para esta pergunta. Por favor, tente reformular sua pergunta."
        
        # Remove any trailing 'undefined' and clean up the response
        cleaned_response = response.strip()
        if cleaned_response.endswith('undefined'):
            cleaned_response = cleaned_response[:-9].strip()
            
        # Ensure the response ends with proper punctuation
        if cleaned_response and not cleaned_response[-1] in {'.', '!', '?', ':'}:
            cleaned_response += '.'
            
        return cleaned_response
        
    except Exception as e:
        # Log do erro para depuração
        print(f"Erro no DataAnalystAgent: {str(e)}")
        return f"Ocorreu um erro ao processar sua solicitação: {str(e)}"