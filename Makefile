.PHONY: install up down logs migrate run test lint format fetch-usda

# Instalacja zależności (uv) i hooków pre-commit
install:
	uv sync
	uv run pre-commit install

# Start bazy i backendu (obraz budowany z bieżącego kodu); czeka, aż serwisy będą zdrowe
up:
	docker compose up -d --build --wait

down:
	docker compose down

logs:
	docker compose logs -f backend

# Migracje bazy (Alembic) w kontenerze backendu; backend robi je też sam przy starcie
migrate:
	docker compose exec backend alembic upgrade head

# Backend lokalnie, poza Dockerem, z przeładowaniem kodu (baza z make up, DATABASE_URL z .env)
run:
	uv run --directory backend uvicorn daiet_backend.main:app --reload --env-file ../.env

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy .

format:
	uv run ruff format .
	uv run ruff check --fix .

# Surowe dane USDA SR Legacy do data/raw/usda_sr_legacy/ (lokalna kopia z USDA_SOURCE_DIR albo pobranie)
fetch-usda:
	uv run python data-pipeline/fetch_usda.py
