from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "ai-engine/.env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "FinTrace API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # SQLite default for hackathon MVP, PostgreSQL-ready architecture
    DATABASE_URL: str = "sqlite:///./fintrace.db"

    # AI Provider Credentials (loaded strictly from environment, never hardcoded)
    GROQ_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None

    # Model identifiers
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"

    PRIMARY_AI_PROVIDER: str = "groq"
    SECONDARY_AI_PROVIDER: str = "gemini"
    AI_REQUEST_TIMEOUT_SECONDS: float = 25.0
    AI_MAX_RETRIES: int = 2

    # CORS configuration
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # Authentication & Security
    JWT_SECRET_KEY: str = "fintrace-production-auth-jwt-secret-key-32-chars-min-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    @property
    def cors_origins_list(self) -> List[str]:
        if not self.CORS_ORIGINS:
            return ["*"]
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
