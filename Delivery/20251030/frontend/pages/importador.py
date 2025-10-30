"""Importador page for processing XML/PDF/image files."""
import json
import logging
import streamlit as st
from pathlib import Path
from datetime import datetime
import re
from zoneinfo import ZoneInfo
from typing import List, Dict, Any, Optional
from decimal import Decimal
import concurrent.futures

# Expressão regular para formatos ISO básicos (YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SSZ)
ISO_DATE_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}:\d{2}(?:Z|[+-]\d{2}:?\d{2})?)?$"
)


def convert_date_to_iso(date_value: Optional[Any]) -> Optional[str]:
    """Converte datas comuns (DD/MM/YYYY, DD/MM/YY) para ISO 8601.

    Mantém strings já em formato ISO e lida com objetos datetime.
    """

    if date_value is None:
        return None

    if isinstance(date_value, datetime):
        # Normaliza para UTC sem frações
        return date_value.strftime('%Y-%m-%dT%H:%M:%SZ')

    date_str = str(date_value).strip()
    if not date_str:
        return None

    # Mantém formatos ISO (YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SSZ)
    if ISO_DATE_PATTERN.match(date_str):
        # Normaliza espaços para 'T'
        return date_str.replace(' ', 'T')

    if '/' in date_str:
        parts = date_str.split('/')
        if len(parts) == 3:
            day, month, year_part = parts
            if not (day.isdigit() and month.isdigit()):
                return None

            year_part = year_part.strip()
            if len(year_part) == 2 and year_part.isdigit():
                year = int(year_part)
                year += 1900 if year >= 70 else 2000
            elif len(year_part) == 4 and year_part.isdigit():
                year = int(year_part)
            else:
                return None

            try:
                dt = datetime(year, int(month), int(day))
                return dt.strftime('%Y-%m-%dT00:00:00Z')
            except ValueError:
                return None

    return None


# Importações locais
from backend.agents import coordinator
from backend.tools.ocr_processor import ocr_text_to_document
from backend.database.storage_manager import storage_manager as storage
from .importador_utils import process_single_file, display_import_results, process_directory

# Configuração do logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('importador.log')
    ]
)


def _validate_document_data(data: any) -> bool:
    """Valida se os dados extraídos estão no formato esperado."""
    if not isinstance(data, dict):
        st.error(f"Erro: Dados em formato inválido. Esperado dicionário, obtido {type(data).__name__}")
        return False

    required_fields = ['emitente', 'itens', 'total']
    missing = [field for field in required_fields if field not in data]
    if missing:
        st.error(f"Erro: Campos obrigatórios ausentes: {', '.join(missing)}")
        return False

    if not isinstance(data.get('itens'), list):
        st.error("Erro: O campo 'itens' deve ser uma lista")
        return False

    return True

def _to_float(value: Any) -> float:
    """Converte diferentes formatos numéricos para float."""
    if value is None:
        return 0.0

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        clean = value.strip().replace('R$', '').replace(' ', '')
        if not clean:
            return 0.0
        if ',' in clean and '.' in clean:
            clean = clean.replace('.', '').replace(',', '.')
        elif ',' in clean:
            clean = clean.replace(',', '.')
        try:
            return float(clean)
        except ValueError:
            return 0.0

    return 0.0

