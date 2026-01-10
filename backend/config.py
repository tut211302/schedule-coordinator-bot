"""
Application configuration using pydantic-settings.
All sensitive values are loaded from environment variables or .env file.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = "mysql+mysqlconnector://devuser:devpass123@db:3306/calendar_db"
    
    # LINE Messaging API
    LINE_CHANNEL_SECRET: str = ""
    LINE_CHANNEL_ACCESS_TOKEN: str = ""
    BOT_MENTION: str = ""  # e.g., "@schedule-bot"
    
    # Google OAuth 2.0
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:3000/auth/google/callback"
    
    # Application
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra env vars


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Using lru_cache to avoid reading .env file on every request.
    """
    return Settings()


settings = get_settings()
