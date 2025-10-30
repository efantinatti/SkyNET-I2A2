"""
Página RAG (Retrieval-Augmented Generation) para o SkyNET-I2A2.

Esta página demonstra o sistema RAG implementado, permitindo:
1. Consultas semânticas em documentos fiscais
2. Visualização de estatísticas do sistema RAG
3. Processamento de documentos para embeddings
4. Validação de documentos usando contexto
"""
import streamlit as st
import asyncio
import logging
import time
from datetime import datetime
import pandas as pd
from typing import Dict, Any, List, Optional
import pandas as pd

# Backend imports
from backend.services import RAGService

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def initialize_rag_service():
    """Inicializa o serviço RAG se ainda não estiver inicializado."""
    if 'rag_service' not in st.session_state:
        try:
            st.session_state.rag_service = RAGService()
            logger.info("RAG service initialized")
        except Exception as e:
            st.error(f"Erro ao inicializar serviço RAG: {str(e)}")
            return False
    return True


def show_rag_monitoring():
    """Monitoramento em tempo real do processamento RAG."""
    st.subheader("🔄 Monitoramento RAG em Tempo Real")

    if not initialize_rag_service():
        return

    try:
        # Buscar documentos do banco de dados
        from backend.database import storage_manager
        storage = storage_manager.storage

        # Buscar todos os documentos
        all_docs = storage.get_fiscal_documents(page=1, page_size=1000)

        if hasattr(all_docs, 'items') and all_docs.items:
            documents = all_docs.items

            # Análise do status dos embeddings
            embedding_stats = {
                'completed': 0,
                'pending': 0,
                'failed': 0,
                'processing': 0,
                'not_started': 0
            }

            docs_with_embeddings = []
            docs_without_embeddings = []

            for doc in documents:
                status = doc.get('embedding_status', 'not_started')
                if status in embedding_stats:
                    embedding_stats[status] += 1
                else:
                    embedding_stats.setdefault(status, 0)
                    embedding_stats[status] += 1

                if status == 'completed':
                    docs_with_embeddings.append(doc)
                else:
                    docs_without_embeddings.append(doc)

            # Exibir estatísticas
            st.markdown("### 📊 Status dos Documentos")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total de Documentos", len(documents))
            with col2:
                st.metric("Com Embeddings", embedding_stats.get('completed', 0),
                         delta=f"{embedding_stats.get('completed', 0)/len(documents)*100:.1f}%" if documents else "0%")
            with col3:
                st.metric("Sem Embeddings", embedding_stats.get('pending', 0) + embedding_stats.get('not_started', 0))
            with col4:
                st.metric("Com Falha", embedding_stats.get('failed', 0))

            # Gráfico de status
            if embedding_stats:
                st.markdown("### 📈 Distribuição por Status")
                status_df = pd.DataFrame(
                    [(k, v) for k, v in embedding_stats.items() if v > 0],
                    columns=['Status', 'Quantidade']
                )

                if not status_df.empty:
                    # Mapear status para cores
                    color_map = {
                        'completed': '🟢',
                        'pending': '🟡',
                        'failed': '🔴',
                        'processing': '🟠',
                        'not_started': '⚪'
                    }

                    status_df['Status_Display'] = status_df['Status'].map(
                        lambda x: f"{color_map.get(x, '⚪')} {x.replace('_', ' ').title()}"
                    )

                    st.bar_chart(status_df.set_index('Status_Display'))

            # Lista de documentos que precisam de processamento
            if docs_without_embeddings:
                st.markdown("### 📋 Documentos que Precisam de Processamento")

                # Tabela de documentos sem embeddings
                docs_data = []
                for doc in docs_without_embeddings[:10]:  # Mostrar apenas os 10 primeiros
                    docs_data.append({
                        'ID': doc.get('id', 'N/A')[:8] + '...',
                        'Tipo': doc.get('document_type', 'N/A'),
                        'Número': doc.get('document_number', 'N/A'),
                        'Emissor': doc.get('issuer_cnpj', 'N/A'),
                        'Status': doc.get('embedding_status', 'not_started'),
                        'Data': (
                            doc.get('created_at', 'N/A').strftime('%Y-%m-%d')[:10]
                            if hasattr(doc.get('created_at'), 'strftime')
                            else str(doc.get('created_at', 'N/A'))[:10]
                        ) if doc.get('created_at') else 'N/A'
                    })

                if docs_data:
                    docs_df = pd.DataFrame(docs_data)
                    st.dataframe(
                        docs_df,
                        column_config={
                            "ID": st.column_config.TextColumn("ID", width="small"),
                            "Tipo": st.column_config.TextColumn("Tipo", width="small"),
                            "Número": st.column_config.TextColumn("Número", width="medium"),
                            "Emissor": st.column_config.TextColumn("Emissor", width="medium"),
                            "Status": st.column_config.TextColumn("Status", width="small"),
                            "Data": st.column_config.TextColumn("Data", width="small")
                        },
                        hide_index=True,
                        width='stretch'
                    )

                    # Botão para processar documentos selecionados
                    if st.button(f'🚀 Processar {len(docs_without_embeddings)} Documentos para RAG',
                               type='primary', width='stretch'):
                        process_documents_for_rag(docs_without_embeddings)

            # Lista de documentos já processados
            if docs_with_embeddings:
                st.markdown("### ✅ Documentos com Embeddings Prontos")

                # Tabela de documentos com embeddings
                processed_data = []
                for doc in docs_with_embeddings[:10]:  # Mostrar apenas os 10 primeiros
                    processed_data.append({
                        'ID': doc.get('id', 'N/A')[:8] + '...',
                        'Tipo': doc.get('document_type', 'N/A'),
                        'Número': doc.get('document_number', 'N/A'),
                        'Chunks': doc.get('chunks_count', 0),
                        'Status': doc.get('embedding_status', 'completed'),
                        'Data': (
                            doc.get('created_at', 'N/A').strftime('%Y-%m-%d')[:10]
                            if hasattr(doc.get('created_at'), 'strftime')
                            else str(doc.get('created_at', 'N/A'))[:10]
                        ) if doc.get('created_at') else 'N/A'
                    })

                if processed_data:
                    processed_df = pd.DataFrame(processed_data)
                    st.dataframe(
                        processed_df,
                        column_config={
                            "ID": st.column_config.TextColumn("ID", width="small"),
                            "Tipo": st.column_config.TextColumn("Tipo", width="small"),
                            "Número": st.column_config.TextColumn("Número", width="medium"),
                            "Chunks": st.column_config.NumberColumn("Chunks", width="small"),
                            "Status": st.column_config.TextColumn("Status", width="small"),
                            "Data": st.column_config.TextColumn("Data", width="small")
                        },
                        hide_index=True,
                        width='stretch'
                    )

        else:
            st.info("ℹ️ Nenhum documento encontrado no banco de dados.")
            st.info("💡 **Para usar o monitoramento RAG:**")
            st.markdown("""
            1. **Importe documentos** usando a aba "Importador"
            2. **Aguarde o processamento** - embeddings são gerados automaticamente
            3. **Monitore aqui** o progresso do processamento RAG
            """)

    except Exception as e:
        st.error(f"Erro ao carregar monitoramento: {str(e)}")


