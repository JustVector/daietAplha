"""Słownik kategorii produktów podstawowych (S-105): wczytanie i walidacja `categories.yaml`.

Dwa poziomy: kategoria → podkategoria. Walidacja sprawdza typy pól, format kodów (snake_case),
unikalność kodów w całym pliku i polskich nazw (kategorii w pliku, podkategorii w kategorii)
oraz to, że każda kategoria ma co najmniej jedną podkategorię. Zgodność listy produktów
ze słownikiem sprawdza `product_list.py`.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

CATEGORIES_FILE = Path(__file__).resolve().parent / "categories.yaml"

CODE_PATTERN = r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$"


class CategoriesError(Exception):
    """Plik `categories.yaml` jest niepoprawny."""


class Subcategory(BaseModel):
    """Podkategoria produktów, np. „korzeniowe i bulwiaste” w kategorii „warzywa”."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str = Field(pattern=CODE_PATTERN)
    name_pl: str = Field(min_length=1)


class Category(BaseModel):
    """Kategoria produktów (grupa z S-101) z listą podkategorii."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str = Field(pattern=CODE_PATTERN)
    name_pl: str = Field(min_length=1)
    required: bool
    subcategories: tuple[Subcategory, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique_subcategory_names(self) -> Category:
        duplicates = _duplicates([sub.name_pl for sub in self.subcategories])
        if duplicates:
            raise ValueError(f"powtórzone nazwy podkategorii: {', '.join(duplicates)}")
        return self

    def subcategory_names(self) -> frozenset[str]:
        """Polskie nazwy podkategorii tej kategorii."""
        return frozenset(sub.name_pl for sub in self.subcategories)


class Categories(BaseModel):
    """Cały słownik kategorii."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    categories: tuple[Category, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique_names_and_codes(self) -> Categories:
        duplicates = _duplicates([category.name_pl for category in self.categories])
        if duplicates:
            raise ValueError(f"powtórzone nazwy kategorii: {', '.join(duplicates)}")
        codes = [category.code for category in self.categories] + [
            sub.code for category in self.categories for sub in category.subcategories
        ]
        duplicates = _duplicates(codes)
        if duplicates:
            raise ValueError(f"powtórzone kody: {', '.join(duplicates)}")
        return self

    def by_name(self) -> dict[str, Category]:
        """Kategorie według polskiej nazwy."""
        return {category.name_pl: category for category in self.categories}

    def required_names(self) -> frozenset[str]:
        """Polskie nazwy kategorii, które muszą wystąpić na liście produktów."""
        return frozenset(category.name_pl for category in self.categories if category.required)


def _duplicates(values: list[str]) -> list[str]:
    return sorted(value for value, count in Counter(values).items() if count > 1)


def load_categories(path: Path = CATEGORIES_FILE) -> Categories:
    """Wczytuje i waliduje słownik kategorii."""
    try:
        with path.open(encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except (OSError, yaml.YAMLError) as error:
        raise CategoriesError(f"nie można wczytać {path.name}: {error}") from error
    try:
        return Categories.model_validate(data)
    except ValidationError as error:
        details = "; ".join(
            f"{'.'.join(map(str, e['loc'])) or '(plik)'}: {e['msg']}" for e in error.errors()
        )
        raise CategoriesError(f"niepoprawny {path.name}: {details}") from error
