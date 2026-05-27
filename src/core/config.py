"""Configuração da aplicação carregada a partir do ambiente (.env)."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações globais lidas de variáveis de ambiente / arquivo .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # URL de conexão com o PostgreSQL (formato SQLAlchemy/psycopg2).
    database_url: str = "postgresql://user:pass@localhost:5432/leiloes"
    # Nível de log usado pelo structlog (DEBUG, INFO, WARNING, ...).
    log_level: str = "INFO"


def get_settings() -> Settings:
    """Retorna uma instância de Settings (lê o .env na primeira chamada)."""
    return Settings()


settings = get_settings()
