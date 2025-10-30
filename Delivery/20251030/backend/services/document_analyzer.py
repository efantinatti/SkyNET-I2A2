"""
Document Analyzer Service

Fornece funcionalidades avançadas de análise de documentos fiscais
usando PostgreSQL direto para melhor performance e consistência.
"""
import json
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
import logging

from config import DATABASE_CONFIG
from backend.database.storage_manager import get_async_storage

logger = logging.getLogger(__name__)


class DocumentAnalyzer:
    """Serviço de análise de documentos fiscais."""

    def __init__(self, supabase_client=None, db=None):
        """Initialize with asynchronous PostgreSQL storage instead of Supabase client."""
        if db is None:
            self.db = get_async_storage()
        else:
            self.db = db
        # Keep supabase_client for backward compatibility if needed
        self.supabase = supabase_client

    async def get_documents_summary(self, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """Obtém um resumo dos documentos com base nos filtros fornecidos."""
        try:
            # Use PostgreSQL direct instead of Supabase API
            result = await self.db.get_fiscal_documents(page=1, page_size=10000, **filters)
            documents = result.items

            # Processar e resumir os documentos
            summary = {
                'total_documents': len(documents),
                'by_type': {},
                'by_issuer': {},
                'total_value': 0.0,
                'documents': []
            }

            for doc in documents:
                # Categorização melhorada baseada no document_type e extracted_data
                doc_type = self._categorize_document(doc)
                summary['by_type'][doc_type] = summary['by_type'].get(doc_type, 0) + 1

                # Contagem por emissor
                issuer = doc.get('issuer_cnpj', 'Desconhecido')
                summary['by_issuer'][issuer] = summary['by_issuer'].get(issuer, 0) + 1

                # Extrair valor total se disponível
                try:
                    if doc.get('extracted_data') and 'total' in doc['extracted_data']:
                        total = float(doc['extracted_data']['total'])
                        summary['total_value'] += total
                except (ValueError, TypeError):
                    pass

                # Adicionar documento à lista com categorização
                summary['documents'].append({
                    'id': doc['id'],
                    'file_name': doc.get('file_name', 'Sem nome'),
                    'document_type': doc.get('document_type', 'N/A'),
                    'categorized_type': doc_type,
                    'issuer_cnpj': issuer,
                    'created_at': doc.get('created_at'),
                    'validation_status': doc.get('validation_status', 'não validado')
                })

            return summary

        except Exception as e:
            logger.error(f"Erro ao resumir documentos: {e}")
            raise

    async def get_all_documents_summary(self, time_filter: Union[datetime, str, None] = None) -> Dict[str, Any]:
        """
        Obtém um resumo dos documentos para análise de categorias.
        
        Args:
            time_filter: Filtra documentos criados após esta data/hora.
                        Se None, retorna todos os documentos.
        """
        try:
            # Parâmetros de filtro para o banco de dados
            filters = {}
            if time_filter:
                # Formata a data para o formato ISO esperado pelo banco de dados
                if isinstance(time_filter, datetime):
                    time_filter = time_filter.isoformat()
                filters['created_after'] = time_filter
            
            # Buscar documentos com filtro de tempo, se aplicável
            result = await self.db.get_fiscal_documents(page=1, page_size=10000, **filters)
            documents = result.items

            # Processar e resumir os documentos
            summary = {
                'total_documents': len(documents),
                'by_type': {},
                'by_issuer': {},
                'total_value': 0.0,
                'documents': []
            }

            for doc in documents:
                # Categorização melhorada baseada no document_type e extracted_data
                doc_type = self._categorize_document(doc)
                summary['by_type'][doc_type] = summary['by_type'].get(doc_type, 0) + 1

                # Contagem por emissor
                issuer = doc.get('issuer_cnpj', 'Desconhecido')
                summary['by_issuer'][issuer] = summary['by_issuer'].get(issuer, 0) + 1

                # Extrair valor total se disponível
                try:
                    if doc.get('extracted_data'):
                        data = doc['extracted_data']
                        if isinstance(data, str):
                            data = json.loads(data)

                        if isinstance(data, dict):
                            total = data.get('total', data.get('valor_total', data.get('value', 0)))
                            if total:
                                summary['total_value'] += float(total)
                except (ValueError, TypeError, json.JSONDecodeError):
                    pass

                # Adicionar documento à lista com categorização
                summary['documents'].append({
                    'id': doc['id'],
                    'file_name': doc.get('file_name', 'Sem nome'),
                    'document_type': doc.get('document_type', 'N/A'),
                    'categorized_type': doc_type,
                    'issuer_cnpj': issuer,
                    'created_at': doc.get('created_at'),
                    'validation_status': doc.get('validation_status', 'não validado')
                })

            return summary

        except Exception as e:
            logger.error(f"Erro ao resumir todos os documentos: {e}")
            return {
                'total_documents': 0,
                'by_type': {},
                'by_issuer': {},
                'total_value': 0.0,
                'documents': []
            }

    def _categorize_document(self, doc: Dict[str, Any]) -> str:
        """Categoriza um documento baseado em múltiplas fontes de informação."""
        # Primeiro, tentar usar o document_type se estiver preenchido
        doc_type = doc.get('document_type', '').upper()

        if doc_type and doc_type != 'N/A':
            # Normalizar tipos comuns
            type_mapping = {
                'NFE': 'NF-e',
                'NF-E': 'NF-e',
                'NF_E': 'NF-e',
                'NFC': 'NFC-e',
                'NFC-E': 'NFC-e',
                'NFC_E': 'NFC-e',
                'CTE': 'CT-e',
                'CT-E': 'CT-e',
                'CT_E': 'CT-e',
                'MDFE': 'MDF-e',
                'MDF-E': 'MDF-e',
                'MDF_E': 'MDF-e',
                'NFSE': 'NFSe',
                'NFS-E': 'NFSe',
                'NFS_E': 'NFSe'
            }
            return type_mapping.get(doc_type, doc_type)

        # Se document_type estiver vazio, tentar extrair dos dados extraídos
        if doc.get('extracted_data'):
            try:
                data = doc['extracted_data']
                if isinstance(data, str):
                    data = json.loads(data)

                if isinstance(data, dict):
                    # Verificar campos que indicam o tipo
                    tipo_nf = data.get('tipo_nf', data.get('tipo', '')).upper()
                    if tipo_nf:
                        if '55' in tipo_nf or 'NFE' in tipo_nf:
                            return 'NF-e'
                        elif '65' in tipo_nf or 'NFC' in tipo_nf:
                            return 'NFC-e'
                        elif '57' in tipo_nf or 'CTE' in tipo_nf:
                            return 'CT-e'

                    # Verificar modelo da nota
                    modelo = str(data.get('modelo', data.get('mod', '')))
                    if modelo == '55':
                        return 'NF-e'
                    elif modelo == '65':
                        return 'NFC-e'
                    elif modelo == '57':
                        return 'CT-e'

            except (json.JSONDecodeError, AttributeError):
                pass

        # Tentar extrair do nome do arquivo
        file_name = doc.get('file_name', '').upper()
        if 'NFE' in file_name or 'NF-E' in file_name or 'NOTA' in file_name:
            return 'NF-e'
        elif 'NFC' in file_name or 'NFC-E' in file_name:
            return 'NFC-e'
        elif 'CTE' in file_name or 'CT-E' in file_name or 'CONHECIMENTO' in file_name:
            return 'CT-e'
        elif 'MDF' in file_name or 'MDF-E' in file_name or 'MANIFESTO' in file_name:
            return 'MDF-e'
        elif 'NFS' in file_name or 'NFSE' in file_name or 'SERVIC' in file_name:
            return 'NFSe'

        return 'Desconhecido'

    async def search_documents(self, query: str, limit: int = 5) -> List[Dict]:
        """Busca documentos relevantes usando busca inteligente por texto."""
        try:
            # Use PostgreSQL direct search instead of Supabase API
            # This is a simplified version - for full text search, consider using PostgreSQL full-text search
            result = await self.db.get_fiscal_documents(page=1, page_size=limit)
            documents = result.items

            # Filter documents based on query
            filtered_docs = []
            query_lower = query.lower()

            for doc in documents:
                # Search in multiple fields
                search_fields = [
                    doc.get('file_name', ''),
                    doc.get('document_type', ''),
                    doc.get('document_number', ''),
                    doc.get('issuer_cnpj', ''),
                    doc.get('issuer_name', ''),
                    str(doc.get('extracted_data', '')),
                ]

                if any(query_lower in field.lower() for field in search_fields):
                    filtered_docs.append(doc)

                if len(filtered_docs) >= limit:
                    break

            return filtered_docs

        except Exception as e:
            logger.error(f"Erro na busca de documentos: {e}")
            return []
