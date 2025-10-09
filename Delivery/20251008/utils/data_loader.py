import pandas as pd
import io
import hashlib


def load_csv(uploaded_file, max_size_mb=200):
    """Carrega, valida e detecta automaticamente o formato de um arquivo CSV."""
    if uploaded_file.size > max_size_mb * 1024 * 1024:
        raise ValueError(f"Arquivo excede o tamanho máximo de {max_size_mb} MB.")

    # Tenta diferentes encodings e separadores
    encodings = ['utf-8', 'iso-8859-1', 'latin1']
    separators = [',', ';', '\t', '|']

    file_content = uploaded_file.getvalue()

    for encoding in encodings:
        try:
            content_str = file_content.decode(encoding)
            for sep in separators:
                try:
                    df = pd.read_csv(io.StringIO(content_str), sep=sep)
                    # Heurística simples: se a maioria das colunas foi criada, sucesso.
                    if len(df.columns) > 1 or sep == separators[-1]:
                        # Calcula o hash do conteúdo para identificar o dataset
                        file_hash = hashlib.md5(file_content).hexdigest()
                        return df, file_hash
                except Exception:
                    continue
        except UnicodeDecodeError:
            continue

    raise ValueError("Não foi possível decodificar ou parsear o arquivo CSV. Verifique o encoding e o separador.")


def get_dataset_info(df: pd.DataFrame, dataset_name: str) -> dict:
    """Extrai metadados e estatísticas básicas de um dataframe."""
    buffer = io.StringIO()
    df.info(buf=buffer)
    info_str = buffer.getvalue()

    return {
        "name": dataset_name,
        "shape": df.shape,
        "columns": df.columns.tolist(),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "missing_values": df.isnull().sum().to_dict(),
        "duplicated_rows": int(df.duplicated().sum()),
        "info_string": info_str,
        "head": df.head().to_json(orient='split')
    }