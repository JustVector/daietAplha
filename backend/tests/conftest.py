"""Wspólne fixture'y testów backendu."""

from collections.abc import Iterator

import pytest

from daiet_backend.config import get_settings
from daiet_backend.db import get_engine


@pytest.fixture(autouse=True)
def _fresh_settings() -> Iterator[None]:
    """Każdy test czyta ustawienia i silnik od nowa (cache między testami by przeciekał)."""
    get_settings.cache_clear()
    get_engine.cache_clear()
    yield
    get_settings.cache_clear()
    get_engine.cache_clear()
