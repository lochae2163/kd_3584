from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    """Application settings."""
    
    # Application
    app_name: str = "KvK Kingdom Tracker"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Security
    secret_key: str = "default-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    
    # Admin
    admin_username: str = "admin"
    admin_password: str = "admin123"
    
    # Database
    mongodb_url: str = ""
    database_name: str = "kvk_tracker"
    
    # CORS
    cors_origins: List[str] = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()