.PHONY: install up down logs migrate run test lint format fetch-usda sr-wide nutrient-coverage product-list map-products portions cooked-variants product-tags

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

# Surowe dane USDA: SR Legacy do data/raw/usda_sr_legacy/ (lokalna kopia z USDA_SOURCE_DIR albo pobranie)
# i tabela retencji R6 do data/raw/usda_retention/ (S-106)
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

# Mapowanie listy produktów do fdc_id USDA (S-104): kandydaci, mapping.csv i raport braków;
# wiersze `zweryfikowany` w mapping.csv nie są nadpisywane
map-products:
	uv run python -X utf8 data-pipeline/map_products.py

# Miary domowe wariantów produktów (S-109): portions.csv i raport pokrycia;
# wymaga mapping.csv (make map-products) i danych z make fetch-usda
portions:
	uv run python -X utf8 data-pipeline/build_portions.py

# Warianty po obróbce termicznej (S-106): wyliczenie brakujących wariantów współczynnikami retencji R6
# i wydajności, raport pokrycia i tabela wartości z flagami measured/calculated w data/interim/;
# wymaga mapping.csv (make map-products) i danych z make fetch-usda
cooked-variants:
	uv run python -X utf8 data-pipeline/cooking.py

# Tagi wykluczeń i diet (S-108): propozycja automatyczna w tags/product_tags.csv (wiersze
# `zweryfikowany` nie są nadpisywane); wymaga mapping.csv (make map-products) i danych z make fetch-usda
product-tags:
	uv run python -X utf8 data-pipeline/product_tags.py