def _prepare_document_record(uploaded, parsed, classification=None) -> dict:
    """Prepara o registro do documento para ser salvo."""
    if not isinstance(parsed, dict):
        raise ValueError("Dados do documento devem ser um dicionário")

    # Extrair dados de validação da classificação, se disponível
    validation = {}
    if classification and isinstance(classification, dict):
        validation = classification.get('validacao', {})

    # Obter o status de validação ou definir como 'pending' se não houver
    validation_status = validation.get('status', 'pending')

    # Extrair dados do emitente
    emitente = parsed.get('emitente') or {}

    # Extrair dados do destinatário, se disponível
    destinatario = parsed.get('destinatario') or {}

    # Extrair dados de itens, se disponível
    itens = parsed.get('itens') or []

    # Extrair totais, se disponível
    totais = parsed.get('totals') or {}

    # Preparar dados do documento
    doc_data = {
        'file_name': str(uploaded.name if hasattr(uploaded, 'name') else 'documento_sem_nome.pdf'),
        'document_type': parsed.get('document_type', 'CTe' if 'cte' in str(uploaded.name).lower() else 'NFe'),
        'document_number': parsed.get('numero') or parsed.get('nNF') or parsed.get('nCT'),
        'issuer_cnpj': emitente.get('cnpj') or emitente.get('CNPJ'),
        'issuer_name': emitente.get('razao_social') or emitente.get('nome') or emitente.get('xNome', ''),
        'recipient_cnpj': (
            destinatario.get('cnpj')
            or destinatario.get('cnpj_cpf')
            or destinatario.get('CNPJ')
            or destinatario.get('CPF')
        ),
        'recipient_name': destinatario.get('razao_social') or destinatario.get('nome') or destinatario.get('xNome', ''),
        'issue_date': convert_date_to_iso(parsed.get('data_emissao') or parsed.get('dhEmi')),
        'total_value': _to_float(parsed.get('total') or totais.get('valorTotal') or 0.0),
        'cfop': parsed.get('cfop') or (itens[0].get('cfop') if itens else None),
        'extracted_data': parsed,
        'validation_status': validation_status,
        'validation_details': {
            'issues': validation.get('issues', []),
            'warnings': validation.get('warnings', []),
            'validations': validation.get('validations', {})
        },
        'classification': classification or {},
        'raw_text': parsed.get('raw_text', ''),
        'uploaded_at': datetime.now(ZoneInfo('UTC')).isoformat(),
        'processed_at': datetime.now(ZoneInfo('UTC')).isoformat(),
        # Adiciona metadados adicionais para facilitar buscas
        'metadata': {
            'has_issues': len(validation.get('issues', [])) > 0,
            'has_warnings': len(validation.get('warnings', [])) > 0,
            'item_count': len(itens),
            'document_subtype': parsed.get('tipoDocumento') or 'Outros'
        }
    }

    # Garante que todos os campos necessários tenham valores padrão
    doc_data['document_type'] = doc_data.get('document_type') or 'Outros'
    doc_data['document_number'] = doc_data.get('document_number') or 'SEM_NUMERO'
    doc_data['issuer_cnpj'] = (doc_data.get('issuer_cnpj') or '').strip() or '00000000000000'
    doc_data['issuer_name'] = (doc_data.get('issuer_name') or '').strip() or 'Emitente não identificado'
    doc_data['recipient_cnpj'] = (doc_data.get('recipient_cnpj') or '').strip() or None
    doc_data['recipient_name'] = (doc_data.get('recipient_name') or '').strip() or None
    doc_data['total_value'] = doc_data.get('total_value') or 0.0

    # Normaliza issue_date vazia como None
    doc_data['issue_date'] = doc_data.get('issue_date') or None

    return doc_data

