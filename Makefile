.PHONY: install up down test lint format

# Instalacja zależności (uv) i hooków pre-commit
install:
	uv sync
	uv run pre-commit install

# Start PostgreSQL (od S-007 także backendu); czeka, aż serwisy będą zdrowe
up:
	docker compose up -d --wait

down:
	docker compose down

test:
	uv run pytest

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy .

format:
	uv run ruff format .
	uv run ruff check --fix .
