"""Lista produktów podstawowych bazy v1 (S-101, S-105): wczytanie i walidacja `product_list.csv`.

Plik `input/product_list.csv` (UTF-8, separator `,`): 1 wiersz = wariant produktu
(produkt podstawowy + wariant obróbki), jak w CSV bazy (ADR-0001).
Kolumny opisuje `data-pipeline/README.md`. Walidacja sprawdza typy pól, warianty obróbki,
kategorie i podkategorie ze słownika `categories.yaml` (S-105), unikalność identyfikatorów
i nazw (także prawie identycznych), spójność wierszy jednego produktu oraz zakres listy
(liczba produktów, wszystkie wymagane grupy, użycie każdej podkategorii).

Uruchomienie: `make product-list` – wypisuje podsumowanie albo błędy.
"""

from __future__ import annotations

import csv
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from categories import Categories, CategoriesError, load_categories

PRODUCT_LIST_FILE = Path(__file__).resolve().parent / "input" / "product_list.csv"

COLUMNS = [
    "variant_id",
    "food_id",
    "name_pl",
    "preparation",
    "category",
    "subcategory",
    "polish_specific",
    "notes",
]

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

# Pola wspólne dla wszystkich wariantów jednego produktu podstawowego
FOOD_FIELDS = ("name_pl", "category", "subcategory", "polish_specific")

# Zakres bazy v1 z ADR-0001 (liczba produktów podstawowych, nie wariantów)
MIN_PRODUCTS = 300
MAX_PRODUCTS = 500


class ProductListError(Exception):
    """Plik `product_list.csv` jest niepoprawny."""