def process_documents_for_rag(documents):
    """Processa uma lista de documentos para RAG com feedback em tempo real."""
    if not documents:
        st.warning("Nenhum documento para processar.")
        return

    total_docs = len(documents)
    
    # Configuração do layout
    st.markdown(f"### 🚀 Processando {total_docs} Documentos...")
    
    # Criar colunas para o contador e barra de progresso
    col_counter, col_progress = st.columns([1, 4])
    
    with col_counter:
        st.markdown("#### Progresso")
        progress_text = st.empty()
        progress_text.markdown(f"**0 de {total_docs}** documentos processados")
    
    with col_progress:
        st.markdown("#### &nbsp;")  # Espaçador para alinhar com o contador
        progress_bar = st.progress(0)
    
    # Área para status detalhado
    status_container = st.container()
    status_text = status_container.empty()
    
    # Inicializar contadores
    success_count = 0
    error_count = 0
    results = []
    
    # Criar colunas para métricas em tempo real
    metrics_col1, metrics_col2, metrics_col3 = st.columns(3)
    
    with metrics_col1:
        st.metric("Total de Documentos", total_docs)
    
    with metrics_col2:
        success_metric = st.metric("Processados com Sucesso", "0")
    
    with metrics_col3:
        error_metric = st.metric("Com Erros", "0")
    
    # Processar cada documento
    for i, doc in enumerate(documents, 1):
        doc_id_short = str(doc.get('id', 'N/A'))[:8] + '...' if doc.get('id') else 'N/A'
        doc_name = doc.get('file_name', doc_id_short)
        
        try:
            # Atualizar status
            status_text.markdown(f"""
            **Documento {i} de {total_docs}**  
            📄 **Arquivo:** {doc_name}  
            🔄 **Status:** Processando...
            """)
            
            # Garantir que o documento tem formato correto para RAG
            rag_document = {
                'id': doc.get('id'),
                'file_name': doc.get('file_name'),
                'document_type': doc.get('document_type'),
                'document_number': doc.get('document_number'),
                'issuer_cnpj': doc.get('issuer_cnpj'),
                'recipient_cnpj': doc.get('recipient_cnpj'),
                'issue_date': doc.get('issue_date'),
                'total_value': doc.get('total_value'),
                'cfop': doc.get('cfop'),
                'extracted_data': doc.get('extracted_data', {}),
                'validation_status': doc.get('validation_status'),
                'classification': doc.get('classification', {}),
                'raw_text': doc.get('raw_text', ''),
                'validation_details': doc.get('validation_details', {}),
                'metadata': doc.get('metadata', {}),
                'document_data': doc.get('document_data', {})
            }

            # Remover campos None/empty
            rag_document = {k: v for k, v in rag_document.items() if v is not None}

            # Processar documento
            result = asyncio.run(st.session_state.rag_service.process_document_for_rag(rag_document))

            if result.get('success', False):
                success_count += 1
                chunks_count = result.get('chunks_processed', 0)
                results.append((doc['id'], True, chunks_count, None))
                
                # Atualizar métricas
                success_metric.metric("Processados com Sucesso", success_count)
                
                # Atualizar status
                status_text.markdown(f"""
                **Documento {i} de {total_docs}**  
                📄 **Arquivo:** {doc_name}  
                ✅ **Status:** Processado com sucesso!  
                🔢 **Chunks criados:** {chunks_count}
                """)
            else:
                error_count += 1
                error_msg = result.get('error', 'Erro desconhecido')
                results.append((doc['id'], False, 0, error_msg))
                
                # Atualizar métricas
                error_metric.metric("Com Erros", error_count)
                
                # Atualizar status
                status_text.markdown(f"""
                **Documento {i} de {total_docs}**  
                📄 **Arquivo:** {doc_name}  
                ❌ **Status:** Falha no processamento  
                📝 **Erro:** {error_msg[:100]}{'...' if len(str(error_msg)) > 100 else ''}
                """)

        except Exception as e:
            error_count += 1
            error_msg = str(e)
            results.append((doc.get('id', 'N/A'), False, 0, error_msg))
            
            # Atualizar métricas
            error_metric.metric("Com Erros", error_count)
            
            # Atualizar status
            status_text.markdown(f"""
            **Documento {i} de {total_docs}**  
            📄 **Arquivo:** {doc_name}  
            ❌ **Status:** Erro inesperado  
            🐞 **Detalhes:** {error_msg[:150]}{'...' if len(error_msg) > 150 else ''}
            """)

        # Atualizar barra de progresso e contador
        progress = i / total_docs
        progress_bar.progress(progress)
        progress_text.markdown(f"**{i} de {total_docs}** documentos processados")
        
        # Pequena pausa para atualizar a UI
        time.sleep(0.1)

    # Concluir processamento
    progress_bar.progress(1.0)
    progress_text.markdown(f"**{total_docs} de {total_docs}** documentos processados")
    status_text.markdown("### ✅ Processamento concluído!")

    # Mostrar resumo final
    st.balloons()  # Efeito de confetes
    
    # Criar colunas para o resumo
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    with summary_col1:
        st.metric("Total Processado", total_docs)
    
    with summary_col2:
        st.metric("Sucesso", f"{success_count} ({success_count/max(total_docs, 1)*100:.1f}%)", 
                 delta=f"{success_count} documentos" if success_count > 0 else None)
    
    with summary_col3:
        st.metric("Falhas", f"{error_count} ({error_count/max(total_docs, 1)*100:.1f}%)", 
                 delta=f"{error_count} documentos" if error_count > 0 else None,
                 delta_color="inverse")

    # Detalhes dos resultados
    if results:
        with st.expander('📊 Detalhes do Processamento', expanded=error_count > 0):
            for doc_id, success, chunks, error in results:
                doc_id_display = str(doc_id)[:8] + '...' if doc_id else 'N/A'
                if success:
                    st.success(f'✅ Documento {doc_id_display}: {chunks} chunks criados')
                else:
                    st.error(f'❌ Documento {doc_id_display}: {error}')
                    
        # Botão para baixar relatório
        csv = 'ID,Status,Chunks Criados,Detalhes\n' + '\n'.join(
            f'{doc_id},{success},{chunks if success else "N/A"},"{error if not success else ""}"'
            for doc_id, success, chunks, error in results
        )
        
        st.download_button(
            label="📥 Baixar Relatório em CSV",
            data=csv,
            file_name=f'relatorio_rag_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            mime='text/csv',
        )

    # Atualizar estatísticas
    st.rerun()


