"""
SkyNET-I2A2 - Configurações da Aplicação
Centraliza todas as configurações de ambiente, banco de dados, APIs, etc.
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import validator, Field


class Settings(BaseSettings):
    """Configurações da aplicação usando Pydantic Settings"""
    
    # Aplicação
    app_name: str = "SkyNET-I2A2"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"
    
    # Banco de Dados (Supabase)
    supabase_url: str = Field(..., description="URL do projeto Supabase")
    supabase_key: str = Field(..., description="Chave anônima do Supabase")
    supabase_service_role_key: Optional[str] = Field(None, description="Service role key para operações admin")
    
    # JWT & Autenticação
    jwt_secret_key: str = Field(..., description="Chave secreta para JWT")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    
    # Segurança
    bcrypt_rounds: int = 12
    login_attempts_limit: int = 5
    login_attempts_window: int = 600  # 10 minutos
    
    # APIs Externas
    google_api_key: str = Field(..., description="Chave da API Google Gemini")
    openai_api_key: Optional[str] = Field(None, description="Chave da API OpenAI (opcional)")
    
    # Cache & Redis
    redis_url: str = "redis://localhost:6379"
    redis_password: Optional[str] = None
    cache_ttl_hours: int = 24
    
    # Email
    sendgrid_api_key: Optional[str] = Field(None, description="Chave da API SendGrid")
    from_email: str = "noreply@skynet-i2a2.com"
    from_name: str = "SkyNET-I2A2"
    email_enabled: bool = True
    
    # Upload de Arquivos
    max_file_size_mb: int = 10
    allowed_extensions: List[str] = ["pdf", "xml", "csv", "xlsx", "xls"]
    upload_path: str = "uploads"
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    
    # Processamento
    max_concurrent_processes: int = 5
    processing_timeout_seconds: int = 300  # 5 minutos
    
    # LLM Settings
    gemini_model: str = "gemini-pro"
    openai_model: str = "gpt-4o"
    max_tokens: int = 4000
    temperature: float = 0.1
    
    # Auditoria
    audit_enabled: bool = True
    
    # Webhook (para integrações futuras)
    webhook_url: Optional[str] = None
    webhook_secret: Optional[str] = None
    
    # Ambiente
    environment: str = Field(default="development", description="development, staging, production")
    
    @validator('allowed_extensions')
    def validate_extensions(cls, v):
        """Valida extensões permitidas"""
        valid_extensions = ["pdf", "xml", "csv", "xlsx", "xls", "jpg", "jpeg", "png"]
        for ext in v:
            if ext.lower() not in valid_extensions:
                raise ValueError(f"Extensão '{ext}' não é válida")
        return [ext.lower() for ext in v]
    
    @validator('environment')
    def validate_environment(cls, v):
        """Valida ambiente"""
        if v not in ["development", "staging", "production"]:
            raise ValueError("Environment deve ser: development, staging ou production")
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Valida nível de log"""
        if v.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ValueError("Log level inválido")
        return v.upper()
    
    @property
    def is_production(self) -> bool:
        """Verifica se está em produção"""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Verifica se está em desenvolvimento"""
        return self.environment == "development"
    
    @property
    def database_url(self) -> str:
        """Constrói URL do banco Supabase"""
        return f"{self.supabase_url}/rest/v1"
    
    @property
    def max_file_size_bytes(self) -> int:
        """Converte tamanho máximo para bytes"""
        return self.max_file_size_mb * 1024 * 1024
    
    @property
    def cors_origins(self) -> List[str]:
        """Define origens CORS baseado no ambiente"""
        if self.is_production:
            return [
                "https://skynet-i2a2.streamlit.app",
                "https://app.skynet-i2a2.com"
            ]
        else:
            return [
                "http://localhost:3000",
                "http://localhost:8501",  # Streamlit
                "http://127.0.0.1:8501",
                "http://localhost:8000",  # FastAPI
            ]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        # Permite que variáveis de ambiente substituam valores padrão
        env_prefix = ""


# Configurações específicas por ambiente
class DevelopmentSettings(Settings):
    """Configurações para desenvolvimento"""
    debug: bool = True
    log_level: str = "DEBUG"
    environment: str = "development"


class ProductionSettings(Settings):
    """Configurações para produção"""
    debug: bool = False
    log_level: str = "WARNING"
    environment: str = "production"
    bcrypt_rounds: int = 14  # Mais seguro em produção


class TestSettings(Settings):
    """Configurações para testes"""
    debug: bool = True
    log_level: str = "DEBUG"
    environment: str = "testing"
    bcrypt_rounds: int = 4  # Mais rápido para testes
    

def get_settings() -> Settings:
    """Factory function para obter configurações baseado no ambiente"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestSettings()
    else:
        return DevelopmentSettings()


