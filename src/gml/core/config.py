"""
Configuration Management Module

This module provides centralized configuration management using Pydantic BaseSettings.
All configuration values are loaded from environment variables with sensible defaults
for development environments.

Features:
    - Type-safe configuration with Pydantic validation
    - Environment variable loading with .env file support
    - Singleton pattern for consistent configuration access
    - Sensible defaults for local development
    - Production-ready settings structure

Usage:
    >>> from src.gml.core.config import get_settings
    >>> settings = get_settings()
    >>> print(settings.APP_NAME)
    'gml-infrastructure'
"""

import logging
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """
    Application configuration settings.

    All settings can be overridden via environment variables.
    Loads from .env file in development environments.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",  # Allow extra fields for flexibility
    )

    # ============================================================================
    # APPLICATION SETTINGS
    # ============================================================================

    APP_NAME: str = Field(
        default="gml-infrastructure",
        description="Application name used in logging and monitoring",
    )

    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode (verbose logging, detailed errors)",
    )

    ENVIRONMENT: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Deployment environment identifier",
    )

    # ============================================================================
    # DATABASE & INFRASTRUCTURE
    # ============================================================================

    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/gml_db",
        description="PostgreSQL database connection URL",
    )

    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Redis cache connection URL",
    )

    # ============================================================================
    # PINECONE VECTOR DATABASE
    # ============================================================================

    PINECONE_API_KEY: str = Field(
        default="",
        description="Pinecone API key for vector database",
    )

    PINECONE_ENVIRONMENT: str = Field(
        default="us-east-1",
        description="Pinecone environment/region",
    )

    PINECONE_INDEX_NAME: str = Field(
        default="gml-memories",
        description="Pinecone index name for memory vectors",
    )

    # ============================================================================
    # SUPABASE CONFIGURATION (for future REST API usage)
    # ============================================================================

    SUPABASE_URL: str = Field(
        default="",
        description="Supabase project URL (for REST API)",
    )

    SUPABASE_ANON_KEY: str = Field(
        default="",
        description="Supabase anonymous key (public, for client-side)",
    )

    SUPABASE_SERVICE_KEY: str = Field(
        default="",
        description="Supabase service role key (secret, for server-side)",
    )

    # ============================================================================
    # SECURITY & AUTHENTICATION
    # ============================================================================

    SECRET_KEY: str = Field(
        default="dev-secret-key-change-in-production",
        description="Secret key for cryptographic operations",
    )

    # CORS Configuration for production
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Comma-separated list of allowed CORS origins (set to Vercel URL in production)",
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS into a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    ALGORITHM: str = Field(
        default="HS256",
        description="JWT signing algorithm",
    )

    JWT_EXPIRY_HOURS: int = Field(
        default=24,
        description="JWT token expiration time in hours",
        gt=0,
    )

    # ============================================================================
    # AI/ML CONFIGURATION
    # ============================================================================

    OPENAI_API_KEY: str = Field(
        default="",
        description="OpenAI API key for LLM and embedding operations",
    )

    OPENAI_MODEL: str = Field(
        default="gpt-4o-mini",
        description="Default OpenAI model identifier",
    )

    LLM_PROVIDER: Literal["openai", "openrouter", "ollama"] = Field(
        default="openrouter",
        description="LLM provider selection (openrouter is free-tier friendly)",
    )

    # OpenRouter Configuration (OpenAI-compatible API) - PRIMARY
    OPENROUTER_API_KEY: str = Field(
        default="",
        description="OpenRouter API key for LLM operations (PRIMARY)",
    )

    OPENROUTER_BASE_URL: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter OpenAI-compatible base URL",
    )

    OPENROUTER_MODEL: str = Field(
        default="meta-llama/llama-3.2-3b-instruct:free",
        description="Default OpenRouter model (free tier available)",
    )

    EMBEDDING_MODEL: str = Field(
        default="text-embedding-3-small",
        description="OpenAI embedding model identifier",
    )

    # Ollama Configuration
    OLLAMA_BASE_URL: str = Field(
        default="http://localhost:11434/v1",
        description="Ollama API base URL",
    )

    OLLAMA_API_KEY: str = Field(
        default="ollama",
        description="Ollama API key (dummy key for local)",
    )

    OLLAMA_MODEL: str = Field(
        default="gpt-oss:20b",
        description="Default Ollama model name",
    )

    USE_OLLAMA: bool = Field(
        default=False,
        description="Use Ollama instead of OpenAI for LLM operations",
    )

    @field_validator("OPENROUTER_API_KEY")
    @classmethod
    def validate_openrouter_key(cls, v: str) -> str:
        if v and not v.startswith("sk-"):
            logger.warning("OPENROUTER_API_KEY does not start with 'sk-'. Format may be invalid.")
        return v

    # ============================================================================
    # LOGGING CONFIGURATION
    # ============================================================================

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Application logging level",
    )

    # ============================================================================
    # VALIDATORS
    # ============================================================================

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Validate DATABASE_URL format."""
        if not v.startswith(("postgresql://", "postgres://")):
            raise ValueError("DATABASE_URL must start with 'postgresql://' or 'postgres://'")
        return v

    @field_validator("REDIS_URL")
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        """Validate REDIS_URL format."""
        if not v.startswith(("redis://", "rediss://")):
            raise ValueError("REDIS_URL must start with 'redis://' or 'rediss://'")
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str, info) -> str:
        """Warn if using default secret key in non-development environments."""
        environment = info.data.get("ENVIRONMENT", "development")
        if environment != "development" and v == "dev-secret-key-change-in-production":
            logger.warning(
                "Using default SECRET_KEY in %s environment! "
                "Generate a secure key with: openssl rand -hex 32",
                environment,
            )
        return v

    @field_validator("OPENAI_API_KEY")
    @classmethod
    def validate_openai_key(cls, v: str) -> str:
        """Validate OpenAI API key format."""
        if v and not v.startswith("sk-"):
            logger.warning("OPENAI_API_KEY does not start with 'sk-'. Format may be invalid.")
        return v

    # ============================================================================
    # COMPUTED PROPERTIES
    # ============================================================================

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"

    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.ENVIRONMENT == "staging"

    @property
    def database_pool_size(self) -> int:
        """Get recommended database connection pool size based on environment."""
        return 5 if self.is_development else 20

    @property
    def log_level_int(self) -> int:
        """Get numeric log level for Python logging module."""
        return getattr(logging, self.LOG_LEVEL)

    # ============================================================================
    # METHODS
    # ============================================================================

    def configure_logging(self) -> None:
        """
        Configure application logging based on settings.

        Sets up the root logger with appropriate level and format.
        """
        log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            if not self.DEBUG
            else "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
        )

        logging.basicConfig(
            level=self.log_level_int,
            format=log_format,
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        if self.is_development:
            logger.info("Logging configured for development environment")

    def model_dump_safe(self) -> dict:
        """
        Dump settings as dictionary with sensitive values masked.

        Returns:
            Dictionary with masked sensitive values
        """
        data = self.model_dump()

        # Mask sensitive values
        sensitive_keys = ["SECRET_KEY", "OPENAI_API_KEY", "QDRANT_API_KEY", "DATABASE_URL"]
        for key in sensitive_keys:
            if key in data and data[key]:
                if isinstance(data[key], str) and len(data[key]) > 8:
                    data[key] = data[key][:4] + "***" + data[key][-4:]
                else:
                    data[key] = "***"

        return data


@lru_cache()
def get_settings() -> Settings:
    """
    Get application settings (singleton).

    This function uses lru_cache to ensure only one Settings instance
    is created and reused throughout the application lifecycle.

    Returns:
        Settings instance with loaded configuration

    Example:
        >>> settings = get_settings()
        >>> print(settings.APP_NAME)
        'gml-infrastructure'

        >>> # Always returns the same instance
        >>> settings2 = get_settings()
        >>> assert settings is settings2
    """
    settings = Settings()

    # Configure logging on first access
    settings.configure_logging()

    if settings.is_development:
        logger.info("Settings loaded: %s", settings.APP_NAME)
        logger.debug("Configuration: %s", settings.model_dump_safe())

    return settings


# Convenience export for common usage pattern
settings = get_settings()


if __name__ == "__main__":
    # Example usage and validation
    config = get_settings()

    print(f"App Name: {config.APP_NAME}")
    print(f"Environment: {config.ENVIRONMENT}")
    print(f"Debug Mode: {config.DEBUG}")
    print(f"Log Level: {config.LOG_LEVEL}")
    print(f"\nDatabase URL: {config.DATABASE_URL}")
    print(f"Redis URL: {config.REDIS_URL}")
    print(f"Qdrant URL: {config.QDRANT_URL}")
    print(f"\nIs Development: {config.is_development}")
    print(f"Is Production: {config.is_production}")
    print(f"\nSafe Config Dump:")
    import json

    print(json.dumps(config.model_dump_safe(), indent=2))
