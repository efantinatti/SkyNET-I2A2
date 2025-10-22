"""
SkyNET-I2A2 - CoordinatorAgent
Agente orquestrador principal que coordena todos os outros agentes
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from uuid import UUID
from enum import Enum

from ..llm import LLMOrchestrator, generate_text
from ..memory import MemoryManager
from ...config import settings, AgentSettings


class TaskType(str, Enum):
    """Tipos de tarefas que o coordenador pode executar"""
    DOCUMENT_ANALYSIS = "document_analysis"
    DATA_ANALYSIS = "data_analysis"
    CHAT_RESPONSE = "chat_response"
    FISCAL_VALIDATION = "fiscal_validation"
    VISUALIZATION = "visualization"
    INSIGHT_GENERATION = "insight_generation"


class AgentRole(str, Enum):
    """Roles dos agentes disponíveis"""
    EXTRACTION = "extraction"
    ANALYST = "analyst"
    CLASSIFIER = "classifier"
    VISUALIZER = "visualizer"
    CONSULTANT = "consultant"


class CoordinatorAgent:
    """
    Agente Coordenador Principal
    
    Responsável por:
    - Analisar requisições do usuário
    - Rotear tarefas para agentes especializados
    - Manter contexto da conversa
    - Orquestrar respostas finais
    """
    
    def __init__(self):
        """Inicializa o CoordinatorAgent"""
        self.llm = LLMOrchestrator()
        self.memory = MemoryManager()
        
        # Configurações específicas
        self.agent_settings = AgentSettings()
        
        # Cache de agentes ativos
        self.active_agents = {}
        
        # Templates de prompt
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self) -> str:
        """Constrói o prompt de sistema para o coordenador"""
        return f"""
Você é o CoordinatorAgent do sistema SkyNET-I2A2, um assistente inteligente especializado em análise fiscal e de dados.

## SUAS RESPONSABILIDADES:
1. **Análise de Requisições**: Interpretar solicitações do usuário e determinar ações necessárias
2. **Roteamento de Tarefas**: Direcionar trabalho para agentes especializados apropriados
3. **Manutenção de Contexto**: Lembrar conversas e análises anteriores
4. **Orquestração**: Coordenar múltiplos agentes quando necessário
5. **Síntese de Respostas**: Consolidar resultados em respostas claras e úteis

## AGENTES DISPONÍVEIS:
- **ExtractionAgent**: OCR, parsing de NFe/NFCe/CTe, extração de dados
- **AnalystAgent**: EDA, estatísticas, correlações, detecção de outliers
- **ClassifierAgent**: Classificação automática de documentos e transações
- **VisualizationAgent**: Gráficos, dashboards, relatórios visuais
- **ConsultantAgent**: Insights fiscais, recomendações, consultoria

## TIPOS DE TAREFAS:
- {TaskType.DOCUMENT_ANALYSIS.value}: Análise de documentos fiscais
- {TaskType.DATA_ANALYSIS.value}: Análise exploratória de dados
- {TaskType.CHAT_RESPONSE.value}: Respostas conversacionais
- {TaskType.FISCAL_VALIDATION.value}: Validação de dados fiscais
- {TaskType.VISUALIZATION.value}: Criação de visualizações
- {TaskType.INSIGHT_GENERATION.value}: Geração de insights

## DIRETRIZES:
- Seja preciso e direto nas análises
- Mantenha contexto de conversas anteriores
- Sempre explique o que está fazendo e por quê
- Use terminologia técnica apropriada
- Priorize qualidade sobre velocidade
- Integre resultados de múltiplos agentes quando necessário

