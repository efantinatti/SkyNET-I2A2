"""Document history and listing page."""
import streamlit as st
import importlib
import importlib.util
import json
import sys
from datetime import datetime, timedelta
import base64
import io
from typing import Any, Dict, List
from decimal import Decimal

# Inicializa a variável pd como None
pd = None
PANDAS_AVAILABLE = False

# Tenta importar pandas, mas não falha se não estiver disponível
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    st.warning("O módulo pandas não está disponível. Algumas funcionalidades podem estar limitadas.")

# Importações que dependem do Streamlit
try:
    from frontend.components import document_renderer
except ImportError:
    document_renderer = None
    st.warning("Módulo document_renderer não encontrado. Algumas funcionalidades podem estar desabilitadas.")

# Função auxiliar para criar DataFrame com verificação
def safe_dataframe(data):
    """Cria um DataFrame de forma segura, verificando se o pandas está disponível."""
    if not PANDAS_AVAILABLE or pd is None:
        st.error("A biblioteca pandas não está disponível. Não é possível criar DataFrames.")
        return None
    try:
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Erro ao criar DataFrame: {str(e)}")
        return None

def _to_float(value: Any) -> float:
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

def _format_currency(value: Any) -> str:
    amount = _to_float(value)
    return f"R$ {amount:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def get_validation_errors(doc):
    """Extrai informações de validação do documento."""
    if not isinstance(doc, dict):
        return 0, []

    # Check both validation and validation_details fields
    validation = doc.get('validation', {}) or {}
    validation_details = doc.get('validation_details', {}) or {}

    # Extract errors from validation field
    errors: List[Dict[str, Any]] = []
    seen_map: Dict[str, int] = {}

    def _normalize(value: Any) -> str:
        return '' if value is None else str(value).strip()

    def add_issue(message: Any, category: Any, details: Any = '') -> None:
        msg_str = _normalize(message)
        cat_str = _normalize(category)
        details_str = _normalize(details)
        key = msg_str.lower()

        if key in seen_map:
            idx = seen_map[key]
            existing = errors[idx]
            existing_cat = _normalize(existing.get('category'))

            if existing_cat.lower() in ('aviso', 'warning') and cat_str.lower() not in ('aviso', 'warning'):
                existing['category'] = category

            if not _normalize(existing.get('details')) and details_str:
                existing['details'] = details
            return

        errors.append({
            'message': message,
            'details': details,
            'category': category
        })
        seen_map[key] = len(errors) - 1

    raw_errors = validation.get('errors') if isinstance(validation.get('errors'), list) else []
    for err in raw_errors:
        if isinstance(err, dict):
            add_issue(err.get('message'), err.get('category', 'Erro'), err.get('details'))
        else:
            add_issue(err, 'Erro')
    
    # Extract errors and issues from validation_details field if available
    if validation_details and isinstance(validation_details, dict):
        # Extract issues (erros)
        issues = validation_details.get('issues', [])
        if isinstance(issues, list):
            for issue in issues:
                add_issue(issue if isinstance(issue, str) else str(issue), 'Erro')
        
        # Extract warnings (avisos)
        warnings = validation_details.get('warnings', [])
        if isinstance(warnings, list):
            for warning in warnings:
                add_issue(warning if isinstance(warning, str) else str(warning), 'Aviso')
        
        # Extract status-based errors
        if validation_details.get('status') == 'error' and not errors:
            add_issue(
                validation_details.get('message', 'Erro na validação'),
                'Status',
                str(validation_details)
            )
        
        # Extract field-level validation errors
        if validation_details.get('validations'):
            for field, result in validation_details['validations'].items():
                # Handle case where result is a boolean
                if isinstance(result, bool):
                    if not result:
                        field_lower = field.lower()
                        if any(token in field_lower for token in ('valido', 'válido', 'valid', 'status')):
                            continue
                        add_issue(
                            f'Erro na validação de {field}',
                            field,
                            'A validação retornou falso'
                        )
                # Handle case where result is a dictionary
                elif isinstance(result, dict):
                    if not result.get('valido', result.get('is_valid', True)):
                        add_issue(
                            result.get('message', f'Erro na validação de {field}'),
                            field,
                            result.get('details', '')
                        )
                # Handle other cases (string, number, etc.)
                elif not result:
                    add_issue(
                        f'Erro na validação de {field}',
                        field,
                        f'Valor inválido: {result}'
                    )
    
    error_count = sum(
        1 for err in errors
        if str(err.get('category', '')).lower() not in ('aviso', 'warning')
    )
    return error_count, errors

