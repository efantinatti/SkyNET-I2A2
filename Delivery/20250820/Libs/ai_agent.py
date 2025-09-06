"""
AI Agent for SkyNET I2A2 HR Automation
Agente de IA principal que integra todos os componentes de inteligência artificial
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import json
from pathlib import Path

from .ai_memory_system import AIMemorySystem, Experience
from .ai_reasoning_engine import AIReasoningEngine, AnalysisResult, DecisionResult
from .ai_adaptive_parameters import AIAdaptiveParameters, AdaptationResult
from .ai_predictive_engine import AIPredictiveEngine, TrendPrediction, OptimizationSuggestion, ActionPlan

@dataclass
class AgentStatus:
    """Status atual do agente IA"""
    is_initialized: bool
    memory_size: int
    total_experiences: int
    current_parameters: Dict[str, float]
    learning_rate: float
    confidence_level: float
    last_adaptation: Optional[str]
    performance_trend: str
    active_insights: int

@dataclass
class AgentDecision:
    """Decisão tomada pelo agente IA"""
    decision_id: str
    timestamp: str
    context: Dict[str, Any]
    analysis: AnalysisResult
    decision: DecisionResult
    expected_outcome: Dict[str, Any]
    confidence: float
    reasoning: str
    parameters_used: Dict[str, float]

@dataclass
class AgentResponse:
    """Resposta completa do agente IA"""
    decision: AgentDecision
    predictions: List[TrendPrediction]
    optimizations: List[OptimizationSuggestion]
    action_plan: Optional[ActionPlan]
    insights: List[str]
    recommendations: List[str]
    confidence: float
    processing_time: float

class AIAgent:
    """
    Agente de IA principal para automação HR
    
    Funcionalidades:
    - Tomada de decisões inteligentes
    - Aprendizado contínuo
    - Previsão de tendências
    - Otimização automática
    - Planejamento estratégico
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializa o agente IA
        
        Args:
            config: Configuração do agente
        """
        self.config = config or self._get_default_config()
        
        # Inicializar componentes
        self.memory = AIMemorySystem(self.config.get('memory_path', 'ai_memory'))
        self.reasoning_engine = AIReasoningEngine(self.memory)
        self.adaptive_parameters = AIAdaptiveParameters(self.memory)
        self.predictive_engine = AIPredictiveEngine(self.memory)
        
        # Estado do agente
        self.is_initialized = True
        self.decision_count = 0
        self.performance_history = []
        
        print("🤖 AI Agent initialized successfully")
        print(f"   Memory: {len(self.memory.experiences)} experiences")
        print(f"   Parameters: {len(self.adaptive_parameters.parameters)} adaptive parameters")
    
    def process_hr_request(self, context: Dict[str, Any]) -> AgentResponse:
        """
        Processa uma solicitação HR com inteligência artificial
        
        Args:
            context: Contexto da solicitação HR
            
        Returns:
            Resposta completa do agente IA
        """
        start_time = datetime.now()
        print("🤖 AI Agent processing HR request...")
        
        # 1. Analisar situação
        analysis = self.reasoning_engine.analyze_situation(context)
        print(f"   📊 Situation analysis: {analysis.situation_type}")
        
        # 2. Gerar opções de decisão
        options = self.reasoning_engine.generate_decision_options(analysis, context)
        print(f"   💡 Generated {len(options)} decision options")
        
        # 3. Avaliar e selecionar melhor opção
        decision_result = self.reasoning_engine.evaluate_and_select_option(options, analysis, context)
        print(f"   🎯 Selected: {decision_result.selected_option.name}")
        
        # 4. Aplicar parâmetros adaptativos
        adaptive_context = self._apply_adaptive_parameters(context, decision_result)
        
        # 5. Executar processamento
        processing_results = self._execute_processing(adaptive_context, decision_result)
        
        # 6. Armazenar experiência
        experience_id = self.memory.store_experience(
            context, 
            asdict(decision_result.selected_option), 
            processing_results
        )
        
        # 7. Gerar previsões
        predictions = self.predictive_engine.predict_trends(context)
        
        # 8. Sugerir otimizações
        optimizations = self.predictive_engine.suggest_optimizations(processing_results)
        
        # 9. Criar plano de ação
        action_plan = self._create_action_plan(decision_result, context)
        
        # 10. Gerar insights
        insights = self._generate_insights(analysis, decision_result, processing_results)
        
        # 11. Gerar recomendações
        recommendations = self._generate_recommendations(analysis, decision_result, predictions)
        
        # 12. Calcular confiança geral
        overall_confidence = self._calculate_overall_confidence(decision_result, predictions, optimizations)
        
        # 13. Criar decisão do agente
        agent_decision = AgentDecision(
            decision_id=experience_id,
            timestamp=datetime.now().isoformat(),
            context=context,
            analysis=analysis,
            decision=decision_result,
            expected_outcome=processing_results,
            confidence=decision_result.confidence,
            reasoning=decision_result.reasoning,
            parameters_used=self.adaptive_parameters.get_all_parameters()
        )
        
        # 14. Criar resposta completa
        processing_time = (datetime.now() - start_time).total_seconds()
        
        response = AgentResponse(
            decision=agent_decision,
            predictions=predictions,
            optimizations=optimizations,
            action_plan=action_plan,
            insights=insights,
            recommendations=recommendations,
            confidence=overall_confidence,
            processing_time=processing_time
        )
        
        # 15. Atualizar contadores
        self.decision_count += 1
        self.performance_history.append(decision_result.confidence)
        
        print(f"✅ AI Agent processing complete (confidence: {overall_confidence:.2%}, time: {processing_time:.2f}s)")
        
        return response
    
    def learn_from_feedback(self, decision_id: str, feedback: Dict[str, Any]) -> List[AdaptationResult]:
        """
        Aprende com feedback sobre uma decisão
        
        Args:
            decision_id: ID da decisão
            feedback: Feedback sobre a decisão
            
        Returns:
            Lista de adaptações realizadas
        """
        print(f"📚 AI Agent learning from feedback for decision {decision_id[:8]}...")
        
        # Aprender com feedback na memória
        self.memory.learn_from_feedback(decision_id, feedback)
        
        # Adaptar parâmetros baseado no feedback
        adaptations = self.adaptive_parameters.update_parameters_from_feedback(feedback)
        
        if adaptations:
            print(f"   🔄 Adapted {len(adaptations)} parameters")
            for adaptation in adaptations:
                print(f"      {adaptation.parameter_name}: {adaptation.old_value:.3f} → {adaptation.new_value:.3f}")
        
        return adaptations
    
    def get_agent_status(self) -> AgentStatus:
        """
        Retorna status atual do agente
        
        Returns:
            Status do agente
        """
        # Calcular tendência de performance
        if len(self.performance_history) >= 3:
            recent_performance = self.performance_history[-3:]
            if np.mean(recent_performance) > np.mean(self.performance_history[:-3]):
                performance_trend = "improving"
            elif np.mean(recent_performance) < np.mean(self.performance_history[:-3]):
                performance_trend = "declining"
            else:
                performance_trend = "stable"
        else:
            performance_trend = "insufficient_data"
        
        # Obter última adaptação
        last_adaptation = None
        for param_name, adaptations in self.adaptive_parameters.adaptation_history.items():
            if adaptations:
                last_adaptation = adaptations[-1].timestamp
                break
        
        # Calcular confiança geral
        confidence_level = np.mean(self.performance_history) if self.performance_history else 0.5
        
        return AgentStatus(
            is_initialized=self.is_initialized,
            memory_size=len(self.memory.experiences),
            total_experiences=len(self.memory.experiences),
            current_parameters=self.adaptive_parameters.get_all_parameters(),
            learning_rate=0.1,  # Placeholder
            confidence_level=confidence_level,
            last_adaptation=last_adaptation,
            performance_trend=performance_trend,
            active_insights=len(self.memory.get_learning_insights())
        )
    
    def get_learning_insights(self) -> List[str]:
        """
        Retorna insights aprendidos pelo agente
        
        Returns:
            Lista de insights
        """
        insights = []
        
        # Insights da memória
        memory_insights = self.memory.get_learning_insights()
        for insight in memory_insights:
            insights.append(f"{insight.insight_type}: {insight.description}")
        
        # Insights de performance
        if self.performance_history:
            avg_performance = np.mean(self.performance_history)
            if avg_performance > 0.9:
                insights.append("High performance achieved - current strategies are effective")
            elif avg_performance < 0.8:
                insights.append("Performance below target - parameter adjustment recommended")
        
        # Insights de tendências
        if len(self.performance_history) >= 5:
            recent_trend = np.mean(self.performance_history[-3:]) - np.mean(self.performance_history[-5:-3])
            if recent_trend > 0.05:
                insights.append("Performance improving - continue current approach")
            elif recent_trend < -0.05:
                insights.append("Performance declining - review and adjust strategies")
        
        return insights
    
    def suggest_parameter_optimization(self) -> Dict[str, Any]:
        """
        Sugere otimizações de parâmetros
        
        Returns:
            Sugestões de otimização
        """
        return self.adaptive_parameters.suggest_parameter_optimization()
    
    def get_performance_forecast(self, metric: str = "performance") -> Dict[str, Any]:
        """
        Obtém previsão de performance
        
        Args:
            metric: Métrica para previsão
            
        Returns:
            Previsão de performance
        """
        forecast = self.predictive_engine.forecast_performance(metric)
        return asdict(forecast)
    
    def _apply_adaptive_parameters(self, context: Dict[str, Any], 
                                 decision_result: DecisionResult) -> Dict[str, Any]:
        """Aplica parâmetros adaptativos ao contexto"""
        adaptive_context = context.copy()
        
        # Obter parâmetros atuais
        current_parameters = self.adaptive_parameters.get_all_parameters()
        
        # Aplicar parâmetros ao contexto
        adaptive_context['ai_parameters'] = current_parameters
        
        # Ajustar contexto baseado na decisão
        if decision_result.selected_option.name == "optimized":
            adaptive_context['optimization_mode'] = True
            adaptive_context['optimization_factor'] = current_parameters.get('optimization_factor', 0.8)
        elif decision_result.selected_option.name == "adaptive":
            adaptive_context['adaptive_mode'] = True
            adaptive_context['adaptation_factor'] = current_parameters.get('adaptation_factor', 0.9)
        
        return adaptive_context
    
    def _execute_processing(self, context: Dict[str, Any], 
                          decision_result: DecisionResult) -> Dict[str, Any]:
        """Executa processamento baseado na decisão"""
        # Calcular valor total baseado nos dados reais
        base_total_value = context.get('calculated_value', 0)  # Usar valor calculado fornecido no contexto
        
        # Simular processamento baseado na decisão
        processing_results = {
            'accuracy': decision_result.expected_outcome.get('expected_accuracy', 0.95),
            'total_value': base_total_value,
            'employee_count': context.get('employee_count', 1792),
            'processing_time': decision_result.expected_outcome.get('estimated_processing_time', 60),
            'cost': decision_result.expected_outcome.get('estimated_cost', 1000),
            'risk_level': decision_result.expected_outcome.get('risk_level', 'low')
        }
        
        # Ajustar resultados baseado nos parâmetros adaptativos
        ai_parameters = context.get('ai_parameters', {})
        
        if 'vacation_benefit_factor' in ai_parameters:
            # Ajustar valor total baseado no fator de benefício
            factor = ai_parameters['vacation_benefit_factor']
            processing_results['total_value'] *= (factor / 3.5)  # Normalizar para fator padrão
        
        if 'company_cost_percentage' in ai_parameters:
            # Ajustar custo baseado na porcentagem da empresa
            percentage = ai_parameters['company_cost_percentage']
            processing_results['cost'] *= (percentage / 0.8)  # Normalizar para porcentagem padrão
        
        return processing_results
    
    def _create_action_plan(self, decision_result: DecisionResult, 
                          context: Dict[str, Any]) -> Optional[ActionPlan]:
        """Cria plano de ação baseado na decisão"""
        goals = {
            'target_accuracy': 0.99,
            'cost_optimization': True,
            'employee_satisfaction': True
        }
        
        constraints = {
            'max_processing_time': 300,
            'budget_limit': context.get('budget_limit'),  # Let budget limit be dynamic
            'compliance_required': True
        }
        
        return self.predictive_engine.plan_actions(goals, constraints)
    
    def _generate_insights(self, analysis: AnalysisResult, decision_result: DecisionResult, 
                         processing_results: Dict[str, Any]) -> List[str]:
        """Gera insights baseados na análise e decisão"""
        insights = []
        
        # Insight sobre a situação
        if analysis.complexity_score > 0.7:
            insights.append("Complex situation handled with sophisticated strategy")
        elif analysis.risk_level == "high":
            insights.append("High-risk situation managed with appropriate caution")
        
        # Insight sobre a decisão
        if decision_result.confidence > 0.9:
            insights.append("High-confidence decision based on strong evidence")
        elif decision_result.confidence < 0.7:
            insights.append("Decision made with moderate confidence - monitor results")
        
        # Insight sobre o resultado
        if processing_results.get('accuracy', 0) > 0.98:
            insights.append("Excellent accuracy achieved")
        elif processing_results.get('accuracy', 0) < 0.9:
            insights.append("Accuracy below target - optimization needed")
        
        return insights
    
    def _generate_recommendations(self, analysis: AnalysisResult, decision_result: DecisionResult, 
                                predictions: List[TrendPrediction]) -> List[str]:
        """Gera recomendações baseadas na análise e previsões"""
        recommendations = []
        
        # Recomendações baseadas na análise
        recommendations.extend(analysis.recommendations)
        
        # Recomendações baseadas na decisão
        if decision_result.confidence < 0.8:
            recommendations.append("Monitor decision outcome closely due to moderate confidence")
        
        # Recomendações baseadas em previsões
        for prediction in predictions:
            if prediction.trend_direction == "declining":
                recommendations.append(f"Take action to reverse declining trend in {prediction.metric_name}")
            elif prediction.trend_direction == "improving":
                recommendations.append(f"Continue strategies to maintain improvement in {prediction.metric_name}")
        
        return recommendations
    
    def _calculate_overall_confidence(self, decision_result: DecisionResult, 
                                    predictions: List[TrendPrediction], 
                                    optimizations: List[OptimizationSuggestion]) -> float:
        """Calcula confiança geral do agente"""
        # Confiança baseada na decisão
        decision_confidence = decision_result.confidence
        
        # Confiança baseada nas previsões
        if predictions:
            prediction_confidence = np.mean([p.confidence for p in predictions])
        else:
            prediction_confidence = 0.5
        
        # Confiança baseada nas otimizações
        if optimizations:
            optimization_confidence = np.mean([o.confidence for o in optimizations])
        else:
            optimization_confidence = 0.5
        
        # Peso das diferentes fontes de confiança
        weights = [0.5, 0.3, 0.2]  # Decisão, previsões, otimizações
        
        overall_confidence = (
            decision_confidence * weights[0] +
            prediction_confidence * weights[1] +
            optimization_confidence * weights[2]
        )
        
        return min(1.0, max(0.0, overall_confidence))
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Retorna configuração padrão do agente"""
        return {
            'memory_path': 'ai_memory',
            'learning_rate': 0.1,
            'confidence_threshold': 0.7,
            'adaptation_frequency': 10,
            'prediction_horizon': 30,
            'goals': {
                'target_accuracy': 0.99,
                'cost_optimization': True,
                'employee_satisfaction': True,
                'efficiency': True
            },
            'constraints': {
                'max_processing_time': 300,
                'budget_limit': None,  # Will be set dynamically
                'compliance_required': True
            }
        }
    
    def save_agent_state(self, file_path: str) -> None:
        """Salva estado do agente"""
        state = {
            'config': self.config,
            'decision_count': self.decision_count,
            'performance_history': self.performance_history,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(file_path, 'w') as f:
            json.dump(state, f, indent=2)
        
        print(f"💾 Agent state saved to {file_path}")
    
    def load_agent_state(self, file_path: str) -> None:
        """Carrega estado do agente"""
        try:
            with open(file_path, 'r') as f:
                state = json.load(f)
            
            self.config = state.get('config', self.config)
            self.decision_count = state.get('decision_count', 0)
            self.performance_history = state.get('performance_history', [])
            
            print(f"📂 Agent state loaded from {file_path}")
        except Exception as e:
            print(f"⚠️ Error loading agent state: {e}")