Data/Hora atual: {datetime.now().strftime("%d/%m/%Y %H:%M")}
"""
    
    async def process_request(self, request: Dict[str, Any], user_id: UUID) -> Dict[str, Any]:
        """
        Processa uma requisição do usuário
        
        Args:
            request: Dados da requisição
            user_id: ID do usuário
            
        Returns:
            Resposta processada
        """
        try:
            # Extrai informações da requisição
            message = request.get("message", "")
            context = request.get("context", {})
            files = request.get("files", [])
            
            # Salva mensagem do usuário na memória
            await self.memory.save_message(
                user_id=user_id,
                role="user",
                content=message,
                metadata={"context": context, "files": files}
            )
            
            # Analisa a requisição e determina ação
            analysis = await self._analyze_request(message, context, files)
            
            # Roteamento baseado na análise
            response = await self._route_and_execute(analysis, user_id)
            
            # Salva resposta na memória
            await self.memory.save_message(
                user_id=user_id,
                role="assistant",
                content=response["content"],
                metadata=response.get("metadata", {})
            )
            
            return response
            
        except Exception as e:
            error_response = {
                "content": f"Erro interno no coordenador: {str(e)}",
                "type": "error",
                "timestamp": datetime.now().isoformat()
            }
            
            await self.memory.save_message(
                user_id=user_id,
                role="assistant",
                content=error_response["content"],
                metadata={"error": str(e)}
            )
            
            return error_response
    
    async def _analyze_request(self, message: str, context: Dict, files: List) -> Dict[str, Any]:
        """Analisa a requisição para determinar tipo de tarefa e agente necessário"""
        
        analysis_prompt = f"""
Analise a seguinte requisição do usuário e determine:

1. Tipo de tarefa (document_analysis, data_analysis, chat_response, etc.)
2. Agente(s) necessário(s)
3. Prioridade (1-5)
4. Dados necessários
5. Complexidade estimada

REQUISIÇÃO: {message}
CONTEXTO: {json.dumps(context, ensure_ascii=False)}
ARQUIVOS: {len(files)} arquivo(s) anexado(s)

