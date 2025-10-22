"""
SkyNET-I2A2 - Manipulador de JWT
Funções para criação, validação e decodificação de tokens JWT
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from uuid import UUID

from ..config import settings
from .models import TokenData, AuthConstants


class JWTHandler:
    """Manipulador de tokens JWT"""
    
    @staticmethod
    def create_access_token(
        user_id: UUID,
        email: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Cria token de acesso JWT
        
        Args:
            user_id: ID do usuário
            email: Email do usuário
            expires_delta: Tempo de expiração customizado
            
        Returns:
            Token JWT string
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.access_token_expire_minutes
            )
        
        payload = {
            AuthConstants.USER_ID_CLAIM: str(user_id),
            AuthConstants.EMAIL_CLAIM: email,
            AuthConstants.TYPE_CLAIM: AuthConstants.ACCESS_TOKEN,
            "exp": expire,
            "iat": datetime.utcnow(),
            "iss": settings.app_name,
        }
        
        return jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
    
    @staticmethod
    def create_refresh_token(
        user_id: UUID,
        email: str,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Cria token de refresh JWT
        
        Args:
            user_id: ID do usuário
            email: Email do usuário
            expires_delta: Tempo de expiração customizado
            
        Returns:
            Refresh token JWT string
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                days=settings.refresh_token_expire_days
            )
        
        payload = {
            AuthConstants.USER_ID_CLAIM: str(user_id),
            AuthConstants.EMAIL_CLAIM: email,
            AuthConstants.TYPE_CLAIM: AuthConstants.REFRESH_TOKEN,
            "exp": expire,
            "iat": datetime.utcnow(),
            "iss": settings.app_name,
        }
        
        return jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
    
    @staticmethod
    def create_reset_token(
        user_id: UUID,
        email: str,
        expires_hours: int = 1
    ) -> str:
        """
        Cria token para reset de senha
        
        Args:
            user_id: ID do usuário
            email: Email do usuário
            expires_hours: Horas até expirar
            
        Returns:
            Reset token JWT string
        """
        expire = datetime.utcnow() + timedelta(hours=expires_hours)
        
        payload = {
            AuthConstants.USER_ID_CLAIM: str(user_id),
            AuthConstants.EMAIL_CLAIM: email,
            AuthConstants.TYPE_CLAIM: AuthConstants.RESET_TOKEN,
            "exp": expire,
            "iat": datetime.utcnow(),
            "iss": settings.app_name,
        }
        
        return jwt.encode(
            payload,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm
        )
    
    @staticmethod
    def decode_token(token: str) -> Optional[TokenData]:
        """
        Decodifica e valida token JWT
        
        Args:
            token: Token JWT string
            
        Returns:
            TokenData se válido, None se inválido
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
                issuer=settings.app_name
            )
            
            user_id_str = payload.get(AuthConstants.USER_ID_CLAIM)
            if not user_id_str:
                return None
            
            return TokenData(
                user_id=UUID(user_id_str),
                email=payload.get(AuthConstants.EMAIL_CLAIM),
                exp=datetime.fromtimestamp(payload.get("exp", 0)),
                type=payload.get(AuthConstants.TYPE_CLAIM, AuthConstants.ACCESS_TOKEN)
            )
            
        except jwt.ExpiredSignatureError:
            # Token expirado
            return None
        except jwt.InvalidTokenError:
            # Token inválido
            return None
        except ValueError:
            # UUID inválido
            return None
    
    @staticmethod
    def is_token_expired(token_data: TokenData) -> bool:
        """
        Verifica se token está expirado
        
        Args:
            token_data: Dados do token decodificado
            
        Returns:
            True se expirado
        """
        if not token_data.exp:
            return True
        
        return datetime.utcnow() > token_data.exp
    
    @staticmethod
    def extract_token_from_header(authorization: str) -> Optional[str]:
        """
        Extrai token do header Authorization
        
        Args:
            authorization: Header Authorization completo
            
        Returns:
            Token string ou None
        """
        if not authorization:
            return None
        
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        
        return parts[1]
    
    @staticmethod
    def get_token_payload(token: str) -> Optional[Dict[str, Any]]:
        """
        Obtém payload do token sem validar assinatura (para debug)
        
        Args:
            token: Token JWT string
            
        Returns:
            Payload do token ou None
        """
        try:
            # Decodifica sem verificar assinatura (para debug apenas)
            return jwt.decode(token, options={"verify_signature": False})
        except Exception:
            return None
    
    @staticmethod
    def create_token_pair(user_id: UUID, email: str) -> Dict[str, str]:
        """
        Cria par de tokens (access + refresh)
        
        Args:
            user_id: ID do usuário
            email: Email do usuário
            
        Returns:
            Dict com access_token e refresh_token
        """
        access_token = JWTHandler.create_access_token(user_id, email)
        refresh_token = JWTHandler.create_refresh_token(user_id, email)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60
        }
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> Optional[Dict[str, str]]:
        """
        Gera novo access token usando refresh token
        
        Args:
            refresh_token: Refresh token válido
            
        Returns:
            Novo par de tokens ou None se inválido
        """
        token_data = JWTHandler.decode_token(refresh_token)
        
        if not token_data:
            return None
        
        if token_data.type != AuthConstants.REFRESH_TOKEN:
            return None
        
        if JWTHandler.is_token_expired(token_data):
            return None
        
        # Cria novo par de tokens
        return JWTHandler.create_token_pair(token_data.user_id, token_data.email)


