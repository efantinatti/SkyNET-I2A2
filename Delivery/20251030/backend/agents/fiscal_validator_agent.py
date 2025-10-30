"""Agente de validação fiscal com LLM.

Este módulo implementa um agente que utiliza LLM para validar e normalizar
códigos fiscais como CFOP, CST e NCM.
"""
from typing import Dict, Any, Optional, List, Union
import asyncio
import logging
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
import google.generativeai as genai
from langchain_core.output_parsers import JsonOutputParser
import json
import hashlib
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

class FiscalCache:
    """Classe para gerenciar o cache de validações fiscais."""
    
    def __init__(self, cache_dir: str = ".fiscal_cache", ttl_days: int = 30):
        """Inicializa o gerenciador de cache.
        
        Args:
            cache_dir: Diretório para armazenar o cache
            ttl_days: Tempo de vida do cache em dias
        """
        self.cache_dir = Path(cache_dir)
        self.ttl = timedelta(days=ttl_days)
        self._ensure_cache_dir()
    
    def _ensure_cache_dir(self) -> None:
        """Garante que o diretório de cache existe."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, data: Dict[str, Any]) -> str:
        """Gera uma chave de cache única para os dados fornecidos."""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    def _get_cache_path(self, key: str) -> Path:
        """Retorna o caminho completo para um item de cache."""
        return self.cache_dir / f"{key}.json"
    
    def get(self, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Obtém um item do cache, se existir e não estiver expirado."""
        try:
            key = self._get_cache_key(data)
            cache_file = self._get_cache_path(key)
            
            if not cache_file.exists():
                return None
                
            # Verifica se o cache expirou
            file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
            if file_age > self.ttl:
                return None
                
            # Lê o cache
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Erro ao ler do cache: {e}")
            return None
    
    def set(self, data: Dict[str, Any], result: Dict[str, Any]) -> None:
        """Armazena um resultado no cache."""
        try:
            key = self._get_cache_key(data)
            cache_file = self._get_cache_path(key)
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'data': data,
                    'result': result,
                    'cached_at': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
                
        except OSError as e:
            logger.warning(f"Erro ao salvar no cache: {e}")
    
    def clear_expired(self) -> int:
        """Remove itens de cache expirados.
        
        Returns:
            Número de itens removidos
        """
        removed = 0
        now = datetime.now()
        
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                file_age = now - datetime.fromtimestamp(cache_file.stat().st_mtime)
                if file_age > self.ttl:
                    cache_file.unlink()
                    removed += 1
            except OSError as e:
                logger.warning(f"Erro ao remover cache expirado {cache_file}: {e}")
        
        return removed

class FiscalCodeValidation(BaseModel):
    """Modelo para validação de um código fiscal."""
    is_valid: bool = Field(..., description="Se o código é válido")
    normalized_code: str = Field(..., description="Código normalizado")
    description: str = Field(..., description="Descrição do código")
    confidence: float = Field(..., description="Nível de confiança da validação (0-1)")

class FiscalDocumentValidation(BaseModel):
    """Modelo para validação de um documento fiscal completo."""
    cfop: FiscalCodeValidation
    cst_icms: Optional[FiscalCodeValidation] = None
    cst_pis: Optional[FiscalCodeValidation] = None
    cst_cofins: Optional[FiscalCodeValidation] = None
    ncm: Optional[FiscalCodeValidation] = None

