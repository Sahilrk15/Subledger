"""Application configuration.

All settings come from environment variables (or a local .env file), so the
same code runs unchanged on a laptop, in Docker, or in production.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "SubLedger"
    # SQLite by default for quick local runs; docker-compose overrides this with PostgreSQL.
    database_url: str = "sqlite:///./subledger.db"
    # An invoice is due this many days after it is issued.
    invoice_due_days: int = 7


@lru_cache
def get_settings() -> Settings:
    return Settings()