# Instância global das configurações
settings = get_settings()


# Configurações específicas para agentes
class AgentSettings:
    """Configurações específicas para os agentes AI"""
    
    # Configurações do CoordinatorAgent
    COORDINATOR_MAX_ITERATIONS = 5
    COORDINATOR_TIMEOUT = 30
    
    # Configurações do ExtractionAgent
    OCR_LANGUAGE = "por"  # Português
    OCR_CONFIDENCE_THRESHOLD = 0.7
    PDF_DPI = 300
    
    # Configurações do AnalystAgent
    MAX_ROWS_ANALYSIS = 100000  # Máximo de linhas para análise
    CORRELATION_THRESHOLD = 0.5
    OUTLIER_METHOD = "iqr"  # iqr, zscore
    
    # Configurações do ClassifierAgent
    FISCAL_VALIDATION_STRICT = True
    CFOP_VALIDATION_ENABLED = True
    NCM_VALIDATION_ENABLED = True
    
    # Configurações do VisualizationAgent
    CHART_WIDTH = 800
    CHART_HEIGHT = 600
    CHART_THEME = "plotly_white"
    MAX_CATEGORIES_PIE = 10
    
    # Configurações do ConsultantAgent
    INSIGHTS_MAX_LENGTH = 2000
    RECOMMENDATIONS_ENABLED = True


# Configurações de logging
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        },
        "detailed": {
            "format": "%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s"
        }
    },
    "handlers": {
        "default": {
            "level": settings.log_level,
            "formatter": "standard",
            "class": "logging.StreamHandler",
        },
        "file": {
            "level": "INFO",
            "formatter": "detailed",
            "class": "logging.FileHandler",
            "filename": "logs/app.log",
            "mode": "a",
        },
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["default", "file"] if settings.is_production else ["default"],
            "level": settings.log_level,
            "propagate": False
        },
        "uvicorn": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False
        },
        "sqlalchemy": {
            "handlers": ["default"],
            "level": "WARNING",
            "propagate": False
        }
    }
}


# Mensagens padrão do sistema
class Messages:
    """Mensagens padrão do sistema"""
    
    # Sucesso
    USER_CREATED = "Usuário criado com sucesso"
    LOGIN_SUCCESS = "Login realizado com sucesso"
    LOGOUT_SUCCESS = "Logout realizado com sucesso"
    DOCUMENT_UPLOADED = "Documento enviado com sucesso"
    ANALYSIS_COMPLETED = "Análise concluída com sucesso"
    
    # Erro
    INVALID_CREDENTIALS = "Email ou senha inválidos"
    USER_NOT_FOUND = "Usuário não encontrado"
    USER_ALREADY_EXISTS = "Email já está em uso"
    INVALID_TOKEN = "Token inválido ou expirado"
    FILE_TOO_LARGE = "Arquivo muito grande"
    INVALID_FILE_TYPE = "Tipo de arquivo não permitido"
    PROCESSING_ERROR = "Erro durante o processamento"
    
    # Validação
    INVALID_EMAIL = "Email inválido"
    WEAK_PASSWORD = "Senha muito fraca"
    REQUIRED_FIELD = "Campo obrigatório"
    
    # Sistema
    MAINTENANCE_MODE = "Sistema em manutenção"
    RATE_LIMITED = "Muitas tentativas. Tente novamente em alguns minutos"