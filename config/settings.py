# config/settings.py
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Application
    APP_ENV: str = "development"
    APP_URL: str = "http://localhost:8501"
    SECRET_KEY: str
    DEBUG: bool = True

    # Database
    SUPABASE_URL: str
    SUPABASE_KEY: str
    DATABASE_URL: str

    # X/Twitter OAuth
    X_CLIENT_ID: Optional[str] = None
    X_CLIENT_SECRET: Optional[str] = None
    X_REDIRECT_URI: str = "http://localhost:8501/callback"

    # TwitterAPI.io
    TWITTERAPI_KEY: Optional[str] = None

    # xAI Grok (REPLACED Claude AI)
    XAI_API_KEY: Optional[str] = None

    # Stripe
    STRIPE_PUBLIC_KEY: Optional[str] = None
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None

    # Analytics
    POSTHOG_API_KEY: Optional[str] = None

    # Rate Limiting
    MAX_FREE_ANALYSES_PER_WEEK: int = 1
    MAX_PRO_ANALYSES_PER_DAY: int = 1
    CACHE_TTL_HOURS: int = 6

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()