class FiscalValidatorAgent:
    """Agente para validação de códigos fiscais usando LLM."""
    
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash", cache_enabled: bool = True, cache_dir: str = ".fiscal_cache"):
        """Inicializa o validador fiscal.
        
        Args:
            api_key: Chave da API do Google AI Studio
            model_name: Nome do modelo a ser usado (padrão: gemini-pro)
            cache_enabled: Se o cache deve ser habilitado
            cache_dir: Diretório para armazenar o cache
        """
        # Configura a API do Google Generative AI
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.llm = self.model  # Mantido para compatibilidade
        
        # Configura o cache
        self.cache_enabled = cache_enabled
        self.cache = FiscalCache(cache_dir) if cache_enabled else None
        
        # Limpa o cache expirado ao iniciar
        if self.cache_enabled:
            removed = self.cache.clear_expired()
            if removed > 0:
                logger.info(f"Limpos {removed} itens expirados do cache")
        
        # Configuração de geração
        self.generation_config = {
            "temperature": 0.1,  # Baixa temperatura para respostas mais previsíveis
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 4096,
        }
        self.parser = JsonOutputParser(pydantic_object=FiscalDocumentValidation)
        
        # Template de prompt para validação fiscal
        self.validation_prompt = """
Valide e normalize os códigos fiscais abaixo segundo as regras atuais do Brasil.
Campos:
- CFOP: {cfop}
- CST ICMS: {cst_icms}
- CST PIS: {cst_pis}
- CST COFINS: {cst_cofins}
- NCM: {ncm}

Para cada código, retorne:
- is_valid
- normalized_code
- description
- confidence (0-1)

Responda APENAS com o JSON no formato:
{
  "cfop": {...},
  "cst_icms": {...},
  "cst_pis": {...},
  "cst_cofins": {...},
  "ncm": {...}
}
"""
        
    
    def _process_llm_response(self, response_text: str, original_data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa a resposta do LLM e formata o resultado.
        
        Args:
            response_text: Texto da resposta do LLM
            original_data: Dados originais enviados para validação
            
        Returns:
            Dicionário com os resultados processados
        """
        try:
            # Tenta fazer o parse do JSON retornado pelo LLM
            result = json.loads(response_text)
            
            # Extrai os campos de validação do resultado
            validation_result = {}
            
            # Se o resultado tiver um campo 'validation', extrai dele
            if 'validation' in result and isinstance(result['validation'], dict):
                validation_result = result['validation']
            # Se o resultado já tiver os campos diretamente, usa como está
            elif all(field in result for field in ['cfop', 'cst_icms', 'cst_pis', 'cst_cofins', 'ncm']):
                validation_result = result
            # Se for um dicionário com os campos de validação aninhados, extrai
            else:
                validation_result = {
                    'cfop': result.get('cfop', {}),
                    'cst_icms': result.get('cst_icms', {}),
                    'cst_pis': result.get('cst_pis', {}),
                    'cst_cofins': result.get('cst_cofins', {}),
                    'ncm': result.get('ncm', {})
                }
            
            # Garante que todos os campos esperados existam no resultado
            for field in ['cfop', 'cst_icms', 'cst_pis', 'cst_cofins', 'ncm']:
                if field not in validation_result:
                    validation_result[field] = {
                        'is_valid': False,
                        'normalized_code': '',
                        'description': f'Campo {field} não encontrado na resposta',
                        'confidence': 0.0
                    }
            
            return validation_result
            
        except (json.JSONDecodeError, Exception) as e:
            error_type = 'JSON inválido' if isinstance(e, json.JSONDecodeError) else 'Erro no processamento'
            logger.error(f"{error_type} na resposta do LLM: {response_text}", exc_info=True)
            
            # Cria um dicionário com todos os campos inválidos
            error_result = {}
            for field in ['cfop', 'cst_icms', 'cst_pis', 'cst_cofins', 'ncm']:
                error_result[field] = {
                    'is_valid': False,
                    'normalized_code': '',
                    'description': f'Erro: {str(e)}',
                    'confidence': 0.0
                }
            return error_result
    
    def _build_validation_prompt(self, fiscal_data: Dict[str, Any]) -> str:
        """Constrói o prompt para validação com base nos dados fornecidos.
        
        Args:
            fiscal_data: Dicionário com os dados fiscais a serem validados
            
        Returns:
            String com o prompt formatado
        """
        # Cria uma cópia do dicionário para não modificar o original
        data = fiscal_data.copy()
        
        # Garante que todos os campos esperados existam no dicionário
        for field in ['cfop', 'cst_icms', 'cst_pis', 'cst_cofins', 'ncm']:
            if field not in data:
                data[field] = ''
        
        # Remove campos vazios para não poluir o prompt
        data = {k: v for k, v in data.items() if v or k in ['cfop']}  # CFOP é obrigatório
        
        # Formata o prompt com os dados fornecidos
        try:
            return self.validation_prompt.format(**data)
        except KeyError as e:
            logger.error(f"Erro ao formatar prompt: campo faltando - {e}")
            # Adiciona o campo faltante com valor vazio
            data[str(e).strip("'")] = ''
            return self.validation_prompt.format(**data)
    
    async def validate_document(self, fiscal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Valida os códigos fiscais de um documento.
        
        Args:
            fiscal_data: Dicionário contendo os códigos fiscais a serem validados
            
        Returns:
            Dicionário com os resultados da validação
        """
        if not fiscal_data:
            return {
                'status': 'error',
                'message': 'Nenhum dado fiscal fornecido',
                'timestamp': datetime.now().isoformat()
            }
        
        # Verifica o cache primeiro
        cached_result = None
        if self.cache_enabled:
            cached_result = self.cache.get(fiscal_data)
            if cached_result:
                logger.info("Retornando resultado do cache")
                # Retorna apenas o dicionário de validação, não o resultado completo
                return cached_result['result'].get('validation', {})
        
        try:
            # Prepara o prompt para o LLM
            prompt = self._build_validation_prompt(fiscal_data)
            
            # Chama o modelo
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.model.generate_content(prompt)
            )
            
            # Processa a resposta
            result = self._process_llm_response(response.text, fiscal_data)
            
            # Cria o resultado completo com metadados
            full_result = {
                'status': 'success',
                'validated_at': datetime.now().isoformat(),
                'original_data': fiscal_data,
                'validation': result
            }
            
            # Armazena o resultado completo no cache
            if self.cache_enabled:
                self.cache.set(fiscal_data, full_result)
            
            # Retorna apenas o dicionário de validação para compatibilidade com os testes
            return result
            
        except Exception as e:
            logger.error(f"Erro ao validar documento: {e}", exc_info=True)
            # Retorna todos os campos como inválidos em caso de erro
            error_result = {}
            for field in ['cfop', 'cst_icms', 'cst_pis', 'cst_cofins', 'ncm']:
                error_result[field] = {
                    'is_valid': False,
                    'normalized_code': '',
                    'description': f'Erro: {str(e)}',
                    'confidence': 0.0
                }
            return error_result

# Função auxiliar para criar uma instância do validador
def create_fiscal_validator(api_key: str = None, cache_enabled: bool = True, cache_dir: str = ".fiscal_cache") -> Optional['FiscalValidatorAgent']:
    """Cria uma instância do validador fiscal.
    
    Args:
        api_key: Chave da API do Google AI Studio. Se não for fornecida,
                tenta obter do ambiente.
        cache_enabled: Se o cache deve ser habilitado (padrão: True)
        cache_dir: Diretório para armazenar o cache (padrão: ".fiscal_cache")
                
    Returns:
        Instância do FiscalValidatorAgent ou None se não for possível configurar
    """
    try:
        if not api_key:
            # Tenta obter a chave da API do ambiente
            from config import GOOGLE_AI_API_KEY
            api_key = GOOGLE_AI_API_KEY
            
            if not api_key:
                logger.warning("Chave da API do Google AI não encontrada")
                return None
                
        return FiscalValidatorAgent(
            api_key=api_key,
            cache_enabled=cache_enabled,
            cache_dir=cache_dir
        )
        
    except Exception as e:
        logger.error(f"Erro ao criar validador fiscal: {e}", exc_info=True)
        return None