def get_document_summary(doc):
    """Extrai um resumo das informações principais do documento."""
    if not isinstance(doc, dict):
        return {}
    
    # Tenta extrair dados do documento processado
    doc_data = doc.get('parsed', {}) or doc.get('extracted_data', {}) or {}
    if not isinstance(doc_data, dict):
        doc_data = {}
    
    # Informações básicas
    doc_type = doc.get('document_type', 'Desconhecido')
    document_number = doc_data.get('numero') or doc.get('document_number', 'N/A')
    
    # Emitente/Destinatário
    emitente = doc_data.get('emitente') or {}
    destinatario = doc_data.get('destinatario') or {}
    
    # Valores
    total_value = doc_data.get('total')
    if _to_float(total_value) == 0.0:
        total_value = doc_data.get('valor_servico', doc.get('total_value', 0))
    total = _format_currency(total_value)
    
    # Conta itens
    itens = doc_data.get('itens') or []
    num_itens = len(itens) if isinstance(itens, list) else 0
    
    # Informações de validação
    num_errors, _ = get_validation_errors(doc)
    
    return {
        'Tipo': doc_type,
        'Número': document_number,
        'Emitente': emitente.get('razao_social', 'N/A'),
        'CNPJ Emitente': emitente.get('cnpj', 'N/A'),
        'Destinatário': destinatario.get('razao_social', 'N/A'),
        'Valor Total': total,
        'Itens': num_itens,
        'Erros de Validação': num_errors,
        'Data Processamento': (
            doc.get('created_at', 'N/A').strftime('%Y-%m-%d %H:%M:%S')[:19]
            if hasattr(doc.get('created_at'), 'strftime')
            else str(doc.get('created_at', 'N/A'))[:19]
        ) if doc.get('created_at') else 'N/A',
        'ID': doc.get('id', '')
    }

