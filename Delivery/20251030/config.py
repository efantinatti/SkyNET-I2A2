"""
Project configuration loader.

Loads values from environment variables first. If not present, tries to read
Streamlit secrets via `streamlit.secrets` (when available). As a final fallback
it will try to parse `.streamlit/secrets.toml` in the project root.

Exports commonly used keys like SUPABASE_URL and SUPABASE_KEY so `app.py` can
import a single source of truth.
"""
from pathlib import Path
import os
from typing import Dict


def _read_secrets_file(path: Path) -> Dict[str, str]:
    """Parse a very small TOML-like KEY=VALUE secrets file used by Streamlit.
    This is intentionally permissive and only supports simple KEY=VALUE lines.
    """
    if not path.exists():
        return {}
    out = {}
    for raw in path.read_text(encoding='utf-8').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or line.startswith('['):
            continue
        if '=' not in line:
            continue
        k, v = line.split('=', 1)
        k = k.strip()
        v = v.strip().strip('"').strip("'")
        out[k] = v
    return out


# try to get Streamlit secrets if running under Streamlit
_streamlit_secrets = {}
try:
    import streamlit as _st
    _streamlit_secrets = getattr(_st, 'secrets', {}) or {}
except Exception:
    _streamlit_secrets = {}

# read file fallback
_project_root = Path(__file__).resolve().parent
_secrets_file = _project_root / '.streamlit' / 'secrets.toml'
_file_secrets = _read_secrets_file(_secrets_file)

# Compose final secrets: env vars override Streamlit secrets override file secrets
def _get(key: str, default=None):
    # For Supabase database configuration, prioritize file secrets over environment variables
    # to avoid conflicts with system user variables
    if key in ['USER', 'user', 'PASSWORD', 'password', 'HOST', 'host', 'PORT', 'port', 'DATABASE', 'database']:
        return _file_secrets.get(key) or _streamlit_secrets.get(key) or os.getenv(key) or default
    else:
        return os.getenv(key) or _streamlit_secrets.get(key) or _file_secrets.get(key) or default


# Common config entries
# Try to get Supabase URL and KEY from environment variables or secrets.toml
SUPABASE_URL = _get('SUPABASE_URL') or _get('connections.supabase.URL')
SUPABASE_KEY = _get('SUPABASE_KEY') or _get('connections.supabase.KEY')

# Database connection settings for direct database access (migrations)
# Prioritize root level settings from secrets.toml, then fallback to connections section
DATABASE = _get('DATABASE') or _get('connections.supabase.database.DATABASE') or 'postgres'
DB_USER = _get('USER') or _get('connections.supabase.database.USER')
DB_PASSWORD = _get('PASSWORD') or _get('connections.supabase.database.PASSWORD')
DB_HOST = _get('HOST') or _get('connections.supabase.database.HOST')
DB_PORT = _get('PORT') or _get('connections.supabase.database.PORT') or '5432'
DB_POOL_MODE = _get('POOL_MODE') or _get('connections.supabase.database.POOL_MODE') or 'transaction'
DB_SSL_MODE = _get('SSL_MODE') or _get('connections.supabase.database.SSL_MODE') or 'require'
DB_CONNECT_TIMEOUT = _get('CONNECT_TIMEOUT') or _get('connections.supabase.database.CONNECT_TIMEOUT') or '10'

# Other settings
GOOGLE_API_KEY = _get('GOOGLE_API_KEY')
TESSERACT_PATH = _get('TESSERACT_PATH')
LOG_LEVEL = _get('LOG_LEVEL', 'INFO')

# FiscalValidatorAgent settings
FISCAL_VALIDATOR_CONFIG = {
    'api_key': GOOGLE_API_KEY,  # Usando a mesma chave da API do Google
    'cache_enabled': _get('FISCAL_VALIDATOR.cache_enabled', 'true').lower() == 'true',
    'cache_dir': _get('FISCAL_VALIDATOR.cache_dir', '.fiscal_cache'),
    'cache_ttl_days': int(_get('FISCAL_VALIDATOR.cache_ttl_days', '30')),
    'model_name': 'gemini-1.5-flash'  # Modelo mais avançado
}

