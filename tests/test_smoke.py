"""Test dymny środowiska: czy testy uruchamiają się na właściwej wersji Pythona."""

import sys


def test_python_version_is_313() -> None:
    """Projekt jest przypięty do gałęzi 3.13 (decyzja z S-003)."""
    assert sys.version_info[:2] == (3, 13)
