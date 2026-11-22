"""Test integracyjny /health z prawdziwym PostgreSQL.

Lokalnie: wymaga `make up` i DATABASE_URL (środowisko lub .env); bez bazy test jest pomijany.
W CI: REQUIRE_DB=1 – brak bazy to błąd, nie pominięcie.
"""

import os

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from daiet_backend.config import get_settings
from daiet_backend.db import database_is_available, get_engine
from daiet_backend.main import create_app


@pytest.fixture
def require_database() -> None:
    try:
        get_settings()
        database_is_available(get_engine())
    except (ValidationError, SQLAlchemyError) as error:
        if os.environ.get("REQUIRE_DB") == "1":
            pytest.fail(f"REQUIRE_DB=1, ale baza jest niedostępna: {error}")
        pytest.skip("brak działającej bazy (uruchom make up i ustaw DATABASE_URL)")


@pytest.mark.usefixtures("require_database")
def test_health_with_real_database() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
