"""
Example: Configuration Usage

This script demonstrates how to use the configuration module
in your application code.
"""

from src.gml.core.config import get_settings, settings


def example_basic_usage():
    """Basic configuration access."""
    print("=" * 60)
    print("BASIC CONFIGURATION ACCESS")
    print("=" * 60)

    # Method 1: Using the cached settings instance
    print(f"App Name: {settings.APP_NAME}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"Log Level: {settings.LOG_LEVEL}")

    # Method 2: Using the getter function (returns same instance)
    config = get_settings()
    print(f"\nDatabase URL: {config.DATABASE_URL}")
    print(f"Redis URL: {config.REDIS_URL}")
    print(f"Qdrant URL: {config.QDRANT_URL}")


def example_environment_checks():
    """Check environment-specific behavior."""
    print("\n" + "=" * 60)
    print("ENVIRONMENT CHECKS")
    print("=" * 60)

    config = get_settings()

    print(f"Is Development: {config.is_development}")
    print(f"Is Staging: {config.is_staging}")
    print(f"Is Production: {config.is_production}")
    print(f"Recommended Pool Size: {config.database_pool_size}")


def example_safe_logging():
    """Safely log configuration (masks sensitive values)."""
    print("\n" + "=" * 60)
    print("SAFE CONFIGURATION DUMP")
    print("=" * 60)

    config = get_settings()
    safe_config = config.model_dump_safe()

    import json

    print(json.dumps(safe_config, indent=2))


def example_feature_flags():
    """Use configuration for feature flags."""
    print("\n" + "=" * 60)
    print("FEATURE FLAGS EXAMPLE")
    print("=" * 60)

    config = get_settings()

    # Example: Enable verbose logging in debug mode
    if config.DEBUG:
        print("✓ Verbose logging enabled")

    # Example: Use different timeout based on environment
    timeout = 5 if config.is_development else 30
    print(f"✓ API timeout set to: {timeout}s")

    # Example: Check if AI features are available
    if config.OPENAI_API_KEY:
        print("✓ AI features enabled")
    else:
        print("✗ AI features disabled (no API key)")


def example_database_config():
    """Access database configuration."""
    print("\n" + "=" * 60)
    print("DATABASE CONFIGURATION")
    print("=" * 60)

    config = get_settings()

    # Parse database URL components (simplified example)
    print(f"Database URL: {config.DATABASE_URL}")
    print(f"Pool Size: {config.database_pool_size}")

    # Example: Use in SQLAlchemy
    print("\nExample SQLAlchemy usage:")
    print(f"""
from sqlalchemy.ext.asyncio import create_async_engine
from src.gml.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size={config.database_pool_size},
    echo=settings.DEBUG
)
    """)


if __name__ == "__main__":
    try:
        example_basic_usage()
        example_environment_checks()
        example_feature_flags()
        example_database_config()
        example_safe_logging()

        print("\n" + "=" * 60)
        print("✓ All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
