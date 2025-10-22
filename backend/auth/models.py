"""
SkyNET-I2A2 - Modelos de Autenticação
Schemas Pydantic para validação de dados de usuários, tokens, etc.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, validator
from enum import Enum


class UserIndustryType(str, Enum):
    """Tipos de indústria/setor"""
    INDUSTRIA = "Indústria"
    COMERCIO = "Comércio" 
    AGRONEGOCIO = "Agronegócio"
    SERVICOS = "Serviços"
    TECNOLOGIA = "Tecnologia"
    OUTROS = "Outros"


class UserBase(BaseModel):
    """Schema base do usuário"""
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=255)
    company_name: Optional[str] = Field(None, max_length=255)
    industry: UserIndustryType = UserIndustryType.OUTROS
    phone: Optional[str] = Field(None, max_length=20)
    
    @validator('phone')
    def validate_phone(cls, v):
        """Valida formato do telefone brasileiro"""
        if v:
            import re
            # Remove caracteres não numéricos
            phone_clean = re.sub(r'[^0-9]', '', v)
            if len(phone_clean) not in [10, 11]:  # (11) 99999-9999 ou (11) 9999-9999
                raise ValueError('Telefone deve ter 10 ou 11 dígitos')
        return v


class UserCreate(UserBase):
    """Schema para criação de usuário"""
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('password')
    def validate_password_strength(cls, v):
        """Valida força da senha"""
        if len(v) < 8:
            raise ValueError('Senha deve ter pelo menos 8 caracteres')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('Senha deve conter ao menos uma letra maiúscula, minúscula e um número')
        
        return v
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Valida se senhas coincidem"""
        if 'password' in values and v != values['password']:
            raise ValueError('Senhas não coincidem')
        return v


class UserUpdate(BaseModel):
    """Schema para atualização de usuário"""
    full_name: Optional[str] = Field(None, max_length=255)
    company_name: Optional[str] = Field(None, max_length=255)
    industry: Optional[UserIndustryType] = None
    phone: Optional[str] = Field(None, max_length=20)


class UserInDB(UserBase):
    """Schema do usuário no banco de dados"""
    id: UUID
    password_hash: str
    is_active: bool = True
    is_verified: bool = False
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserResponse(UserBase):
    """Schema de resposta do usuário (sem dados sensíveis)"""
    id: UUID
    is_active: bool
    is_verified: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """Schema para login"""
    email: EmailStr
    password: str = Field(..., min_length=1)
    remember_me: bool = False


class PasswordReset(BaseModel):
    """Schema para reset de senha"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Schema para confirmação de reset de senha"""
    token: str = Field(..., min_length=32)
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Valida se senhas coincidem"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Senhas não coincidem')
        return v


class PasswordChange(BaseModel):
    """Schema para mudança de senha"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """Valida se senhas coincidem"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Senhas não coincidem')
        return v


class Token(BaseModel):
    """Schema do token JWT"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # Segundos até expirar


class TokenData(BaseModel):
    """Dados decodificados do token"""
    user_id: Optional[UUID] = None
    email: Optional[str] = None
    exp: Optional[datetime] = None
    type: str = "access"  # access, refresh


class RefreshTokenRequest(BaseModel):
    """Schema para refresh token"""
    refresh_token: str = Field(..., min_length=1)


class SessionCreate(BaseModel):
    """Schema para criação de sessão"""
    user_id: UUID
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class SessionInDB(BaseModel):
    """Schema da sessão no banco"""
    id: UUID
    user_id: UUID
    session_token: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    started_at: datetime
    last_activity: datetime
    expires_at: datetime
    is_active: bool = True
    
    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Schema de resposta do login"""
    user: UserResponse
    tokens: Token
    session_id: UUID
    message: str = "Login realizado com sucesso"


class LogoutResponse(BaseModel):
    """Schema de resposta do logout"""
    message: str = "Logout realizado com sucesso"


class UserStats(BaseModel):
    """Estatísticas do usuário"""
    total_documents: int = 0
    total_analyses: int = 0
    total_conversations: int = 0
    total_document_value: float = 0.0
    last_activity: Optional[datetime] = None


class UserWithStats(UserResponse):
    """Usuário com estatísticas"""
    stats: UserStats


# Validadores customizados
class EmailValidator:
    """Validadores para email"""
    
    @staticmethod
    def is_business_email(email: str) -> bool:
        """Verifica se é email corporativo"""
        free_providers = [
            'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
            'uol.com.br', 'terra.com.br', 'bol.com.br'
        ]
        domain = email.split('@')[1].lower()
        return domain not in free_providers


class SecurityValidators:
    """Validadores de segurança"""
    
    @staticmethod
    def check_password_compromised(password: str) -> bool:
        """Verifica se senha está em lista de senhas vazadas (simulado)"""
        # Em produção, integrar com HaveIBeenPwned API
        common_passwords = [
            '123456', 'password', '123456789', 'qwerty',
            'abc123', 'password123', 'admin', '123123'
        ]
        return password.lower() in common_passwords
    
    @staticmethod
    def is_suspicious_login(ip: str, user_agent: str, user_id: UUID) -> bool:
        """Detecta tentativas suspeitas de login (simulado)"""
        # Em produção, implementar detecção de anomalias
        # - Localização geográfica incomum
        # - User agent diferente
        # - Horário fora do padrão
        return False


# Exceções customizadas
class AuthenticationError(Exception):
    """Erro de autenticação"""
    pass


class AuthorizationError(Exception):
    """Erro de autorização"""
    pass


class AccountLockedError(Exception):
    """Conta bloqueada"""
    pass


class TokenExpiredError(Exception):
    """Token expirado"""
    pass


class WeakPasswordError(Exception):
    """Senha fraca"""
    pass


# Constantes
class AuthConstants:
    """Constantes de autenticação"""
    
    # Tipos de token
    ACCESS_TOKEN = "access"
    REFRESH_TOKEN = "refresh"
    RESET_TOKEN = "reset"
    
    # Headers
    AUTHORIZATION_HEADER = "Authorization"
    BEARER_PREFIX = "Bearer"
    
    # Claims JWT
    USER_ID_CLAIM = "user_id"
    EMAIL_CLAIM = "email"
    TYPE_CLAIM = "type"
    
    # Rate limiting
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30
    
    # Session
    SESSION_COOKIE_NAME = "session_id"
    REMEMBER_ME_DAYS = 30