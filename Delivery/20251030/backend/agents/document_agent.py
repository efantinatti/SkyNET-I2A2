"""
Document Agent - Processa documentos fiscais e extrai informações estruturadas.

Este módulo fornece um agente que pode processar diferentes tipos de documentos fiscais,
extraindo informações estruturadas e integrando-se com o restante do sistema.
"""
import os
import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple
import shutil
from datetime import datetime

from ..tools.fiscal_document_processor import FiscalDocumentProcessor
from ..tools.ocr_processor import ocr_text_to_document
from ..tools.llm_ocr_mapper import LLMOCRMapper
from ..models.document import Document, DocumentType, DocumentStatus
from .fiscal_validator_agent import create_fiscal_validator

# Configura o logger
logger = logging.getLogger(__name__)

class DocumentAgent:
    """
    Agente responsável por processar documentos fiscais e extrair informações estruturadas.
    
    Este agente lida com diferentes tipos de documentos (NFe, NFCe, CTe, etc.)
    e extrai informações estruturadas usando OCR e processamento de texto.
    """
    
    def __init__(self, upload_dir: str = "uploads", processed_dir: str = "processed"):
        """
        Inicializa o DocumentAgent.
        
        Args:
            upload_dir: Diretório onde os arquivos enviados são armazenados temporariamente
            processed_dir: Diretório onde os arquivos processados são armazenados
        """
        self.upload_dir = Path(upload_dir)
        self.processed_dir = Path(processed_dir)
        self.processor = FiscalDocumentProcessor()
        
        # Inicializa o validador fiscal com LLM
        self.fiscal_validator = create_fiscal_validator()
        
        # Cria os diretórios se não existirem
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    async def process_uploaded_file(self, file_path: Union[str, Path], move_after_process: bool = True) -> Dict[str, Any]:
        """
        Processa um arquivo enviado e extrai informações estruturadas.
        
        Args:
            file_path: Caminho para o arquivo a ser processado
            move_after_process: Se True, move o arquivo para o diretório de processados após o processamento
            
        Returns:
            Dicionário com os resultados do processamento, incluindo validação fiscal
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
        logger.info(f"Processando arquivo: {file_path}")
        
        try:
            # 1. Processa o documento
            result = self.processor.process_document(file_path)
            
            # 2. Se o processamento foi bem-sucedido, valida os códigos fiscais
            if result.get('success'):
                # Extrai os dados fiscais
                fiscal_data = self._extract_fiscal_data(result)
                
                # Valida os códigos fiscais
                if self.fiscal_validator and fiscal_data:
                    validation_result = await self._validate_fiscal_codes(fiscal_data)
                    result['fiscal_validation'] = validation_result
                    
                    # Adiciona um resumo da validação
                    if 'summary' not in result:
                        result['summary'] = {}
                    
                    result['summary']['fiscal_validation_summary'] = self._generate_validation_summary(validation_result)
                    
                    # Prepara os detalhes de validação para persistência
                    result['validation_details'] = self._prepare_validation_details(validation_result)
                    
                    # Atualiza o status com base na validação
                    result['validation_status'] = self._determine_validation_status(validation_result)
                
                # Move o arquivo para o diretório de processados
                if move_after_process:
                    self._move_to_processed(file_path)
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao processar o arquivo {file_path}: {str(e)}", exc_info=True)
            raise
    
    def _move_to_processed(self, file_path: Path) -> Path:
        """
        Move um arquivo processado para o diretório de processados.
        
        Args:
            file_path: Caminho para o arquivo a ser movido
            
        Returns:
            Novo caminho do arquivo
        """
        # Cria um nome único para o arquivo processado
        timestamp = int(datetime.now().timestamp())
        new_filename = f"{timestamp}_{file_path.name}"
        new_path = self.processed_dir / new_filename
        
        # Move o arquivo
        shutil.move(str(file_path), str(new_path))
        
        return new_path
    
    def _extract_fiscal_data(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extrai os dados fiscais do resultado do processamento.
        
        Args:
            result: Resultado do processamento do documento
            
        Returns:
            Dicionário com os dados fiscais extraídos
        """
        fiscal_data = {}
        
        # Extrai os dados do documento principal
        doc_data = result.get('document', {})
        
        # CFOP
        if 'cfop' in doc_data:
            fiscal_data['cfop'] = doc_data['cfop']
        
        # CST ICMS
        if 'cst_icms' in doc_data:
            fiscal_data['cst_icms'] = doc_data['cst_icms']
        
        # CST PIS/COFINS
        if 'cst_pis' in doc_data:
            fiscal_data['cst_pis'] = doc_data['cst_pis']
        if 'cst_cofins' in doc_data:
            fiscal_data['cst_cofins'] = doc_data['cst_cofins']
        
        # NCM (pega o primeiro item se existir)
        items = result.get('items', [])
        if items and 'ncm' in items[0]:
            fiscal_data['ncm'] = items[0]['ncm']
        
        return fiscal_data
    
    async def _validate_fiscal_codes(self, fiscal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida os códigos fiscais usando o LLM.
        
        Args:
            fiscal_data: Dicionário com os códigos fiscais a serem validados
            
        Returns:
            Dicionário com os resultados da validação
        """
        if not self.fiscal_validator:
            return {
                'status': 'disabled',
                'message': 'Validador fiscal não está disponível'
            }
        
        try:
            # Chama o validador fiscal
            validation_result = await self.fiscal_validator.validate_document(fiscal_data)
            
            # Formata o resultado para incluir apenas os códigos fornecidos
            filtered_result = {}
            for code_type in fiscal_data:
                if code_type in validation_result:
                    filtered_result[code_type] = validation_result[code_type]
            
            return {
                'status': 'success',
                'validations': filtered_result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Erro ao validar códigos fiscais: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _prepare_validation_details(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Prepara os detalhes de validação para persistência."""
        if not validation_result or validation_result.get('status') != 'success':
            return {
                'status': 'error',
                'message': validation_result.get('message', 'Erro desconhecido na validação'),
                'timestamp': datetime.now().isoformat()
            }
        
        validations = validation_result.get('validations', {})
        
        # Conta validações bem-sucedidas e com falha
        valid = sum(1 for v in validations.values() if v.get('is_valid', False))
        invalid = len(validations) - valid
        
        return {
            'status': 'success',
            'validations': validations,
            'summary': {
                'valid': valid,
                'invalid': invalid,
                'total': len(validations)
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _determine_validation_status(self, validation_result: Dict[str, Any]) -> str:
        """Determina o status de validação com base nos resultados."""
        if not validation_result or validation_result.get('status') != 'success':
            return 'error'
        
        validations = validation_result.get('validations', {})
        if not validations:
            return 'pending'
        
        # Se todas as validações forem bem-sucedidas
        if all(v.get('is_valid', False) for v in validations.values()):
            return 'valid'
        
        # Se houver alguma validação com falha
        if any(not v.get('is_valid', True) for v in validations.values()):
            return 'invalid'
        
        return 'pending'

    def _generate_validation_summary(self, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Gera um resumo da validação fiscal.
        
        Args:
            validation_result: Resultado da validação
            
        Returns:
            Dicionário com um resumo da validação
        """
        if validation_result.get('status') != 'success' or 'validations' not in validation_result:
            return {
                'status': validation_result.get('status', 'unknown'),
                'message': validation_result.get('message', 'Erro desconhecido na validação')
            }
        
        validations = validation_result['validations']
        summary = {
            'status': 'success',
            'valid_codes': 0,
            'invalid_codes': 0,
            'total_codes': len(validations),
            'codes': {}
        }
        
        for code_type, validation in validations.items():
            is_valid = validation.get('is_valid', False)
            if is_valid:
                summary['valid_codes'] += 1
            else:
                summary['invalid_codes'] += 1
                
            summary['codes'][code_type] = {
                'is_valid': is_valid,
                'normalized': validation.get('normalized_code', ''),
                'description': validation.get('description', ''),
                'confidence': validation.get('confidence', 0.0)
            }
        
        return summary
    
    async def save_document_to_db(self, result: Dict[str, Any], user_id: Optional[str] = None) -> Document:
        """
        Salva os resultados do processamento no banco de dados.
        
        Args:
            result: Resultado do processamento do documento
            user_id: ID do usuário que enviou o documento (opcional)
            
        Returns:
            Instância do documento salvo
        """
        # Mapeia o tipo de documento para o enum DocumentType
        doc_type_map = {
            'nfe': DocumentType.NFE,
            'nfce': DocumentType.NFCE,
            'cte': DocumentType.CTE,
            'mdfe': DocumentType.MDFE
        }
        
        doc_type = doc_type_map.get(result.get('document_type', '').lower(), DocumentType.UNKNOWN)
        
        # Formata a data de emissão se existir
        issue_date = result.get('data_emissao')
        if issue_date:
            try:
                # Tenta converter para datetime e depois para o formato desejado
                if isinstance(issue_date, str):
                    # Se já estiver no formato YYYY-MM-DD HH:MM:SS, mantém
                    if not re.match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', issue_date):
                        # Tenta converter de DD/MM/YYYY HH:MM:SS para YYYY-MM-DD HH:MM:SS
                        try:
                            # Tenta com horas, minutos e segundos
                            dt = datetime.strptime(issue_date, '%d/%m/%Y %H:%M:%S')
                            issue_date = dt.strftime('%Y-%m-%d %H:%M:%S')
                        except ValueError:
                            # Se falhar, tenta apenas com a data
                            try:
                                dt = datetime.strptime(issue_date, '%d/%m/%Y')
                                issue_date = dt.strftime('%Y-%m-%d 00:00:00')
                            except ValueError:
                                # Se não conseguir converter, mantém o valor original
                                logger.warning(f"Formato de data não reconhecido: {issue_date}")
                elif hasattr(issue_date, 'strftime'):
                    # Se for um objeto datetime, converte para string
                    issue_date = issue_date.strftime('%Y-%m-%d %H:%M:%S')
            except Exception as e:
                logger.warning(f"Erro ao formatar data de emissão: {e}")
                # Em caso de erro, mantém o valor original
        
        # Cria o documento no banco de dados
        document = Document.create(
            document_type=doc_type,
            document_number=result.get('numero'),
            issue_date=issue_date,
            total_amount=result.get('valor_total', 0.0),
            issuer_name=result.get('emitente', {}).get('razao_social'),
            issuer_document=result.get('emitente', {}).get('cnpj'),
            receiver_name=result.get('destinatario', {}).get('razao_social'),
            receiver_document=result.get('destinatario', {}).get('cpf') or result.get('destinatario', {}).get('cnpj'),
            access_key=result.get('chave_acesso'),
            authorization_protocol=result.get('protocolo_autorizacao'),
            raw_data=json.dumps(result, ensure_ascii=False),
            status=DocumentStatus.PROCESSED,
            user_id=user_id
        )
        
        # Salva os itens do documento
        for item_data in result.get('itens', []):
            document.add_item(
                code=item_data.get('codigo'),
                description=item_data.get('descricao'),
                quantity=item_data.get('quantidade', 0),
                unit_value=item_data.get('valor_unitario', 0),
                total_value=item_data.get('valor_total', 0)
            )
        
        # Salva os impostos do documento
        for tax_type, tax_value in result.get('impostos', {}).items():
            document.add_tax(
                tax_type=tax_type.upper(),
                amount=float(tax_value)
            )
        
        return document
    
    def process_and_save(self, file_path: Union[str, Path], user_id: Optional[str] = None) -> Document:
        """
        Processa um documento e salva os resultados no banco de dados.
        
        Args:
            file_path: Caminho para o arquivo a ser processado
            user_id: ID do usuário que enviou o documento (opcional)
            
        Returns:
            Instância do documento salvo
        """
        # Processa o documento
        result = self.process_uploaded_file(file_path)
        
        # Salva no banco de dados
        return self.save_document_to_db(result, user_id)
    
    def batch_process(self, directory: Union[str, Path], user_id: Optional[str] = None) -> List[Document]:
        """
        Processa todos os arquivos em um diretório.
        
        Args:
            directory: Diretório contendo os arquivos a serem processados
            user_id: ID do usuário que enviou os documentos (opcional)
            
        Returns:
            Lista de documentos processados
        """
        directory = Path(directory)
        if not directory.is_dir():
            raise NotADirectoryError(f"O diretório não existe: {directory}")
        
        processed_docs = []
        
        # Processa todos os arquivos suportados no diretório
        for file_path in directory.glob("*"):
            if file_path.suffix.lower() in ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.xml']:
                try:
                    logger.info(f"Processando arquivo: {file_path}")
                    doc = self.process_and_save(file_path, user_id)
                    processed_docs.append(doc)
                    logger.info(f"Documento processado com sucesso: {doc.id}")
                except Exception as e:
                    logger.error(f"Erro ao processar o arquivo {file_path}: {str(e)}", exc_info=True)
        
        return processed_docs


def create_document_agent() -> DocumentAgent:
    """
    Função de fábrica para criar uma instância do DocumentAgent.
    
    Returns:
        Instância do DocumentAgent configurada
    """
    from config import UPLOAD_DIR, PROCESSED_DIR
    
    return DocumentAgent(
        upload_dir=UPLOAD_DIR or "uploads",
        processed_dir=PROCESSED_DIR or "processed"
    )


if __name__ == "__main__":
    # Exemplo de uso
    import sys
    
    # Configura o logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    if len(sys.argv) < 2:
        print("Uso: python -m backend.agents.document_agent <caminho_do_arquivo_ou_diretorio> [user_id]")
        sys.exit(1)
    
    path = Path(sys.argv[1])
    user_id = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        agent = create_document_agent()
        
        if path.is_file():
            # Processa um único arquivo
            doc = agent.process_and_save(path, user_id)
            print(f"Documento processado com sucesso! ID: {doc.id}")
        else:
            # Processa todos os arquivos no diretório
            docs = agent.batch_process(path, user_id)
            print(f"Processados {len(docs)} documentos com sucesso!")
            
    except Exception as e:
        print(f"Erro: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