def render_document_details(doc):
    """Renderiza os detalhes de um documento selecionado."""
    st.subheader('Detalhes do Documento')
    
    # Extrai os dados do documento
    doc_data = doc.get('parsed', {}) or doc.get('extracted_data', {}) or {}
    
    # Cria abas para organizar as informações
    tab1, tab2, tab3, tab4 = st.tabs(["📄 Visão Geral", "📋 Itens", "✅ Validação", "📊 Dados Completos"])
    
    with tab1:
        # Visão geral
        st.markdown("### Informações do Documento")
        
        # Cria colunas para melhor organização
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Dados Básicos**")
            st.write(f"**Tipo:** {doc.get('document_type', 'N/A')}")
            st.write(f"**Número:** {doc_data.get('numero', 'N/A')}")
            st.write(f"**Série:** {doc_data.get('serie', 'N/A')}")
            st.write(f"**Data de Emissão:** {doc_data.get('data_emissao', 'N/A')}")
            
        with col2:
            st.markdown("**Valores**")
            total_value = doc_data.get('total')
            if _to_float(total_value) == 0.0:
                total_value = doc_data.get('valor_servico', doc.get('total_value', 0))
            st.write(f"**Valor Total:** {_format_currency(total_value)}")
            
            # Conta itens
            itens = doc_data.get('itens', [])
            num_itens = len(itens) if isinstance(itens, list) else 0
            st.write(f"**Quantidade de Itens:** {num_itens}")
            
            # Status de validação
            num_errors, _ = get_validation_errors(doc)
            status_color = "green" if num_errors == 0 else "red"
            st.markdown(f"**Status de Validação:** :{status_color}[{'Válido' if num_errors == 0 else f'{num_errors} erro(s)'}]")
    
    with tab2:
        # Itens do documento
        st.markdown("### Itens do Documento")
        itens = doc_data.get('itens', [])
        
        if itens and isinstance(itens, list):
            # Cria um DataFrame com os itens
            itens_data = []
            for i, item in enumerate(itens, 1):
                if not isinstance(item, dict):
                    continue
                    
                valor_unitario = item.get('valor_unitario', 0)
                if isinstance(valor_unitario, (int, float)):
                    valor_unitario = f'R$ {valor_unitario:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
                
                valor_total = item.get('valor_total', 0)
                if isinstance(valor_total, (int, float)):
                    valor_total = f'R$ {valor_total:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
                
                itens_data.append({
                    'Item': i,
                    'Descrição': item.get('descricao', 'N/A'),
                    'Quantidade': item.get('quantidade', 'N/A'),
                    'Valor Unitário': valor_unitario,
                    'Valor Total': valor_total,
                    'NCM': item.get('ncm', 'N/A'),
                    'CFOP': item.get('cfop', 'N/A')
                })
            
            if itens_data:
                df_itens = pd.DataFrame(itens_data)
                st.dataframe(df_itens, width='stretch', hide_index=True)
                
                # Botão para baixar itens como CSV
                csv = df_itens.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
                st.download_button(
                    label="⬇️ Baixar Itens (CSV)",
                    data=csv,
                    file_name=f"itens_documento_{doc.get('id', '')}.csv",
                    mime='text/csv'
                )
            else:
                st.info("Nenhum item encontrado neste documento.")
        else:
            st.info("Nenhum item encontrado neste documento.")
    
    with tab3:
        # Validação
        st.markdown("### Validação do Documento")
        
        # Get validation data from both possible locations
        validation_status = doc.get('validation_status', 'pending')
        validation_details = doc.get('validation_details', {}) or {}
        
        # Extrai informações de validação
        issues = validation_details.get('issues', []) if isinstance(validation_details, dict) else []
        warnings = validation_details.get('warnings', []) if isinstance(validation_details, dict) else []
        validations = validation_details.get('validations', {}) if isinstance(validation_details, dict) else {}
        
        # Mostra status geral de validação
        st.markdown("#### Status Geral")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if validation_status == 'error':
                st.error(f"❌ Status: Erros Encontrados")
            elif validation_status == 'warning':
                st.warning(f"⚠️ Status: Avisos")
            else:
                st.success(f"✅ Status: Válido")
        
        with col2:
            st.metric("Erros", len(issues))
        
        with col3:
            st.metric("Avisos", len(warnings))
        
        # Mostra erros encontrados
        if issues:
            st.markdown("#### ❌ Erros Encontrados")
            for i, issue in enumerate(issues, 1):
                st.error(f"{i}. {issue}")
        
        # Mostra avisos encontrados
        if warnings:
            st.markdown("#### ⚠️ Avisos")
            for i, warning in enumerate(warnings, 1):
                st.warning(f"{i}. {warning}")
        
        # Mostra dados brutos de validação se disponível
        if validation_details:
            with st.expander("📊 Dados Brutos de Validação (JSON)"):
                st.json(validation_details)
    
    with tab4:
        # Dados completos em formato JSON
        st.markdown("### Dados Completos (JSON)")
        st.json(doc_data)
        
        # Botões de download
        col1, col2 = st.columns(2)
        
        with col1:
            # Botão para baixar JSON
            json_str = json.dumps(doc_data, ensure_ascii=False, indent=2)
            st.download_button(
                label="⬇️ Baixar JSON",
                data=json_str,
                file_name=f"documento_{doc.get('id', '')}.json",
                mime='application/json'
            )
        
        with col2:
            # Botão para baixar texto OCR (se disponível)
            if 'ocr_text' in doc:
                st.download_button(
                    label="⬇️ Baixar Texto OCR",
                    data=doc['ocr_text'],
                    file_name=f"ocr_documento_{doc.get('id', '')}.txt",
                    mime='text/plain'
                )
            else:
                st.download_button(
                    label="⬇️ Baixar Texto OCR",
                    data="Texto OCR não disponível",
                    file_name=f"ocr_documento_{doc.get('id', '')}.txt",
                    mime='text/plain',
                    disabled=True,
                    help="Texto OCR não disponível para este documento"
                )

