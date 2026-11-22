.PHONY: install up down logs migrate run test lint format fetch-usda sr-wide nutrient-coverage product-list

# Instalacja zależności (uv, wszyscy członkowie workspace) i hooków pre-commit
install:
	uv sync --all-packages
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

# Tabela szeroka SR Legacy (1 wiersz = produkt) do data/interim/ – wymaga danych z make fetch-usda
sr-wide:
	uv run python data-pipeline/build_sr_wide.py

# Raport pokrycia składników odżywczych (docs/data/nutrient_coverage.md) i sprawdzenie nutrients.yaml
nutrient-coverage:
	uv run python data-pipeline/nutrient_coverage.py

# Walidacja i podsumowanie listy produktów podstawowych (data-pipeline/input/product_list.csv)
product-list:
	uv run python -X utf8 data-pipeline/product_list.py
