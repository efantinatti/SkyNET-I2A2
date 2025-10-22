"""
SkyNET-I2A2 - Utilitários de Senha
Funções para hashing, verificação e validação de senhas usando bcrypt
"""

import bcrypt
import secrets
import string
from typing import Tuple
from datetime import datetime, timedelta

from ..config import settings


class PasswordManager:
    """Gerenciador de senhas com bcrypt"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Gera hash da senha usando bcrypt
        
        Args:
            password: Senha em texto plano
            
        Returns:
            Hash da senha em string
        """
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=settings.bcrypt_rounds)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Verifica se a senha corresponde ao hash
        
        Args:
            password: Senha em texto plano
            hashed_password: Hash armazenado
            
        Returns:
            True se a senha for válida
        """
        try:
            password_bytes = password.encode('utf-8')
            hashed_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception:
            return False
    
    @staticmethod
    def generate_secure_password(length: int = 12) -> str:
        """
        Gera uma senha segura aleatória
        
        Args:
            length: Comprimento da senha
            
        Returns:
            Senha segura gerada
        """
        if length < 8:
            length = 8
            
        # Garante pelo menos um de cada tipo
        password = [
            secrets.choice(string.ascii_lowercase),
            secrets.choice(string.ascii_uppercase),
            secrets.choice(string.digits),
            secrets.choice("!@#$%^&*")
        ]
        
        # Completa o resto aleatoriamente
        all_chars = string.ascii_letters + string.digits + "!@#$%^&*"
        for _ in range(length - 4):
            password.append(secrets.choice(all_chars))
        
        # Embaralha
        secrets.SystemRandom().shuffle(password)
        return ''.join(password)
    
    @staticmethod
    def check_password_strength(password: str) -> Tuple[bool, list]:
        """
        Verifica a força de uma senha
        
        Args:
            password: Senha para verificar
            
        Returns:
            Tuple (is_strong, list_of_issues)
        """
        issues = []
        
        if len(password) < 8:
            issues.append("Senha deve ter pelo menos 8 caracteres")
        
        if len(password) > 128:
            issues.append("Senha muito longa (máximo 128 caracteres)")
        
        if not any(c.islower() for c in password):
            issues.append("Senha deve conter pelo menos uma letra minúscula")
        
        if not any(c.isupper() for c in password):
            issues.append("Senha deve conter pelo menos uma letra maiúscula")
        
        if not any(c.isdigit() for c in password):
            issues.append("Senha deve conter pelo menos um número")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            issues.append("Senha deve conter pelo menos um caractere especial")
        
        # Verifica senhas comuns
        common_passwords = [
            "password", "123456", "123456789", "qwerty", "abc123",
            "password123", "admin", "123123", "senha123", "12345678"
        ]
        
        if password.lower() in common_passwords:
            issues.append("Senha muito comum, escolha uma mais segura")
        
        # Verifica padrões simples
        if password.lower() == password:
            issues.append("Senha deve conter letras maiúsculas")
        
        if password.upper() == password:
            issues.append("Senha deve conter letras minúsculas")
        
        if password.isdigit():
            issues.append("Senha não pode ser apenas números")
        
        # Verifica sequências
        sequences = ["123", "abc", "qwe", "asd", "zxc"]
        for seq in sequences:
            if seq in password.lower():
                issues.append("Evite sequências óbvias na senha")
                break
        
        return len(issues) == 0, issues


class PasswordResetManager:
    """Gerenciador de reset de senhas"""
    
    @staticmethod
    def generate_reset_token() -> str:
        """
        Gera token seguro para reset de senha
        
        Returns:
            Token de 32 caracteres
        """
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def is_token_expired(created_at: datetime, expires_in_hours: int = 1) -> bool:
        """
        Verifica se token de reset expirou
        
        Args:
            created_at: Data de criação do token
            expires_in_hours: Horas até expirar
            
        Returns:
            True se expirado
        """
        expiry_time = created_at + timedelta(hours=expires_in_hours)
        return datetime.utcnow() > expiry_time
    
    @staticmethod
    def hash_token(token: str) -> str:
        """
        Gera hash do token para armazenamento seguro
        
        Args:
            token: Token em texto plano
            
        Returns:
            Hash do token
        """
        return bcrypt.hashpw(token.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_token(token: str, hashed_token: str) -> bool:
        """
        Verifica se token corresponde ao hash
        
        Args:
            token: Token em texto plano
            hashed_token: Hash armazenado
            
        Returns:
            True se válido
        """
        try:
            return bcrypt.checkpw(token.encode('utf-8'), hashed_token.encode('utf-8'))
        except Exception:
            return False


class AccountSecurity:
    """Utilitários de segurança da conta"""
    
    @staticmethod
    def should_lock_account(failed_attempts: int, 
                           last_attempt: datetime = None) -> bool:
        """
        Verifica se conta deve ser bloqueada
        
        Args:
            failed_attempts: Número de tentativas falhadas
            last_attempt: Data da última tentativa
            
        Returns:
            True se deve bloquear
        """
        if failed_attempts >= settings.login_attempts_limit:
            # Se não há última tentativa registrada, bloqueia
            if not last_attempt:
                return True
            
            # Verifica se ainda está dentro da janela de tempo
            time_window = timedelta(seconds=settings.login_attempts_window)
            if datetime.utcnow() - last_attempt < time_window:
                return True
        
        return False
    
    @staticmethod
    def calculate_lockout_time(failed_attempts: int) -> datetime:
        """
        Calcula tempo de bloqueio baseado em tentativas falhadas
        
        Args:
            failed_attempts: Número de tentativas falhadas
            
        Returns:
            Data/hora quando bloqueio expira
        """
        # Bloqueio progressivo: 5 min, 15 min, 30 min, 1h, 2h
        lockout_minutes = min(5 * (2 ** (failed_attempts - settings.login_attempts_limit)), 120)
        return datetime.utcnow() + timedelta(minutes=lockout_minutes)
    
    @staticmethod
    def is_account_locked(locked_until: datetime = None) -> bool:
        """
        Verifica se conta está bloqueada
        
        Args:
            locked_until: Data/hora até quando está bloqueada
            
        Returns:
            True se bloqueada
        """
        if not locked_until:
            return False
        
        return datetime.utcnow() < locked_until
    
    @staticmethod
    def generate_session_token() -> str:
        """
        Gera token de sessão seguro
        
        Returns:
            Token de sessão
        """
        return secrets.token_urlsafe(64)


# Funções de conveniência (compatibilidade com código legacy)
def hash_password(password: str) -> str:
    """Conveniência: gera hash da senha"""
    return PasswordManager.hash_password(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Conveniência: verifica senha"""
    return PasswordManager.verify_password(password, hashed_password)


