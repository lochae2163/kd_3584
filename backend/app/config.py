from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import List
import os

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All sensitive values MUST be provided via .env file.
    See .env.example for configuration template.
    """

    # Application
    app_name: str = "KvK Kingdom Tracker"
    app_version: str = "1.0.0"
    debug: bool = False

    # Security - NO DEFAULTS FOR PRODUCTION SAFETY
    secret_key: str = Field(
        ...,  # Required field, no default
        min_length=32,
        description="JWT secret key. Generate with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # Admin - NO DEFAULTS FOR PRODUCTION SAFETY
    admin_username: str = Field(
        ...,  # Required field, no default
        min_length=4,
        description="Admin username for dashboard access"
    )
    admin_password: str = Field(
        ...,  # Required field, no default
        min_length=8,
        description="Admin password - MUST be strong and unique"
    )
    admin_email: str = "admin@kd3584tracker.com"

    # SendGrid (optional - for password reset emails)
    sendgrid_api_key: str = ""
    sendgrid_from_email: str = "noreply@kd3584tracker.com"

    # Database - REQUIRED
    mongodb_url: str = Field(
        ...,  # Required field, no default
        description="MongoDB connection string"
    )
    database_name: str = "kvk_tracker"

    # Redis (optional - for caching)
    redis_url: str = Field(
        default="",
        description="Redis connection URL for caching (optional). Example: redis://localhost:6379"
    )

    # CORS - NO WILDCARD DEFAULT
    cors_origins: List[str] = Field(
        default=[],  # Empty by default - must be explicitly configured
        description="List of allowed CORS origins. NO wildcards in production!"
    )

    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v):
        """Ensure secret key is not a default/weak value."""
        weak_keys = [
            'default-secret-key-change-in-production',
            'your-secret-key-here',
            'secret',
            'password',
            '12345'
        ]
        if any(weak in v.lower() for weak in weak_keys):
            raise ValueError(
                "SECRET_KEY appears to be a default/weak value. "
                "Generate a strong key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'"
            )
        return v

    @field_validator('admin_password')
    @classmethod
    def validate_admin_password(cls, v):
        """Ensure admin password is not a default/weak value."""
        weak_passwords = [
            'admin',
            'admin123',
            'password',
            '12345',
            'your-password-here'
        ]
        if v.lower() in weak_passwords:
            raise ValueError(
                "ADMIN_PASSWORD is too weak or default. "
                "Use a strong password with 16+ characters, mixed case, numbers, and symbols."
            )
        return v

    @field_validator('cors_origins')
    @classmethod
    def validate_cors_origins(cls, v):
        """Warn if wildcard CORS is used."""
        if "*" in v and not os.getenv('DEBUG', 'false').lower() == 'true':
            raise ValueError(
                "Wildcard '*' in CORS_ORIGINS is not allowed in production. "
                "Specify exact allowed origins in .env file."
            )
        return v

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env

settings = Settings()