def show_semantic_search():
    """Interface para busca semântica usando RAG."""
    st.subheader("🔍 Busca Semântica")

    if not initialize_rag_service():
        return

    # Filtros para a busca
    col1, col2, col3 = st.columns(3)

    with col1:
        document_type = st.selectbox(
            "Tipo de Documento",
            ["Todos", "NFe", "NFCe", "CTe"],
            help="Filtrar por tipo de documento"
        )

    with col2:
        similarity_threshold = st.slider(
            "Limite de Similaridade",
            0.1, 1.0, 0.6,
            help="Documentos com similaridade acima deste valor serão retornados"
        )

    with col3:
        max_results = st.slider(
            "Máximo de Resultados",
            1, 10, 5,
            help="Número máximo de documentos a retornar"
        )

    # Campo de consulta
    query = st.text_area(
        "Digite sua pergunta sobre os documentos fiscais:",
        height=100,
        placeholder="Ex: 'Encontre notas fiscais da empresa XYZ' ou 'Documentos com produtos de escritório'"
    )

    # Botão de busca
    if st.button("🔍 Buscar", type="primary", width='stretch'):
        if not query.strip():
            st.warning("Por favor, digite uma consulta.")
            return

        try:
            with st.spinner("Buscando documentos relevantes..."):
                # Preparar filtros
                filters = {}
                if document_type != "Todos":
                    filters['document_type'] = document_type

                # Executar busca RAG
                result = asyncio.run(st.session_state.rag_service.answer_query(
                    query=query,
                    filters=filters if filters else None,
                    max_context_docs=3
                ))

            # Exibir resultados
            if result['status'] == 'success':
                st.success("✅ Consulta executada com sucesso!")

                # Resposta principal
                st.subheader("Resposta:")
                st.write(result['answer'])

                # Métricas da busca
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Documentos Relevantes", len(result.get('context_docs', [])))
                with col2:
                    st.metric("Chunks Similares", result.get('total_chunks', 0))
                with col3:
                    st.metric("Filtros Aplicados", len(result.get('filters_applied', {})))

                # Documentos de contexto
                if result.get('context_docs'):
                    with st.expander("📄 Documentos de Contexto"):
                        for i, doc in enumerate(result['context_docs'], 1):
                            st.markdown(f"**Documento {i}**")
                            st.write(f"- **Tipo:** {doc.get('document_type', 'N/A')}")
                            st.write(f"- **Emissor:** {doc.get('issuer_cnpj', 'N/A')}")
                            st.write(f"- **Similaridade:** {doc.get('total_similarity', 0):.3f}")
                            st.write(f"- **Conteúdo:** {doc.get('chunks_content', 'N/A')[:300]}...")
                            st.divider()

                # Chunks similares detalhados
                if result.get('similar_chunks'):
                    with st.expander("🔍 Detalhes dos Chunks"):
                        for chunk in result['similar_chunks'][:5]:  # Mostrar apenas os 5 primeiros
                            st.write(f"**Similaridade:** {chunk.get('similarity', 0):.3f}")
                            st.write(f"**Conteúdo:** {chunk.get('content_text', '')[:200]}...")
                            st.divider()

            elif result['status'] == 'no_documents':
                st.warning("⚠️ Nenhum documento processado")
                st.write(result['answer'])

                # Mostrar estatísticas do sistema
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Documentos Processados", 0)
                with col2:
                    st.metric("Chunks Totais", 0)
                with col3:
                    st.metric("Insights Gerados", 0)

                st.info("📝 **Para usar o sistema RAG:**")
                st.markdown("""
                1. **Processar documentos:** Use a aba "Processar Documento" para adicionar documentos
                2. **Aguardar embeddings:** O sistema gerará automaticamente embeddings
                3. **Fazer consultas:** Retorne aqui para buscar nos documentos processados

                💡 **Dica:** Comece processando alguns documentos fiscais de exemplo!
                """)

            elif result['status'] == 'no_matches':
                st.info("ℹ️ Documentos processados, mas nenhum relevante encontrado")
                st.write(result['answer'])

                # Mostrar métricas do sistema
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Documentos Processados", "N/A")
                with col2:
                    st.metric("Chunks Similares", 0)
                with col3:
                    st.metric("Filtros Aplicados", len(result.get('filters_applied', {})))

                st.info("💡 **Sugestões para melhorar a busca:**")
                st.markdown("""
                - Tente palavras-chave diferentes na consulta
                - Ajuste os filtros (tipo de documento, emissor, etc.)
                - Reduza o limite de similaridade se necessário
                - Use a aba "Estatísticas" para ver quantos documentos foram processados
                """)

            else:
                st.error(f"❌ Erro na consulta: {result.get('error', 'Erro desconhecido')}")

        except Exception as e:
            st.error(f"Erro ao executar consulta: {str(e)}")


