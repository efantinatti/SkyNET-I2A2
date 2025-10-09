from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from agents.agent_setup import get_llm
import json

SUGGESTION_PROMPT_TEMPLATE = """
Você é um assistente que gera sugestões de perguntas inteligentes e relevantes para análise de dados.

**Contexto do Sistema:**
O sistema possui 4 tipos de agentes especializados:
- DataAnalystAgent: Para análises estatísticas, números, métricas, padrões, outliers, correlações
- VisualizationAgent: Para criação de gráficos, visualizações e plots
- ConsultantAgent: Para insights de negócio, recomendações e conclusões
- CodeGeneratorAgent: Para geração de código Python e notebooks

**Contexto da Análise:**
- Dataset: {dataset_preview}
- Histórico da conversa: {conversation_history}

**Sua Tarefa:**
Analise o histórico da conversa e o contexto do dataset para gerar 3 sugestões de perguntas que sejam:
1. **Relevantes**: Baseadas no que já foi discutido na conversa
2. **Progressivas**: Levando a uma análise mais profunda dos tópicos abordados
3. **Diversificadas**: Cobrindo diferentes aspectos dos dados (estatística, visualização, insights)
4. **Específicas**: Direcionadas a análises concretas
5. **Acionáveis**: Perguntas claras que geram respostas úteis

**Restrições:**
- Retorne APENAS um JSON válido com a estrutura especificada
- Não inclua explicações ou texto adicional
- Mantenha as sugestões concisas (máximo 15 palavras cada)
- NÃO mencione o nome de nenhum agente nas sugestões

**Formato de Saída:**
{{
  "suggestions": [
    "Pergunta específica sobre análise de dados",
    "Pergunta específica sobre visualização de dados",
    "Pergunta específica sobre insights e recomendações"
  ]
}}

**Exemplos de boas sugestões:**
- "Quais são as estatísticas descritivas das variáveis numéricas?"
- "Existem outliers significativos nos dados?"
- "Qual é a correlação entre as principais variáveis?"
- "Mostre a distribuição dos dados em um histograma"
- "Como as categorias se comparam em termos de desempenho?"
- "Quais são os principais insights que podemos extrair?"
- "Quais recomendações podem ser feitas com base nos dados?"
- "Gere um relatório completo das análises realizadas"
"""

def get_suggestion_generator(api_key: str):
    """Cria o agente gerador de sugestões."""
    llm = get_llm(api_key)
    prompt = ChatPromptTemplate.from_template(SUGGESTION_PROMPT_TEMPLATE)
    chain = prompt | llm | StrOutputParser()
    return chain

def generate_dynamic_suggestions(api_key: str, dataset_preview: str, conversation_history: str) -> list:
    """
    Gera sugestões dinâmicas baseadas no contexto da conversa.

    Args:
        api_key: Chave da API do Google
        dataset_preview: Preview do dataset
        conversation_history: Histórico completo da conversa

    Returns:
        Lista com 3 sugestões de perguntas
    """
    try:
        agent = get_suggestion_generator(api_key)

        response = agent.invoke({
            "dataset_preview": dataset_preview,
            "conversation_history": conversation_history
        })

        # Limpar a resposta para extrair JSON
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0].strip()
        elif "```" in response:
            response = response.replace("```", "").strip()

        # Tentar fazer parse do JSON
        suggestions_data = json.loads(response)

        suggestions = suggestions_data.get("suggestions", [])

        # Garantir que temos exatamente 3 sugestões
        if len(suggestions) < 3:
            # Completar com sugestões padrão se necessário
            default_suggestions = [
                "Quais são os tipos de dados e estatísticas básicas deste dataset?",
                "Mostre a distribuição das variáveis numéricas em histogramas.",
                "Existe correlação entre as variáveis? Mostre um heatmap."
            ]
            while len(suggestions) < 3:
                remaining = 3 - len(suggestions)
                suggestions.extend(default_suggestions[:remaining])

        return suggestions[:3]

    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON das sugestões: {e}")
        print(f"Resposta bruta recebida: {response}")
        return get_fallback_suggestions()[:3]

    except Exception as e:
        # Em caso de erro, retornar sugestões padrão
        print(f"Erro ao gerar sugestões dinâmicas: {e}")
        return get_fallback_suggestions()[:3]

def extract_conversation_context(conversation_history: str) -> dict:
    """
    Extrai informações contextuais do histórico da conversa.

    Args:
        conversation_history: Histórico completo da conversa

    Returns:
        Dicionário com informações contextuais
    """
    context = {
        "topics_discussed": [],
        "agents_used": [],
        "analysis_types": [],
        "has_visualization": False,
        "has_statistics": False,
        "has_insights": False,
        "has_code": False
    }

    if not conversation_history:
        return context

    # Palavras-chave para identificar tipos de análise
    stat_keywords = ["estatística", "correlação", "média", "mediana", "desvio", "outlier", "distribuição"]
    viz_keywords = ["gráfico", "plot", "visualização", "histograma", "scatter", "heatmap", "box plot"]
    insight_keywords = ["insight", "recomendação", "conclusão", "negócio", "estratégia", "otimizar"]
    code_keywords = ["código", "python", "notebook", "script", "função"]

    conversation_lower = conversation_history.lower()

    # Verificar tipos de análise realizados
    for keyword in stat_keywords:
        if keyword in conversation_lower:
            context["has_statistics"] = True
            context["analysis_types"].append("estatística")
            break

    for keyword in viz_keywords:
        if keyword in conversation_lower:
            context["has_visualization"] = True
            context["analysis_types"].append("visualização")
            break

    for keyword in insight_keywords:
        if keyword in conversation_lower:
            context["has_insights"] = True
            context["analysis_types"].append("insights")
            break

    for keyword in code_keywords:
        if keyword in conversation_lower:
            context["has_code"] = True
            context["analysis_types"].append("código")
            break

    # Identificar agentes usados (baseado em padrões de resposta)
    if "dataanalystagent" in conversation_lower or context["has_statistics"]:
        context["agents_used"].append("DataAnalystAgent")

    if "visualizationagent" in conversation_lower or context["has_visualization"]:
        context["agents_used"].append("VisualizationAgent")

    if "consultantagent" in conversation_lower or context["has_insights"]:
        context["agents_used"].append("ConsultantAgent")

    if "codegeneratoragent" in conversation_lower or context["has_code"]:
        context["agents_used"].append("CodeGeneratorAgent")

    return context

def get_fallback_suggestions() -> list:
    """Retorna sugestões padrão quando não há contexto suficiente."""
    return [
        "Quais são os tipos de dados e estatísticas básicas?",
        "Mostre a distribuição dos dados em gráficos.",
        "Existe correlação entre as principais variáveis?",
        "Há valores atípicos que merecem atenção?",
        "Quais são as principais descobertas neste conjunto de dados?",
        "Como as variáveis se relacionam entre si?",
        "Quais são os próximos passos recomendados para análise?"
    ]
