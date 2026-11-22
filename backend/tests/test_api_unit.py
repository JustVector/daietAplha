"""Testy API bez prawdziwej bazy: /health przy działającej i niedostępnej bazie, format błędów."""

from collections.abc import Iterator

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine

from daiet_backend.db import get_engine
from daiet_backend.main import create_app

# Port 1 na localhost – połączenie odrzucone od razu, bez czekania na timeout
UNREACHABLE_DB_URL = "postgresql+psycopg://daiet:daiet@127.0.0.1:1/daiet"


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("DATABASE_URL", UNREACHABLE_DB_URL)
    app = create_app()

    failing = APIRouter()

    @failing.get("/_test/boom")
    def boom() -> None:
        raise RuntimeError("tajny szczegół wewnętrzny")

    app.include_router(failing)
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def test_health_ok_when_database_answers(client: TestClient) -> None:
    sqlite: Engine = create_engine("sqlite://")
    client.app.dependency_overrides[get_engine] = lambda: sqlite  # type: ignore[attr-defined]
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_503_when_database_unavailable(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "unavailable"}


def test_not_found_uses_common_error_format(client: TestClient) -> None:
    response = client.get("/nie-ma-takiego-adresu")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found", "error": "http_404"}


def test_unhandled_error_hides_details(client: TestClient) -> None:
    response = client.get("/_test/boom")
    assert response.status_code == 500
    assert response.json() == {"detail": "Wewnętrzny błąd serwera", "error": "internal_error"}
    assert "tajny" not in response.text


def test_openapi_documents_health(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()
    assert schema["info"]["title"] == "dAIet API"
    assert "/health" in schema["paths"]
    assert client.get("/docs").status_code == 200


def test_missing_database_url_stops_startup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.chdir("/")  # bez pliku .env w katalogu roboczym
    with pytest.raises(Exception, match="database_url"), TestClient(create_app()):
        pass