def show_document_processing():
    """Interface para processamento de documentos para RAG."""
    st.subheader("📝 Processar Documento para RAG")

    if not initialize_rag_service():
        return

    st.info("💡 Use esta funcionalidade para processar documentos fiscais e gerar embeddings para busca semântica.")

    # Exemplo de documento para teste
    with st.expander("📄 Exemplo de Documento Fiscal"):
        st.json({
            "file_name": "nfe_exemplo_001.xml",
            "document_type": "NFe",
            "document_number": "12345",
            "issuer_cnpj": "12345678000199",
            "extracted_data": {
                "emitente": {
                    "razao_social": "EMPRESA EXEMPLO LTDA",
                    "cnpj": "12345678000199"
                },
                "destinatario": {
                    "razao_social": "CLIENTE EXEMPLO S.A.",
                    "cnpj": "98765432000100"
                },
                "itens": [
                    {
                        "descricao": "Produto A - Material de Escritório",
                        "quantidade": 10,
                        "valor_unitario": 25.50,
                        "valor_total": 255.00
                    }
                ],
                "totais": {
                    "valor_produtos": 255.00,
                    "valor_total": 255.00
                }
            }
        })

    # Formulário para processamento
    with st.form("process_document_form"):
        st.write("**Dados do Documento:**")

        col1, col2 = st.columns(2)

        with col1:
            file_name = st.text_input("Nome do Arquivo", "nfe_exemplo_001.xml")
            document_type = st.selectbox("Tipo de Documento", ["NFe", "NFCe", "CTe"])
            document_number = st.text_input("Número do Documento", "12345")

        with col2:
            issuer_cnpj = st.text_input("CNPJ do Emissor", "12345678000199")
            total_value = st.number_input("Valor Total (R$)", 0.0, 1000000.0, 255.00)

        # Dados extraídos (JSON)
        extracted_data = st.text_area(
            "Dados Extraídos (JSON)",
            height=200,
            value="""{
  "emitente": {
    "razao_social": "EMPRESA EXEMPLO LTDA",
    "cnpj": "12345678000199"
  },
  "destinatario": {
    "razao_social": "CLIENTE EXEMPLO S.A.",
    "cnpj": "98765432000100"
  },
  "itens": [
    {
      "descricao": "Produto A - Material de Escritório",
      "quantidade": 10,
      "valor_unitario": 25.50,
      "valor_total": 255.00
    }
  ],
  "totais": {
    "valor_produtos": 255.00,
    "valor_total": 255.00
  }
}"""
        )

        submitted = st.form_submit_button("🚀 Processar Documento", type="primary", width='stretch')

        if submitted:
            try:
                # Parse JSON data
                import json
                extracted_data_parsed = json.loads(extracted_data)

                # Create document object
                document = {
                    'id': f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    'file_name': file_name,
                    'document_type': document_type,
                    'document_number': document_number,
                    'issuer_cnpj': issuer_cnpj,
                    'extracted_data': extracted_data_parsed,
                    'validation_status': 'pending',
                    'classification': {'tipo': 'venda', 'categoria': 'mercadorias'}
                }

                with st.spinner("Processando documento e gerando embeddings..."):
                    # Process document for RAG
                    result = asyncio.run(st.session_state.rag_service.process_document_for_rag(document))

                if result['success']:
                    st.success("✅ Documento processado com sucesso!")

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Chunks Processados", result['chunks_processed'])
                    with col2:
                        st.metric("Total de Chunks", result['total_chunks'])
                    with col3:
                        st.metric("Document ID", document['id'])

                    st.info("💡 O documento agora está disponível para consultas semânticas!")
                else:
                    st.error(f"❌ Erro no processamento: {result['error']}")

            except json.JSONDecodeError:
                st.error("❌ Erro no formato JSON dos dados extraídos.")
            except Exception as e:
                st.error(f"❌ Erro ao processar documento: {str(e)}")


