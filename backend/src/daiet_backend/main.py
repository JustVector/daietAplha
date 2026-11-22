"""Aplikacja FastAPI. Uruchomienie: uvicorn daiet_backend.main:app"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from daiet_backend import __version__
from daiet_backend.api import health
from daiet_backend.config import get_settings
from daiet_backend.errors import register_error_handlers
from daiet_backend.logging_config import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Odczyt ustawień przy starcie: brak DATABASE_URL zatrzymuje aplikację od razu
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("Start backendu dAIet %s", __version__)
    yield
    logger.info("Zatrzymanie backendu dAIet")


def create_app() -> FastAPI:
    app = FastAPI(
        title="dAIet API",
        version=__version__,
        description=(
            "REST API planera posiłków dAIet. Jedyny dostęp do bazy danych – "
            "bot Discord, CLI i przyszły WebApp są klientami tego API."
        ),
        lifespan=lifespan,
    )
    register_error_handlers(app)
    app.include_router(health.router)
    return app


app = create_app()