# Database connection details for direct database access (migrations and direct queries)
DATABASE_CONFIG = {
    'dbname': DATABASE,
    'user': DB_USER,
    'password': DB_PASSWORD,
    'host': DB_HOST,
    'port': DB_PORT,
    'sslmode': DB_SSL_MODE,
    'connect_timeout': DB_CONNECT_TIMEOUT
}

# Connection string for direct database access (for SQLAlchemy, psycopg2, etc.)
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DATABASE}?sslmode={DB_SSL_MODE}&connect_timeout={DB_CONNECT_TIMEOUT}"

# Supabase client configuration (for API access - only for auth/chat if needed)
SUPABASE_CONFIG = {
    'url': SUPABASE_URL,
    'key': SUPABASE_KEY,
    'service_key': SUPABASE_KEY  # Add this if you need to use the service role key
}

# SQLAlchemy engine URL for migrations
SQLALCHEMY_DATABASE_URL = DATABASE_URL

# Tesseract path - configuração para Windows e Linux
TESSERACT_PATH = _get('TESSERACT_PATH')
TESSDATA_PREFIX = _get('TESSDATA_PREFIX')

# Se não estiver definido, tenta encontrar automaticamente
if not TESSERACT_PATH:
    import platform
    
    if platform.system() == 'Windows':
        # Caminhos comuns no Windows
        alt_paths = [
            'C:\\Program Files\\Tesseract-OCR\\tesseract.exe',
            'C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe',
            'D:\\Program Files\\Tesseract-OCR\\tesseract.exe'
        ]
        TESSDATA_PREFIX = TESSDATA_PREFIX or 'C:\\Program Files\\Tesseract-OCR'
    else:
        # Caminhos comuns no Linux/Streamlit Cloud
        alt_paths = [
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract',
            '/app/.apt/usr/bin/tesseract',
            '/home/appuser/streamlit-app/tesseract/tesseract',
            '/usr/bin/tesseract-ocr',
            '/usr/local/bin/tesseract-ocr'
        ]
        TESSDATA_PREFIX = TESSDATA_PREFIX or '/usr/share/tesseract-ocr/4.00/tessdata/'
    
    # Tenta usar o primeiro caminho disponível sem verificar a existência
    TESSERACT_PATH = alt_paths[0] if alt_paths else 'tesseract'

# Configura o TESSDATA_PREFIX como variável de ambiente se não estiver definido
if TESSDATA_PREFIX and 'TESSDATA_PREFIX' not in os.environ:
    os.environ['TESSDATA_PREFIX'] = TESSDATA_PREFIX

LOG_LEVEL = _get('LOG_LEVEL', 'INFO')


# Configurações para o DocumentAgent
UPLOAD_DIR = os.getenv('UPLOAD_DIR', str(Path(__file__).parent / 'uploads'))
PROCESSED_DIR = os.getenv('PROCESSED_DIR', str(Path(__file__).parent / 'processed'))

# Cria os diretórios se não existirem
Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
Path(PROCESSED_DIR).mkdir(parents=True, exist_ok=True)

# Expose a dict if callers prefer
ALL = {
    'SUPABASE_URL': SUPABASE_URL,
    'SUPABASE_KEY': SUPABASE_KEY,
    'DATABASE': DATABASE,
    'DB_USER': DB_USER,
    'DB_PASSWORD': DB_PASSWORD,
    'DB_HOST': DB_HOST,
    'DB_PORT': DB_PORT,
    'DB_POOL_MODE': DB_POOL_MODE,
    'DB_SSL_MODE': DB_SSL_MODE,
    'DB_CONNECT_TIMEOUT': DB_CONNECT_TIMEOUT,
    'DATABASE_CONFIG': DATABASE_CONFIG,
    'DATABASE_URL': DATABASE_URL,
    'SQLALCHEMY_DATABASE_URL': SQLALCHEMY_DATABASE_URL,
    'TESSERACT_PATH': TESSERACT_PATH,
    'GOOGLE_API_KEY': GOOGLE_API_KEY,
    'LOG_LEVEL': LOG_LEVEL,
    'UPLOAD_DIR': UPLOAD_DIR,
    'PROCESSED_DIR': PROCESSED_DIR,
}
