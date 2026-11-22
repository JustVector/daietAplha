# Obraz backendu dAIet. Budowanie z katalogu głównego repo (workspace uv):
#   docker build -f backend/Dockerfile .
# Gałąź Pythona 3.13 – ta sama co w .python-version, pyproject.toml i CI.
FROM python:3.13-slim-trixie

COPY --from=ghcr.io/astral-sh/uv:0.13.9 /uv /usr/local/bin/uv

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# Najpierw same zależności (warstwa cache'owana, dopóki nie zmieni się uv.lock)
COPY pyproject.toml uv.lock README.md ./
COPY backend/pyproject.toml backend/README.md backend/
RUN uv sync --locked --no-dev --package daiet-backend --no-install-workspace

# Potem kod backendu
COPY backend/ backend/
RUN uv sync --locked --no-dev --package daiet-backend \
    && useradd --create-home --uid 10001 app

USER app
ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app/backend
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=5 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"]

# Migracje przy starcie, potem serwer (exec – uvicorn dostaje sygnały zatrzymania)
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn daiet_backend.main:app --host 0.0.0.0 --port 8000"]