def show_document_validation():
    """Interface para validação de documentos usando RAG."""
    st.subheader("✅ Validação de Documentos")

    if not initialize_rag_service():
        return

    st.info("🔍 Use esta funcionalidade para validar documentos fiscais comparando com padrões de documentos similares.")

    # Formulário de validação
    with st.form("validation_form"):
        st.write("**Documento para Validar:**")

        col1, col2 = st.columns(2)

        with col1:
            doc_type = st.selectbox("Tipo de Documento", ["NFe", "NFCe", "CTe"])
            doc_number = st.text_input("Número do Documento", "99999")

        with col2:
            issuer_cnpj_val = st.text_input("CNPJ do Emissor", "55566677000188")
            total_value_val = st.number_input("Valor Total (R$)", 0.0, 10000000.0, 999999.99)

        # Regras de validação
        validation_rules = st.multiselect(
            "Regras de Validação",
            ["document_format", "required_fields", "value_ranges", "issuer_validation"],
            default=["document_format", "value_ranges", "issuer_validation"]
        )

        validate_submitted = st.form_submit_button("🔍 Validar Documento", type="primary", width='stretch')

        if validate_submitted:
            try:
                # Create validation document
                validation_doc = {
                    'id': f"val_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    'file_name': f'{doc_type.lower()}_validation_{doc_number}.xml',
                    'document_type': doc_type,
                    'document_number': doc_number,
                    'issuer_cnpj': issuer_cnpj_val,
                    'extracted_data': {
                        'emitente': {
                            'razao_social': 'EMPRESA VALIDATION LTDA',
                            'cnpj': issuer_cnpj_val
                        },
                        'totais': {
                            'valor_total': total_value_val
                        }
                    }
                }

                with st.spinner("Validando documento usando contexto de documentos similares..."):
                    # Run validation
                    validation_result = asyncio.run(st.session_state.rag_service.validate_document_with_rag(
                        document=validation_doc,
                        validation_rules=validation_rules
                    ))

                if validation_result.get('validation_results'):
                    st.success("✅ Validação concluída!")

                    # Exibir resultados da validação
                    for i, validation in enumerate(validation_result['validation_results'], 1):
                        confidence = validation.get('confidence', 0)

                        if confidence > 0.7:
                            st.success(f"**✅ {i}. {validation['insight']}**")
                        elif confidence > 0.4:
                            st.warning(f"**⚠️ {i}. {validation['insight']}**")
                        else:
                            st.error(f"**❌ {i}. {validation['insight']}**")

                        st.caption(f"Confiança: {confidence:.2f}")

                        # Metadados adicionais
                        metadata = validation.get('metadata', {})
                        if metadata:
                            with st.expander("📊 Detalhes da Análise"):
                                st.json(metadata)

                        st.divider()

                else:
                    st.warning("⚠️ Nenhum resultado de validação obtido.")

            except Exception as e:
                st.error(f"❌ Erro na validação: {str(e)}")


