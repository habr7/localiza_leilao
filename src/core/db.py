"""Infraestrutura de acesso ao banco: engine, sessões e Base declarativa."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from src.core.config import settings


class Base(DeclarativeBase):
    """Base declarativa compartilhada por todos os modelos ORM."""


# Engine único da aplicação. `pool_pre_ping` evita conexões mortas no pool.
engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)

# Fábrica de sessões. `expire_on_commit=False` mantém objetos utilizáveis
# após o commit (conveniente para scripts e testes).
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@contextmanager
def get_session() -> Iterator[Session]:
    """Abre uma sessão, faz commit ao final e rollback em caso de erro."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
