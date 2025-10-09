from langchain_google_genai import ChatGoogleGenerativeAI

import pandas as pd
import io
import json

def get_llm(api_key: str):
    """Retorna uma instância do LLM Gemini Flash com timeout."""
    try:
        return ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=api_key,
            temperature=0.0,
            request_timeout=30  # Timeout de 30 segundos
        )
    except Exception as e:
        error_msg = str(e)
        if "quota" in error_msg.lower() or "429" in error_msg:
            friendly_msg = (
                "Parece que excedemos o limite de requisições gratuitas da API do Gemini para hoje.\n\n"
                "- Limite diário atingido: 200 requisições\n"
                "- Tempo estimado para liberação: aproximadamente 1 minuto\n"
                "- Modelo afetado: Gemini 2.0 Flash\n\n"
                "O que você pode fazer:\n"
                "1. Aguarde cerca de 1 minuto antes de tentar novamente\n"
                "2. Se precisar de mais requisições, considere:\n"
                "   - Verificar seu plano e limites de cota\n"
                "   - Acessar: https://ai.google.dev/gemini-api/docs/rate-limits"
            )
            print(f"Erro de cota da API: {error_msg}")
            raise Exception(friendly_msg) from e
        
        print(f"Erro ao criar LLM: {error_msg}")
        raise e

def get_dataset_preview(df: pd.DataFrame) -> str:
    """Preview compacto para reduzir tokens."""
    MAX_COLS = 30
    MAX_ROWS_SAMPLE = 3  # Número de linhas para amostra
    cols = df.columns.tolist()[:MAX_COLS]
    dtypes = {c: str(df.dtypes[c]) for c in cols}
    sample = df[cols].head(MAX_ROWS_SAMPLE).to_dict(orient="records")

    preview = (
        f"Shape: {df.shape}\n"
        f"Columns (limited to {MAX_COLS}): {cols}\n"
        f"Dtypes: {dtypes}\n"
        f"Sample first {MAX_ROWS_SAMPLE} rows (dict): {sample}\n"
    )
    return preview