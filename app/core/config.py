# app/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database settings (keeping your existing default)
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/fastapi_db"

    # JWT Settings
    JWT_SECRET_KEY: str
    JWT_REFRESH_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Security
    BCRYPT_ROUNDS: int = 12

    # Redis (optional, for token blacklisting)
    REDIS_URL: Optional[str] = "redis://localhost:6379/0"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create a global settings instance
settings = Settings()

# Optional: Add cached settings getter
@lru_cache()
def get_settings() -> Settings:
    return Settings()