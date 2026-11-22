"""Konfiguracja backendu – wyłącznie ze zmiennych środowiskowych i pliku .env."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Ustawienia aplikacji. Brak wymaganej zmiennej zatrzymuje start z czytelnym błędem."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # np. postgresql+psycopg://daiet:haslo@localhost:5432/daiet
    database_url: str
    log_level: LogLevel = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Ustawienia wczytywane raz na proces."""
    return Settings()  # type: ignore[call-arg]  # wartości pochodzą ze środowiska