def render(storage):
    """Render the importador page."""
    st.header('📥 Importador de Documentos Fiscais')
    st.caption('Inteligência artificial para processamento automático de documentos fiscais')

    # Informações sobre tipos de arquivo suportados
    with st.expander('📋 Tipos de arquivo suportados', expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **Documentos Estruturados:**
            - **XML**: NF-e, NFC-e, CT-e, MDF-e
            - Extração automática de campos
            - Validação fiscal completa
            """)

        with col2:
            st.markdown("""
            **Documentos Digitais:**
            - **PDF**: Documentos escaneados
            - **JPG/PNG**: Imagens de documentos
            - OCR com IA para extração
            """)

    # Área de upload com melhor visual
    st.markdown("---")
    st.markdown("### 📄 Upload de Documentos")
    st.info("""
**Atenção:** Para substituir arquivos enviados, remova manualmente os arquivos antigos clicando no **'X'** ao lado do nome do arquivo antes de fazer um novo upload. 

*Esta é uma limitação do componente de upload do Streamlit: não é possível limpar a lista de arquivos via código.*
""")

    # Botão para limpar todos os uploads (troca a chave do file_uploader)
    if 'uploader_key' not in st.session_state:
        st.session_state.uploader_key = 0
    clear_uploads = st.button('🗑️ Limpar uploads')
    if clear_uploads:
        st.session_state.uploader_key += 1

    # Upload múltiplo de arquivos
    # Upload múltiplo de arquivos
    uploaded_files = st.file_uploader(
        'Arraste ou selecione um ou mais arquivos',
        type=['xml', 'pdf', 'png', 'jpg', 'jpeg'],
        help='Selecione um ou mais documentos fiscais para processamento em lote.',
        accept_multiple_files=True,
        key=f'document_uploader_{st.session_state.uploader_key}'
    )
    if uploaded_files and len(uploaded_files) > 0:
        st.warning('Para fazer novo upload, limpe os arquivos atuais.')

    
    # Opção para selecionar diretório (apenas para execução local)
    process_dir = st.checkbox('Processar diretório local (apenas para desenvolvimento)')
    dir_path = ''
    
    if process_dir:
        dir_path = st.text_input('Caminho do diretório (ex: /caminho/para/documentos)')
    
    # Botão para processar diretório
    process_dir_btn = st.button('Processar Diretório') if process_dir and dir_path else False
    
    # Se não há arquivos carregados e não foi solicitado processamento de diretório
    if not uploaded_files and not process_dir_btn:
        st.info('👆 Selecione um ou mais arquivos ou um diretório para começar o processamento automático.')
        
        # Mostrar dicas sobre o processamento em lote
        with st.expander("💡 Dicas para processamento em lote", expanded=False):
            st.markdown("""
            - **Arquivos suportados**: XML, PDF, JPG, PNG
            - **Tamanho máximo por arquivo**: 200MB
            - **Processamento em paralelo**: Até 4 arquivos simultaneamente
            - **Relatório de erros**: Um resumo é exibido ao final
            - **Arquivos com problemas**: São ignorados, permitindo que os demais sejam processados
            """)
            
        # Seção para processar documentos existentes
        st.markdown("---")
        st.markdown("### 🧠 Processar Documentos Existentes")
        st.markdown("""
        **O que acontece após o upload:**
        1. 🔍 **Extração**: IA extrai dados automaticamente
        2. 🏷️ **Classificação**: Identifica tipo e validade
        3. ✅ **Validação**: Verifica conformidade fiscal
        4. 💾 **Armazenamento**: Salva com embeddings para busca
        """)

        # Seção para processar documentos existentes
        st.markdown("---")
        st.markdown("### 🧠 Processar Documentos Existentes")

        col1, col2 = st.columns(2)

        with col1:
            if st.button('🔄 Processar Todos os Documentos para RAG',
                        help='Processa todos os documentos salvos que ainda não têm embeddings',
                        type='secondary'):
                if 'rag_service' in st.session_state and st.session_state.rag_service:
                    with st.spinner('🔄 Processando todos os documentos para busca inteligente...'):
                        try:
                            import asyncio

                            # Buscar documentos que não foram processados pelo RAG
                            all_docs = storage.get_fiscal_documents(page=1, page_size=1000)
                            docs_to_process = []

                            if hasattr(all_docs, 'items'):
                                for doc in all_docs.items:
                                    # Verificar se o documento já tem embeddings
                                    if doc.get('embedding_status') != 'completed':
                                        docs_to_process.append(doc)

                            if docs_to_process:
                                st.info(f'📋 Encontrados {len(docs_to_process)} documentos para processar')

                                async def process_all_rag():
                                    results = []
                                    for doc in docs_to_process:
                                        try:
                                            result = await st.session_state.rag_service.process_document_for_rag(doc)
                                            results.append((doc['id'], result))
                                        except Exception as e:
                                            results.append((doc['id'], {'success': False, 'error': str(e)}))
                                    return results

                                # Processar em background
                                rag_results = asyncio.run(process_all_rag())

                                # Mostrar resultados
                                success_count = sum(1 for _, result in rag_results if result.get('success', False))
                                error_count = len(rag_results) - success_count

                                if success_count > 0:
                                    st.success(f'✅ {success_count} documentos processados com sucesso!')
                                if error_count > 0:
                                    st.warning(f'⚠️ {error_count} documentos tiveram problemas no processamento')

                                # Detalhes dos resultados
                                with st.expander('📊 Detalhes do Processamento', expanded=False):
                                    for doc_id, result in rag_results:
                                        if result.get('success', False):
                                            chunks = result.get('chunks_processed', 0)
                                            st.success(f'✅ Documento {doc_id}: {chunks} chunks criados')
                                        else:
                                            error = result.get('error', 'Erro desconhecido')
                                            st.error(f'❌ Documento {doc_id}: {error}')

                            else:
                                st.info('ℹ️ Todos os documentos já estão processados para busca inteligente!')

                        except Exception as e:
                            st.error(f'Erro no processamento em lote: {str(e)}')
                else:
                    st.error('❌ Sistema RAG não disponível. Reinicie a aplicação.')

        with col2:
            if st.button('📈 Verificar Status do RAG',
                        help='Mostra estatísticas do sistema RAG',
                        type='secondary'):
                if 'rag_service' in st.session_state and st.session_state.rag_service:
                    try:
                        stats = st.session_state.rag_service.get_embedding_statistics()

                        if 'error' not in stats:
                            st.markdown("**📊 Estatísticas do Sistema RAG:**")
                            col1, col2, col3 = st.columns(3)

                            with col1:
                                st.metric("Total de Chunks", f"{stats.get('total_chunks', 0):,}")
                            with col2:
                                st.metric("Documentos com Embeddings", f"{stats.get('documents_with_embeddings', 0):,}")
                            with col3:
                                st.metric("Total de Insights", f"{stats.get('total_insights', 0):,}")

                            # Status dos embeddings
                            status_dist = stats.get('embedding_status_distribution', {})
                            if status_dist:
                                with st.expander('📋 Status dos Embeddings', expanded=False):
                                    for status, count in status_dist.items():
                                        if status == 'completed':
                                            st.success(f'✅ {status.title()}: {count} documentos')
                                        elif status == 'failed':
                                            st.error(f'❌ {status.title()}: {count} documentos')
                                        else:
                                            st.info(f'⏳ {status.title()}: {count} documentos')
                        else:
                            st.error(f"Erro ao carregar estatísticas: {stats['error']}")

                    except Exception as e:
                        st.error(f'Erro ao carregar estatísticas: {str(e)}')
                else:
                    st.error('❌ Sistema RAG não disponível')

        return

        # Processar diretório se solicitado
    if process_dir_btn and dir_path:
        try:
            uploaded_files = process_directory(dir_path)
            if not uploaded_files:
                st.warning("Nenhum arquivo compatível encontrado no diretório.")
                return
            st.success(f"{len(uploaded_files)} arquivos encontrados no diretório.")
        except Exception as e:
            st.error(f"Erro ao acessar diretório: {str(e)}")
            return
    
    # Se não há arquivos para processar, retorna
    if not uploaded_files:
        return
        
    # Criar diretório temporário
    tmp_dir = Path('tmp_upload')
    tmp_dir.mkdir(exist_ok=True, parents=True)
    
    # Processar múltiplos arquivos
    if len(uploaded_files) > 1:
        with st.spinner(f'Processando {len(uploaded_files)} arquivos...'):
            # Usar ThreadPoolExecutor para processar arquivos em paralelo
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                # Iniciar processamento de todos os arquivos
                future_to_file = {
                    executor.submit(
                        process_single_file, 
                        file, 
                        storage, 
                        tmp_dir,
                        _prepare_document_record,  # Passando a função como parâmetro
                        _validate_document_data    # Passando a função como parâmetro
                    ): file 
                    for file in uploaded_files
                }
                
                # Coletar resultados conforme são concluídos
                results = []
                rag_tasks = []
                progress_bar = st.progress(0)
                
                for i, future in enumerate(concurrent.futures.as_completed(future_to_file)):
                    try:
                        result = future.result()
                        results.append(result)
                        
                        # Se o documento foi salvo com sucesso e o RAG está disponível
                        if result.get('success') and 'rag_service' in st.session_state and st.session_state.rag_service:
                            document_id = result.get('document_id')
                            if document_id:
                                # Criar uma tarefa RAG para ser executada após o processamento
                                async def process_rag_task(doc_id):
                                    try:
                                        doc_for_rag = storage.get_fiscal_documents(id=doc_id, page=1, page_size=1)
                                        if doc_for_rag and hasattr(doc_for_rag, 'items') and doc_for_rag.items:
                                            return await st.session_state.rag_service.process_document_for_rag(doc_for_rag.items[0])
                                        return {'success': False, 'error': 'Documento não encontrado para processamento RAG'}
                                    except Exception as e:
                                        logger.error(f"Erro no processamento RAG para documento {doc_id}: {e}")
                                        return {'success': False, 'error': str(e)}
                                
                                # Adicionar a tarefa à lista
                                rag_tasks.append(process_rag_task(document_id))
                                
                    except Exception as e:
                        file = future_to_file[future]
                        results.append({
                            'file_name': file.name,
                            'success': False,
                            'error': str(e),
                            'document_id': None,
                            'document_type': None,
                            'validation_status': 'error'
                        })
                    
                    # Atualizar barra de progresso
                    progress = (i + 1) / len(uploaded_files)
                    progress_bar.progress(progress)
            
                # Executar tarefas RAG em paralelo, se houver
                if rag_tasks:
                    with st.spinner('Processando documentos para busca semântica...'):
                        import asyncio
                        
                        # Criar um novo loop de eventos para executar as tarefas RAG
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        
                        try:
                            # Executar todas as tarefas RAG em paralelo
                            rag_results = loop.run_until_complete(asyncio.gather(*rag_tasks, return_exceptions=True))
                            
                            # Atualizar status dos documentos processados pelo RAG
                            for i, rag_result in enumerate(rag_results):
                                if isinstance(rag_result, dict) and 'success' in rag_result:
                                    if rag_result['success']:
                                        logger.info(f"Documento {i+1} processado com sucesso pelo RAG")
                                    else:
                                        logger.warning(f"Falha ao processar documento {i+1} no RAG: {rag_result.get('error', 'Erro desconhecido')}")
                                else:
                                    logger.error(f"Erro inesperado ao processar documento {i+1} no RAG: {rag_result}")
                            
                        except Exception as e:
                            logger.error(f"Erro ao executar processamento RAG em lote: {e}")
                        finally:
                            loop.close()
            
            # Exibir resultados
            display_import_results(results)
            
            # Limpar diretório temporário
            try:
                for file in tmp_dir.glob('*'):
                    file.unlink()
                tmp_dir.rmdir()
            except Exception as e:
                logger.warning(f"Não foi possível limpar diretório temporário: {e}")
                
            return
    
    # Processar arquivo único (comportamento original)
    uploaded = uploaded_files[0]
    
    # Salvar arquivo temporariamente
    dest = tmp_dir / uploaded.name
    
    try:
        with open(dest, 'wb') as f:
            f.write(uploaded.getbuffer())
    except Exception as e:
        st.error(f'Erro ao salvar arquivo temporário: {str(e)}')
        return

    file_type = dest.suffix.lower()

    with st.spinner(f'Processando {file_type.upper()}...'):
        try:
            # Extract data based on file type
            if file_type == '.xml':
                parsed = coordinator.run_task('extract', {'path': str(dest)})

                if not _validate_document_data(parsed):
                    return

                st.subheader('✅ Dados extraídos')
                with st.expander('Visualizar dados extraídos', expanded=False):
                    st.json(parsed)

                # Classify document
                with st.spinner('Classificando documento...'):
                    classification = coordinator.run_task('classify', {'parsed': parsed})
                    st.subheader('🏷️ Classificação')
                    st.json(classification)

                # Exibir resultados da validação
                validation = classification.get('validacao', {})

                # Mostrar status da validação
                status = validation.get('status', 'unknown')
                status_emoji = {
                    'success': '✅',
                    'warning': '⚠️',
                    'error': '❌',
                    'pending': '⏳'
                }.get(status, '❓')

                st.subheader(f'{status_emoji} Status da Validação: {status.upper()}')

                # Mostrar problemas e avisos
                col1, col2 = st.columns(2)

                with col1:
                    if validation.get('issues'):
                        with st.expander(f'❌ {len(validation["issues"])} Problemas Encontrados', expanded=True):
                            for issue in validation['issues']:
                                st.error(issue)
                    else:
                        st.success('✅ Nenhum problema crítico encontrado')

                with col2:
                    if validation.get('warnings'):
                        with st.expander(f'⚠️ {len(validation["warnings"])} Avisos', expanded=False):
                            for warning in validation['warnings']:
                                st.warning(warning)
                    else:
                        st.info('ℹ️ Nenhum aviso')

                # Mostrar detalhes da validação
                with st.expander('🔍 Detalhes da Validação', expanded=False):
                    validations = validation.get('validations', {})

                    # Validação do Emitente
                    if 'emitente' in validations:
                        st.subheader('Emitente')
                        emit = validations['emitente']
                        cols = st.columns(2)
                        cols[0].metric("CNPJ Válido", "✅ Sim" if emit.get('cnpj') else "❌ Não")
                        cols[1].metric("Razão Social", "✅ Informada" if emit.get('razao_social') else "⚠️ Ausente")

                    # Validação de Itens
                    if 'itens' in validations:
                        st.subheader('Itens')
                        itens = validations['itens']
                        cols = st.columns(2)
                        cols[0].metric("Itens Encontrados",
                                    f"✅ {len(parsed.get('itens', []))}" if itens.get('has_items') else "❌ Nenhum")
                        cols[1].metric("Itens Válidos",
                                    "✅ Todos" if itens.get('all_valid') else "⚠️ Alguns itens inválidos")

                    # Validação de Totais
                    if 'totals' in validations:
                        st.subheader('Totais')
                        totais = validations['totals']
                        if totais.get('valid') is not None:
                            if totais['valid']:
                                st.success("✅ Soma dos itens confere com o total do documento")
                            else:
                                st.error(f"❌ Diferença de R$ {abs(totais.get('document_total', 0) - totais.get('calculated_total', 0)):.2f} nos totais")

                # Preparar e salvar o documento
                try:
                    record = _prepare_document_record(uploaded, parsed, classification)
                    saved = storage.save_fiscal_document(record)

                    # Debug: Exibir a estrutura da resposta salva
                    logger.info(f"Resposta do save_document: {saved}")

                    # Função auxiliar para extrair ID de forma robusta
                    def extract_document_id(response):
                        """Extrai o ID do documento da resposta de forma robusta."""
                        if not response:
                            return None

                        # Se for um dicionário
                        if isinstance(response, dict):
                            # Tenta chaves comuns
                            for key in ['id', 'ID', 'document_id', 'doc_id', 'fiscal_document_id']:
                                if key in response and response[key]:
                                    return str(response[key]).strip()

                            # Tenta em estruturas aninhadas
                            if 'data' in response and isinstance(response['data'], dict):
                                for key in ['id', 'ID', 'document_id', 'doc_id', 'fiscal_document_id']:
                                    if key in response['data'] and response['data'][key]:
                                        return str(response['data'][key]).strip()

                            # Se data for uma lista
                            if 'data' in response and isinstance(response['data'], list) and response['data']:
                                first_item = response['data'][0]
                                if isinstance(first_item, dict):
                                    for key in ['id', 'ID', 'document_id', 'doc_id', 'fiscal_document_id']:
                                        if key in first_item and first_item[key]:
                                            return str(first_item[key]).strip()

                        # Se for uma lista
                        elif isinstance(response, list) and response:
                            first_item = response[0]
                            if isinstance(first_item, dict):
                                for key in ['id', 'ID', 'document_id', 'doc_id', 'fiscal_document_id']:
                                    if key in first_item and first_item[key]:
                                        return str(first_item[key]).strip()

                        return None

                    # Extrai o ID usando a função auxiliar
                    document_id = extract_document_id(saved)
                    logger.info(f"ID do documento obtido: {document_id}")

                    # RAG Processing - Processar documento automaticamente para RAG
                    if document_id:
                        try:
                            # Buscar o documento completo do banco para o RAG
                            full_document = storage.get_fiscal_documents(
                                id=document_id,
                                page=1,
                                page_size=1
                            )

                            if full_document and hasattr(full_document, 'items') and full_document.items:
                                doc_for_rag = full_document.items[0]

                                # Chamar RAG service em background
                                with st.spinner('🧠 Processando documento para busca inteligente...'):
                                    # Usar o RAG service da sessão se disponível
                                    if 'rag_service' in st.session_state and st.session_state.rag_service:
                                        import asyncio

                                        # Executar processamento RAG em background
                                        async def process_rag():
                                            try:
                                                result = await st.session_state.rag_service.process_document_for_rag(doc_for_rag)
                                                return result
                                            except Exception as rag_error:
                                                logger.error(f"Erro no processamento RAG: {rag_error}")
                                                return {'success': False, 'error': str(rag_error)}

                                        # Executar a função assíncrona
                                        rag_result = asyncio.run(process_rag())

                                        if rag_result.get('success', False):
                                            chunks_count = rag_result.get('chunks_processed', 0)
                                            st.success(f'✅ Documento processado para busca inteligente! ({chunks_count} chunks criados)')
                                            logger.info(f"RAG processing completed for document {document_id}: {chunks_count} chunks")
                                        else:
                                            error_msg = rag_result.get('error', 'Erro desconhecido')
                                            st.warning(f'⚠️ Documento salvo, mas houve um problema no processamento inteligente: {error_msg}')
                                            logger.error(f"RAG processing failed for document {document_id}: {error_msg}")
                                    else:
                                        st.info('ℹ️ Sistema RAG não disponível no momento. Documento salvo sem processamento inteligente.')
                                        logger.warning(f"RAG service not available for document {document_id}")
                            else:
                                st.warning('⚠️ Não foi possível recuperar o documento completo para processamento RAG')
                                logger.warning(f"Could not retrieve full document for RAG processing: {document_id}")

                        except Exception as rag_error:
                            st.warning(f'⚠️ Erro no processamento inteligente: {str(rag_error)}')
                            logger.error(f"RAG processing error for document {document_id}: {rag_error}")

                    # Se não conseguiu obter o ID do documento
                    elif not document_id:
                        logger.warning('Documento salvo, mas não foi possível obter o ID para processamento RAG.')
                        logger.warning(f'Resposta completa do save_document: {saved}')

                    # Debug: Exibir o ID do documento salvo
                    if document_id:
                        st.info(f'📄 **ID do documento:** `{document_id}`')
                    else:
                        st.warning('⚠️ Não foi possível obter o ID do documento salvo. Verifique os logs para mais detalhes.')

                    # Mostrar resumo do processamento
                    with st.expander('📊 Resumo do Processamento', expanded=False):
                        col1, col2 = st.columns(2)

                        with col1:
                            total_value = _to_float(record.get('total_value', 0))
                            st.markdown(f"""
                            **Informações Extraídas:**
                            - **Tipo:** {record.get('document_type', 'N/A')}
                            - **Número:** {record.get('document_number', 'N/A')}
                            - **Valor:** R$ {total_value:.2f}
                            """)

                        with col2:
                            validation_status = record.get('validation_status', 'pending')
                            status_icon = {'success': '✅', 'warning': '⚠️', 'error': '❌', 'pending': '⏳'}.get(validation_status, '❓')
                            st.markdown(f"""
                            **Status da Validação:**
                            - **Status:** {status_icon} {validation_status.upper()}
                            - **Itens:** {len(record.get('extracted_data', {}).get('itens', []))}
                            - **Processado:** {datetime.now().strftime('%d/%m/%Y %H:%M')}
                            """)

                except Exception as e:
                    st.error(f'Erro ao salvar documento: {str(e)}')
                    st.exception(e)  # Show full traceback in logs

            else:  # PDF/Image
                st.info('Processando documento não-XML via OCR...')
                parsed = coordinator.run_task('extract', {'path': str(dest)})

                # Tratamento de erros com mensagens claras
                if isinstance(parsed, dict) and parsed.get('error'):
                    error_code = parsed.get('error', 'unknown')
                    error_message = parsed.get('message', 'Erro desconhecido na extração')

                    if error_code == 'empty_ocr':
                        st.error(f'''
                            ❌ Não foi possível extrair texto do documento.

                            Motivo: {error_message}

                            Verifique se:
                            - O documento está legível e em boa qualidade
                            - O PDF contém texto selecionável (não é apenas imagem)
                            - O Poppler está instalado (para PDFs escaneados)
                            - A imagem tem resolução suficiente
                        ''')
                    elif error_code == 'tesseract_not_installed':
                        st.error(f'''
                            ❌ Tesseract OCR não está disponível

                            {error_message}

                            **Instruções de instalação:**
                            - **Windows:** Baixe em https://github.com/UB-Mannheim/tesseract/wiki
                            - **Linux:** `sudo apt-get install tesseract-ocr`
                            - **macOS:** `brew install tesseract`

                            Após instalar, reinicie a aplicação.
                        ''')
                    elif error_code == 'invalid_image_format':
                        st.error(f"❌ Formato de imagem inválido: {error_message}")
                    elif error_code == 'file_not_found':
                        st.error(f"❌ Arquivo não encontrado: {error_message}")
                    elif error_code == 'unsupported_file_type':
                        st.error(f"❌ Tipo de arquivo não suportado: {error_message}")
                    else:
                        st.error(f"❌ Erro na extração ({error_code}): {error_message}")

                    logger.error(f"Erro de extração: {error_code} - {error_message}")
                    return

                # Validação adicional
                if not isinstance(parsed, dict):
                    st.error(f"❌ Resposta inválida da extração: {type(parsed).__name__}")
                    logger.error(f"Resposta inválida: {parsed}")
                    return

                # Show raw OCR text with better formatting
                st.subheader('📝 Texto extraído (OCR)')
                raw_text = parsed.get('raw_text', '').strip()

                if not raw_text:
                    st.warning('Nenhum texto foi extraído do documento.')
                    return

                with st.expander('Visualizar texto extraído', expanded=False):
                    st.text_area(
                        'Texto extraído (apenas leitura)',
                        value=raw_text[:5000] + ('...' if len(raw_text) > 5000 else ''),
                        height=200,
                        disabled=True
                    )

                # Processamento automático com IA
                with st.spinner('Processando texto com IA para extração estruturada...'):
                    try:
                        # Usar IA para extrair campos automaticamente
                        extracted_data = ocr_text_to_document(raw_text, use_llm=True)

                        # Garantir que extracted_data é um dicionário
                        if not isinstance(extracted_data, dict):
                            st.error('Erro: Dados extraídos não estão no formato esperado')
                            st.stop()

                        # Adicionar o texto bruto extraído
                        extracted_data['raw_text'] = raw_text

                        # Se não conseguiu extrair dados suficientes, tentar com heurística
                        if not extracted_data.get('emitente') or not extracted_data.get('itens'):
                            st.warning('IA não conseguiu extrair todos os campos automaticamente. Tentando com heurística...')
                            extracted_data = ocr_text_to_document(raw_text, use_llm=False)

                            # Garantir que os dados extraídos são válidos
                            if not isinstance(extracted_data, dict):
                                st.error('Erro: Falha ao extrair dados usando heurística')
                                st.stop()

                            extracted_data['raw_text'] = raw_text

                        # Classificar o documento
                        classification = coordinator.run_task('classify', {'parsed': extracted_data})

                        try:
                            # Validar os dados extraídos antes de salvar
                            if not _validate_document_data(extracted_data):
                                st.error('Erro: Dados extraídos não contêm campos obrigatórios')
                                st.stop()

                            # Preparar e salvar o registro
                            record = _prepare_document_record(uploaded, extracted_data, classification)

                            # Validar o registro antes de salvar
                            required_fields = ['file_name', 'document_type', 'extracted_data', 'raw_text']
                            missing_fields = [field for field in required_fields if field not in record]
                            if missing_fields:
                                st.error(f'Erro: Registro inválido. Campos faltando: {missing_fields}')
                                st.stop()

                            # Garantir que extracted_data é serializável
                            try:
                                json.dumps(record['extracted_data'])
                            except (TypeError, OverflowError) as e:
                                st.error(f'Erro: Dados extraídos contêm valores não serializáveis: {str(e)}')
                                st.stop()

                            # Salvar o documento
                            saved = storage.save_fiscal_document(record)

                            # Verificar se o documento foi salvo com sucesso
                            if not isinstance(saved, dict) or 'id' not in saved:
                                error_msg = str(saved) if not isinstance(saved, dict) else 'Resposta do servidor não contém ID do documento'
                                st.error(f'Erro ao salvar documento: {error_msg}')
                                if hasattr(storage, '_last_error'):
                                    st.error(f'Detalhes do erro: {getattr(storage, "_last_error", "")}')
                                st.stop()

                            # Documento salvo com sucesso
                            st.success('✅ Documento salvo com sucesso!')
                            st.balloons()

                            # RAG Processing - Processar documento automaticamente para RAG
                            if 'id' in saved:
                                document_id = saved['id']
                                try:
                                    # Chamar RAG service em background
                                    with st.spinner('🧠 Processando documento para busca inteligente...'):
                                        # Usar o RAG service da sessão se disponível
                                        if 'rag_service' in st.session_state and st.session_state.rag_service:
                                            import asyncio

                                            # Executar processamento RAG em background
                                            async def process_rag():
                                                try:
                                                    result = await st.session_state.rag_service.process_document_for_rag(saved)  # ✅ Usar documento salvo com ID correto
                                                    return result
                                                except Exception as rag_error:
                                                    logger.error(f"Erro no processamento RAG: {rag_error}")
                                                    return {'success': False, 'error': str(rag_error)}

                                            # Executar a função assíncrona
                                            rag_result = asyncio.run(process_rag())

                                            if rag_result.get('success', False):
                                                chunks_count = rag_result.get('chunks_processed', 0)
                                                st.success(f'✅ Documento processado para busca inteligente! ({chunks_count} chunks criados)')
                                                logger.info(f"RAG processing completed for document {document_id}: {chunks_count} chunks")
                                            else:
                                                error_msg = rag_result.get('error', 'Erro desconhecido')
                                                st.warning(f'⚠️ Documento salvo, mas houve um problema no processamento inteligente: {error_msg}')
                                                logger.error(f"RAG processing failed for document {document_id}: {error_msg}")
                                        else:
                                            st.info('ℹ️ Sistema RAG não disponível no momento. Documento salvo sem processamento inteligente.')
                                            logger.warning(f"RAG service not available for document {document_id}")

                                except Exception as rag_error:
                                    st.warning(f'⚠️ Erro no processamento inteligente: {str(rag_error)}')
                                    logger.error(f"RAG processing error for document {document_id}: {rag_error}")

                            # Salvar histórico se suportado
                            try:
                                if hasattr(storage, 'save_history'):
                                    history_data = {
                                        'fiscal_document_id': saved.get('id'),
                                        'event_type': 'created',
                                        'event_data': {
                                            'source': 'ocr_auto',
                                            'file_type': file_type,
                                            'validation_status': record.get('validation_status')
                                        }
                                    }
                                    storage.save_history(history_data)
                            except Exception as history_error:
                                st.warning(f'Aviso: Não foi possível salvar o histórico: {str(history_error)}')

                            # Mostrar dados extraídos
                            st.subheader('📊 Dados extraídos automaticamente')
                            st.json(extracted_data)

                            # Mostrar link para visualizar o documento salvo
                            if 'id' in saved:
                                st.markdown(f'''
                                **Ações:**
                                - [Visualizar documento](#)
                                - [Editar informações](#)
                                ''', unsafe_allow_html=True)

                            # Mostrar resumo do processamento OCR
                            with st.expander('🔍 Detalhes do OCR', expanded=False):
                                st.markdown(f"""
                                **Processamento OCR:**
                                - **Arquivo:** {uploaded.name}
                                - **Tipo:** {file_type.upper()}
                                - **Texto extraído:** {len(raw_text)} caracteres
                                - **Campos identificados:** {len(extracted_data)} campos
                                - **Status:** Processamento concluído com IA
                                """)

                        except Exception as e:
                            st.error(f'Erro ao salvar documento: {str(e)}')
                            st.exception(e)  # Log detalhado no console

                    except Exception as e:
                        st.error(f'Erro ao processar documento automaticamente: {str(e)}')
                        st.exception(e)

        except Exception as e:
            st.error(f'❌ Ocorreu um erro inesperado: {str(e)}')
            st.exception(e)  # Show full traceback in logs

        finally:
            # Clean up temporary file
            try:
                if dest.exists():
                    dest.unlink()
            except Exception as e:
                st.warning(f'Aviso: Não foi possível remover o arquivo temporário: {str(e)}')

    # Update session state
    if 'processed_documents' in st.session_state:
        try:
            result = storage.get_fiscal_documents(page=1, page_size=1000)
            # Acessa items diretamente do objeto PaginatedResponse
            st.session_state.processed_documents = result.items if hasattr(result, 'items') else []
            
            # Se estamos processando um único arquivo, rolar para a seção de resultados
            if len(uploaded_files) == 1:
                st.markdown("---")
                st.markdown("### 📝 Resultado do Processamento")
                
        except Exception as e:
            st.warning('Não foi possível atualizar a lista de documentos.')
            st.exception(e)  # Show full traceback in logs
