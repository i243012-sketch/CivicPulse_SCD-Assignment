"""Application configuration from environment variables."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Application
    APP_NAME: str = "CivicPulse"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str
    REDIS_CACHE_TTL_TRIAGE: int = 86400  # 24 hours
    REDIS_CACHE_TTL_STATS: int = 30  # 30 seconds

    # Triage Provider
    TRIAGE_PROVIDER: str = "llm"  # llm | rules | simulated

    # Groq API (LLM Provider)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "mixtral-8x7b-32768"
    GROQ_TIMEOUT: int = 10
    GROQ_MAX_RETRIES: int = 1

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_PER_MINUTE: int = 10

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Metrics
    METRICS_ENABLED: bool = True


settings = Settings()