def render(storage):
    """Render the documents listing and history page."""
    st.title('📋 Histórico de Documentos Fiscais')
    
    # Inicializa as variáveis de estado da sessão se não existirem
    if 'selected_doc_index' not in st.session_state:
        st.session_state.selected_doc_index = 0
    if 'show_document_details' not in st.session_state:
        st.session_state.show_document_details = False
    
    # Barra lateral para filtros
    st.sidebar.header('🔍 Filtros')
    
    # Filtros de busca
    with st.sidebar:
        st.markdown("### Pesquisar por")
        search_cnpj = st.text_input('CNPJ do Emitente')
        search_number = st.text_input('Número do Documento')
        
        # Filtro por tipo de documento
        doc_types = ['Todos', 'NFe', 'NFCe', 'CTe', 'Outros']
        selected_doc_type = st.selectbox('Tipo de Documento', doc_types)
        
        # Filtro por data
        st.markdown("### Período")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("De", value=None)
        with col2:
            end_date = st.date_input("Até", value=None)
        
        # Filtro por status de validação
        st.markdown("### Status de Validação")
        validation_status = st.radio(
            "Status",
            ["Todos", "Válidos", "Com Erros"],
            index=0,
            label_visibility="collapsed"
        )
        
        # Botão para aplicar filtros
        apply_filters = st.button("Aplicar Filtros")
    
    # Configuração de paginação
    if 'doc_page' not in st.session_state:
        st.session_state.doc_page = 1
    
    # Configura o número de itens por página
    page_size = 10
    
    # Aplica os filtros apenas se o botão for clicado ou se houver filtros ativos
    filters = {}
    
    # Verifica se o botão foi clicado
    if apply_filters or 'filters_applied' in st.session_state:
        st.session_state.filters_applied = True
        
        # Aplica filtros de texto
        if search_cnpj and search_cnpj.strip():
            filters['issuer_cnpj'] = search_cnpj.strip()
        if search_number and search_number.strip():
            filters['document_number'] = search_number.strip()
        if selected_doc_type != 'Todos':
            filters['document_type'] = selected_doc_type
        
        # Filtra por status de validação
        if validation_status == 'Válidos':
            filters['is_valid'] = True
        elif validation_status == 'Com Erros':
            filters['is_valid'] = False
            
        # Filtra por data
        if start_date is not None:
            filters['created_after'] = start_date.strftime('%Y-%m-%d')
        if end_date is not None:
            # Adiciona 1 dia para incluir o dia inteiro
            end_date_plus_one = end_date + timedelta(days=1)
            filters['created_before'] = end_date_plus_one.strftime('%Y-%m-%d')
    
    # Valores padrão para resultados e paginação
    docs: List[Dict[str, Any]] = []
    total = 0
    max_page = 1

    # Se não houver filtros ativos, busca todos os documentos
    
    try:
        result = storage.get_fiscal_documents(
            page=st.session_state.doc_page,
            page_size=page_size,
            **filters
        )
        
        # Obtém os documentos e informações de paginação
        if hasattr(result, 'items') and hasattr(result, 'total'):
            # Se for um objeto PaginatedResponse
            docs = result.items
            total = result.total
            max_page = result.total_pages if hasattr(result, 'total_pages') else ((total + page_size - 1) // page_size if page_size > 0 else 1)
        elif isinstance(result, dict) and 'items' in result and 'total' in result:
            # Se for um dicionário com estrutura de paginação
            docs = result['items']
            total = result['total']
            max_page = result.get('total_pages', (total + page_size - 1) // page_size if page_size > 0 else 1)
        else:
            # Se não tiver estrutura de paginação, assume que é uma lista direta
            docs = result if isinstance(result, list) else []
            total = len(docs)
            max_page = 1
        
        # Garante que max_page seja pelo menos 1
        max_page = max(1, max_page) if max_page is not None else 1
        
        # Ajusta a página atual se necessário
        if st.session_state.doc_page > max_page and max_page > 0:
            st.session_state.doc_page = max_page
            st.experimental_rerun()
            
    except Exception as e:
        st.error(f'Erro ao carregar documentos: {e}')
        max_page = 1

    # Exibe o resumo dos filtros
    st.markdown(f"""
    <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h3 style="margin: 0; color: #1f2937;">📊 Resumo</h3>
                <p style="margin: 0.5rem 0 0 0; color: #4b5563;">
                    {total} documento(s) encontrado(s) | Página {st.session_state.doc_page} de {max(1, max_page)}
                </p>
            </div>
            <div style="text-align: right;">
                <p style="margin: 0 0 0.5rem 0; color: #4b5563;">
                    <strong>Tipo:</strong> {selected_doc_type} | 
                    <strong>Status:</strong> {validation_status}
                </p>
                <p style="margin: 0; color: #4b5563;">
                    {f'<strong>Período:</strong> {start_date.strftime("%d/%m/%Y") if start_date else "-"} a {end_date.strftime("%d/%m/%Y") if end_date else "-"}'}
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Se não houver documentos, exibe mensagem
    if not docs:
        st.info('Nenhum documento encontrado com os filtros selecionados.')
        return
    
    # Prepara os dados para a tabela
    table_data = []
    for doc in docs:
        if not isinstance(doc, dict):
            continue
            
        # Obtém o resumo do documento
        doc_summary = get_document_summary(doc)
        
        # Adiciona à lista de dados da tabela
        doc_id = str(doc.get('id', ''))
        table_data.append({
            'Tipo': doc_summary.get('Tipo', 'N/A'),
            'Número': doc_summary.get('Número', 'N/A'),
            'Emitente': doc_summary.get('Emitente', 'N/A'),
            'CNPJ': doc_summary.get('CNPJ Emitente', 'N/A'),
            'Valor Total': doc_summary.get('Valor Total', 'R$ 0,00'),
            'Itens': doc_summary.get('Itens', 0),
            'Erros': doc_summary.get('Erros de Validação', 0),
            'Data': doc_summary.get('Data Processamento', 'N/A'),
            'Ações': doc_id,  # Usado para identificar o documento
            '_doc': doc  # Armazena o documento completo para referência
        })
    
    # Cria o DataFrame para a tabela usando a função segura
    df = safe_dataframe(table_data)
    if df is None:
        st.json(table_data)  # Mostra os dados em formato JSON se não for possível criar o DataFrame
        return
    
    # Exibe a tabela com os documentos
    st.markdown("### Documentos Encontrados")
    
    if len(table_data) > 0:
        # Cria um dicionário para mapear IDs de botão para documentos
        button_key_to_doc = {}
        
        # Cria as colunas da tabela
        cols = st.columns([1, 1, 2, 1, 1, 0.5, 0.5, 1, 1])
        
        # Cabeçalhos da tabela
        headers = ["Tipo", "Número", "Emitente", "CNPJ", "Valor Total", "Itens", "Erros", "Data", "Ações"]
        for i, header in enumerate(headers):
            cols[i].write(f"**{header}**")
        
        # Linhas da tabela
        for doc in table_data:
            cols = st.columns([1, 1, 2, 1, 1, 0.5, 0.5, 1, 1])
            
            # Colunas de dados
            cols[0].write(doc['Tipo'])
            cols[1].write(doc['Número'])
            cols[2].write(doc['Emitente'])
            cols[3].write(doc['CNPJ'])
            cols[4].write(doc['Valor Total'])
            cols[5].write(str(doc['Itens']))
            cols[6].write(str(doc['Erros']))
            cols[7].write(str(doc['Data']))
            
            # Botão de ação
            button_key = f"view_{doc['Ações']}"
            button_key_to_doc[button_key] = doc['_doc']
            
            if cols[8].button("👁️ Ver Detalhes", key=button_key, width='stretch'):
                st.session_state['selected_doc'] = doc['_doc']
        
        # Exibe os detalhes do documento selecionado
        if 'selected_doc' in st.session_state:
            st.markdown("---")
            render_document_details(st.session_state['selected_doc'])
            
            # Botão para fechar os detalhes
            if st.button("❌ Fechar Detalhes"):
                if 'selected_doc' in st.session_state:
                    del st.session_state['selected_doc']
                st.rerun()
    else:
        st.info("Nenhum documento encontrado com os filtros atuais.")
    
    # Controles de paginação
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.session_state.doc_page > 1:
            if st.button('⏪ Página Anterior'):
                st.session_state.doc_page = max(1, st.session_state.doc_page - 1)
                st.rerun()
    
    with col2:
        st.markdown(f"<div style='text-align: center; padding-top: 0.5rem;'>Página {st.session_state.doc_page} de {max_page} | Total: {total} documento(s)</div>", unsafe_allow_html=True)
    
    with col3:
        if st.session_state.doc_page < max_page:
            if st.button('Próxima Página ⏩'):
                st.session_state.doc_page = min(max_page, st.session_state.doc_page + 1)
                st.rerun()
    
    # Botão para exportar resultados
    if not df.empty:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### Exportar Resultados")
        
        # Remove a coluna _doc antes de exportar
        export_df = df.drop(columns=['_doc'], errors='ignore')
        
        # Opções de exportação
        export_format = st.sidebar.selectbox(
            'Formato de Exportação',
            ['CSV', 'Excel', 'JSON']
        )
        
        if st.sidebar.button(f'⬇️ Exportar Dados ({export_format})'):
            if export_format == 'CSV':
                csv = export_df.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')
                st.sidebar.download_button(
                    label="Baixar CSV",
                    data=csv,
                    file_name=f"documentos_fiscais_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime='text/csv'
                )
            elif export_format == 'Excel':
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    export_df.to_excel(writer, index=False, sheet_name='Documentos Fiscais')
                    
                    # Formatação condicional para a coluna de erros
                    workbook = writer.book
                    worksheet = writer.sheets['Documentos Fiscais']
                    
                    # Formato para células com erros
                    error_format = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
                    
                    # Aplica a formatação condicional
                    num_rows = len(export_df)
                    if num_rows > 0:
                        # A coluna 'Erros' está no índice 5 (0-based)
                        worksheet.conditional_format(
                            1, 6, num_rows, 6,  # Linha 1 é o cabeçalho
                            {
                                'type': 'cell',
                                'criteria': 'greater than',
                                'value': 0,
                                'format': error_format
                            }
                        )
                
                excel_data = output.getvalue()
                st.sidebar.download_button(
                    label="Baixar Excel",
                    data=excel_data,
                    file_name=f"documentos_fiscais_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
            elif export_format == 'JSON':
                json_data = export_df.to_json(orient='records', force_ascii=False, indent=2)
                st.sidebar.download_button(
                    label="Baixar JSON",
                    data=json_data,
                    file_name=f"documentos_fiscais_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime='application/json'
                )
        # Items table if present
        itens = None
        if doc.get('parsed') and isinstance(doc.get('parsed'), dict):
            itens = doc['parsed'].get('itens')
        elif doc.get('extracted_data'):
            itens = (doc['extracted_data'] or {}).get('itens')
            
        if itens:
            try:
                # dynamic import to avoid static linter errors when pandas isn't available
                pd_spec = importlib.util.find_spec('pandas')
                if pd_spec is not None:
                    pd = importlib.import_module('pandas')
                    df = pd.DataFrame(itens)
                    st.subheader('Itens')
                    st.dataframe(df)
                else:
                    raise ImportError('pandas not installed')
            except Exception:
                st.write(itens)
                
    with col2:
        if doc.get('classification'):
            document_renderer.render_validation_badge(doc['classification']['validacao']['status'])

    # Document history
    st.subheader('Histórico de eventos')
    history = []
    try:
        # Both backends implement get_document_history
        if doc.get('id'):
            history = storage.get_document_history(doc.get('id'))
    except Exception as e:
        st.error(f'Erro ao carregar histórico: {e}')
        
    if history:
        for h in history:
            st.write(h)
    else:
        st.info('Nenhum evento de histórico encontrado para este documento.')

    # Add history event form
    st.subheader('Adicionar evento ao histórico')
    evt_type = st.selectbox(
        'Tipo de evento',
        ['created', 'validated', 'classified', 'updated', 'note']
    )
    evt_note = st.text_area('Dados do evento (JSON ou texto curto)')
    
    if st.button('Adicionar evento'):
        raw_event_data = (evt_note or '').strip()
        if raw_event_data:
            try:
                event_data = json.loads(raw_event_data)
            except json.JSONDecodeError:
                event_data = {'note': raw_event_data}
        else:
            event_data = {}

        event = {
            'fiscal_document_id': doc.get('id'),
            'event_type': evt_type,
            'event_data': event_data
        }
        try:
            storage.save_history(event)
            st.success('✓ Evento adicionado com sucesso')
            if hasattr(st, 'experimental_rerun'):
                st.experimental_rerun()
            elif hasattr(st, 'rerun'):
                st.rerun()
            else:
                st.info('Atualize a página para ver o novo evento.')
        except Exception as e:
            st.error(f'Erro ao adicionar evento: {e}')