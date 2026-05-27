"""Fixtures de teste compartilhadas."""

import pytest
from sqlalchemy import text

from src.core.db import SessionLocal, engine


@pytest.fixture
def db_session():
    """Sessão transacional contra o Postgres local; faz rollback ao final.

    Pula o teste se o banco estiver indisponível ou as migrations não tiverem
    sido aplicadas — assim a suíte passa em ambientes sem Postgres (ex.: CI sem
    serviço), enquanto roda de verdade em sessões web com o hook de bootstrap.
    """
    try:
        conn = engine.connect()
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"PostgreSQL indisponível: {exc}")

    trans = conn.begin()
    try:
        conn.execute(text("SELECT 1 FROM leiloeiros LIMIT 1"))
    except Exception as exc:  # noqa: BLE001
        trans.rollback()
        conn.close()
        pytest.skip(f"schema não migrado: {exc}")

    session = SessionLocal(bind=conn)
    try:
        yield session
    finally:
        session.close()
        trans.rollback()
        conn.close()
