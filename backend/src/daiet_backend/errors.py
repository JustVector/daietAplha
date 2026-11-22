"""Spójny format błędów API: {"detail": ..., "error": "<kod>"}."""

import logging

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


def error_response(status_code: int, error: str, detail: object) -> JSONResponse:
    """Odpowiedź błędu w jednym formacie dla całego API."""
    return JSONResponse(
        status_code=status_code,
        content={"detail": jsonable_encoder(detail), "error": error},
    )


async def _http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    return error_response(exc.status_code, f"http_{exc.status_code}", exc.detail)


async def _validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    return error_response(422, "validation_error", exc.errors())


async def _unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Szczegóły tylko w logu – klient nie dostaje tracebacku
    logger.exception("Nieobsłużony wyjątek: %s %s", request.method, request.url.path)
    return error_response(500, "internal_error", "Wewnętrzny błąd serwera")


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    app.add_exception_handler(Exception, _unhandled_exception_handler)
