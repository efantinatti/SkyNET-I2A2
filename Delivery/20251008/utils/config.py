import os
import streamlit as st

def get_config():
    """Carrega e retorna as configurações do secrets.toml usando st.secrets (funciona local e no Streamlit Cloud)."""
    try:
        # st.secrets funciona tanto localmente (lendo .streamlit/secrets.toml) 
        # quanto no Streamlit Cloud (lendo do dashboard de secrets)
        return {
            "google_api_key": st.secrets["custom"]["google_api_key"],
            "supabase_url": st.secrets["custom"]["supabase_url"],
            "supabase_key": st.secrets["custom"]["supabase_key"],
        }
    except (KeyError, FileNotFoundError) as e:
        print(f"Aviso: Secrets não encontrados via st.secrets. Usando variáveis de ambiente como fallback. Erro: {e}")
        # Fallback para variáveis de ambiente
        return {
            "google_api_key": os.getenv("GOOGLE_API_KEY"),
            "supabase_url": os.getenv("SUPABASE_URL"),
            "supabase_key": os.getenv("SUPABASE_KEY"),
        }
    except Exception as e:
        print(f"Erro ao carregar configurações: {e}")
        return {
            "google_api_key": None,
            "supabase_url": None,
            "supabase_key": None,
        }