"""GET /health – stan aplikacji i połączenia z bazą."""

import logging
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy import Engine
from sqlalchemy.exc import SQLAlchemyError

from daiet_backend.db import database_is_available, get_engine

logger = logging.getLogger(__name__)

router = APIRouter(tags=["system"])


class HealthStatus(BaseModel):
    status: Literal["ok", "error"]
    database: Literal["ok", "unavailable"]


@router.get(
    "/health",
    response_model=HealthStatus,
    summary="Stan aplikacji",
    description=(
        "Sprawdza połączenie z bazą (SELECT 1). 200 – wszystko działa, 503 – baza niedostępna."
    ),
    responses={503: {"model": HealthStatus, "description": "Baza danych niedostępna"}},
)
def health(response: Response, engine: Annotated[Engine, Depends(get_engine)]) -> HealthStatus:
    try:
        database_is_available(engine)
    except SQLAlchemyError as error:
        logger.warning("Healthcheck: baza danych niedostępna (%s)", type(error).__name__)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthStatus(status="error", database="unavailable")
    return HealthStatus(status="ok", database="ok")
