"""Utilitários para processamento de documentos no importador."""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Configuração do logger
logger = logging.getLogger(__name__)


def process_single_file(uploaded_file, storage, tmp_dir: Path, prepare_doc_func, validate_doc_func):
    """Processa um único arquivo e retorna o resultado.
    
    Args:
        uploaded_file: Arquivo carregado pelo usuário
        storage: Instância do armazenamento
        tmp_dir: Diretório temporário para salvar o arquivo
        
    Returns:
        dict: Dicionário com os resultados do processamento
    """
    from backend.agents import coordinator
    # Importação adiada para evitar circular
# As funções _prepare_document_record e _validate_document_data serão passadas como parâmetro
    from backend.tools.ocr_processor import ocr_text_to_document
    import streamlit as st
    import json
    
    result = {
        'file_name': uploaded_file.name,
        'success': False,
        'error': None,
        'document_id': None,
        'document_type': None,
        'validation_status': 'error'
    }
    
    try:
        # Salvar arquivo temporariamente
        dest = tmp_dir / uploaded_file.name
        with open(dest, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        file_type = dest.suffix.lower()
        
        # Processar o arquivo com base no tipo
        if file_type == '.xml':
            parsed = coordinator.run_task('extract', {'path': str(dest)})
            
            if not validate_doc_func(parsed):
                result['error'] = 'Dados inválidos após extração do XML'
                return result
                
            # Classificar o documento
            classification = coordinator.run_task('classify', {'parsed': parsed})
            record = prepare_doc_func(uploaded_file, parsed, classification)
            
        else:  # PDF/Image
            parsed = coordinator.run_task('extract', {'path': str(dest)})
            
            if isinstance(parsed, dict) and parsed.get('error'):
                result['error'] = f"Erro na extração: {parsed.get('message', 'Erro desconhecido')}"
                return result
                
            raw_text = parsed.get('raw_text', '').strip()
            if not raw_text:
                result['error'] = 'Nenhum texto foi extraído do documento.'
                return result
                
            # Processar com IA para extração estruturada
            extracted_data = ocr_text_to_document(raw_text, use_llm=True)
            if not isinstance(extracted_data, dict):
                result['error'] = 'Falha ao extrair dados estruturados do documento.'
                return result
                
            extracted_data['raw_text'] = raw_text
            classification = coordinator.run_task('classify', {'parsed': extracted_data})
            record = prepare_doc_func(uploaded_file, extracted_data, classification)
        
        # Salvar o documento
        saved = storage.save_fiscal_document(record)
        
        # Extrair o ID do documento salvo
        if hasattr(saved, 'get') and 'id' in saved:
            document_id = saved['id']
            result['document_id'] = document_id
            result['document_type'] = record.get('document_type')
            result['validation_status'] = record.get('validation_status', 'pending')
            result['success'] = True
            
            # Processar com RAG se disponível
            if 'rag_service' in st.session_state and st.session_state.rag_service:
                try:
                    import asyncio
                    
                    async def process_rag():
                        doc_for_rag = storage.get_fiscal_documents(id=document_id, page=1, page_size=1)
                        if doc_for_rag and hasattr(doc_for_rag, 'items') and doc_for_rag.items:
                            return await st.session_state.rag_service.process_document_for_rag(doc_for_rag.items[0])
                        return {'success': False, 'error': 'Documento não encontrado para processamento RAG'}
                    
                    # Executar processamento RAG em segundo plano
                    asyncio.create_task(process_rag())
                    
                except Exception as rag_error:
                    logger.error(f"Erro ao agendar processamento RAG: {rag_error}")
        
    except Exception as e:
        result['error'] = str(e)
        logger.error(f"Erro ao processar {uploaded_file.name}: {str(e)}")
        
    finally:
        # Limpar arquivo temporário
        try:
            if 'dest' in locals() and dest.exists():
                dest.unlink()
        except Exception as e:
            logger.warning(f"Não foi possível remover arquivo temporário {dest}: {e}")
    
    return result


def display_import_results(results):
    """Exibe os resultados da importação em lote."""
    import streamlit as st
    
    st.markdown("---")
    st.subheader("📊 Resumo da Importação em Lote")
    
    total = len(results)
    success = sum(1 for r in results if r['success'])
    failed = total - success
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total de Arquivos", total)
    
    success_percent = (success/total*100) if total > 0 else 0
    col2.metric("Processados com Sucesso", f"{success} ({success_percent:.1f}%)")
    
    failed_percent = (failed/total*100) if total > 0 else 0
    col3.metric("Falhas", f"{failed} ({failed_percent:.1f}%)")
    
    # Mostrar detalhes das falhas
    if failed > 0:
        with st.expander("📋 Detalhes das Falhas", expanded=False):
            for result in results:
                if not result['success']:
                    st.error(f"**{result['file_name']}**: {result.get('error', 'Erro desconhecido')}")
    
    # Mostrar resumo dos sucessos
    if success > 0:
        with st.expander("✅ Documentos Importados", expanded=False):
            for result in results:
                if result['success']:
                    doc_type = result['document_type'] or 'Tipo não identificado'
                    doc_id = result['document_id']
                    st.success(f"**{result['file_name']}**: {doc_type} - ID: {doc_id}")


def process_directory(directory_path: str) -> list:
    """
    Processa todos os arquivos de um diretório local.
    
    Args:
        directory_path: Caminho para o diretório contendo os arquivos
        
    Returns:
        list: Lista de objetos de arquivo simulados para upload
    """
    import os
    from pathlib import Path
    from io import BytesIO
    from streamlit.runtime.uploaded_file_manager import UploadedFile
    
    allowed_extensions = {'.xml', '.pdf', '.png', '.jpg', '.jpeg'}
    uploaded_files = []
    
    for file_path in Path(directory_path).iterdir():
        if file_path.is_file() and file_path.suffix.lower() in allowed_extensions:
            try:
                with open(file_path, 'rb') as f:
                    file_data = f.read()
                    
                    # Criar objeto similar ao retornado pelo file_uploader
                    uploaded_file = UploadedFile(
                        file=BytesIO(file_data),
                        name=file_path.name,
                        type=f"application/{file_path.suffix[1:]}",  # tipo MIME aproximado
                        size=len(file_data)
                    )
                    uploaded_files.append(uploaded_file)
                    
            except Exception as e:
                logger.error(f"Erro ao ler arquivo {file_path}: {str(e)}")
    
    return uploaded_files
