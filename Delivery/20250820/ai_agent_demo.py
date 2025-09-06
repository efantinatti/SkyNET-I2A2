#!/usr/bin/env python3
"""
Demonstração do Agente de IA para SkyNET I2A2 HR Automation
Script para demonstrar as capacidades do verdadeiro agente de IA
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório Libs ao path
sys.path.append(str(Path(__file__).parent / "Libs"))

from Libs.ai_agent import AIAgent
from Libs.ai_memory_system import AIMemorySystem
from Libs.ai_reasoning_engine import AIReasoningEngine
from Libs.ai_adaptive_parameters import AIAdaptiveParameters
from Libs.ai_predictive_engine import AIPredictiveEngine

def main():
    """Demonstração principal do agente IA"""
    print("🤖 SkyNET I2A2 AI Agent Demonstration")
    print("=" * 50)
    
    # 1. Inicializar agente IA
    print("\n1️⃣ Initializing AI Agent...")
    agent = AIAgent()
    
    # 2. Demonstrar status do agente
    print("\n2️⃣ Agent Status:")
    status = agent.get_agent_status()
    print(f"   Memory Size: {status.memory_size}")
    print(f"   Total Experiences: {status.total_experiences}")
    print(f"   Current Parameters: {len(status.current_parameters)}")
    print(f"   Confidence Level: {status.confidence_level:.2%}")
    print(f"   Performance Trend: {status.performance_trend}")
    
    # 3. Simular contexto de processamento HR
    print("\n3️⃣ Simulating HR Processing Context...")
    context = {
        'employee_count': 1792,
        'data_quality_score': 0.95,
        'time_constraint': 'normal',
        'compliance_required': True,
        'business_rules': {
            'vacation_rules': True,
            'termination_rules': True,
            'admission_rules': True
        },
        'historical_data_available': False,
        'flexible_parameters': True
    }
    
    print(f"   Employee Count: {context['employee_count']}")
    print(f"   Data Quality: {context['data_quality_score']:.2%}")
    
    # 4. Processar solicitação com agente IA
    print("\n4️⃣ Processing Request with AI Agent...")
    response = agent.process_hr_request(context)
    
    # 5. Exibir resultados da decisão
    print("\n5️⃣ AI Agent Decision Results:")
    print(f"   Selected Strategy: {response.decision.decision.selected_option.name}")
    print(f"   Decision Confidence: {response.decision.confidence:.2%}")
    print(f"   Overall Confidence: {response.confidence:.2%}")
    print(f"   Processing Time: {response.processing_time:.2f}s")
    print(f"   Reasoning: {response.decision.reasoning}")
    
    # 6. Exibir previsões
    print("\n6️⃣ AI Predictions:")
    for prediction in response.predictions:
        print(f"   {prediction.metric_name}: {prediction.trend_direction}")
        print(f"     Current: {prediction.current_value:.2%}")
        print(f"     Predicted: {prediction.predicted_value:.2%}")
        print(f"     Confidence: {prediction.confidence:.2%}")
    
    # 7. Exibir otimizações sugeridas
    print("\n7️⃣ Optimization Suggestions:")
    for optimization in response.optimizations:
        print(f"   {optimization.suggestion_type}: {optimization.description}")
        print(f"     Expected Improvement: {optimization.expected_improvement:.2%}")
        print(f"     Confidence: {optimization.confidence:.2%}")
        print(f"     Risk Level: {optimization.risk_level}")
    
    # 8. Exibir insights
    print("\n8️⃣ AI Insights:")
    for insight in response.insights:
        print(f"   • {insight}")
    
    # 9. Exibir recomendações
    print("\n9️⃣ AI Recommendations:")
    for recommendation in response.recommendations:
        print(f"   • {recommendation}")
    
    # 10. Simular feedback e aprendizado
    print("\n🔟 Simulating Feedback and Learning...")
    feedback = {
        'performance': {
            'accuracy': 0.98,
            'efficiency': 0.92
        },
        'satisfaction': 0.85,
        'cost_optimization': 0.78
    }
    
    adaptations = agent.learn_from_feedback(response.decision.decision_id, feedback)
    
    if adaptations:
        print(f"   🔄 Adapted {len(adaptations)} parameters:")
        for adaptation in adaptations:
            print(f"      {adaptation.parameter_name}: {adaptation.old_value:.3f} → {adaptation.new_value:.3f}")
            print(f"      Reasoning: {adaptation.reasoning}")
    else:
        print("   No parameter adaptations needed")
    
    # 11. Exibir status atualizado
    print("\n1️⃣1️⃣ Updated Agent Status:")
    updated_status = agent.get_agent_status()
    print(f"   Memory Size: {updated_status.memory_size}")
    print(f"   Confidence Level: {updated_status.confidence_level:.2%}")
    print(f"   Performance Trend: {updated_status.performance_trend}")
    
    # 12. Exibir insights aprendidos
    print("\n1️⃣2️⃣ Learning Insights:")
    insights = agent.get_learning_insights()
    for insight in insights:
        print(f"   • {insight}")
    
    # 13. Demonstrar previsão de performance
    print("\n1️⃣3️⃣ Performance Forecast:")
    forecast = agent.get_performance_forecast("performance")
    print(f"   Current Performance: {forecast['current_performance']:.2%}")
    print(f"   Forecasted Performance: {forecast['forecasted_performance']:.2%}")
    print(f"   Trend: {forecast['trend']}")
    print(f"   Key Drivers: {', '.join(forecast['key_drivers'])}")
    
    # 14. Demonstrar sugestões de otimização
    print("\n1️⃣4️⃣ Parameter Optimization Suggestions:")
    suggestions = agent.suggest_parameter_optimization()
    for param_name, suggestion in suggestions.items():
        print(f"   {param_name}:")
        print(f"     Current: {suggestion['current_value']:.3f}")
        print(f"     Suggested: {suggestion['suggested_value']:.3f}")
        print(f"     Confidence: {suggestion['confidence']:.2%}")
        print(f"     Reasoning: {', '.join(suggestion['reasoning'])}")
    
    print("\n✅ AI Agent Demonstration Complete!")
    print("=" * 50)
    
    # 15. Salvar estado do agente
    print("\n1️⃣5️⃣ Saving Agent State...")
    agent.save_agent_state("ai_agent_state.json")
    print("   Agent state saved to ai_agent_state.json")

def demonstrate_individual_components():
    """Demonstra componentes individuais do agente IA"""
    print("\n🔧 Individual Components Demonstration")
    print("=" * 50)
    
    # 1. Sistema de Memória
    print("\n1️⃣ Memory System:")
    memory = AIMemorySystem("demo_memory")
    
    # Simular algumas experiências
    context1 = {'employee_count': 1000, 'data_quality': 0.9}
    decision1 = {'strategy': 'conservative', 'parameters': {'safety_margin': 0.1}}
    outcome1 = {'accuracy': 0.95, 'total_value': 1000000}
    
    experience_id = memory.store_experience(context1, decision1, outcome1)
    print(f"   Stored experience: {experience_id[:8]}...")
    
    # Buscar experiências similares
    similar = memory.retrieve_similar_experiences(context1)
    print(f"   Found {len(similar)} similar experiences")
    
    # 2. Motor de Raciocínio
    print("\n2️⃣ Reasoning Engine:")
    reasoning = AIReasoningEngine(memory)
    
    analysis = reasoning.analyze_situation(context1)
    print(f"   Situation Type: {analysis.situation_type}")
    print(f"   Complexity Score: {analysis.complexity_score:.2f}")
    print(f"   Risk Level: {analysis.risk_level}")
    
    # 3. Parâmetros Adaptativos
    print("\n3️⃣ Adaptive Parameters:")
    adaptive = AIAdaptiveParameters(memory)
    
    current_params = adaptive.get_all_parameters()
    print(f"   Current Parameters: {len(current_params)}")
    for param, value in current_params.items():
        print(f"     {param}: {value:.3f}")
    
    # 4. Motor de Previsão
    print("\n4️⃣ Predictive Engine:")
    predictive = AIPredictiveEngine(memory)
    
    trends = predictive.predict_trends(context1)
    print(f"   Generated {len(trends)} trend predictions")
    
    optimizations = predictive.suggest_optimizations(context1)
    print(f"   Generated {len(optimizations)} optimization suggestions")

if __name__ == "__main__":
    try:
        # Demonstração principal
        main()
        
        # Demonstração de componentes individuais
        demonstrate_individual_components()
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