def show_rag_statistics():
    """Exibe estatísticas do sistema RAG."""
    st.subheader("📊 Estatísticas do Sistema RAG")
    
    if 'rag_service' not in st.session_state:
        st.warning("Serviço RAG não inicializado. Por favor, aguarde...")
        return
    
    try:
        # Get basic statistics
        stats = st.session_state.rag_service.get_statistics()
        
        # Display basic stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Documentos", stats.get('total_documents', 0))
        with col2:
            st.metric("Total de Embeddings", stats.get('total_embeddings', 0))
        with col3:
            st.metric("Tamanho do Índice", f"{stats.get('index_size_mb', 0):.2f} MB")
        
        # Display document type distribution if available
        if 'documents_by_type' in stats and stats['documents_by_type']:
            st.subheader("📄 Documentos por Tipo")
            df_types = pd.DataFrame(
                list(stats['documents_by_type'].items()),
                columns=['Tipo de Documento', 'Quantidade']
            )
            st.bar_chart(df_types.set_index('Tipo de Documento'))
        
        # Display embedding statistics if available
        if 'embedding_stats' in stats:
            st.subheader("🧮 Estatísticas de Embeddings")
            st.json(stats['embedding_stats'])
            
    except Exception as e:
        st.error(f"Erro ao carregar estatísticas: {str(e)}")
        logger.error(f"Error in show_rag_statistics: {str(e)}")