class TokenValidator:
    """Validador de tokens com regras de negócio"""
    
    @staticmethod
    def validate_access_token(token: str) -> Optional[TokenData]:
        """
        Valida token de acesso com regras específicas
        
        Args:
            token: Token de acesso
            
        Returns:
            TokenData se válido
        """
        token_data = JWTHandler.decode_token(token)
        
        if not token_data:
            return None
        
        if token_data.type != AuthConstants.ACCESS_TOKEN:
            return None
        
        if JWTHandler.is_token_expired(token_data):
            return None
        
        return token_data
    
    @staticmethod
    def validate_refresh_token(token: str) -> Optional[TokenData]:
        """
        Valida refresh token
        
        Args:
            token: Refresh token
            
        Returns:
            TokenData se válido
        """
        token_data = JWTHandler.decode_token(token)
        
        if not token_data:
            return None
        
        if token_data.type != AuthConstants.REFRESH_TOKEN:
            return None
        
        if JWTHandler.is_token_expired(token_data):
            return None
        
        return token_data
    
    @staticmethod
    def validate_reset_token(token: str) -> Optional[TokenData]:
        """
        Valida token de reset de senha
        
        Args:
            token: Reset token
            
        Returns:
            TokenData se válido
        """
        token_data = JWTHandler.decode_token(token)
        
        if not token_data:
            return None
        
        if token_data.type != AuthConstants.RESET_TOKEN:
            return None
        
        if JWTHandler.is_token_expired(token_data):
            return None
        
        return token_data


# Middleware helpers
class TokenExtractor:
    """Extrator de tokens de diferentes fontes"""
    
    @staticmethod
    def from_header(request) -> Optional[str]:
        """Extrai token do header Authorization"""
        auth_header = request.headers.get(AuthConstants.AUTHORIZATION_HEADER)
        return JWTHandler.extract_token_from_header(auth_header)
    
    @staticmethod
    def from_cookie(request, cookie_name: str = "access_token") -> Optional[str]:
        """Extrai token de cookie"""
        return request.cookies.get(cookie_name)
    
    @staticmethod
    def from_query(request, param_name: str = "token") -> Optional[str]:
        """Extrai token de query parameter"""
        return request.query_params.get(param_name)


# Funções de conveniência
def create_access_token(user_id: UUID, email: str) -> str:
    """Conveniência: cria access token"""
    return JWTHandler.create_access_token(user_id, email)


def create_refresh_token(user_id: UUID, email: str) -> str:
    """Conveniência: cria refresh token"""
    return JWTHandler.create_refresh_token(user_id, email)


def decode_token(token: str) -> Optional[TokenData]:
    """Conveniência: decodifica token"""
    return JWTHandler.decode_token(token)


def validate_token(token: str) -> Optional[TokenData]:
    """Conveniência: valida access token"""
    return TokenValidator.validate_access_token(token)


# Exceções específicas
class JWTError(Exception):
    """Erro base para JWT"""
    pass


class TokenExpiredError(JWTError):
    """Token expirado"""
    pass


class InvalidTokenError(JWTError):
    """Token inválido"""
    pass


class UnsupportedTokenError(JWTError):
    """Tipo de token não suportado"""
    pass