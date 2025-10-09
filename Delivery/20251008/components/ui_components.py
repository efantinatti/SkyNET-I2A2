import streamlit as st
import pandas as pd
import time
import hashlib
from datetime import datetime, timezone, timedelta



def build_sidebar(memory, user_id):
    """Constrói a sidebar do aplicativo."""
    with st.sidebar:
        st.header("Análise EDA com IA")
        st.caption("👨‍💻 Ernani Fantinatti")

        # Key única baseada no user_id para manter consistência
        unique_key = f"file_uploader_{user_id}"

        uploaded_file = st.file_uploader(
            "Faça o upload do seu arquivo CSV",
            type=["csv"],
            accept_multiple_files=False,
            key=unique_key
        )

        st.subheader("Histórico de Sessões")
        sessions = memory.get_user_sessions(user_id)
        if sessions:
            for session in sessions:
                try:
                    # Converte a string de data/hora para um objeto datetime com timezone UTC
                    # O formato esperado é algo como '2025-09-26T22:26:00.000000+00:00'
                    created_at_str = session['created_at']
                    
                    # Verifica se já tem timezone (deve ter vindo do Supabase com +00:00)
                    if 'Z' in created_at_str or '+00:00' in created_at_str:
                        # Se já tiver timezone UTC, converte para objeto datetime com timezone
                        created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                        # Converte para o fuso horário local do sistema
                        local_time = created_at.astimezone()
                        # Obtém o offset local formatado (ex: -03:00)
                        offset = local_time.strftime('%z')
                        offset_str = f"UTC{offset[:3]}:{offset[3:5]}"
                    else:
                        # Se não tiver timezone, assume UTC e converte para local
                        created_at = datetime.fromisoformat(created_at_str).replace(tzinfo=timezone.utc)
                        local_time = created_at.astimezone()
                        offset = local_time.strftime('%z')
                        offset_str = f"UTC{offset[:3]}:{offset[3:5]}"
                    
                    st.info(
                        f"ID: ...{session['id'][-6:]}\n"
                        f"Dataset: {session['dataset_name']}\n"
                        f"Data: {local_time.strftime('%d/%m/%Y %H:%M')} ({offset_str})"
                    )
                except Exception as e:
                    st.error(f"Erro ao exibir sessão: {e}")
        else:
            st.write("Nenhuma sessão anterior encontrada.")

        st.subheader("Configurações")
        st.info("Configurações futuras aqui.")
    return uploaded_file


def display_chat_message(role, content, chart_fig=None, key=None, generated_code=None):
    """Exibe uma mensagem no chat."""
    execution_container = None
    results_container = None

    with st.chat_message(role):
        st.markdown(content)

        # Sempre exibe o código se estiver disponível (ANTES do gráfico)
        # O código deve aparecer antes do gráfico para melhor UX
        if generated_code and role == "assistant":
            execution_container, results_container = display_code_with_streamlit_suggestion(
                generated_code,
                auto_execute=False
            )

        # Verificar se o gráfico existe e é válido antes de exibir
        if chart_fig and role == "assistant":
            try:
                # Verificar se o gráfico ainda é válido
                if _is_chart_valid(chart_fig):
                    # Gera uma chave única se não foi fornecida
                    if key is None:
                        content_hash = hashlib.md5(f"{role}_{content}_{str(chart_fig)}".encode()).hexdigest()[:8]
                        key = f"chart_{role}_{content_hash}"

                    # Exibir o gráfico com verificação de erro
                    st.plotly_chart(chart_fig, use_container_width=True, key=key)
                else:
                    st.warning("⚠️ Gráfico não está mais disponível.")
                    st.info("O gráfico foi gerado anteriormente mas não pôde ser restaurado.")
            except Exception as e:
                # Se houver erro ao exibir o gráfico, mostrar aviso
                st.warning(f"⚠️ Erro ao exibir gráfico: {str(e)}")
                st.info("O gráfico foi gerado mas não pôde ser exibido.")

    return execution_container, results_container


def _is_chart_valid(chart_fig):
    """Verifica se um gráfico Plotly é válido e pode ser exibido."""
    try:
        if chart_fig is None:
            return False

        # Tentar serializar o gráfico para verificar se está íntegro
        chart_fig.to_json()
        return True
    except Exception:
        return False


def display_code_with_streamlit_suggestion(code, auto_execute=True):
    """Exibe código Python com opção de execução na própria interface."""
    st.code(code, language='python')

    if auto_execute:
        st.info("💡 **Código Gerado:** Este código será executado automaticamente na própria interface!")

        # Expander para mostrar que o código está sendo executado
        with st.expander("🔄 Executando código automaticamente...", expanded=True):
            st.markdown("**Status:** Executando código Python gerado...")

            # Simular execução (iremos implementar a execução real no app.py)
            execution_container = st.empty()

            # Placeholder para resultados da execução
            st.markdown("**Resultados da Execução:**")
            results_container = st.empty()

            # Retornar os containers para serem atualizados pelo app.py
            return execution_container, results_container

    # Quando auto_execute=False, apenas exibe o código sem containers
    return None, None