"""
AI Predictive Engine for SkyNET I2A2 HR Automation
Motor de previsão e planejamento para antecipar tendências e otimizações
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
from .ai_memory_system import AIMemorySystem, Experience

@dataclass
class TrendPrediction:
    """Predição de tendência"""
    metric_name: str
    current_value: float
    predicted_value: float
    confidence: float
    trend_direction: str
    time_horizon: int  # dias
    factors: List[str]
    reasoning: str

@dataclass
class OptimizationSuggestion:
    """Sugestão de otimização"""
    suggestion_type: str
    description: str
    expected_improvement: float
    confidence: float
    implementation_effort: str
    risk_level: str
    parameters_affected: List[str]
    reasoning: str

@dataclass
class ActionPlan:
    """Plano de ação"""
    goal: str
    actions: List[Dict[str, Any]]
    timeline: Dict[str, datetime]
    success_metrics: List[str]
    risk_mitigation: List[str]
    expected_outcome: Dict[str, Any]

@dataclass
class PerformanceForecast:
    """Previsão de performance"""
    metric: str
    current_performance: float
    forecasted_performance: float
    confidence_interval: Tuple[float, float]
    trend: str
    key_drivers: List[str]
    recommendations: List[str]

class AIPredictiveEngine:
    """
    Motor de previsão e planejamento para antecipar tendências e otimizações
    
    Funcionalidades:
    - Previsão de tendências de performance
    - Análise de padrões temporais
    - Sugestões de otimização proativa
    - Planejamento de ações estratégicas
    - Análise de cenários futuros
    """
    
    def __init__(self, memory_system: AIMemorySystem):
        self.memory = memory_system
        
        # Configurações de previsão
        self.prediction_config = {
            'min_data_points': 10,
            'forecast_horizon': 30,  # dias
            'confidence_threshold': 0.7,
            'trend_sensitivity': 0.1,
            'optimization_threshold': 0.05
        }
        
        # Modelos de previsão
        self.models = {}
        self.scalers = {}
        
        print("🔮 AI Predictive Engine initialized")
    
    def predict_trends(self, context: Dict[str, Any]) -> List[TrendPrediction]:
        """
        Preve tendências futuras baseadas em dados históricos
        
        Args:
            context: Contexto atual para previsão
            
        Returns:
            Lista de predições de tendências
        """
        print("📈 Predicting future trends...")
        
        predictions = []
        
        # Prever tendência de performance
        performance_prediction = self._predict_performance_trend()
        if performance_prediction:
            predictions.append(performance_prediction)
        
        # Prever tendência de custos
        cost_prediction = self._predict_cost_trend()
        if cost_prediction:
            predictions.append(cost_prediction)
        
        # Prever tendência de satisfação
        satisfaction_prediction = self._predict_satisfaction_trend()
        if satisfaction_prediction:
            predictions.append(satisfaction_prediction)
        
        # Prever tendência de eficiência
        efficiency_prediction = self._predict_efficiency_trend()
        if efficiency_prediction:
            predictions.append(efficiency_prediction)
        
        print(f"✅ Generated {len(predictions)} trend predictions")
        return predictions
    
    def suggest_optimizations(self, current_state: Dict[str, Any]) -> List[OptimizationSuggestion]:
        """
        Sugere otimizações baseadas em análise preditiva
        
        Args:
            current_state: Estado atual do sistema
            
        Returns:
            Lista de sugestões de otimização
        """
        print("💡 Generating optimization suggestions...")
        
        suggestions = []
        
        # Analisar performance atual
        performance_analysis = self._analyze_current_performance(current_state)
        
        # Sugestões baseadas em performance
        if performance_analysis['accuracy'] < 0.95:
            suggestions.append(self._suggest_accuracy_optimization(performance_analysis))
        
        # Sugestões baseadas em eficiência
        if performance_analysis['efficiency'] < 0.8:
            suggestions.append(self._suggest_efficiency_optimization(performance_analysis))
        
        # Sugestões baseadas em custos
        if performance_analysis['cost_optimization'] < 0.7:
            suggestions.append(self._suggest_cost_optimization(performance_analysis))
        
        # Sugestões baseadas em satisfação
        if performance_analysis['satisfaction'] < 0.8:
            suggestions.append(self._suggest_satisfaction_optimization(performance_analysis))
        
        # Filtrar sugestões por confiança
        suggestions = [s for s in suggestions if s.confidence >= self.prediction_config['confidence_threshold']]
        
        print(f"✅ Generated {len(suggestions)} optimization suggestions")
        return suggestions
    
    def plan_actions(self, goals: Dict[str, Any], constraints: Dict[str, Any]) -> ActionPlan:
        """
        Planeja ações para atingir objetivos
        
        Args:
            goals: Objetivos a serem atingidos
            constraints: Restrições do sistema
            
        Returns:
            Plano de ação estruturado
        """
        print("📋 Planning strategic actions...")
        
        # Analisar objetivos
        primary_goal = self._identify_primary_goal(goals)
        
        # Gerar ações
        actions = self._generate_actions(primary_goal, constraints)
        
        # Definir timeline
        timeline = self._create_timeline(actions)
        
        # Definir métricas de sucesso
        success_metrics = self._define_success_metrics(primary_goal)
        
        # Identificar riscos
        risk_mitigation = self._identify_risks_and_mitigation(actions, constraints)
        
        # Prever resultado
        expected_outcome = self._predict_outcome(actions, primary_goal)
        
        action_plan = ActionPlan(
            goal=primary_goal,
            actions=actions,
            timeline=timeline,
            success_metrics=success_metrics,
            risk_mitigation=risk_mitigation,
            expected_outcome=expected_outcome
        )
        
        print(f"✅ Created action plan with {len(actions)} actions")
        return action_plan
    
    def forecast_performance(self, metric: str, horizon_days: int = 30) -> PerformanceForecast:
        """
        Preve performance de uma métrica específica
        
        Args:
            metric: Nome da métrica
            horizon_days: Horizonte de previsão em dias
            
        Returns:
            Previsão de performance
        """
        print(f"🔮 Forecasting {metric} performance...")
        
        # Preparar dados históricos
        historical_data = self._prepare_historical_data(metric)
        
        if len(historical_data) < self.prediction_config['min_data_points']:
            return self._create_default_forecast(metric)
        
        # Treinar modelo
        model = self._train_forecast_model(historical_data, metric)
        
        if not model:
            return self._create_default_forecast(metric)
        
        # Fazer previsão
        current_performance = historical_data['performance'].iloc[-1]
        forecasted_performance = self._make_forecast(model, horizon_days)
        
        # Calcular intervalo de confiança
        confidence_interval = self._calculate_confidence_interval(
            model, historical_data, horizon_days
        )
        
        # Identificar tendência
        trend = self._identify_trend(historical_data['performance'])
        
        # Identificar drivers-chave
        key_drivers = self._identify_key_drivers(historical_data, metric)
        
        # Gerar recomendações
        recommendations = self._generate_forecast_recommendations(
            current_performance, forecasted_performance, trend
        )
        
        forecast = PerformanceForecast(
            metric=metric,
            current_performance=current_performance,
            forecasted_performance=forecasted_performance,
            confidence_interval=confidence_interval,
            trend=trend,
            key_drivers=key_drivers,
            recommendations=recommendations
        )
        
        print(f"✅ Forecasted {metric}: {forecasted_performance:.2%} (trend: {trend})")
        return forecast
    
    def _predict_performance_trend(self) -> Optional[TrendPrediction]:
        """Preve tendência de performance"""
        if len(self.memory.experiences) < self.prediction_config['min_data_points']:
            return None
        
        # Extrair dados de performance
        performance_data = []
        for exp in self.memory.experiences:
            performance_data.append({
                'timestamp': exp.timestamp,
                'performance': exp.performance_score,
                'context': exp.context
            })
        
        # Converter para DataFrame
        df = pd.DataFrame(performance_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')
        
        # Calcular tendência
        if len(df) < 3:
            return None
        
        # Regressão linear simples
        x = np.arange(len(df)).reshape(-1, 1)
        y = df['performance'].values
        
        model = LinearRegression()
        model.fit(x, y)
        
        # Prever próximo valor
        next_x = len(df)
        predicted_performance = model.predict([[next_x]])[0]
        current_performance = y[-1]
        
        # Calcular confiança
        confidence = self._calculate_trend_confidence(model, x, y)
        
        # Determinar direção da tendência
        slope = model.coef_[0]
        if slope > self.prediction_config['trend_sensitivity']:
            trend_direction = "improving"
        elif slope < -self.prediction_config['trend_sensitivity']:
            trend_direction = "declining"
        else:
            trend_direction = "stable"
        
        # Identificar fatores
        factors = self._identify_performance_factors(df)
        
        # Gerar raciocínio
        reasoning = self._generate_trend_reasoning(
            current_performance, predicted_performance, trend_direction, factors
        )
        
        return TrendPrediction(
            metric_name="performance",
            current_value=current_performance,
            predicted_value=predicted_performance,
            confidence=confidence,
            trend_direction=trend_direction,
            time_horizon=self.prediction_config['forecast_horizon'],
            factors=factors,
            reasoning=reasoning
        )
    
    def _predict_cost_trend(self) -> Optional[TrendPrediction]:
        """Preve tendência de custos"""
        # Implementar previsão de custos
        return None
    
    def _predict_satisfaction_trend(self) -> Optional[TrendPrediction]:
        """Preve tendência de satisfação"""
        # Implementar previsão de satisfação
        return None
    
    def _predict_efficiency_trend(self) -> Optional[TrendPrediction]:
        """Preve tendência de eficiência"""
        # Implementar previsão de eficiência
        return None
    
    def _analyze_current_performance(self, current_state: Dict[str, Any]) -> Dict[str, float]:
        """Analisa performance atual"""
        analysis = {
            'accuracy': 0.95,  # Placeholder
            'efficiency': 0.85,  # Placeholder
            'cost_optimization': 0.75,  # Placeholder
            'satisfaction': 0.80  # Placeholder
        }
        
        # Analisar baseado em experiências recentes
        recent_experiences = self.memory.experiences[-10:]
        if recent_experiences:
            avg_performance = np.mean([exp.performance_score for exp in recent_experiences])
            analysis['accuracy'] = avg_performance
        
        return analysis
    
    def _suggest_accuracy_optimization(self, performance_analysis: Dict[str, float]) -> OptimizationSuggestion:
        """Sugere otimização de precisão"""
        return OptimizationSuggestion(
            suggestion_type="accuracy_optimization",
            description="Improve calculation accuracy through parameter tuning",
            expected_improvement=0.05,
            confidence=0.8,
            implementation_effort="medium",
            risk_level="low",
            parameters_affected=["vacation_benefit_factor", "safety_margin"],
            reasoning="Current accuracy below target, parameter adjustment can improve precision"
        )
    
    def _suggest_efficiency_optimization(self, performance_analysis: Dict[str, float]) -> OptimizationSuggestion:
        """Sugere otimização de eficiência"""
        return OptimizationSuggestion(
            suggestion_type="efficiency_optimization",
            description="Optimize processing efficiency through algorithm improvements",
            expected_improvement=0.1,
            confidence=0.7,
            implementation_effort="high",
            risk_level="medium",
            parameters_affected=["optimization_factor", "processing_strategy"],
            reasoning="Efficiency below optimal level, algorithm optimization can improve speed"
        )
    
    def _suggest_cost_optimization(self, performance_analysis: Dict[str, float]) -> OptimizationSuggestion:
        """Sugere otimização de custos"""
        return OptimizationSuggestion(
            suggestion_type="cost_optimization",
            description="Optimize cost distribution between company and employees",
            expected_improvement=0.08,
            confidence=0.75,
            implementation_effort="low",
            risk_level="low",
            parameters_affected=["company_cost_percentage", "employee_cost_percentage"],
            reasoning="Cost optimization opportunities identified, parameter adjustment can reduce expenses"
        )
    
    def _suggest_satisfaction_optimization(self, performance_analysis: Dict[str, float]) -> OptimizationSuggestion:
        """Sugere otimização de satisfação"""
        return OptimizationSuggestion(
            suggestion_type="satisfaction_optimization",
            description="Improve employee satisfaction through benefit adjustments",
            expected_improvement=0.06,
            confidence=0.8,
            implementation_effort="medium",
            risk_level="low",
            parameters_affected=["vacation_benefit_factor", "employee_cost_percentage"],
            reasoning="Employee satisfaction below target, benefit adjustments can improve satisfaction"
        )
    
    def _identify_primary_goal(self, goals: Dict[str, Any]) -> str:
        """Identifica objetivo primário"""
        if 'target_accuracy' in goals and goals['target_accuracy'] > 0.95:
            return "achieve_high_accuracy"
        elif 'cost_optimization' in goals and goals['cost_optimization']:
            return "optimize_costs"
        elif 'employee_satisfaction' in goals and goals['employee_satisfaction']:
            return "improve_satisfaction"
        else:
            return "maintain_performance"
    
    def _generate_actions(self, goal: str, constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Gera ações para atingir objetivo"""
        actions = []
        
        if goal == "achieve_high_accuracy":
            actions.extend([
                {
                    'action': 'tune_parameters',
                    'description': 'Adjust calculation parameters for higher accuracy',
                    'priority': 'high',
                    'estimated_impact': 0.05
                },
                {
                    'action': 'improve_data_quality',
                    'description': 'Enhance data validation and cleaning',
                    'priority': 'medium',
                    'estimated_impact': 0.03
                }
            ])
        elif goal == "optimize_costs":
            actions.extend([
                {
                    'action': 'adjust_cost_distribution',
                    'description': 'Optimize cost distribution between company and employees',
                    'priority': 'high',
                    'estimated_impact': 0.08
                },
                {
                    'action': 'streamline_processes',
                    'description': 'Streamline processing workflows',
                    'priority': 'medium',
                    'estimated_impact': 0.05
                }
            ])
        elif goal == "improve_satisfaction":
            actions.extend([
                {
                    'action': 'enhance_benefits',
                    'description': 'Improve employee benefits and calculations',
                    'priority': 'high',
                    'estimated_impact': 0.06
                },
                {
                    'action': 'improve_communication',
                    'description': 'Enhance communication about benefits',
                    'priority': 'medium',
                    'estimated_impact': 0.03
                }
            ])
        
        return actions
    
    def _create_timeline(self, actions: List[Dict[str, Any]]) -> Dict[str, datetime]:
        """Cria timeline para as ações"""
        timeline = {}
        current_date = datetime.now()
        
        for i, action in enumerate(actions):
            if action['priority'] == 'high':
                timeline[action['action']] = current_date + timedelta(days=7)
            elif action['priority'] == 'medium':
                timeline[action['action']] = current_date + timedelta(days=14)
            else:
                timeline[action['action']] = current_date + timedelta(days=30)
        
        return timeline
    
    def _define_success_metrics(self, goal: str) -> List[str]:
        """Define métricas de sucesso"""
        if goal == "achieve_high_accuracy":
            return ["accuracy > 0.95", "calculation_precision > 0.98"]
        elif goal == "optimize_costs":
            return ["cost_reduction > 5%", "efficiency_improvement > 10%"]
        elif goal == "improve_satisfaction":
            return ["satisfaction_score > 0.85", "complaint_reduction > 20%"]
        else:
            return ["performance_maintained", "stability_improved"]
    
    def _identify_risks_and_mitigation(self, actions: List[Dict[str, Any]], 
                                     constraints: Dict[str, Any]) -> List[str]:
        """Identifica riscos e estratégias de mitigação"""
        risks = []
        
        for action in actions:
            if action['priority'] == 'high':
                risks.append(f"High priority action {action['action']} may impact system stability")
            elif action['estimated_impact'] > 0.1:
                risks.append(f"High impact action {action['action']} requires careful monitoring")
        
        # Estratégias de mitigação
        mitigation = [
            "Implement gradual rollout for high-impact changes",
            "Monitor system performance during implementation",
            "Maintain rollback capability for all changes",
            "Conduct thorough testing before deployment"
        ]
        
        return mitigation
    
    def _predict_outcome(self, actions: List[Dict[str, Any]], goal: str) -> Dict[str, Any]:
        """Prevê resultado das ações"""
        total_impact = sum(action['estimated_impact'] for action in actions)
        
        outcome = {
            'expected_improvement': total_impact,
            'confidence': 0.8,
            'timeline': '2-4 weeks',
            'success_probability': min(0.95, 0.7 + total_impact)
        }
        
        return outcome
    
    def _prepare_historical_data(self, metric: str) -> pd.DataFrame:
        """Prepara dados históricos para previsão"""
        data = []
        
        for exp in self.memory.experiences:
            if metric == "performance":
                data.append({
                    'timestamp': exp.timestamp,
                    'performance': exp.performance_score,
                    'context': exp.context
                })
        
        df = pd.DataFrame(data)
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
        
        return df
    
    def _train_forecast_model(self, data: pd.DataFrame, metric: str) -> Optional[LinearRegression]:
        """Treina modelo de previsão"""
        if len(data) < 3:
            return None
        
        try:
            # Preparar features
            x = np.arange(len(data)).reshape(-1, 1)
            y = data['performance'].values
            
            # Treinar modelo
            model = LinearRegression()
            model.fit(x, y)
            
            return model
        except Exception as e:
            print(f"⚠️ Error training forecast model: {e}")
            return None
    
    def _make_forecast(self, model: LinearRegression, horizon_days: int) -> float:
        """Faz previsão usando modelo treinado"""
        # Assumir que cada ponto representa 1 dia
        next_point = model.n_features_in_ + horizon_days
        forecast = model.predict([[next_point]])[0]
        
        # Garantir que está dentro de limites razoáveis
        return max(0.0, min(1.0, forecast))
    
    def _calculate_confidence_interval(self, model: LinearRegression, data: pd.DataFrame, 
                                     horizon_days: int) -> Tuple[float, float]:
        """Calcula intervalo de confiança"""
        # Implementação simplificada
        forecast = self._make_forecast(model, horizon_days)
        margin = 0.05  # Margem de 5%
        
        return (max(0.0, forecast - margin), min(1.0, forecast + margin))
    
    def _identify_trend(self, performance_series: pd.Series) -> str:
        """Identifica tendência da série"""
        if len(performance_series) < 3:
            return "insufficient_data"
        
        # Calcular tendência usando regressão linear
        x = np.arange(len(performance_series))
        y = performance_series.values
        
        slope = np.polyfit(x, y, 1)[0]
        
        if slope > 0.01:
            return "improving"
        elif slope < -0.01:
            return "declining"
        else:
            return "stable"
    
    def _identify_key_drivers(self, data: pd.DataFrame, metric: str) -> List[str]:
        """Identifica drivers-chave da métrica"""
        drivers = []
        
        # Analisar correlações com contexto
        if 'context' in data.columns:
            # Implementar análise de correlação
            drivers.append("context_factors")
        
        # Drivers baseados na métrica
        if metric == "performance":
            drivers.extend(["calculation_accuracy", "parameter_tuning", "data_quality"])
        elif metric == "cost":
            drivers.extend(["cost_distribution", "efficiency", "optimization"])
        elif metric == "satisfaction":
            drivers.extend(["benefit_calculation", "employee_cost", "communication"])
        
        return drivers
    
    def _generate_forecast_recommendations(self, current: float, forecasted: float, 
                                         trend: str) -> List[str]:
        """Gera recomendações baseadas na previsão"""
        recommendations = []
        
        if trend == "declining":
            recommendations.append("Take immediate action to reverse declining trend")
        elif trend == "improving":
            recommendations.append("Continue current strategies to maintain improvement")
        else:
            recommendations.append("Monitor closely for trend changes")
        
        if forecasted < 0.9:
            recommendations.append("Focus on improving performance to reach target levels")
        
        if abs(forecasted - current) > 0.05:
            recommendations.append("Prepare for significant performance change")
        
        return recommendations
    
    def _calculate_trend_confidence(self, model: LinearRegression, x: np.ndarray, y: np.ndarray) -> float:
        """Calcula confiança na tendência"""
        try:
            # Calcular R²
            y_pred = model.predict(x)
            r2 = r2_score(y, y_pred)
            
            # Calcular confiança baseada em R²
            confidence = max(0.0, min(1.0, r2))
            
            return confidence
        except:
            return 0.5  # Confiança neutra se erro
    
    def _identify_performance_factors(self, data: pd.DataFrame) -> List[str]:
        """Identifica fatores que afetam performance"""
        factors = []
        
        # Analisar contexto das experiências
        if 'context' in data.columns:
            # Implementar análise de fatores
            factors.append("context_complexity")
        
        # Fatores baseados em performance
        if data['performance'].std() > 0.1:
            factors.append("high_variability")
        
        if data['performance'].mean() > 0.9:
            factors.append("high_performance")
        elif data['performance'].mean() < 0.8:
            factors.append("low_performance")
        
        return factors
    
    def _generate_trend_reasoning(self, current: float, predicted: float, 
                                trend: str, factors: List[str]) -> str:
        """Gera raciocínio para a tendência"""
        reasoning_parts = []
        
        # Raciocínio sobre a tendência
        if trend == "improving":
            reasoning_parts.append("Performance is showing an improving trend")
        elif trend == "declining":
            reasoning_parts.append("Performance is showing a declining trend")
        else:
            reasoning_parts.append("Performance is relatively stable")
        
        # Raciocínio sobre a previsão
        if predicted > current:
            reasoning_parts.append(f"Expected improvement from {current:.2%} to {predicted:.2%}")
        elif predicted < current:
            reasoning_parts.append(f"Expected decline from {current:.2%} to {predicted:.2%}")
        else:
            reasoning_parts.append("Performance expected to remain stable")
        
        # Raciocínio sobre fatores
        if factors:
            reasoning_parts.append(f"Key factors: {', '.join(factors)}")
        
        return ". ".join(reasoning_parts) + "."
    
    def _create_default_forecast(self, metric: str) -> PerformanceForecast:
        """Cria previsão padrão quando não há dados suficientes"""
        return PerformanceForecast(
            metric=metric,
            current_performance=0.5,
            forecasted_performance=0.5,
            confidence_interval=(0.4, 0.6),
            trend="insufficient_data",
            key_drivers=["data_insufficient"],
            recommendations=["Collect more data for accurate forecasting"]
        )
