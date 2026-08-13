"""
Application configuration.

All values are loaded from environment variables (or a local .env file that
is NEVER committed to git). See .env.example at the project root for the
full list of variables this app expects.
"""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    ENV: str = "development"

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/lexora"

    # JWT
    JWT_SECRET: str = "insecure-dev-secret-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Google OAuth (Phase 3)
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None

    # AI / external APIs (later phases)
    GEMINI_API_KEY: Optional[str] = None
    GOOGLE_BOOKS_API_KEY: Optional[str] = None

    # URLs
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_URL: str = "http://localhost:8000"


settings = Settings()