def generate_password(length: int = 12) -> str:
    """Conveniência: gera senha segura"""
    return PasswordManager.generate_secure_password(length)


def check_password_strength(password: str) -> Tuple[bool, list]:
    """Conveniência: verifica força da senha"""
    return PasswordManager.check_password_strength(password)


# Constantes de segurança
class SecurityConstants:
    """Constantes de segurança"""
    
    # Configurações de senha
    MIN_PASSWORD_LENGTH = 8
    MAX_PASSWORD_LENGTH = 128
    PASSWORD_HISTORY_COUNT = 5  # Últimas 5 senhas não podem ser reutilizadas
    
    # Configurações de bloqueio
    BASE_LOCKOUT_MINUTES = 5
    MAX_LOCKOUT_MINUTES = 120
    
    # Configurações de token
    RESET_TOKEN_LENGTH = 32
    SESSION_TOKEN_LENGTH = 64
    RESET_TOKEN_EXPIRY_HOURS = 1
    
    # Caracteres permitidos
    SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    # Mensagens de erro
    WEAK_PASSWORD_MSG = "Senha não atende aos critérios de segurança"
    ACCOUNT_LOCKED_MSG = "Conta temporariamente bloqueada por excesso de tentativas"
    INVALID_CREDENTIALS_MSG = "Email ou senha incorretos"
    TOKEN_EXPIRED_MSG = "Token expirado ou inválido"