"""Lista produktów podstawowych bazy v1 (S-101): wczytanie i walidacja `product_list.csv`.

Plik `input/product_list.csv` (UTF-8, separator `,`): 1 wiersz = produkt podstawowy z listą
wariantów obróbki. Kolumny opisuje `data-pipeline/README.md`. Walidacja sprawdza typy pól,
dozwolone kategorie i warianty obróbki, unikalność identyfikatorów i nazw oraz zakres listy
(liczba produktów, wszystkie wymagane grupy).

Uruchomienie: `make product-list` – wypisuje podsumowanie albo błędy.
"""

from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path
from typing import Literal, get_args

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

PRODUCT_LIST_FILE = Path(__file__).resolve().parent / "input" / "product_list.csv"

COLUMNS = ["product_id", "name_pl", "category", "preparations", "polish_specific", "notes"]

# Grupy z kryteriów S-101 (wszystkie muszą wystąpić) oraz „inne” na produkty spoza nich
Category = Literal[
    "warzywa",
    "owoce",
    "zboża i kasze",
    "nabiał",
    "mięso",
    "ryby i owoce morza",
    "jaja",
    "rośliny strączkowe",
    "orzechy i nasiona",
    "tłuszcze",
    "inne",
]
REQUIRED_CATEGORIES: frozenset[str] = frozenset(get_args(Category)) - {"inne"}

# Warianty obróbki; `surowy` przy kaszach, ryżu, makaronie i strączkach = produkt suchy,
# `gotowy` = do jedzenia bez obróbki (np. chleb, ser, wędlina)
Preparation = Literal[
    "surowy",
    "gotowy",
    "gotowany",
    "gotowany na parze",
    "pieczony",
    "smażony",
    "duszony",
    "grillowany",
]
PREPARATION_SEPARATOR = "|"

# Zakres bazy v1 z ADR-0001
MIN_PRODUCTS = 300
MAX_PRODUCTS = 500


class ProductListError(Exception):
    """Plik `product_list.csv` jest niepoprawny."""


class Product(BaseModel):
    """Produkt podstawowy z listy bazy v1."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    product_id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    name_pl: str = Field(min_length=1)
    category: Category
    preparations: tuple[Preparation, ...] = Field(min_length=1)
    polish_specific: bool
    notes: str = ""

    @field_validator("name_pl", "notes")
    @classmethod
    def _no_outer_whitespace(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("tekst ze spacjami na początku lub końcu")
        return value

    @field_validator("preparations", mode="before")
    @classmethod
    def _split_preparations(cls, value: object) -> object:
        if isinstance(value, str):
            parts = value.split(PREPARATION_SEPARATOR)
            if len(parts) != len(set(parts)):
                raise ValueError(f"powtórzony wariant obróbki: {value}")
            return tuple(parts)
        return value

    @field_validator("polish_specific", mode="before")
    @classmethod
    def _strict_bool(cls, value: object) -> object:
        if isinstance(value, str) and value not in ("true", "false"):
            raise ValueError("dozwolone wartości: true, false")
        return value


def _duplicates(values: list[str]) -> list[str]:
    return sorted(value for value, count in Counter(values).items() if count > 1)


def load_products(path: Path = PRODUCT_LIST_FILE) -> list[Product]:
    """Wczytuje i waliduje wiersze listy produktów (bez sprawdzania zakresu całej listy)."""
    try:
        with path.open(encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != COLUMNS:
                raise ProductListError(
                    f"{path.name}: kolumny {reader.fieldnames}, oczekiwane {COLUMNS}"
                )
            rows = list(reader)
    except OSError as error:
        raise ProductListError(f"nie można wczytać {path.name}: {error}") from error

    products = []
    errors = []
    for line, row in enumerate(rows, start=2):
        try:
            products.append(Product.model_validate(row))
        except ValidationError as error:
            details = "; ".join(
                f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in error.errors()
            )
            errors.append(f"wiersz {line} ({row.get('product_id')}): {details}")
    if errors:
        raise ProductListError(f"niepoprawny {path.name}:\n" + "\n".join(errors))

    problems = []
    for field in ("product_id", "name_pl"):
        duplicates = _duplicates([getattr(product, field) for product in products])
        if duplicates:
            problems.append(f"powtórzone {field}: {', '.join(duplicates)}")
    if problems:
        raise ProductListError(f"niepoprawny {path.name}:\n" + "\n".join(problems))
    return products


def check_scope(products: list[Product]) -> list[str]:
    """Problemy zakresu listy: liczba produktów i obecność wymaganych grup. Pusta lista = zgodna."""
    problems = []
    if not MIN_PRODUCTS <= len(products) <= MAX_PRODUCTS:
        problems.append(
            f"liczba produktów {len(products)} poza zakresem {MIN_PRODUCTS}–{MAX_PRODUCTS}"
        )
    missing = REQUIRED_CATEGORIES - {product.category for product in products}
    if missing:
        problems.append(f"brak produktów w grupach: {', '.join(sorted(missing))}")
    return problems


def main() -> int:
    """Waliduje listę i wypisuje podsumowanie; kod wyjścia 1 przy błędach."""
    try:
        products = load_products()
    except ProductListError as error:
        print(error, file=sys.stderr)
        return 1
    problems = check_scope(products)
    for problem in problems:
        print(problem, file=sys.stderr)

    variants = sum(len(product.preparations) for product in products)
    polish = sum(product.polish_specific for product in products)
    print(f"Produkty: {len(products)}, warianty produktów: {variants}, typowo polskie: {polish}")
    for category, count in Counter(product.category for product in products).most_common():
        print(f"  {category}: {count}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
