from . import extraction, classifier, analyst
from typing import Dict, Any, Optional, Union, List
from pathlib import Path
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CoordinatorAgent:
    """Orquestrador principal para processamento de documentos fiscais."""
    
    def __init__(self):
        self.valid_tasks = {'extract', 'classify', 'analyze'}
        self.supported_extensions = {
            'extract': {'.xml', '.pdf', '.png', '.jpg', '.jpeg'},
            'analyze': {'.csv'}
        }
    
    def _validate_task(self, task: str) -> bool:
        """Valida se a tarefa é suportada."""
        if task not in self.valid_tasks:
            logger.error(f'Tarefa não suportada: {task}')
            return False
        return True
    
    def _validate_file(self, path: str, task: str) -> bool:
        """Valida se o arquivo existe e tem a extensão correta."""
        try:
            file_path = Path(path)
            if not file_path.exists():
                logger.error(f'Arquivo não encontrado: {path}')
                return False
                
            if task in self.supported_extensions:
                ext = file_path.suffix.lower()
                if ext not in self.supported_extensions[task]:
                    logger.error(f'Extensão não suportada para {task}: {ext}')
                    return False
                    
            return True
        except Exception as e:
            logger.error(f'Erro ao validar arquivo {path}: {str(e)}')
            return False
    
    def _handle_extract(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Gerencia a extração de dados de documentos."""
        path = payload.get('path')
        if not path:
            return self._create_error_response('missing_path', 'Path é obrigatório')
            
        if not self._validate_file(path, 'extract'):
            return self._create_error_response('invalid_file', 'Arquivo inválido ou não suportado')
        
        try:
            logger.info(f'Iniciando extração do arquivo: {path}')
            extracted = extraction.extract_from_file(path)
            
            if not isinstance(extracted, dict):
                return self._create_error_response(
                    'invalid_format',
                    f'Formato inválido: esperado dicionário, obtido {type(extracted).__name__}',
                    {'raw_data': str(extracted)[:500]}
                )
                
            logger.info('Extração concluída com sucesso')
            return extracted
            
        except Exception as e:
            logger.exception(f'Erro durante a extração: {str(e)}')
            return self._create_error_response('extraction_error', f'Falha na extração: {str(e)}')
    
    def _handle_classify(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Gerencia a classificação de documentos."""
        if not isinstance(payload, dict):
            return self._create_classification_error('invalid_payload', 'Payload inválido')
        
        parsed = payload.get('parsed')
        if parsed is None:
            return self._create_classification_error('missing_parsed', 'Campo "parsed" é obrigatório')
            
        if isinstance(parsed, str):
            try:
                # Tenta converter string JSON para dicionário
                import json
                parsed = json.loads(parsed)
            except json.JSONDecodeError:
                return self._create_classification_error(
                    'invalid_parsed_format',
                    'Formato inválido para o campo "parsed" (esperado JSON ou dicionário)'
                )
        
        if not isinstance(parsed, dict):
            return self._create_classification_error(
                'invalid_parsed_type',
                f'Tipo inválido para o campo "parsed": {type(parsed).__name__}'
            )
            
        try:
            logger.info('Iniciando classificação do documento')
            result = classifier.classify_document(parsed)
            logger.info('Classificação concluída com sucesso')
            return result
            
        except Exception as e:
            logger.exception(f'Erro durante a classificação: {str(e)}')
            return self._create_classification_error('classification_error', f'Falha na classificação: {str(e)}')
    
    def _handle_analyze(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Gerencia a análise de dados."""
        path = payload.get('path')
        if not path:
            return self._create_error_response('missing_path', 'Path é obrigatório')
            
        if not self._validate_file(path, 'analyze'):
            return self._create_error_response('invalid_file', 'Arquivo CSV inválido ou não encontrado')
            
        try:
            logger.info(f'Iniciando análise do arquivo: {path}')
            result = analyst.analyze_csv(path)
            logger.info('Análise concluída com sucesso')
            return result
            
        except Exception as e:
            logger.exception(f'Erro durante a análise: {str(e)}')
            return self._create_error_response('analysis_error', f'Falha na análise: {str(e)}')
    
    def run_task(self, task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa uma tarefa através do agente apropriado.
        
        Args:
            task: Nome da tarefa ('extract', 'classify' ou 'analyze')
            payload: Dados necessários para a tarefa
            
        Returns:
            Dicionário com o resultado da operação ou mensagem de erro
        """
        logger.info(f'Iniciando tarefa: {task}')
        
        if not self._validate_task(task):
            return self._create_error_response('invalid_task', f'Tarefa não suportada: {task}')
        
        try:
            if task == 'extract':
                return self._handle_extract(payload)
            elif task == 'classify':
                return self._handle_classify(payload)
            elif task == 'analyze':
                return self._handle_analyze(payload)
                
        except Exception as e:
            logger.exception(f'Erro inesperado ao executar tarefa {task}: {str(e)}')
            return self._create_error_response(
                'unexpected_error',
                f'Erro inesperado: {str(e)}',
                {'task': task}
            )
    
    @staticmethod
    def _create_error_response(
        error_code: str, 
        message: str, 
        details: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Cria uma resposta de erro padronizada."""
        response = {
            'success': False,
            'error': {
                'code': error_code,
                'message': message
            }
        }
        if details:
            response['error']['details'] = details
        return response
    
    @staticmethod
    def _create_classification_error(
        error_code: str, 
        message: str
    ) -> Dict[str, Any]:
        """Cria uma resposta de erro padronizada para classificação."""
        return {
            'tipo': 'unknown',
            'setor': 'unknown',
            'perfil_emitente': 'unknown',
            'validacao': {
                'status': 'error',
                'issues': [f'{error_code}: {message}'],
                'calculated_sum': 0.0,
                'warnings': []
            },
            'error': {
                'code': error_code,
                'message': message
            }
        }

# Instância singleton para uso em outros módulos
coordinator = CoordinatorAgent()

def run_task(task: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Função de compatibilidade para manter a API existente."""
    return coordinator.run_task(task, payload)
