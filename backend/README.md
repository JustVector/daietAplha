# backend

REST API (FastAPI) na PostgreSQL, uruchamiane w Dockerze. Jedyne miejsce logiki i dostępu do danych –
bot Discord, CLI i przyszły WebApp są wyłącznie klientami tego API.

Zasada: LLM nigdy nie podaje wartości odżywczych – liczby pochodzą z bazy.

## Uruchomienie

| Komenda | Działanie |
| --- | --- |
| `make up` | buduje obraz i startuje bazę + backend; czeka, aż oba będą zdrowe |
| `make logs` | logi backendu |
| `make migrate` | migracje Alembic w kontenerze (backend robi je też sam przy starcie) |
| `make run` | backend lokalnie z przeładowaniem kodu (baza z `make up`, `DATABASE_URL` z `.env`) |

- API: http://localhost:8000, dokumentacja OpenAPI: http://localhost:8000/docs
- `GET /health` – `200 {"status": "ok", "database": "ok"}` albo `503` z `"database": "unavailable"`

## Struktura

| Ścieżka | Zawartość |
| --- | --- |
| `src/daiet_backend/main.py` | aplikacja FastAPI (`create_app`), start i zatrzymanie |
| `src/daiet_backend/config.py` | ustawienia z `.env` / środowiska (`DATABASE_URL`, `LOG_LEVEL`) |
| `src/daiet_backend/db.py` | silnik SQLAlchemy – jedyne miejsce połączenia z bazą |
| `src/daiet_backend/errors.py` | wspólny format błędów `{"detail": ..., "error": "<kod>"}` |
| `src/daiet_backend/logging_config.py` | jeden format logów na stdout (aplikacja i uvicorn) |
| `src/daiet_backend/api/` | endpointy (routery) |
| `migrations/` | migracje Alembic (`alembic.ini` obok); pierwsze tabele w S-201 |
| `tests/` | testy: jednostkowe bez bazy i integracyjne z PostgreSQL |
| `Dockerfile` | obraz `python:3.13-slim-trixie`, budowany z katalogu głównego repo |

Backend jest pakietem `daiet-backend` w workspace uv (jeden `uv.lock` w katalogu głównym). Nowa zależność
backendu: `uv add --package daiet-backend <pakiet>`.

## Testy

- `make test` – wszystkie testy. Test integracyjny `/health` potrzebuje bazy (`make up`) i `DATABASE_URL`;
  bez niej lokalnie jest pomijany.
- W CI baza PostgreSQL działa jako serwis, a `REQUIRE_DB=1` sprawia, że brak bazy to błąd, nie pominięcie.

## Dalszy zakres

- schemat bazy produktów i loader CSV → DB (S-201, S-202),
- encje użytkownika, historia planów, oceny dań (S-203, S-206, S-308),
- silnik więzów, kalkulator przepisu, adapter Claude API (E3),
- planer na N dni i lista zakupów (S-401, S-402).
