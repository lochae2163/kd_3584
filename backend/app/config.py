from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses pydantic for validation and type checking.
    """
    
    # Application
    app_name: str = "KvK Contribution Tracker"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours
    
    # Admin credentials (temporary - will move to database later)
    admin_username: str
    admin_password: str
    
    # Database
    mongodb_url: str
    database_name: str = "kd3584"
    
    # CORS
    cors_origins: List[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create single instance to use across app
settings = Settings()