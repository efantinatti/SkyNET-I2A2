"""
AI Reasoning Engine for SkyNET I2A2 HR Automation
Motor de raciocínio multi-fatorial para tomada de decisões inteligentes
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
from .ai_memory_system import AIMemorySystem, Experience

@dataclass
class DecisionOption:
    """Representa uma opção de decisão"""
    name: str
    description: str
    parameters: Dict[str, Any]
    expected_performance: float
    confidence: float
    reasoning: str
    risks: List[str]
    benefits: List[str]

@dataclass
class AnalysisResult:
    """Resultado da análise de situação"""
    situation_type: str
    complexity_score: float
    risk_level: str
    key_factors: Dict[str, float]
    constraints: List[str]
    opportunities: List[str]
    recommendations: List[str]

@dataclass
class DecisionResult:
    """Resultado de uma decisão"""
    selected_option: DecisionOption
    confidence: float
    reasoning: str
    expected_outcome: Dict[str, Any]
    alternative_options: List[DecisionOption]
    risk_assessment: Dict[str, float]

class AIReasoningEngine:
    """
    Motor de raciocínio multi-fatorial para tomada de decisões inteligentes
    
    Funcionalidades:
    - Análise de situação complexa
    - Geração de opções de decisão
    - Avaliação multi-critério
    - Raciocínio baseado em evidências
    - Consideração de riscos e benefícios
    """
    
    def __init__(self, memory_system: AIMemorySystem):
        self.memory = memory_system
        
        # Pesos dos fatores de decisão
        self.factor_weights = {
            'business_rules': 0.25,
            'historical_performance': 0.20,
            'employee_satisfaction': 0.15,
            'cost_optimization': 0.15,
            'compliance': 0.10,
            'efficiency': 0.10,
            'risk_mitigation': 0.05
        }
        
        # Estratégias de decisão disponíveis
        self.decision_strategies = {
            'conservative': {
                'description': 'Aplicar regras padrão com margem de segurança',
                'risk_tolerance': 0.2,
                'innovation_level': 0.1,
                'parameters': {
                    'safety_margin': 0.1,
                    'rule_strictness': 1.0,
                    'adaptation_factor': 0.5
                }
            },
            'optimized': {
                'description': 'Otimizar baseado em dados históricos e padrões',
                'risk_tolerance': 0.5,
                'innovation_level': 0.6,
                'parameters': {
                    'optimization_factor': 0.8,
                    'learning_rate': 0.1,
                    'historical_weight': 0.7
                }
            },
            'adaptive': {
                'description': 'Adaptar dinamicamente baseado no contexto específico',
                'risk_tolerance': 0.7,
                'innovation_level': 0.8,
                'parameters': {
                    'adaptation_factor': 0.9,
                    'context_sensitivity': 0.7,
                    'dynamic_adjustment': 0.8
                }
            },
            'innovative': {
                'description': 'Explorar novas abordagens e otimizações criativas',
                'risk_tolerance': 0.8,
                'innovation_level': 0.9,
                'parameters': {
                    'creativity_factor': 0.9,
                    'exploration_rate': 0.7,
                    'novelty_weight': 0.8
                }
            }
        }
        
        print("🧠 AI Reasoning Engine initialized")
    
    def analyze_situation(self, context: Dict[str, Any]) -> AnalysisResult:
        """
        Analisa a situação atual e identifica fatores relevantes
        
        Args:
            context: Contexto da situação atual
            
        Returns:
            Resultado da análise
        """
        print("🔍 Analyzing current situation...")
        
        # Identificar tipo de situação
        situation_type = self._identify_situation_type(context)
        
        # Calcular complexidade
        complexity_score = self._calculate_complexity(context)
        
        # Avaliar nível de risco
        risk_level = self._assess_risk_level(context)
        
        # Identificar fatores-chave
        key_factors = self._identify_key_factors(context)
        
        # Identificar restrições
        constraints = self._identify_constraints(context)
        
        # Identificar oportunidades
        opportunities = self._identify_opportunities(context)
        
        # Gerar recomendações
        recommendations = self._generate_recommendations(context, key_factors)
        
        analysis = AnalysisResult(
            situation_type=situation_type,
            complexity_score=complexity_score,
            risk_level=risk_level,
            key_factors=key_factors,
            constraints=constraints,
            opportunities=opportunities,
            recommendations=recommendations
        )
        
        print(f"📊 Situation analysis complete: {situation_type} (complexity: {complexity_score:.2f})")
        return analysis
    
    def generate_decision_options(self, analysis: AnalysisResult, 
                                context: Dict[str, Any]) -> List[DecisionOption]:
        """
        Gera opções de decisão baseadas na análise
        
        Args:
            analysis: Resultado da análise de situação
            context: Contexto atual
            
        Returns:
            Lista de opções de decisão
        """
        print("💡 Generating decision options...")
        
        options = []
        
        # Gerar opções baseadas na situação
        for strategy_name, strategy_config in self.decision_strategies.items():
            # Verificar se a estratégia é apropriada para a situação
            if self._is_strategy_appropriate(strategy_name, analysis, context):
                option = self._create_decision_option(
                    strategy_name, strategy_config, analysis, context
                )
                options.append(option)
        
        # Ordenar por performance esperada
        options.sort(key=lambda x: x.expected_performance, reverse=True)
        
        print(f"✅ Generated {len(options)} decision options")
        return options
    
    def evaluate_and_select_option(self, options: List[DecisionOption], 
                                 analysis: AnalysisResult,
                                 context: Dict[str, Any]) -> DecisionResult:
        """
        Avalia opções e seleciona a melhor
        
        Args:
            options: Lista de opções de decisão
            analysis: Análise da situação
            context: Contexto atual
            
        Returns:
            Resultado da decisão
        """
        print("⚖️ Evaluating decision options...")
        
        if not options:
            raise ValueError("No decision options provided")
        
        # Avaliar cada opção
        evaluated_options = []
        for option in options:
            score = self._evaluate_option(option, analysis, context)
            option.expected_performance = score
            evaluated_options.append(option)
        
        # Ordenar por score
        evaluated_options.sort(key=lambda x: x.expected_performance, reverse=True)
        
        # Selecionar melhor opção
        selected_option = evaluated_options[0]
        
        # Calcular confiança
        confidence = self._calculate_confidence(selected_option, evaluated_options, analysis)
        
        # Gerar raciocínio
        reasoning = self._generate_reasoning(selected_option, analysis, context)
        
        # Prever resultado
        expected_outcome = self._predict_outcome(selected_option, context)
        
        # Avaliar riscos
        risk_assessment = self._assess_risks(selected_option, context)
        
        result = DecisionResult(
            selected_option=selected_option,
            confidence=confidence,
            reasoning=reasoning,
            expected_outcome=expected_outcome,
            alternative_options=evaluated_options[1:],
            risk_assessment=risk_assessment
        )
        
        print(f"🎯 Decision made: {selected_option.name} (confidence: {confidence:.2%})")
        return result
    
    def _identify_situation_type(self, context: Dict[str, Any]) -> str:
        """Identifica o tipo de situação"""
        employee_count = context.get('employee_count', 0)
        data_quality = context.get('data_quality_score', 1.0)
        time_constraint = context.get('time_constraint', 'normal')
        
        if employee_count > 1500:
            if data_quality < 0.8:
                return "large_scale_complex"
            else:
                return "large_scale_standard"
        elif employee_count > 500:
            return "medium_scale"
        else:
            return "small_scale"
    
    def _calculate_complexity(self, context: Dict[str, Any]) -> float:
        """Calcula score de complexidade da situação"""
        complexity_factors = {
            'employee_count': min(1.0, context.get('employee_count', 0) / 2000),
            'data_quality': 1.0 - context.get('data_quality_score', 1.0),
            'rule_conflicts': len(context.get('rule_conflicts', [])),
            'time_pressure': 1.0 if context.get('time_constraint') == 'urgent' else 0.0,
            'budget_constraints': 1.0 if context.get('budget_limit', 0) < 1000000 else 0.0
        }
        
        # Peso dos fatores
        weights = [0.3, 0.25, 0.2, 0.15, 0.1]
        
        complexity = sum(factor * weight for factor, weight in zip(complexity_factors.values(), weights))
        return min(1.0, complexity)
    
    def _assess_risk_level(self, context: Dict[str, Any]) -> str:
        """Avalia nível de risco"""
        risk_factors = 0
        
        if context.get('data_quality_score', 1.0) < 0.8:
            risk_factors += 1
        
        if context.get('employee_count', 0) > 1000:
            risk_factors += 1
        
        if context.get('budget_limit', 0) < 1000000:
            risk_factors += 1
        
        if context.get('time_constraint') == 'urgent':
            risk_factors += 1
        
        if risk_factors >= 3:
            return "high"
        elif risk_factors >= 2:
            return "medium"
        else:
            return "low"
    
    def _identify_key_factors(self, context: Dict[str, Any]) -> Dict[str, float]:
        """Identifica fatores-chave da situação"""
        factors = {}
        
        # Fator de escala
        employee_count = context.get('employee_count', 0)
        factors['scale'] = min(1.0, employee_count / 2000)
        
        # Fator de qualidade de dados
        factors['data_quality'] = context.get('data_quality_score', 1.0)
        
        # Fator de restrições orçamentárias
        budget_limit = context.get('budget_limit', 0)
        factors['budget_pressure'] = 1.0 - min(1.0, budget_limit / 2000000)
        
        # Fator de pressão temporal
        time_constraint = context.get('time_constraint', 'normal')
        factors['time_pressure'] = 1.0 if time_constraint == 'urgent' else 0.0
        
        # Fator de complexidade de regras
        factors['rule_complexity'] = len(context.get('business_rules', {})) / 10
        
        return factors
    
    def _identify_constraints(self, context: Dict[str, Any]) -> List[str]:
        """Identifica restrições da situação"""
        constraints = []
        
        if context.get('budget_limit', 0) < 1000000:
            constraints.append("budget_limited")
        
        if context.get('time_constraint') == 'urgent':
            constraints.append("time_critical")
        
        if context.get('data_quality_score', 1.0) < 0.8:
            constraints.append("data_quality_issues")
        
        if context.get('compliance_required', False):
            constraints.append("strict_compliance")
        
        return constraints
    
    def _identify_opportunities(self, context: Dict[str, Any]) -> List[str]:
        """Identifica oportunidades de melhoria"""
        opportunities = []
        
        if context.get('data_quality_score', 1.0) > 0.9:
            opportunities.append("high_quality_data")
        
        if context.get('employee_count', 0) > 1000:
            opportunities.append("economies_of_scale")
        
        if context.get('historical_data_available', False):
            opportunities.append("historical_learning")
        
        if context.get('flexible_parameters', False):
            opportunities.append("parameter_optimization")
        
        return opportunities
    
    def _generate_recommendations(self, context: Dict[str, Any], 
                                key_factors: Dict[str, float]) -> List[str]:
        """Gera recomendações baseadas na análise"""
        recommendations = []
        
        if key_factors.get('data_quality', 1.0) < 0.8:
            recommendations.append("Improve data quality before processing")
        
        if key_factors.get('scale', 0) > 0.7:
            recommendations.append("Consider batch processing for large scale")
        
        if key_factors.get('budget_pressure', 0) > 0.5:
            recommendations.append("Focus on cost optimization strategies")
        
        if key_factors.get('time_pressure', 0) > 0.5:
            recommendations.append("Prioritize efficiency over optimization")
        
        return recommendations
    
    def _is_strategy_appropriate(self, strategy_name: str, analysis: AnalysisResult, 
                               context: Dict[str, Any]) -> bool:
        """Verifica se uma estratégia é apropriada para a situação"""
        strategy_config = self.decision_strategies[strategy_name]
        
        # Verificar tolerância ao risco
        if analysis.risk_level == "high" and strategy_config['risk_tolerance'] > 0.6:
            return False
        
        # Verificar nível de inovação
        if analysis.complexity_score < 0.3 and strategy_config['innovation_level'] > 0.7:
            return False
        
        # Verificar restrições
        if "strict_compliance" in analysis.constraints and strategy_name == "innovative":
            return False
        
        return True
    
    def _create_decision_option(self, strategy_name: str, strategy_config: Dict,
                              analysis: AnalysisResult, context: Dict[str, Any]) -> DecisionOption:
        """Cria uma opção de decisão"""
        # Calcular performance esperada
        expected_performance = self._estimate_performance(strategy_name, analysis, context)
        
        # Calcular confiança
        confidence = self._estimate_confidence(strategy_name, analysis, context)
        
        # Gerar raciocínio
        reasoning = self._generate_option_reasoning(strategy_name, analysis, context)
        
        # Identificar riscos
        risks = self._identify_option_risks(strategy_name, analysis, context)
        
        # Identificar benefícios
        benefits = self._identify_option_benefits(strategy_name, analysis, context)
        
        return DecisionOption(
            name=strategy_name,
            description=strategy_config['description'],
            parameters=strategy_config['parameters'],
            expected_performance=expected_performance,
            confidence=confidence,
            reasoning=reasoning,
            risks=risks,
            benefits=benefits
        )
    
    def _estimate_performance(self, strategy_name: str, analysis: AnalysisResult, 
                            context: Dict[str, Any]) -> float:
        """Estima performance esperada de uma estratégia"""
        base_performance = 0.7  # Performance base
        
        # Ajustar baseado na estratégia
        strategy_config = self.decision_strategies[strategy_name]
        
        if strategy_name == "conservative":
            base_performance += 0.1  # Mais seguro
        elif strategy_name == "optimized":
            base_performance += 0.15  # Boa performance
        elif strategy_name == "adaptive":
            base_performance += 0.2  # Melhor performance
        elif strategy_name == "innovative":
            base_performance += 0.1  # Potencial alto, mas risco
        
        # Ajustar baseado na situação
        if analysis.risk_level == "low":
            base_performance += 0.1
        elif analysis.risk_level == "high":
            base_performance -= 0.1
        
        # Ajustar baseado na qualidade dos dados
        data_quality = analysis.key_factors.get('data_quality', 1.0)
        base_performance += (data_quality - 0.5) * 0.2
        
        return min(1.0, max(0.0, base_performance))
    
    def _estimate_confidence(self, strategy_name: str, analysis: AnalysisResult, 
                           context: Dict[str, Any]) -> float:
        """Estima confiança na estratégia"""
        confidence = 0.8  # Confiança base
        
        # Ajustar baseado na estratégia
        if strategy_name == "conservative":
            confidence += 0.1  # Mais confiável
        elif strategy_name == "innovative":
            confidence -= 0.2  # Menos confiável
        
        # Ajustar baseado na complexidade
        confidence -= analysis.complexity_score * 0.3
        
        # Ajustar baseado em experiências similares
        similar_experiences = self.memory.retrieve_similar_experiences(context, max_results=5)
        if similar_experiences:
            strategy_experiences = [exp for exp in similar_experiences 
                                  if exp.decision.get('strategy') == strategy_name]
            if strategy_experiences:
                avg_performance = np.mean([exp.performance_score for exp in strategy_experiences])
                confidence += (avg_performance - 0.5) * 0.4
        
        return min(1.0, max(0.0, confidence))
    
    def _generate_option_reasoning(self, strategy_name: str, analysis: AnalysisResult, 
                                 context: Dict[str, Any]) -> str:
        """Gera raciocínio para uma opção"""
        reasoning_parts = []
        
        # Raciocínio baseado na estratégia
        if strategy_name == "conservative":
            reasoning_parts.append("Conservative approach ensures compliance and reduces risk")
        elif strategy_name == "optimized":
            reasoning_parts.append("Optimized approach leverages historical data for better performance")
        elif strategy_name == "adaptive":
            reasoning_parts.append("Adaptive approach adjusts to specific context for optimal results")
        elif strategy_name == "innovative":
            reasoning_parts.append("Innovative approach explores new possibilities for breakthrough performance")
        
        # Raciocínio baseado na situação
        if analysis.risk_level == "high":
            reasoning_parts.append("High risk situation requires careful consideration")
        
        if analysis.complexity_score > 0.7:
            reasoning_parts.append("Complex situation benefits from sophisticated approach")
        
        return ". ".join(reasoning_parts) + "."
    
    def _identify_option_risks(self, strategy_name: str, analysis: AnalysisResult, 
                             context: Dict[str, Any]) -> List[str]:
        """Identifica riscos de uma opção"""
        risks = []
        
        if strategy_name == "innovative":
            risks.extend(["unproven_approach", "potential_failure", "learning_curve"])
        elif strategy_name == "adaptive":
            risks.extend(["complexity", "parameter_tuning"])
        elif strategy_name == "optimized":
            risks.extend(["overfitting", "historical_bias"])
        elif strategy_name == "conservative":
            risks.extend(["missed_opportunities", "suboptimal_performance"])
        
        if analysis.risk_level == "high":
            risks.append("high_risk_environment")
        
        return risks
    
    def _identify_option_benefits(self, strategy_name: str, analysis: AnalysisResult, 
                                context: Dict[str, Any]) -> List[str]:
        """Identifica benefícios de uma opção"""
        benefits = []
        
        if strategy_name == "conservative":
            benefits.extend(["reliable", "compliant", "low_risk"])
        elif strategy_name == "optimized":
            benefits.extend(["data_driven", "efficient", "proven"])
        elif strategy_name == "adaptive":
            benefits.extend(["context_aware", "flexible", "optimal"])
        elif strategy_name == "innovative":
            benefits.extend(["breakthrough_potential", "competitive_advantage", "future_ready"])
        
        if analysis.risk_level == "low":
            benefits.append("favorable_environment")
        
        return benefits
    
    def _evaluate_option(self, option: DecisionOption, analysis: AnalysisResult, 
                        context: Dict[str, Any]) -> float:
        """Avalia uma opção de decisão"""
        score = 0.0
        
        # Score baseado na performance esperada
        score += option.expected_performance * 0.4
        
        # Score baseado na confiança
        score += option.confidence * 0.3
        
        # Score baseado na adequação à situação
        situation_fit = self._calculate_situation_fit(option, analysis, context)
        score += situation_fit * 0.2
        
        # Score baseado em experiências similares
        historical_score = self._calculate_historical_score(option, context)
        score += historical_score * 0.1
        
        return min(1.0, max(0.0, score))
    
    def _calculate_situation_fit(self, option: DecisionOption, analysis: AnalysisResult, 
                               context: Dict[str, Any]) -> float:
        """Calcula adequação da opção à situação"""
        fit = 0.5  # Fit base
        
        # Ajustar baseado no nível de risco
        if analysis.risk_level == "high" and "low_risk" in option.benefits:
            fit += 0.3
        elif analysis.risk_level == "low" and "breakthrough_potential" in option.benefits:
            fit += 0.2
        
        # Ajustar baseado na complexidade
        if analysis.complexity_score > 0.7 and "sophisticated" in option.description:
            fit += 0.2
        
        return min(1.0, max(0.0, fit))
    
    def _calculate_historical_score(self, option: DecisionOption, context: Dict[str, Any]) -> float:
        """Calcula score baseado em experiências históricas"""
        similar_experiences = self.memory.retrieve_similar_experiences(context, max_results=10)
        
        if not similar_experiences:
            return 0.5  # Score neutro se não há histórico
        
        # Filtrar experiências com a mesma estratégia
        strategy_experiences = [exp for exp in similar_experiences 
                              if exp.decision.get('strategy') == option.name]
        
        if not strategy_experiences:
            return 0.5  # Score neutro se não há histórico da estratégia
        
        # Calcular score médio
        avg_performance = np.mean([exp.performance_score for exp in strategy_experiences])
        return avg_performance
    
    def _calculate_confidence(self, selected_option: DecisionOption, 
                            all_options: List[DecisionOption], 
                            analysis: AnalysisResult) -> float:
        """Calcula confiança na decisão"""
        # Confiança baseada na diferença entre opções
        if len(all_options) > 1:
            score_diff = selected_option.expected_performance - all_options[1].expected_performance
            confidence = 0.5 + score_diff * 0.5
        else:
            confidence = selected_option.confidence
        
        # Ajustar baseado na complexidade
        confidence -= analysis.complexity_score * 0.2
        
        # Ajustar baseado no nível de risco
        if analysis.risk_level == "high":
            confidence -= 0.1
        
        return min(1.0, max(0.0, confidence))
    
    def _generate_reasoning(self, selected_option: DecisionOption, 
                          analysis: AnalysisResult, context: Dict[str, Any]) -> str:
        """Gera raciocínio para a decisão"""
        reasoning_parts = []
        
        # Raciocínio principal
        reasoning_parts.append(f"Selected {selected_option.name} strategy because: {selected_option.reasoning}")
        
        # Raciocínio baseado na situação
        if analysis.risk_level == "high":
            reasoning_parts.append("High risk environment requires careful approach")
        elif analysis.risk_level == "low":
            reasoning_parts.append("Low risk environment allows for optimization")
        
        # Raciocínio baseado na complexidade
        if analysis.complexity_score > 0.7:
            reasoning_parts.append("Complex situation benefits from sophisticated strategy")
        
        # Raciocínio baseado em histórico
        similar_experiences = self.memory.retrieve_similar_experiences(context, max_results=3)
        if similar_experiences:
            strategy_experiences = [exp for exp in similar_experiences 
                                  if exp.decision.get('strategy') == selected_option.name]
            if strategy_experiences:
                avg_performance = np.mean([exp.performance_score for exp in strategy_experiences])
                reasoning_parts.append(f"Historical performance with this strategy: {avg_performance:.2%}")
        
        return " ".join(reasoning_parts)
    
    def _predict_outcome(self, selected_option: DecisionOption, 
                        context: Dict[str, Any]) -> Dict[str, Any]:
        """Prevê resultado da decisão"""
        outcome = {
            'expected_accuracy': selected_option.expected_performance,
            'confidence': selected_option.confidence,
            'estimated_processing_time': self._estimate_processing_time(selected_option, context),
            'estimated_cost': self._estimate_cost(selected_option, context),
            'risk_level': self._assess_outcome_risk(selected_option, context)
        }
        
        return outcome
    
    def _assess_risks(self, selected_option: DecisionOption, 
                     context: Dict[str, Any]) -> Dict[str, float]:
        """Avalia riscos da decisão"""
        risks = {}
        
        # Risco de performance
        risks['performance_risk'] = 1.0 - selected_option.expected_performance
        
        # Risco de tempo
        risks['time_risk'] = 0.2 if context.get('time_constraint') == 'urgent' else 0.1
        
        # Risco de custo
        budget_pressure = 1.0 - min(1.0, context.get('budget_limit', 0) / 2000000)
        risks['cost_risk'] = budget_pressure * 0.3
        
        # Risco de compliance
        risks['compliance_risk'] = 0.1 if context.get('compliance_required', False) else 0.05
        
        return risks
    
    def _estimate_processing_time(self, option: DecisionOption, context: Dict[str, Any]) -> int:
        """Estima tempo de processamento"""
        base_time = 60  # 1 minuto base
        
        # Ajustar baseado no número de funcionários
        employee_count = context.get('employee_count', 0)
        time_factor = 1 + (employee_count / 1000) * 0.5
        
        # Ajustar baseado na estratégia
        if option.name == "conservative":
            time_factor *= 0.8  # Mais rápido
        elif option.name == "adaptive":
            time_factor *= 1.2  # Mais lento
        elif option.name == "innovative":
            time_factor *= 1.5  # Muito mais lento
        
        return int(base_time * time_factor)
    
    def _estimate_cost(self, option: DecisionOption, context: Dict[str, Any]) -> float:
        """Estima custo da decisão"""
        base_cost = 1000  # Custo base
        
        # Ajustar baseado na estratégia
        if option.name == "conservative":
            cost_factor = 1.0
        elif option.name == "optimized":
            cost_factor = 0.9
        elif option.name == "adaptive":
            cost_factor = 1.1
        elif option.name == "innovative":
            cost_factor = 1.3
        
        return base_cost * cost_factor
    
    def _assess_outcome_risk(self, option: DecisionOption, context: Dict[str, Any]) -> str:
        """Avalia nível de risco do resultado"""
        # Contar riscos por nível
        risk_counts = {'high': 0, 'medium': 0, 'low': 0}
        
        for risk in option.risks:
            if 'high' in risk.lower():
                risk_counts['high'] += 1
            elif 'medium' in risk.lower():
                risk_counts['medium'] += 1
            else:
                risk_counts['low'] += 1
        
        # Determinar nível de risco baseado na contagem
        if risk_counts['high'] > 0:
            return "high"
        elif risk_counts['medium'] > 0:
            return "medium"
        else:
            return "low"
