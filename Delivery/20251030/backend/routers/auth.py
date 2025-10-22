"""
SkyNET-I2A2 - Endpoints de Autenticação
Rotas FastAPI para registro, login, logout, reset de senha, etc.
"""

from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from ..auth.models import (
    UserCreate, UserLogin, UserResponse, LoginResponse, LogoutResponse,
    PasswordReset, PasswordResetConfirm, PasswordChange, RefreshTokenRequest,
    Token, TokenData
)
from ..auth.jwt_handler import JWTHandler, TokenValidator
from ..auth.password import PasswordManager, AccountSecurity
from ..core.memory import SupabaseManager
from ..config import settings, Messages

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])
security = HTTPBearer(auto_error=False)


# Dependency para obter usuário atual
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> TokenData:
    """Dependency para obter usuário autenticado atual"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso necessário",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = TokenValidator.validate_access_token(credentials.credentials)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data


# Dependency para verificar se usuário está ativo
async def get_active_user(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """Dependency para verificar se usuário está ativo"""
    supabase = SupabaseManager()
    
    user = await supabase.get_user_by_id(current_user.user_id)
    if not user or not user.get('is_active'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )
    
    return current_user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, request: Request):
    """
    Registra novo usuário
    """
    supabase = SupabaseManager()
    
    # Verifica se email já existe
    existing_user = await supabase.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=Messages.USER_ALREADY_EXISTS
        )
    
    # Valida força da senha
    is_strong, issues = PasswordManager.check_password_strength(user_data.password)
    if not is_strong:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Senha fraca: {', '.join(issues)}"
        )
    
    # Hash da senha
    password_hash = PasswordManager.hash_password(user_data.password)
    
    # Cria usuário
    user_dict = user_data.dict(exclude={'password', 'confirm_password'})
    user_dict['password_hash'] = password_hash
    user_dict['id'] = str(uuid4())
    
    try:
        created_user = await supabase.create_user(user_dict)
        
        # Log de auditoria
        await supabase.log_audit(
            user_id=created_user['id'],
            action="user_register",
            resource_type="user",
            resource_id=created_user['id'],
            details={"email": user_data.email, "ip": str(request.client.host)},
            ip_address=str(request.client.host)
        )
        
        # TODO: Enviar email de boas-vindas
        
        return UserResponse(**created_user)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor"
        )


@router.post("/login", response_model=LoginResponse)
async def login_user(user_data: UserLogin, request: Request, response: Response):
    """
    Realiza login do usuário
    """
    supabase = SupabaseManager()
    
    # Busca usuário pelo email
    user = await supabase.get_user_by_email(user_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=Messages.INVALID_CREDENTIALS
        )
    
    # Verifica se conta está bloqueada
    if AccountSecurity.is_account_locked(user.get('locked_until')):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Conta temporariamente bloqueada"
        )
    
    # Verifica senha
    if not PasswordManager.verify_password(user_data.password, user['password_hash']):
        # Incrementa tentativas falhadas
        failed_attempts = user.get('failed_login_attempts', 0) + 1
        
        update_data = {
            'failed_login_attempts': failed_attempts,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Bloqueia conta se necessário
        if AccountSecurity.should_lock_account(failed_attempts):
            update_data['locked_until'] = AccountSecurity.calculate_lockout_time(failed_attempts).isoformat()
        
        await supabase.update_user(user['id'], update_data)
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=Messages.INVALID_CREDENTIALS
        )
    
    # Login bem-sucedido - reseta tentativas falhadas
    await supabase.update_user(user['id'], {
        'failed_login_attempts': 0,
        'locked_until': None,
        'last_login': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    })
    
    # Cria tokens
    tokens = JWTHandler.create_token_pair(user['id'], user['email'])
    
    # Cria sessão
    session_data = {
        'id': str(uuid4()),
        'user_id': user['id'],
        'session_token': AccountSecurity.generate_session_token(),
        'ip_address': str(request.client.host),
        'user_agent': request.headers.get('user-agent', ''),
        'expires_at': (datetime.utcnow() + timedelta(days=7 if user_data.remember_me else 1)).isoformat()
    }
    
    session = await supabase.create_session(session_data)
    
    # Log de auditoria
    await supabase.log_audit(
        user_id=user['id'],
        action="user_login",
        resource_type="session",
        resource_id=session['id'],
        details={"ip": str(request.client.host), "user_agent": request.headers.get('user-agent')},
        ip_address=str(request.client.host)
    )
    
    # Define cookie de sessão se remember_me
    if user_data.remember_me:
        response.set_cookie(
            key="session_id",
            value=session['session_token'],
            max_age=30 * 24 * 60 * 60,  # 30 dias
            httponly=True,
            secure=settings.is_production,
            samesite="lax"
        )
    
    return LoginResponse(
        user=UserResponse(**user),
        tokens=Token(**tokens),
        session_id=session['id']
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout_user(
    request: Request,
    response: Response,
    current_user: TokenData = Depends(get_current_user)
):
    """
    Realiza logout do usuário
    """
    supabase = SupabaseManager()
    
    # Invalida sessão atual
    # TODO: Implementar blacklist de tokens
    
    # Remove cookie de sessão
    response.delete_cookie("session_id")
    
    # Log de auditoria
    await supabase.log_audit(
        user_id=current_user.user_id,
        action="user_logout",
        resource_type="session",
        resource_id="",
        details={"ip": str(request.client.host)},
        ip_address=str(request.client.host)
    )
    
    return LogoutResponse()


@router.post("/refresh", response_model=Token)
async def refresh_access_token(refresh_data: RefreshTokenRequest):
    """
    Renova access token usando refresh token
    """
    new_tokens = JWTHandler.refresh_access_token(refresh_data.refresh_token)
    
    if not new_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado"
        )
    
    return Token(**new_tokens)


@router.post("/forgot-password")
async def forgot_password(reset_data: PasswordReset):
    """
    Solicita reset de senha
    """
    supabase = SupabaseManager()
    
    user = await supabase.get_user_by_email(reset_data.email)
    if not user:
        # Não revela se email existe ou não por segurança
        return {"message": "Se o email existir, um link de reset será enviado"}
    
    # Gera token de reset
    reset_token = JWTHandler.create_reset_token(user['id'], user['email'])
    
    # Salva token no banco
    token_data = {
        'id': str(uuid4()),
        'user_id': user['id'],
        'token': reset_token,
        'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat()
    }
    
    await supabase.create_password_reset_token(token_data)
    
    # TODO: Enviar email com link de reset
    
    return {"message": "Se o email existir, um link de reset será enviado"}


@router.post("/reset-password")
async def reset_password(reset_data: PasswordResetConfirm):
    """
    Confirma reset de senha
    """
    supabase = SupabaseManager()
    
    # Valida token de reset
    token_data = TokenValidator.validate_reset_token(reset_data.token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado"
        )
    
    # Verifica se token ainda está válido no banco
    stored_token = await supabase.get_password_reset_token(reset_data.token)
    if not stored_token or stored_token.get('used_at'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token já foi usado ou expirado"
        )
    
    # Valida nova senha
    is_strong, issues = PasswordManager.check_password_strength(reset_data.new_password)
    if not is_strong:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Senha fraca: {', '.join(issues)}"
        )
    
    # Atualiza senha
    password_hash = PasswordManager.hash_password(reset_data.new_password)
    await supabase.update_user(token_data.user_id, {
        'password_hash': password_hash,
        'updated_at': datetime.utcnow().isoformat()
    })
    
    # Marca token como usado
    await supabase.update_password_reset_token(stored_token['id'], {
        'used_at': datetime.utcnow().isoformat()
    })
    
    return {"message": "Senha alterada com sucesso"}


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: TokenData = Depends(get_active_user)
):
    """
    Altera senha do usuário logado
    """
    supabase = SupabaseManager()
    
    # Busca usuário atual
    user = await supabase.get_user_by_id(current_user.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=Messages.USER_NOT_FOUND
        )
    
    # Verifica senha atual
    if not PasswordManager.verify_password(password_data.current_password, user['password_hash']):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta"
        )
    
    # Valida nova senha
    is_strong, issues = PasswordManager.check_password_strength(password_data.new_password)
    if not is_strong:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Senha fraca: {', '.join(issues)}"
        )
    
    # Atualiza senha
    password_hash = PasswordManager.hash_password(password_data.new_password)
    await supabase.update_user(current_user.user_id, {
        'password_hash': password_hash,
        'updated_at': datetime.utcnow().isoformat()
    })
    
    return {"message": "Senha alterada com sucesso"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: TokenData = Depends(get_active_user)):
    """
    Obtém informações do usuário atual
    """
    supabase = SupabaseManager()
    
    user = await supabase.get_user_by_id(current_user.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=Messages.USER_NOT_FOUND
        )
    
    return UserResponse(**user)


@router.get("/verify-token")
async def verify_token(current_user: TokenData = Depends(get_current_user)):
    """
    Verifica se token é válido
    """
    return {
        "valid": True,
        "user_id": str(current_user.user_id),
        "email": current_user.email,
        "expires_at": current_user.exp.isoformat() if current_user.exp else None
    }