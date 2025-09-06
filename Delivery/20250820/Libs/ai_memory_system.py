"""
AI Memory System for SkyNET I2A2 HR Automation
Sistema de memória persistente para aprendizado contínuo do agente IA
"""

import json
import pickle
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import hashlib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

@dataclass
class Experience:
    """Representa uma experiência do agente IA"""
    timestamp: str
    context_hash: str
    context: Dict[str, Any]
    decision: Dict[str, Any]
    outcome: Dict[str, Any]
    performance_score: float
    feedback: Optional[Dict[str, Any]] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []

@dataclass
class LearningInsight:
    """Insight aprendido pelo agente"""
    insight_type: str
    description: str
    confidence: float
    evidence_count: int
    last_updated: str
    parameters_affected: List[str]

class AIMemorySystem:
    """
    Sistema de memória persistente para o agente IA
    
    Funcionalidades:
    - Armazenamento de experiências
    - Busca por similaridade
    - Aprendizado com feedback
    - Geração de insights
    - Análise de padrões
    """
    
    def __init__(self, memory_path: str = "ai_memory"):
        self.memory_path = Path(memory_path)
        self.memory_path.mkdir(exist_ok=True)
        
        # Carregar dados existentes
        self.experiences = self._load_experiences()
        self.insights = self._load_insights()
        self.performance_history = self._load_performance_history()
        
        # Inicializar vetorizador para busca por similaridade
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self._update_vectorizer()
        
        print(f"🧠 AI Memory System initialized with {len(self.experiences)} experiences")
    
    def store_experience(self, context: Dict, decision: Dict, outcome: Dict, 
                        feedback: Optional[Dict] = None) -> str:
        """
        Armazena uma nova experiência para aprendizado futuro
        
        Args:
            context: Contexto da situação
            decision: Decisão tomada
            outcome: Resultado obtido
            feedback: Feedback opcional sobre a decisão
            
        Returns:
            ID da experiência armazenada
        """
        # Gerar hash do contexto para identificação única
        context_hash = self._generate_context_hash(context)
        
        # Calcular score de performance
        performance_score = self._calculate_performance_score(outcome, feedback)
        
        # Criar experiência
        experience = Experience(
            timestamp=datetime.now().isoformat(),
            context_hash=context_hash,
            context=context,
            decision=decision,
            outcome=outcome,
            performance_score=performance_score,
            feedback=feedback,
            tags=self._generate_tags(context, decision, outcome)
        )
        
        # Armazenar experiência
        self.experiences.append(experience)
        self._save_experiences()
        
        # Atualizar vetorizador
        self._update_vectorizer()
        
        # Gerar insights se necessário
        self._generate_insights_from_experience(experience)
        
        print(f"💾 Stored experience: {context_hash[:8]}... (score: {performance_score:.2f})")
        return context_hash
    
    def retrieve_similar_experiences(self, context: Dict, 
                                   similarity_threshold: float = 0.7,
                                   max_results: int = 10) -> List[Experience]:
        """
        Recupera experiências similares baseadas no contexto
        
        Args:
            context: Contexto atual para busca
            similarity_threshold: Limiar de similaridade (0-1)
            max_results: Número máximo de resultados
            
        Returns:
            Lista de experiências similares
        """
        if not self.experiences:
            return []
        
        # Converter contexto em texto para análise
        context_text = self._context_to_text(context)
        
        # Calcular similaridade
        similarities = self._calculate_similarities(context_text)
        
        # Filtrar por threshold e ordenar por similaridade
        similar_experiences = []
        for i, similarity in enumerate(similarities):
            if similarity >= similarity_threshold:
                experience = self.experiences[i]
                experience.similarity_score = similarity
                similar_experiences.append(experience)
        
        # Ordenar por similaridade e performance
        similar_experiences.sort(key=lambda x: (x.similarity_score, x.performance_score), reverse=True)
        
        return similar_experiences[:max_results]
    
    def learn_from_feedback(self, experience_id: str, feedback: Dict) -> None:
        """
        Aprende com feedback sobre uma experiência específica
        
        Args:
            experience_id: ID da experiência
            feedback: Feedback sobre a decisão
        """
        # Encontrar experiência
        experience = self._find_experience_by_id(experience_id)
        if not experience:
            print(f"⚠️ Experience {experience_id} not found")
            return
        
        # Atualizar feedback
        experience.feedback = feedback
        
        # Recalcular performance score
        experience.performance_score = self._calculate_performance_score(
            experience.outcome, feedback
        )
        
        # Salvar alterações
        self._save_experiences()
        
        # Gerar insights baseados no feedback
        self._generate_insights_from_feedback(experience, feedback)
        
        print(f"📚 Learned from feedback for experience {experience_id[:8]}...")
    
    def get_learning_insights(self, insight_type: Optional[str] = None) -> List[LearningInsight]:
        """
        Retorna insights aprendidos pelo agente
        
        Args:
            insight_type: Tipo específico de insight (opcional)
            
        Returns:
            Lista de insights
        """
        if insight_type:
            return [insight for insight in self.insights if insight.insight_type == insight_type]
        return self.insights
    
    def analyze_performance_trends(self, days: int = 30) -> Dict[str, Any]:
        """
        Analisa tendências de performance do agente
        
        Args:
            days: Número de dias para análise
            
        Returns:
            Análise de tendências
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filtrar experiências recentes
        recent_experiences = [
            exp for exp in self.experiences
            if datetime.fromisoformat(exp.timestamp) >= cutoff_date
        ]
        
        if not recent_experiences:
            return {"error": "No recent experiences found"}
        
        # Calcular métricas
        scores = [exp.performance_score for exp in recent_experiences]
        
        analysis = {
            "period_days": days,
            "total_experiences": len(recent_experiences),
            "average_performance": np.mean(scores),
            "performance_std": np.std(scores),
            "performance_trend": self._calculate_trend(scores),
            "best_performance": max(scores),
            "worst_performance": min(scores),
            "improvement_rate": self._calculate_improvement_rate(recent_experiences)
        }
        
        return analysis
    
    def suggest_parameter_adjustments(self) -> Dict[str, float]:
        """
        Sugere ajustes de parâmetros baseados no aprendizado
        
        Returns:
            Sugestões de ajuste de parâmetros
        """
        if not self.experiences:
            return {}
        
        # Analisar padrões de sucesso
        successful_experiences = [
            exp for exp in self.experiences 
            if exp.performance_score > 0.8
        ]
        
        if not successful_experiences:
            return {}
        
        # Extrair parâmetros de decisões bem-sucedidas
        parameter_suggestions = {}
        
        for exp in successful_experiences:
            decision_params = exp.decision.get('parameters', {})
            for param, value in decision_params.items():
                if param not in parameter_suggestions:
                    parameter_suggestions[param] = []
                parameter_suggestions[param].append(value)
        
        # Calcular médias dos parâmetros bem-sucedidos
        suggestions = {}
        for param, values in parameter_suggestions.items():
            if len(values) >= 3:  # Mínimo de 3 experiências
                suggestions[param] = np.mean(values)
        
        return suggestions
    
    def _generate_context_hash(self, context: Dict) -> str:
        """Gera hash único para o contexto"""
        context_str = json.dumps(context, sort_keys=True)
        return hashlib.md5(context_str.encode()).hexdigest()
    
    def _calculate_performance_score(self, outcome: Dict, feedback: Optional[Dict]) -> float:
        """Calcula score de performance baseado no resultado e feedback"""
        score = 0.0
        
        # Score baseado no resultado
        if 'accuracy' in outcome:
            score += outcome['accuracy'] * 0.4
        
        if 'total_value' in outcome and 'target_value' in outcome:
            accuracy = min(1.0, outcome['total_value'] / outcome['target_value'])
            score += accuracy * 0.3
        
        if 'employee_count' in outcome:
            # Bonus por processar muitos funcionários
            score += min(0.1, outcome['employee_count'] / 10000)
        
        # Score baseado no feedback
        if feedback:
            if 'satisfaction' in feedback:
                score += feedback['satisfaction'] * 0.2
            
            if 'quality_rating' in feedback:
                score += feedback['quality_rating'] * 0.1
        
        return min(1.0, max(0.0, score))
    
    def _generate_tags(self, context: Dict, decision: Dict, outcome: Dict) -> List[str]:
        """Gera tags para categorização da experiência"""
        tags = []
        
        # Tags baseadas no contexto
        if 'employee_count' in context:
            if context['employee_count'] > 1000:
                tags.append('large_scale')
            elif context['employee_count'] > 500:
                tags.append('medium_scale')
            else:
                tags.append('small_scale')
        
        # Tags baseadas na decisão
        if 'strategy' in decision:
            tags.append(f"strategy_{decision['strategy']}")
        
        # Tags baseadas no resultado
        if 'accuracy' in outcome:
            if outcome['accuracy'] > 0.95:
                tags.append('high_accuracy')
            elif outcome['accuracy'] > 0.90:
                tags.append('medium_accuracy')
            else:
                tags.append('low_accuracy')
        
        return tags
    
    def _context_to_text(self, context: Dict) -> str:
        """Converte contexto em texto para análise de similaridade"""
        text_parts = []
        
        for key, value in context.items():
            if isinstance(value, (str, int, float)):
                text_parts.append(f"{key}: {value}")
            elif isinstance(value, dict):
                text_parts.append(f"{key}: {json.dumps(value)}")
            elif isinstance(value, list):
                text_parts.append(f"{key}: {len(value)} items")
        
        return " ".join(text_parts)
    
    def _update_vectorizer(self) -> None:
        """Atualiza o vetorizador com todas as experiências"""
        if not self.experiences:
            return
        
        # Converter experiências em textos
        texts = [self._context_to_text(exp.context) for exp in self.experiences]
        
        # Treinar vetorizador
        self.vectorizer.fit(texts)
    
    def _calculate_similarities(self, context_text: str) -> List[float]:
        """Calcula similaridades entre contexto atual e experiências"""
        if not self.experiences:
            return []
        
        # Converter contexto atual em vetor
        current_vector = self.vectorizer.transform([context_text])
        
        # Converter experiências em vetores
        experience_texts = [self._context_to_text(exp.context) for exp in self.experiences]
        experience_vectors = self.vectorizer.transform(experience_texts)
        
        # Calcular similaridades
        similarities = cosine_similarity(current_vector, experience_vectors)[0]
        
        return similarities.tolist()
    
    def _find_experience_by_id(self, experience_id: str) -> Optional[Experience]:
        """Encontra experiência por ID"""
        for exp in self.experiences:
            if exp.context_hash == experience_id:
                return exp
        return None
    
    def _generate_insights_from_experience(self, experience: Experience) -> None:
        """Gera insights baseados em uma nova experiência"""
        # Insight sobre performance
        if experience.performance_score > 0.9:
            insight = LearningInsight(
                insight_type="high_performance",
                description=f"High performance achieved with {experience.decision.get('strategy', 'unknown')} strategy",
                confidence=0.8,
                evidence_count=1,
                last_updated=datetime.now().isoformat(),
                parameters_affected=list(experience.decision.get('parameters', {}).keys())
            )
            self.insights.append(insight)
        
        # Insight sobre padrões
        if len(self.experiences) >= 10:
            self._analyze_patterns()
    
    def _generate_insights_from_feedback(self, experience: Experience, feedback: Dict) -> None:
        """Gera insights baseados em feedback"""
        if feedback.get('satisfaction', 0) < 0.5:
            insight = LearningInsight(
                insight_type="low_satisfaction",
                description=f"Low satisfaction reported for {experience.decision.get('strategy', 'unknown')} strategy",
                confidence=0.7,
                evidence_count=1,
                last_updated=datetime.now().isoformat(),
                parameters_affected=list(experience.decision.get('parameters', {}).keys())
            )
            self.insights.append(insight)
    
    def _analyze_patterns(self) -> None:
        """Analisa padrões nas experiências"""
        # Implementar análise de padrões
        pass
    
    def _calculate_trend(self, scores: List[float]) -> str:
        """Calcula tendência de performance"""
        if len(scores) < 2:
            return "insufficient_data"
        
        # Calcular tendência usando regressão linear simples
        x = np.arange(len(scores))
        y = np.array(scores)
        
        slope = np.polyfit(x, y, 1)[0]
        
        if slope > 0.01:
            return "improving"
        elif slope < -0.01:
            return "declining"
        else:
            return "stable"
    
    def _calculate_improvement_rate(self, experiences: List[Experience]) -> float:
        """Calcula taxa de melhoria"""
        if len(experiences) < 2:
            return 0.0
        
        # Ordenar por timestamp
        sorted_experiences = sorted(experiences, key=lambda x: x.timestamp)
        
        # Calcular melhoria
        first_half = sorted_experiences[:len(sorted_experiences)//2]
        second_half = sorted_experiences[len(sorted_experiences)//2:]
        
        first_avg = np.mean([exp.performance_score for exp in first_half])
        second_avg = np.mean([exp.performance_score for exp in second_half])
        
        return (second_avg - first_avg) / first_avg if first_avg > 0 else 0.0
    
    def _load_experiences(self) -> List[Experience]:
        """Carrega experiências do disco"""
        try:
            with open(self.memory_path / "experiences.json", 'r') as f:
                data = json.load(f)
                return [Experience(**exp) for exp in data]
        except FileNotFoundError:
            return []
    
    def _save_experiences(self) -> None:
        """Salva experiências no disco"""
        data = [asdict(exp) for exp in self.experiences]
        with open(self.memory_path / "experiences.json", 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_insights(self) -> List[LearningInsight]:
        """Carrega insights do disco"""
        try:
            with open(self.memory_path / "insights.json", 'r') as f:
                data = json.load(f)
                return [LearningInsight(**insight) for insight in data]
        except FileNotFoundError:
            return []
    
    def _save_insights(self) -> None:
        """Salva insights no disco"""
        data = [asdict(insight) for insight in self.insights]
        with open(self.memory_path / "insights.json", 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_performance_history(self) -> List[Dict]:
        """Carrega histórico de performance"""
        try:
            with open(self.memory_path / "performance_history.json", 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def _save_performance_history(self) -> None:
        """Salva histórico de performance"""
        with open(self.memory_path / "performance_history.json", 'w') as f:
            json.dump(self.performance_history, f, indent=2)
