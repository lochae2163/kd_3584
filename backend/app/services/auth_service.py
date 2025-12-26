from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from app.config import settings


class AuthService:
    """Authentication service for admin users."""
    
    @staticmethod
    def verify_admin_credentials(username: str, password: str) -> bool:
        """
        Verify admin credentials against .env values.
        No password hashing for now (simple MVP).
        """
        return (
            username == settings.admin_username and
            password == settings.admin_password
        )
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token.
        
        Args:
            data: Payload to encode in the token
            expires_delta: Token expiration time
            
        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.access_token_expire_minutes
            )
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode,
            settings.secret_key,
            algorithm=settings.algorithm,
        )
        
        return encoded_jwt