class FoodVariant(BaseModel):
    """Wariant produktu z listy bazy v1: produkt podstawowy + wariant obróbki.

    Kategorię i podkategorię ze słownikiem `categories.yaml` sprawdza `load_variants`.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    variant_id: int = Field(gt=0)
    food_id: int = Field(gt=0)
    name_pl: str = Field(min_length=1)
    preparation: Preparation
    category: str = Field(min_length=1)
    subcategory: str = Field(min_length=1)
    polish_specific: bool
    notes: str = ""

    @field_validator("name_pl", "category", "subcategory", "notes")
    @classmethod
    def _no_outer_whitespace(cls, value: str) -> str:
        if value != value.strip():
            raise ValueError("tekst ze spacjami na początku lub końcu")
        return value

    @field_validator("polish_specific", mode="before")
    @classmethod
    def _strict_bool(cls, value: object) -> object:
        if isinstance(value, str) and value not in ("true", "false"):
            raise ValueError("dozwolone wartości: true, false")
        return value


def name_key(name: str) -> str:
    """Klucz porównania nazw: małe litery, bez polskich znaków, spacji i interpunkcji.

    Nazwy z tym samym kluczem (np. „kasza manna” i „Kasza-Manna”) to duplikat, choć różnią
    się zapisem.
    """
    decomposed = unicodedata.normalize("NFKD", name.casefold().replace("ł", "l"))
    return "".join(char for char in decomposed if char.isalnum())


def _duplicates(values: list[object]) -> list[str]:
    return sorted(str(value) for value, count in Counter(values).items() if count > 1)


def _category_problems(variant: FoodVariant, categories: Categories) -> list[str]:
    """Kategoria i podkategoria wiersza zgodne ze słownikiem `categories.yaml`."""
    category = categories.by_name().get(variant.category)
    if category is None:
        return [f"category: nieznana kategoria {variant.category!r}"]
    if variant.subcategory not in category.subcategory_names():
        return [f"subcategory: {variant.subcategory!r} nie jest podkategorią {variant.category!r}"]
    return []


def _consistency_problems(variants: list[FoodVariant]) -> list[str]:
    """Problemy unikalności i spójności całej listy."""
    problems = []
    duplicates = _duplicates([v.variant_id for v in variants])
    if duplicates:
        problems.append(f"powtórzone variant_id: {', '.join(duplicates)}")
    duplicates = _duplicates([(v.food_id, v.preparation) for v in variants])
    if duplicates:
        problems.append(f"powtórzony wariant obróbki produktu: {', '.join(duplicates)}")

    first: dict[int, FoodVariant] = {}
    for variant in variants:
        reference = first.setdefault(variant.food_id, variant)
        for field in FOOD_FIELDS:
            if getattr(variant, field) != getattr(reference, field):
                problems.append(
                    f"food_id {variant.food_id}: różne {field} w variant_id "
                    f"{reference.variant_id} i {variant.variant_id}"
                )
    duplicates = _duplicates([food.name_pl for food in first.values()])
    if duplicates:
        problems.append(f"ta sama name_pl w różnych food_id: {', '.join(duplicates)}")
    by_key: dict[str, set[str]] = {}
    for food in first.values():
        by_key.setdefault(name_key(food.name_pl), set()).add(food.name_pl)
    similar = sorted(" / ".join(sorted(names)) for names in by_key.values() if len(names) > 1)
    if similar:
        problems.append(f"prawie identyczne name_pl: {'; '.join(similar)}")
    return problems


def load_variants(
    path: Path = PRODUCT_LIST_FILE, categories: Categories | None = None
) -> list[FoodVariant]:
    """Wczytuje i waliduje listę wariantów produktów (bez sprawdzania zakresu całej listy).

    `categories` – słownik kategorii; domyślnie z `categories.yaml`.
    """
    if categories is None:
        categories = load_categories()
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

    variants = []
    errors = []
    for line, row in enumerate(rows, start=2):
        prefix = f"wiersz {line} (variant_id {row.get('variant_id')})"
        try:
            variant = FoodVariant.model_validate(row)
        except ValidationError as error:
            details = "; ".join(
                f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in error.errors()
            )
            errors.append(f"{prefix}: {details}")
            continue
        errors += [f"{prefix}: {problem}" for problem in _category_problems(variant, categories)]
        variants.append(variant)
    errors += _consistency_problems(variants)
    if errors:
        raise ProductListError(f"niepoprawny {path.name}:\n" + "\n".join(errors))
    return variants


def check_scope(variants: list[FoodVariant], categories: Categories | None = None) -> list[str]:
    """Problemy zakresu listy: liczba produktów, obecność wymaganych grup i użycie każdej
    podkategorii ze słownika. Pusta lista = zgodna.
    """
    if categories is None:
        categories = load_categories()
    problems = []
    foods = len({variant.food_id for variant in variants})
    if not MIN_PRODUCTS <= foods <= MAX_PRODUCTS:
        problems.append(f"liczba produktów {foods} poza zakresem {MIN_PRODUCTS}–{MAX_PRODUCTS}")
    missing = categories.required_names() - {variant.category for variant in variants}
    if missing:
        problems.append(f"brak produktów w grupach: {', '.join(sorted(missing))}")
    used = {(variant.category, variant.subcategory) for variant in variants}
    unused = [
        f"{category.name_pl} / {sub.name_pl}"
        for category in categories.categories
        for sub in category.subcategories
        if (category.name_pl, sub.name_pl) not in used
    ]
    if unused:
        problems.append(f"podkategorie bez produktów: {', '.join(unused)}")
    return problems


def main() -> int:
    """Waliduje listę i wypisuje podsumowanie; kod wyjścia 1 przy błędach."""
    try:
        categories = load_categories()
        variants = load_variants(categories=categories)
    except (CategoriesError, ProductListError) as error:
        print(error, file=sys.stderr)
        return 1
    problems = check_scope(variants, categories)
    for problem in problems:
        print(problem, file=sys.stderr)

    foods = {variant.food_id: variant for variant in variants}
    polish = sum(food.polish_specific for food in foods.values())
    print(f"Produkty: {len(foods)}, warianty produktów: {len(variants)}, typowo polskie: {polish}")
    counts = Counter((food.category, food.subcategory) for food in foods.values())
    for category in categories.categories:
        total = sum(counts[category.name_pl, sub.name_pl] for sub in category.subcategories)
        print(f"  {category.name_pl}: {total}")
        for sub in category.subcategories:
            print(f"    {sub.name_pl}: {counts[category.name_pl, sub.name_pl]}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