def show_rag_examples():
    """Exibe exemplos de uso do sistema RAG."""
    st.subheader("💡 Exemplos de Uso")
    st.markdown("""
    ### 🔍 **Consultas Semânticas**

    O sistema RAG permite fazer consultas em linguagem natural sobre os documentos fiscais:

    **Exemplos de consultas:**
    - *"Encontre notas fiscais da empresa XYZ"*
    - *"Documentos com produtos de escritório emitidos este mês"*
    - *"Qual o valor total das compras do fornecedor ABC?"*
    - *"Notas fiscais com CFOP 5102"*
    - *"Documentos com valores acima de R$ 10.000"*

    ### ✅ **Validação Inteligente**

    Valide novos documentos comparando com padrões de documentos similares:

    - **Formato do documento:** Verifica se está de acordo com padrões
    - **Campos obrigatórios:** Confirma se todos os campos necessários estão presentes
    - **Faixas de valores:** Compara com valores típicos para o tipo de documento
    - **Padrões do emissor:** Analisa se o documento segue padrões do emissor

    ### 📊 **Processamento de Documentos**

    1. **Upload:** Documentos são processados (OCR/XML) normalmente
    2. **Chunking:** Conteúdo é dividido em pedaços menores (chunks)
    3. **Embedding:** Cada chunk recebe um vetor de embedding usando Gemini
    4. **Armazenamento:** Chunks e embeddings são salvos no banco vetorial
    5. **Busca:** Consultas geram embeddings e buscam chunks similares

    ### 🎯 **Como Funciona o RAG**

    1. **Consulta do usuário** → Embedding gerado
    2. **Busca semântica** → Documentos similares encontrados
    3. **Contexto extraído** → Chunks relevantes selecionados
    4. **Prompt RAG** → Contexto + pergunta enviados ao Gemini
    5. **Resposta gerada** → Baseada apenas no contexto dos documentos
    """)


def main():
    """Página principal do sistema RAG."""
    st.title("🧠 RAG - Retrieval-Augmented Generation")
    st.markdown("*Sistema de busca semântica e geração de respostas usando IA*")

    # Verificar se o serviço RAG está disponível
    if not initialize_rag_service():
        st.error("❌ Sistema RAG não disponível. Verifique as configurações.")
        return

    # Menu de navegação
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🔄 Monitoramento",
        "🔍 Busca Semântica",
        "📝 Processar Documento",
        "✅ Validação",
        "📊 Estatísticas",
        "💡 Exemplos"
    ])

    with tab1:
        show_rag_monitoring()

    with tab2:
        show_semantic_search()

    with tab3:
        show_document_processing()

    with tab4:
        show_document_validation()

    with tab5:
        show_rag_statistics()

    with tab6:
        show_rag_examples()

    # Rodapé com informações técnicas
    st.divider()
    st.caption("""
    **Sistema RAG - SkyNET-I2A2**

    - **Embeddings:** Google Gemini (768 dimensões)
    - **Vector Store:** Supabase com pgvector
    - **LLM:** Google Gemini 2.0-Flash / 1.5-Flash
    - **Busca:** Similaridade de cosseno com HNSW
    """)


if __name__ == "__main__":
    main()
