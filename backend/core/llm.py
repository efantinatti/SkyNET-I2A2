"""
SkyNET-I2A2 - Integração LLM com Cache
Google Gemini + OpenAI com sistema de cache para otimização de tokens
"""

import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Union
from uuid import uuid4, UUID
import asyncio

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from ..config import settings
from .memory import SupabaseManager


class GeminiManager:
    """Gerenciador do Google Gemini com cache inteligente"""
    
    def __init__(self):
        # Configura API do Gemini
        genai.configure(api_key=settings.google_api_key)
        
        # Configurações de segurança (menos restritivas para uso fiscal)
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        }
        
        # Configuração do modelo
        self.generation_config = {
            "temperature": settings.temperature,
            "top_p": 1,
            "top_k": 1,
            "max_output_tokens": settings.max_tokens,
        }
        
        self.model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config=self.generation_config,
            safety_settings=self.safety_settings
        )
        
        self.supabase = SupabaseManager()
    
    def _generate_cache_key(self, prompt: str, user_id: UUID, context: str = "") -> str:
        """Gera chave única para cache baseada no prompt e contexto"""
        content = f"{prompt}:{str(user_id)}:{context}:{settings.gemini_model}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def _extract_content_for_cache(self, prompt: str) -> str:
        """Extrai conteúdo relevante do prompt para cache (remove dados únicos como timestamps)"""
        # Remove timestamps, IDs únicos, etc. para melhor cache hit rate
        import re
        
        # Remove UUIDs
        content = re.sub(r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b', '[UUID]', prompt)
        # Remove timestamps ISO
        content = re.sub(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}', '[TIMESTAMP]', content)
        # Remove números de documento específicos
        content = re.sub(r'\b\d{10,}\b', '[DOCUMENT_NUMBER]', content)
        
        return content.strip()
    
    async def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Busca resposta no cache"""
        try:
            cached = await self.supabase.get_cached_token(cache_key)
            if cached:
                # Atualiza contador de hits
                await self.supabase.update_cache_hit(cached['id'])
                return {
                    'text': cached['api_response'].get('text', ''),
                    'usage': cached['api_response'].get('usage', {}),
                    'cached': True,
                    'cache_id': cached['id']
                }
        except Exception:
            pass
        return None
    
    async def _save_to_cache(self, cache_key: str, response_data: Dict[str, Any], 
                           user_id: UUID, prompt_hash: str) -> None:
        """Salva resposta no cache"""
        try:
            cache_data = {
                'id': str(uuid4()),
                'user_id': str(user_id),
                'cache_key': cache_key,
                'prompt_hash': prompt_hash,
                'api_response': response_data,
                'tokens_used': response_data.get('usage', {}).get('total_tokens', 0),
                'model_used': settings.gemini_model,
                'expires_at': (datetime.utcnow() + timedelta(hours=settings.cache_ttl_hours)).isoformat()
            }
            
            await self.supabase.cache_token(cache_data)
        except Exception as e:
            # Cache failure não deve quebrar a aplicação
            print(f"Cache save error: {e}")
    
    async def generate_text(self, prompt: str, user_id: UUID, 
                          context: str = "", use_cache: bool = True) -> Dict[str, Any]:
        """
        Gera texto usando Gemini com cache inteligente
        
        Args:
            prompt: Prompt para o modelo
            user_id: ID do usuário (para cache personalizado)
            context: Contexto adicional
            use_cache: Se deve usar cache
            
        Returns:
            Dict com resposta, usage e informações de cache
        """
        start_time = time.time()
        
        # Prepara prompt completo
        full_prompt = f"{context}\n\n{prompt}" if context else prompt
        
        # Verifica cache se habilitado
        cache_key = None
        if use_cache:
            cache_content = self._extract_content_for_cache(full_prompt)
            cache_key = self._generate_cache_key(cache_content, user_id, context)
            
            cached_response = await self._get_from_cache(cache_key)
            if cached_response:
                cached_response['response_time_ms'] = int((time.time() - start_time) * 1000)
                return cached_response
        
        try:
            # Gera resposta usando Gemini
            response = self.model.generate_content(full_prompt)
            
            # Extrai informações da resposta
            response_text = response.text if response.text else ""
            
            # Simula usage (Gemini não retorna usage detalhado na versão gratuita)
            estimated_tokens = len(full_prompt.split()) + len(response_text.split())
            
            response_data = {
                'text': response_text,
                'usage': {
                    'prompt_tokens': len(full_prompt.split()),
                    'completion_tokens': len(response_text.split()),
                    'total_tokens': estimated_tokens
                },
                'model': settings.gemini_model,
                'cached': False,
                'response_time_ms': int((time.time() - start_time) * 1000)
            }
            
            # Salva no cache se habilitado
            if use_cache and cache_key:
                prompt_hash = hashlib.sha256(full_prompt.encode()).hexdigest()
                await self._save_to_cache(cache_key, response_data, user_id, prompt_hash)
            
            return response_data
            
        except Exception as e:
            raise LLMError(f"Erro na geração Gemini: {str(e)}")
    
    async def analyze_document(self, document_text: str, user_id: UUID, 
                             doc_type: str = "fiscal") -> Dict[str, Any]:
        """Analisa documento fiscal usando Gemini"""
        
        prompt = f"""
        Analise o seguinte documento fiscal e extraia as informações principais:

        Tipo de documento: {doc_type}
        Texto do documento:
        {document_text}

        Retorne um JSON com as seguintes informações:
        {{
            "numero_documento": "número do documento",
            "data_emissao": "data de emissão",
            "emissor": {{
                "nome": "nome do emissor",
                "cnpj": "CNPJ do emissor"
            }},
            "destinatario": {{
                "nome": "nome do destinatário",
                "cnpj": "CNPJ do destinatário"
            }},
            "valores": {{
                "total": 0.0,
                "impostos": 0.0,
                "desconto": 0.0
            }},
            "itens": [
                {{
                    "descricao": "descrição do item",
                    "quantidade": 0,
                    "valor_unitario": 0.0,
                    "cfop": "CFOP",
                    "ncm": "NCM"
                }}
            ],
            "observacoes": "observações importantes",
            "status_validacao": "válido/inválido/pendente"
        }}
        
        Seja preciso na extração e valide os dados fiscais conforme legislação brasileira.
        """
        
        return await self.generate_text(prompt, user_id, "Análise de documento fiscal")
    
    async def analyze_data(self, data_summary: str, user_id: UUID, 
                         analysis_type: str = "eda") -> Dict[str, Any]:
        """Realiza análise exploratória de dados"""
        
        prompt = f"""
        Como um especialista em análise de dados, analise o seguinte resumo de dados:

        Tipo de análise: {analysis_type}
        Resumo dos dados:
        {data_summary}

        Forneça insights detalhados incluindo:
        1. Principais estatísticas e tendências
        2. Identificação de padrões e anomalias
        3. Recomendações de negócio
        4. Próximos passos para análise
        5. Visualizações recomendadas

        Seja específico e focado em valor de negócio. Use linguagem clara e objetiva.
        Formate a resposta em markdown para melhor legibilidade.
        """
        
        return await self.generate_text(prompt, user_id, "Análise exploratória de dados")
    
    async def generate_insights(self, context: str, question: str, 
                              user_id: UUID) -> Dict[str, Any]:
        """Gera insights baseado em contexto e pergunta"""
        
        prompt = f"""
        Contexto: {context}
        
        Pergunta: {question}
        
        Como um consultor especialista, forneça uma resposta detalhada e útil.
        Baseie-se no contexto fornecido e use seu conhecimento sobre:
        - Legislação fiscal brasileira
        - Análise de dados e estatística
        - Boas práticas empresariais
        - Compliance e auditoria
        
        Responda de forma clara, objetiva e com exemplos práticos quando relevante.
        """
        
        return await self.generate_text(prompt, user_id, "Consultoria especializada")


class OpenAIManager:
    """Gerenciador opcional do OpenAI (para funcionalidades específicas)"""
    
    def __init__(self):
        if not settings.openai_api_key:
            self.enabled = False
            return
        
        try:
            import openai
            self.client = openai.OpenAI(api_key=settings.openai_api_key)
            self.enabled = True
        except ImportError:
            self.enabled = False
    
    async def generate_code(self, task_description: str, language: str = "python") -> str:
        """Gera código usando OpenAI (melhor para código)"""
        if not self.enabled:
            raise LLMError("OpenAI não configurado")
        
        prompt = f"""
        Gere código {language} para a seguinte tarefa:
        {task_description}
        
        Requisitos:
        - Código limpo e bem documentado
        - Tratamento de erros
        - Funções reutilizáveis
        - Comentários explicativos
        
        Retorne apenas o código, sem explicações adicionais.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise LLMError(f"Erro na geração OpenAI: {str(e)}")


class LLMOrchestrator:
    """Orquestrador que escolhe o melhor modelo para cada tarefa"""
    
    def __init__(self):
        self.gemini = GeminiManager()
        self.openai = OpenAIManager()
    
    async def route_request(self, task_type: str, content: str, user_id: UUID, 
                          **kwargs) -> Dict[str, Any]:
        """Roteia requisição para o modelo mais adequado"""
        
        if task_type == "code_generation" and self.openai.enabled:
            # OpenAI é melhor para geração de código
            code = await self.openai.generate_code(content, kwargs.get('language', 'python'))
            return {
                'text': code,
                'model': settings.openai_model,
                'task_type': task_type
            }
        
        elif task_type == "document_analysis":
            # Gemini para análise de documentos
            return await self.gemini.analyze_document(content, user_id, kwargs.get('doc_type', 'fiscal'))
        
        elif task_type == "data_analysis":
            # Gemini para análise de dados
            return await self.gemini.analyze_data(content, user_id, kwargs.get('analysis_type', 'eda'))
        
        elif task_type == "chat" or task_type == "insights":
            # Gemini para chat e insights
            context = kwargs.get('context', '')
            return await self.gemini.generate_insights(context, content, user_id)
        
        else:
            # Default: Gemini
            return await self.gemini.generate_text(content, user_id, kwargs.get('context', ''))


class CacheAnalytics:
    """Analytics do sistema de cache"""
    
    def __init__(self):
        self.supabase = SupabaseManager()
    
    async def get_cache_stats(self, user_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Obtém estatísticas do cache"""
        try:
            # TODO: Implementar queries específicas para analytics
            return {
                'cache_hit_rate': 0.65,  # 65% hit rate simulado
                'total_tokens_saved': 15000,
                'total_requests': 100,
                'cache_hits': 65,
                'cache_misses': 35,
                'average_response_time_ms': 250
            }
        except Exception:
            return {}
    
    async def cleanup_old_cache(self, days_old: int = 7) -> int:
        """Remove cache antigo"""
        try:
            return await self.supabase.cleanup_expired_cache()
        except Exception:
            return 0


# Exceções customizadas
class LLMError(Exception):
    """Erro base para operações LLM"""
    pass


class CacheError(Exception):
    """Erro específico de cache"""
    pass


class ModelNotAvailableError(LLMError):
    """Modelo não disponível"""
    pass


# Funções de conveniência
async def generate_text(prompt: str, user_id: UUID, context: str = "") -> str:
    """Conveniência: gera texto usando Gemini"""
    gemini = GeminiManager()
    result = await gemini.generate_text(prompt, user_id, context)
    return result.get('text', '')


async def analyze_document(document_text: str, user_id: UUID) -> Dict[str, Any]:
    """Conveniência: analisa documento"""
    gemini = GeminiManager()
    return await gemini.analyze_document(document_text, user_id)


async def get_ai_insights(question: str, context: str, user_id: UUID) -> str:
    """Conveniência: obtém insights da IA"""
    gemini = GeminiManager()
    result = await gemini.generate_insights(context, question, user_id)
    return result.get('text', '')


# Factory function para criar instância quando necessário
def create_llm_orchestrator() -> LLMOrchestrator:
    """Cria instância do LLM Orchestrator"""
    return LLMOrchestrator()