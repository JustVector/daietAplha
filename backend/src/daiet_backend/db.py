"""Połączenie z PostgreSQL (SQLAlchemy). Jedyne miejsce, w którym backend tworzy silnik bazy."""

from functools import lru_cache

from sqlalchemy import Engine, create_engine, text

from daiet_backend.config import get_settings

CONNECT_TIMEOUT_SECONDS = 3


@lru_cache
def get_engine() -> Engine:
    """Silnik współdzielony przez proces; pool_pre_ping odrzuca zerwane połączenia."""
    return create_engine(
        get_settings().database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": CONNECT_TIMEOUT_SECONDS},
    )


def database_is_available(engine: Engine) -> bool:
    """Sprawdza połączenie zapytaniem SELECT 1."""
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True