Responda em JSON com as seguintes chaves:
- task_type: tipo da tarefa
- required_agents: lista de agentes necessários
- priority: prioridade numérica
- data_requirements: dados necessários
- complexity: baixa/média/alta
- execution_plan: plano de execução passo a passo
"""
        
        try:
            analysis_result = await self.llm.generate_text(
                prompt=analysis_prompt,
                system_prompt=self.system_prompt,
                max_tokens=1000
            )
            
            return json.loads(analysis_result)
            
        except json.JSONDecodeError:
            # Fallback para análise simples
            return {
                "task_type": TaskType.CHAT_RESPONSE.value,
                "required_agents": [AgentRole.CONSULTANT.value],
                "priority": 3,
                "data_requirements": [],
                "complexity": "baixa",
                "execution_plan": ["Resposta direta via coordenador"]
            }
    
    async def _route_and_execute(self, analysis: Dict[str, Any], user_id: UUID) -> Dict[str, Any]:
        """Roteia e executa a tarefa baseada na análise"""
        
        task_type = TaskType(analysis.get("task_type", TaskType.CHAT_RESPONSE.value))
        required_agents = analysis.get("required_agents", [])
        execution_plan = analysis.get("execution_plan", [])
        
        # Executa o plano
        results = []
        
        for step in execution_plan:
            if any(agent in step.lower() for agent in required_agents):
                # Executa através de agente especializado
                result = await self.route_task(task_type, {
                    "step": step,
                    "user_id": str(user_id),
                    "context": analysis
                })
                results.append(result)
            else:
                # Executa diretamente pelo coordenador
                result = await self._execute_coordination_step(step, analysis, user_id)
                results.append(result)
        
        # Consolida resultados
        final_response = await self._consolidate_results(results, analysis)
        
        return final_response
    
    async def route_task(self, task_type: TaskType, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Roteia tarefa para agente especializado apropriado"""
        
        # Por enquanto, simula roteamento (agentes ainda não implementados)
        agent_mapping = {
            TaskType.DOCUMENT_ANALYSIS: AgentRole.EXTRACTION,
            TaskType.DATA_ANALYSIS: AgentRole.ANALYST,
            TaskType.FISCAL_VALIDATION: AgentRole.CLASSIFIER,
            TaskType.VISUALIZATION: AgentRole.VISUALIZER,
            TaskType.INSIGHT_GENERATION: AgentRole.CONSULTANT,
            TaskType.CHAT_RESPONSE: AgentRole.CONSULTANT
        }
        
        target_agent = agent_mapping.get(task_type, AgentRole.CONSULTANT)
        
        # Simula execução do agente especializado
        return await self._simulate_agent_execution(target_agent, task_type, task_data)
    
    async def _simulate_agent_execution(self, agent: AgentRole, task_type: TaskType, task_data: Dict) -> Dict[str, Any]:
        """Simula execução de agente especializado (até implementação real)"""
        
        simulation_prompts = {
            AgentRole.EXTRACTION: "Simule extração de dados de documento fiscal",
            AgentRole.ANALYST: "Simule análise exploratória de dados",
            AgentRole.CLASSIFIER: "Simule classificação de documento/transação",
            AgentRole.VISUALIZER: "Simule criação de visualização",
            AgentRole.CONSULTANT: "Forneça consultoria especializada"
        }
        
        prompt = f"""
Como {agent.value}Agent do sistema SkyNET-I2A2, execute a seguinte tarefa:

Tipo: {task_type.value}
Dados: {json.dumps(task_data, ensure_ascii=False)}

{simulation_prompts.get(agent, "Execute a tarefa solicitada")}

Responda de forma profissional e detalhada.
"""
        
        try:
            result = await self.llm.generate_text(
                prompt=prompt,
                system_prompt=self.system_prompt,
                max_tokens=2000
            )
            
            return {
                "agent": agent.value,
                "task_type": task_type.value,
                "result": result,
                "timestamp": datetime.now().isoformat(),
                "status": "completed"
            }
            
        except Exception as e:
            return {
                "agent": agent.value,
                "task_type": task_type.value,
                "result": f"Erro na execução: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            }
    
    async def _execute_coordination_step(self, step: str, analysis: Dict, user_id: UUID) -> Dict[str, Any]:
        """Executa passo de coordenação diretamente"""
        
        coordination_prompt = f"""
Como CoordinatorAgent, execute o seguinte passo de coordenação:

PASSO: {step}
ANÁLISE: {json.dumps(analysis, ensure_ascii=False)}
USUÁRIO: {user_id}

Execute este passo e forneça resultado estruturado.
"""
        
        try:
            result = await self.llm.generate_text(
                prompt=coordination_prompt,
                system_prompt=self.system_prompt,
                max_tokens=1500
            )
            
            return {
                "step": step,
                "result": result,
                "timestamp": datetime.now().isoformat(),
                "status": "completed"
            }
            
        except Exception as e:
            return {
                "step": step,
                "result": f"Erro na coordenação: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            }
    
    async def _consolidate_results(self, results: List[Dict], analysis: Dict) -> Dict[str, Any]:
        """Consolida resultados de múltiplas execuções"""
        
        consolidation_prompt = f"""
Consolide os seguintes resultados em uma resposta final coerente e útil:

ANÁLISE INICIAL: {json.dumps(analysis, ensure_ascii=False)}

RESULTADOS:
{json.dumps(results, ensure_ascii=False, indent=2)}

Forneça uma resposta final que:
1. Sintetize todos os resultados
2. Seja clara e actionable
3. Mantenha contexto técnico apropriado
4. Destaque insights principais
"""
        
        try:
            consolidated = await self.llm.generate_text(
                prompt=consolidation_prompt,
                system_prompt=self.system_prompt,
                max_tokens=2500
            )
            
            return {
                "content": consolidated,
                "type": "consolidated_response",
                "analysis": analysis,
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "content": f"Erro na consolidação: {str(e)}",
                "type": "error",
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_conversation_history(self, user_id: UUID, limit: int = 10) -> List[Dict]:
        """Recupera histórico de conversa"""
        return await self.memory.get_conversation_history(user_id, limit)
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do coordenador"""
        try:
            # Testa LLM
            llm_status = await self.llm.health_check()
            
            # Testa memória
            memory_status = await self.memory.health_check()
            
            return {
                "status": "healthy",
                "llm": llm_status,
                "memory": memory_status,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Factory function para facilitar importação
def create_coordinator_agent() -> CoordinatorAgent:
    """Cria instância do CoordinatorAgent"""
    return CoordinatorAgent()