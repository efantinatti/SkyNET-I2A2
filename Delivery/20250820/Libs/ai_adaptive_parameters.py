"""
AI Adaptive Parameters System for SkyNET I2A2 HR Automation
Sistema de parâmetros adaptativos que aprende e se ajusta automaticamente
"""

import numpy as np
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
from .ai_memory_system import AIMemorySystem, Experience

@dataclass
class ParameterConfig:
    """Configuração de um parâmetro adaptativo"""
    name: str
    current_value: float
    min_value: float
    max_value: float
    learning_rate: float
    adaptation_speed: float
    stability_threshold: float
    description: str
    impact_factors: List[str]

@dataclass
class ParameterHistory:
    """Histórico de um parâmetro"""
    timestamp: str
    value: float
    performance_score: float
    context: Dict[str, Any]
    adjustment_reason: str

@dataclass
class AdaptationResult:
    """Resultado de uma adaptação de parâmetros"""
    parameter_name: str
    old_value: float
    new_value: float
    adjustment_amount: float
    confidence: float
    reasoning: str
    expected_impact: Dict[str, float]

class AIAdaptiveParameters:
    """
    Sistema de parâmetros adaptativos que aprende e se ajusta automaticamente
    
    Funcionalidades:
    - Ajuste automático de parâmetros baseado em performance
    - Aprendizado com feedback
    - Análise de correlações
    - Prevenção de overfitting
    - Estabilidade e convergência
    """
    
    def __init__(self, memory_system: AIMemorySystem, config_path: Optional[str] = None):
        self.memory = memory_system
        self.config_path = Path(config_path) if config_path else Path("ai_parameters.json")
        
        # Carregar configuração de parâmetros
        self.parameters = self._load_parameter_configs()
        
        # Histórico de adaptações
        self.adaptation_history = self._load_adaptation_history()
        
        # Configurações de aprendizado
        self.learning_config = {
            'min_experiences_for_adaptation': 5,
            'adaptation_frequency': 10,  # Adaptar a cada 10 experiências
            'stability_window': 20,  # Janela para verificar estabilidade
            'correlation_threshold': 0.3,
            'performance_threshold': 0.8
        }
        
        print(f"🔄 AI Adaptive Parameters initialized with {len(self.parameters)} parameters")
    
    def get_parameter(self, name: str) -> float:
        """Obtém valor atual de um parâmetro"""
        if name in self.parameters:
            return self.parameters[name].current_value
        else:
            print(f"⚠️ Parameter {name} not found, returning default value")
            return 0.0
    
    def get_all_parameters(self) -> Dict[str, float]:
        """Obtém todos os parâmetros atuais"""
        return {name: param.current_value for name, param in self.parameters.items()}
    
    def update_parameters_from_feedback(self, feedback: Dict[str, Any]) -> List[AdaptationResult]:
        """
        Atualiza parâmetros baseado em feedback de performance
        
        Args:
            feedback: Feedback sobre a performance
            
        Returns:
            Lista de resultados de adaptação
        """
        print("🔄 Updating parameters from feedback...")
        
        adaptation_results = []
        
        # Verificar se há experiências suficientes para adaptação
        if len(self.memory.experiences) < self.learning_config['min_experiences_for_adaptation']:
            print("📊 Insufficient experiences for parameter adaptation")
            return adaptation_results
        
        # Analisar feedback e ajustar parâmetros
        for param_name, param_config in self.parameters.items():
            if self._should_adapt_parameter(param_name, feedback):
                result = self._adapt_parameter(param_name, param_config, feedback)
                if result:
                    adaptation_results.append(result)
        
        # Salvar alterações
        if adaptation_results:
            self._save_parameter_configs()
            self._save_adaptation_history()
            print(f"✅ Adapted {len(adaptation_results)} parameters")
        
        return adaptation_results
    
    def analyze_parameter_correlations(self) -> Dict[str, Dict[str, float]]:
        """
        Analisa correlações entre parâmetros e performance
        
        Returns:
            Dicionário de correlações
        """
        print("📊 Analyzing parameter correlations...")
        
        if len(self.memory.experiences) < 10:
            return {}
        
        # Preparar dados para análise
        data = []
        for exp in self.memory.experiences:
            if exp.decision and exp.decision.get('parameters'):
                row = {
                    'performance': exp.performance_score,
                    'timestamp': exp.timestamp
                }
                row.update(exp.decision['parameters'])
                data.append(row)
        
        if not data:
            return {}
        
        # Converter para DataFrame
        df = pd.DataFrame(data)
        
        # Calcular correlações
        correlations = {}
        for param_name in self.parameters.keys():
            if param_name in df.columns:
                corr = df['performance'].corr(df[param_name])
                if not np.isnan(corr):
                    correlations[param_name] = {
                        'correlation': corr,
                        'strength': abs(corr),
                        'direction': 'positive' if corr > 0 else 'negative'
                    }
        
        return correlations
    
    def suggest_parameter_optimization(self) -> Dict[str, Dict[str, Any]]:
        """
        Sugere otimizações de parâmetros baseadas em análise
        
        Returns:
            Sugestões de otimização
        """
        print("💡 Generating parameter optimization suggestions...")
        
        suggestions = {}
        
        # Analisar correlações
        correlations = self.analyze_parameter_correlations()
        
        # Analisar histórico de performance
        performance_analysis = self._analyze_performance_history()
        
        # Gerar sugestões para cada parâmetro
        for param_name, param_config in self.parameters.items():
            suggestion = self._generate_parameter_suggestion(
                param_name, param_config, correlations, performance_analysis
            )
            if suggestion:
                suggestions[param_name] = suggestion
        
        return suggestions
    
    def get_parameter_stability_report(self) -> Dict[str, Any]:
        """
        Gera relatório de estabilidade dos parâmetros
        
        Returns:
            Relatório de estabilidade
        """
        print("📈 Generating parameter stability report...")
        
        report = {
            'total_parameters': len(self.parameters),
            'stable_parameters': 0,
            'unstable_parameters': 0,
            'parameter_details': {}
        }
        
        for param_name, param_config in self.parameters.items():
            stability = self._calculate_parameter_stability(param_name)
            
            report['parameter_details'][param_name] = {
                'current_value': param_config.current_value,
                'stability_score': stability,
                'is_stable': stability > param_config.stability_threshold,
                'recent_changes': self._count_recent_changes(param_name),
                'performance_impact': self._calculate_performance_impact(param_name)
            }
            
            if stability > param_config.stability_threshold:
                report['stable_parameters'] += 1
            else:
                report['unstable_parameters'] += 1
        
        return report
    
    def _load_parameter_configs(self) -> Dict[str, ParameterConfig]:
        """Carrega configurações de parâmetros"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    data = json.load(f)
                    return {
                        name: ParameterConfig(**config) 
                        for name, config in data.items()
                    }
            except Exception as e:
                print(f"⚠️ Error loading parameter configs: {e}")
        
        # Configuração padrão
        return self._create_default_parameters()
    
    def _create_default_parameters(self) -> Dict[str, ParameterConfig]:
        """Cria configuração padrão de parâmetros"""
        default_params = {
            'company_cost_percentage': ParameterConfig(
                name='company_cost_percentage',
                current_value=0.80,
                min_value=0.70,
                max_value=0.90,
                learning_rate=0.01,
                adaptation_speed=0.1,
                stability_threshold=0.95,
                description='Percentage of total cost borne by company',
                impact_factors=['cost_optimization', 'employee_satisfaction']
            ),
            'employee_cost_percentage': ParameterConfig(
                name='employee_cost_percentage',
                current_value=0.20,
                min_value=0.10,
                max_value=0.30,
                learning_rate=0.01,
                adaptation_speed=0.1,
                stability_threshold=0.95,
                description='Percentage of total cost borne by employee',
                impact_factors=['employee_satisfaction', 'cost_optimization']
            ),
            'vacation_benefit_factor': ParameterConfig(
                name='vacation_benefit_factor',
                current_value=3.5,
                min_value=2.0,
                max_value=5.0,
                learning_rate=0.05,
                adaptation_speed=0.2,
                stability_threshold=0.90,
                description='Multiplier for vacation benefit calculation',
                impact_factors=['employee_satisfaction', 'compliance']
            ),
            'termination_cutoff_day': ParameterConfig(
                name='termination_cutoff_day',
                current_value=15,
                min_value=10,
                max_value=20,
                learning_rate=0.1,
                adaptation_speed=0.3,
                stability_threshold=0.85,
                description='Day of month for termination cutoff',
                impact_factors=['compliance', 'business_rules']
            ),
            'safety_margin': ParameterConfig(
                name='safety_margin',
                current_value=0.1,
                min_value=0.05,
                max_value=0.2,
                learning_rate=0.02,
                adaptation_speed=0.15,
                stability_threshold=0.90,
                description='Safety margin for calculations',
                impact_factors=['risk_mitigation', 'compliance']
            ),
            'optimization_factor': ParameterConfig(
                name='optimization_factor',
                current_value=0.8,
                min_value=0.5,
                max_value=1.0,
                learning_rate=0.03,
                adaptation_speed=0.2,
                stability_threshold=0.85,
                description='Factor for optimization calculations',
                impact_factors=['efficiency', 'cost_optimization']
            )
        }
        
        return default_params
    
    def _should_adapt_parameter(self, param_name: str, feedback: Dict[str, Any]) -> bool:
        """Verifica se um parâmetro deve ser adaptado"""
        # Verificar frequência de adaptação
        recent_adaptations = self._count_recent_adaptations(param_name)
        if recent_adaptations >= 3:  # Máximo 3 adaptações por período
            return False
        
        # Verificar se há feedback relevante
        if not self._has_relevant_feedback(param_name, feedback):
            return False
        
        # Verificar estabilidade
        if self._is_parameter_stable(param_name):
            return False
        
        return True
    
    def _adapt_parameter(self, param_name: str, param_config: ParameterConfig, 
                        feedback: Dict[str, Any]) -> Optional[AdaptationResult]:
        """Adapta um parâmetro específico"""
        old_value = param_config.current_value
        
        # Calcular ajuste baseado no feedback
        adjustment = self._calculate_parameter_adjustment(param_name, param_config, feedback)
        
        if abs(adjustment) < 0.001:  # Ajuste muito pequeno
            return None
        
        # Aplicar ajuste
        new_value = old_value + adjustment
        
        # Garantir que está dentro dos limites
        new_value = max(param_config.min_value, min(param_config.max_value, new_value))
        
        # Atualizar parâmetro
        param_config.current_value = new_value
        
        # Calcular confiança
        confidence = self._calculate_adaptation_confidence(param_name, feedback)
        
        # Gerar raciocínio
        reasoning = self._generate_adaptation_reasoning(param_name, old_value, new_value, feedback)
        
        # Prever impacto
        expected_impact = self._predict_adaptation_impact(param_name, new_value)
        
        # Registrar no histórico
        self._record_adaptation(param_name, old_value, new_value, feedback, reasoning)
        
        return AdaptationResult(
            parameter_name=param_name,
            old_value=old_value,
            new_value=new_value,
            adjustment_amount=adjustment,
            confidence=confidence,
            reasoning=reasoning,
            expected_impact=expected_impact
        )
    
    def _calculate_parameter_adjustment(self, param_name: str, param_config: ParameterConfig, 
                                      feedback: Dict[str, Any]) -> float:
        """Calcula ajuste para um parâmetro"""
        # Obter feedback de performance
        performance_feedback = feedback.get('performance', {})
        
        # Calcular ajuste baseado na performance
        if 'accuracy' in performance_feedback:
            accuracy = performance_feedback['accuracy']
            if accuracy < 0.9:  # Performance baixa
                # Ajustar parâmetro para melhorar performance
                if param_name == 'vacation_benefit_factor':
                    return param_config.learning_rate * 0.1  # Aumentar fator
                elif param_name == 'safety_margin':
                    return param_config.learning_rate * 0.05  # Aumentar margem
            elif accuracy > 0.98:  # Performance muito alta
                # Pode otimizar mais
                if param_name == 'safety_margin':
                    return -param_config.learning_rate * 0.02  # Reduzir margem
        
        # Ajuste baseado em feedback específico
        if 'cost_optimization' in feedback:
            cost_feedback = feedback['cost_optimization']
            if cost_feedback > 0.5:  # Precisa otimizar custos
                if param_name == 'company_cost_percentage':
                    return -param_config.learning_rate * 0.05  # Reduzir custo da empresa
                elif param_name == 'optimization_factor':
                    return param_config.learning_rate * 0.1  # Aumentar otimização
        
        if 'employee_satisfaction' in feedback:
            satisfaction = feedback['employee_satisfaction']
            if satisfaction < 0.7:  # Baixa satisfação
                if param_name == 'employee_cost_percentage':
                    return -param_config.learning_rate * 0.05  # Reduzir custo do funcionário
                elif param_name == 'vacation_benefit_factor':
                    return param_config.learning_rate * 0.1  # Aumentar benefício
        
        return 0.0  # Sem ajuste
    
    def _calculate_adaptation_confidence(self, param_name: str, feedback: Dict[str, Any]) -> float:
        """Calcula confiança na adaptação"""
        confidence = 0.5  # Confiança base
        
        # Aumentar confiança baseado em feedback consistente
        if 'performance' in feedback:
            performance = feedback['performance']
            if isinstance(performance, dict) and 'accuracy' in performance:
                accuracy = performance['accuracy']
                confidence += (accuracy - 0.5) * 0.3
        
        # Aumentar confiança baseado em histórico
        recent_experiences = self._get_recent_experiences(param_name)
        if recent_experiences:
            avg_performance = np.mean([exp.performance_score for exp in recent_experiences])
            confidence += (avg_performance - 0.5) * 0.2
        
        return min(1.0, max(0.0, confidence))
    
    def _generate_adaptation_reasoning(self, param_name: str, old_value: float, 
                                     new_value: float, feedback: Dict[str, Any]) -> str:
        """Gera raciocínio para a adaptação"""
        reasoning_parts = []
        
        # Raciocínio baseado no feedback
        if 'performance' in feedback:
            performance = feedback['performance']
            if isinstance(performance, dict) and 'accuracy' in performance:
                accuracy = performance['accuracy']
                if accuracy < 0.9:
                    reasoning_parts.append(f"Low accuracy ({accuracy:.2%}) requires parameter adjustment")
                elif accuracy > 0.98:
                    reasoning_parts.append(f"High accuracy ({accuracy:.2%}) allows for optimization")
        
        # Raciocínio específico do parâmetro
        if param_name == 'vacation_benefit_factor':
            if new_value > old_value:
                reasoning_parts.append("Increasing vacation benefit factor to improve employee satisfaction")
            else:
                reasoning_parts.append("Decreasing vacation benefit factor for cost optimization")
        elif param_name == 'company_cost_percentage':
            if new_value > old_value:
                reasoning_parts.append("Increasing company cost percentage to improve employee satisfaction")
            else:
                reasoning_parts.append("Decreasing company cost percentage for cost optimization")
        
        # Raciocínio baseado em histórico
        recent_experiences = self._get_recent_experiences(param_name)
        if recent_experiences:
            avg_performance = np.mean([exp.performance_score for exp in recent_experiences])
            reasoning_parts.append(f"Based on recent performance ({avg_performance:.2%})")
        
        return ". ".join(reasoning_parts) + "."
    
    def _predict_adaptation_impact(self, param_name: str, new_value: float) -> Dict[str, float]:
        """Prevê impacto da adaptação"""
        impact = {}
        
        # Impacto baseado no tipo de parâmetro
        if param_name == 'company_cost_percentage':
            impact['cost_optimization'] = -new_value * 0.5  # Negativo = melhora
            impact['employee_satisfaction'] = new_value * 0.3  # Positivo = melhora
        elif param_name == 'employee_cost_percentage':
            impact['cost_optimization'] = new_value * 0.4
            impact['employee_satisfaction'] = -new_value * 0.5
        elif param_name == 'vacation_benefit_factor':
            impact['employee_satisfaction'] = new_value * 0.2
            impact['cost_optimization'] = -new_value * 0.1
        elif param_name == 'safety_margin':
            impact['risk_mitigation'] = new_value * 0.8
            impact['efficiency'] = -new_value * 0.3
        
        return impact
    
    def _record_adaptation(self, param_name: str, old_value: float, new_value: float, 
                          feedback: Dict[str, Any], reasoning: str) -> None:
        """Registra adaptação no histórico"""
        adaptation = ParameterHistory(
            timestamp=datetime.now().isoformat(),
            value=new_value,
            performance_score=feedback.get('performance', {}).get('accuracy', 0.5),
            context=feedback,
            adjustment_reason=reasoning
        )
        
        if param_name not in self.adaptation_history:
            self.adaptation_history[param_name] = []
        
        self.adaptation_history[param_name].append(adaptation)
        
        # Manter apenas histórico recente
        if len(self.adaptation_history[param_name]) > 100:
            self.adaptation_history[param_name] = self.adaptation_history[param_name][-100:]
    
    def _count_recent_adaptations(self, param_name: str, days: int = 7) -> int:
        """Conta adaptações recentes de um parâmetro"""
        if param_name not in self.adaptation_history:
            return 0
        
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_adaptations = [
            adaptation for adaptation in self.adaptation_history[param_name]
            if datetime.fromisoformat(adaptation.timestamp) >= cutoff_date
        ]
        
        return len(recent_adaptations)
    
    def _has_relevant_feedback(self, param_name: str, feedback: Dict[str, Any]) -> bool:
        """Verifica se há feedback relevante para o parâmetro"""
        param_config = self.parameters[param_name]
        
        # Verificar se o feedback afeta os fatores de impacto do parâmetro
        for impact_factor in param_config.impact_factors:
            if impact_factor in feedback:
                return True
        
        # Verificar feedback de performance geral
        if 'performance' in feedback:
            return True
        
        return False
    
    def _is_parameter_stable(self, param_name: str) -> bool:
        """Verifica se um parâmetro está estável"""
        if param_name not in self.adaptation_history:
            return True  # Estável se não há histórico
        
        recent_adaptations = self.adaptation_history[param_name][-10:]  # Últimas 10 adaptações
        
        if len(recent_adaptations) < 3:
            return True  # Estável se poucas adaptações
        
        # Verificar variância dos valores
        values = [adaptation.value for adaptation in recent_adaptations]
        variance = np.var(values)
        
        param_config = self.parameters[param_name]
        stability_threshold = param_config.stability_threshold
        
        return variance < (1 - stability_threshold) * 0.1
    
    def _get_recent_experiences(self, param_name: str, count: int = 10) -> List[Experience]:
        """Obtém experiências recentes relacionadas ao parâmetro"""
        recent_experiences = []
        
        for exp in self.memory.experiences[-50:]:  # Últimas 50 experiências
            if exp.decision and exp.decision.get('parameters', {}).get(param_name):
                recent_experiences.append(exp)
                if len(recent_experiences) >= count:
                    break
        
        return recent_experiences
    
    def _analyze_performance_history(self) -> Dict[str, Any]:
        """Analisa histórico de performance"""
        if not self.memory.experiences:
            return {}
        
        # Analisar últimas experiências
        recent_experiences = self.memory.experiences[-20:]
        performance_scores = [exp.performance_score for exp in recent_experiences]
        
        return {
            'average_performance': np.mean(performance_scores),
            'performance_trend': self._calculate_trend(performance_scores),
            'performance_volatility': np.std(performance_scores),
            'best_performance': max(performance_scores),
            'worst_performance': min(performance_scores)
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calcula tendência de uma série de valores"""
        if len(values) < 2:
            return "insufficient_data"
        
        x = np.arange(len(values))
        y = np.array(values)
        
        slope = np.polyfit(x, y, 1)[0]
        
        if slope > 0.01:
            return "improving"
        elif slope < -0.01:
            return "declining"
        else:
            return "stable"
    
    def _generate_parameter_suggestion(self, param_name: str, param_config: ParameterConfig, 
                                     correlations: Dict[str, Dict[str, float]], 
                                     performance_analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Gera sugestão para um parâmetro"""
        suggestion = {
            'parameter_name': param_name,
            'current_value': param_config.current_value,
            'suggested_value': param_config.current_value,
            'confidence': 0.5,
            'reasoning': [],
            'expected_impact': {}
        }
        
        # Sugestão baseada em correlações
        if param_name in correlations:
            corr_data = correlations[param_name]
            if corr_data['strength'] > 0.3:  # Correlação significativa
                if corr_data['direction'] == 'positive':
                    suggestion['suggested_value'] = min(
                        param_config.max_value,
                        param_config.current_value * 1.05
                    )
                    suggestion['reasoning'].append("Positive correlation with performance")
                else:
                    suggestion['suggested_value'] = max(
                        param_config.min_value,
                        param_config.current_value * 0.95
                    )
                    suggestion['reasoning'].append("Negative correlation with performance")
                
                suggestion['confidence'] = corr_data['strength']
        
        # Sugestão baseada em performance
        if performance_analysis.get('performance_trend') == 'declining':
            suggestion['suggested_value'] = min(
                param_config.max_value,
                param_config.current_value * 1.02
            )
            suggestion['reasoning'].append("Declining performance requires adjustment")
            suggestion['confidence'] = 0.7
        
        # Verificar se há sugestão válida
        if abs(suggestion['suggested_value'] - param_config.current_value) < 0.001:
            return None
        
        return suggestion
    
    def _calculate_parameter_stability(self, param_name: str) -> float:
        """Calcula estabilidade de um parâmetro"""
        if param_name not in self.adaptation_history:
            return 1.0  # Muito estável se não há histórico
        
        recent_adaptations = self.adaptation_history[param_name][-10:]
        
        if len(recent_adaptations) < 2:
            return 1.0
        
        # Calcular variância dos valores
        values = [adaptation.value for adaptation in recent_adaptations]
        variance = np.var(values)
        
        # Normalizar para score de estabilidade
        stability = max(0.0, 1.0 - variance * 10)
        
        return stability
    
    def _count_recent_changes(self, param_name: str, days: int = 30) -> int:
        """Conta mudanças recentes de um parâmetro"""
        return self._count_recent_adaptations(param_name, days)
    
    def _calculate_performance_impact(self, param_name: str) -> float:
        """Calcula impacto do parâmetro na performance"""
        if param_name not in self.adaptation_history:
            return 0.0
        
        recent_adaptations = self.adaptation_history[param_name][-10:]
        
        if len(recent_adaptations) < 2:
            return 0.0
        
        # Calcular correlação entre valor do parâmetro e performance
        values = [adaptation.value for adaptation in recent_adaptations]
        performances = [adaptation.performance_score for adaptation in recent_adaptations]
        
        correlation = np.corrcoef(values, performances)[0, 1]
        
        return correlation if not np.isnan(correlation) else 0.0
    
    def _save_parameter_configs(self) -> None:
        """Salva configurações de parâmetros"""
        data = {name: asdict(param) for name, param in self.parameters.items()}
        with open(self.config_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _save_adaptation_history(self) -> None:
        """Salva histórico de adaptações"""
        history_path = self.config_path.parent / "adaptation_history.json"
        data = {
            param_name: [asdict(adaptation) for adaptation in adaptations]
            for param_name, adaptations in self.adaptation_history.items()
        }
        with open(history_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_adaptation_history(self) -> Dict[str, List[ParameterHistory]]:
        """Carrega histórico de adaptações"""
        history_path = self.config_path.parent / "adaptation_history.json"
        
        if history_path.exists():
            try:
                with open(history_path, 'r') as f:
                    data = json.load(f)
                    return {
                        param_name: [ParameterHistory(**adaptation) for adaptation in adaptations]
                        for param_name, adaptations in data.items()
                    }
            except Exception as e:
                print(f"⚠️ Error loading adaptation history: {e}")
        
        return {}
