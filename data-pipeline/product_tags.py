"""Tagi wykluczeń i diet produktów podstawowych (S-108).

Słownik tagów i reguły automatycznej propozycji: `tags.yaml`. Przypisanie tagów:
`tags/product_tags.csv` – 1 wiersz = produkt podstawowy (`food_id`), po jednej kolumnie
`true`/`false` na tag. Propozycja powstaje z kategorii i nazwy produktu (`product_list.csv`,
`categories.yaml`) oraz z kategorii i opisu USDA rekordów przypisanych wariantom produktu
w `mapping/mapping.csv` (S-104). Wiersze ze statusem `zweryfikowany` (sprawdzone przez Piotra)
nigdy nie są nadpisywane.

Uruchomienie:
- `make product-tags` – propozycja dla wierszy `auto` i nowych produktów (wymaga danych
  z `make fetch-usda`), zapis `product_tags.csv` i podsumowanie,
- `uv run python -X utf8 data-pipeline/product_tags.py --check` – tylko walidacja pliku
  (bez danych USDA).
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from build_sr_wide import RAW_DIR, load_foods
from categories import CODE_PATTERN, Categories, CategoriesError, load_categories
from fetch_usda import MANIFEST_PATH, read_manifest, verify_dir
from map_products import MappingError, load_mapping
from product_list import FoodVariant, ProductListError, load_variants

PIPELINE_DIR = Path(__file__).resolve().parent
TAGS_FILE = PIPELINE_DIR / "tags.yaml"
PRODUCT_TAGS_FILE = PIPELINE_DIR / "tags" / "product_tags.csv"

FOOD_COLUMNS = ["food_id", "name_pl", "category", "subcategory"]
END_COLUMNS = ["status", "notes"]

Status = Literal["auto", "zweryfikowany"]


class TagsError(Exception):
    """Słownik tagów, plik `product_tags.csv` albo dane wejściowe są niepoprawne."""


class Rule(BaseModel):
    """Reguła propozycji: trafienie, gdy pasuje dowolne pole (z wyjątkami)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    categories: tuple[str, ...] = ()
    subcategories: tuple[str, ...] = ()
    name_patterns: tuple[str, ...] = ()
    usda_categories: tuple[str, ...] = ()
    usda_patterns: tuple[str, ...] = ()
    except_usda_patterns: tuple[str, ...] = ()
    except_name_patterns: tuple[str, ...] = ()

    @field_validator(
        "name_patterns", "usda_patterns", "except_usda_patterns", "except_name_patterns"
    )
    @classmethod
    def _valid_regex(cls, patterns: tuple[str, ...]) -> tuple[str, ...]:
        for pattern in patterns:
            try:
                re.compile(pattern)
            except re.error as error:
                raise ValueError(f"niepoprawne wyrażenie {pattern!r}: {error}") from error
        return patterns


class Tag(BaseModel):
    """Tag wykluczenia (produkt zawiera składnik) albo diety (produkt nadaje się do diety)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str = Field(pattern=CODE_PATTERN)
    name_pl: str = Field(min_length=1)
    kind: Literal["exclusion", "diet"]
    match: Rule | None = None
    requires: tuple[str, ...] = ()
    excluded_by_tags: tuple[str, ...] = ()
    excluded_by: Rule | None = None

    @model_validator(mode="after")
    def _fields_for_kind(self) -> Tag:
        if self.kind == "exclusion":
            if self.match is None:
                raise ValueError("tag wykluczenia wymaga reguły `match`")
            if self.requires or self.excluded_by_tags or self.excluded_by is not None:
                raise ValueError("`requires`, `excluded_by_tags`, `excluded_by` tylko dla diet")
        elif self.match is not None:
            raise ValueError("tag diety nie ma reguły `match` (służy do tego `excluded_by`)")
        return self


class ReviewNote(BaseModel):
    """Uwaga do przeglądu dla produktów o nazwie pasującej do wzorca."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    name_pattern: str
    note: str = Field(min_length=1)

    @field_validator("name_pattern")
    @classmethod
    def _valid_regex(cls, pattern: str) -> str:
        try:
            re.compile(pattern)
        except re.error as error:
            raise ValueError(f"niepoprawne wyrażenie {pattern!r}: {error}") from error
        return pattern


class TagsConfig(BaseModel):
    """Cały słownik tagów z regułami."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    tags: tuple[Tag, ...] = Field(min_length=1)
    review_notes: tuple[ReviewNote, ...] = ()

    @model_validator(mode="after")
    def _references(self) -> TagsConfig:
        codes = [tag.code for tag in self.tags]
        duplicates = sorted(code for code, count in Counter(codes).items() if count > 1)
        if duplicates:
            raise ValueError(f"powtórzone kody tagów: {', '.join(duplicates)}")
        if set(codes) & set(FOOD_COLUMNS + END_COLUMNS):
            raise ValueError("kod tagu nie może być nazwą innej kolumny product_tags.csv")
        kinds = {tag.code: tag.kind for tag in self.tags}
        for tag in self.tags:
            for code in tag.requires:
                if kinds.get(code) != "diet" or code == tag.code:
                    raise ValueError(f"{tag.code}.requires: {code!r} nie jest innym tagiem diety")
            for code in tag.excluded_by_tags:
                if kinds.get(code) != "exclusion":
                    raise ValueError(
                        f"{tag.code}.excluded_by_tags: {code!r} nie jest tagiem wykluczenia"
                    )
        return self

    @property
    def codes(self) -> list[str]:
        """Kody tagów w kolejności z pliku (= kolejność kolumn w CSV)."""
        return [tag.code for tag in self.tags]

    def columns(self) -> list[str]:
        """Kolumny `product_tags.csv`."""
        return FOOD_COLUMNS + self.codes + END_COLUMNS


def _rules(config: TagsConfig) -> Iterable[tuple[str, Rule]]:
    for tag in config.tags:
        for rule in (tag.match, tag.excluded_by):
            if rule is not None:
                yield tag.code, rule


def load_tags(path: Path = TAGS_FILE, categories: Categories | None = None) -> TagsConfig:
    """Wczytuje i waliduje słownik tagów; kody kategorii w regułach sprawdza z `categories`."""
    if categories is None:
        categories = load_categories()
    try:
        with path.open(encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except (OSError, yaml.YAMLError) as error:
        raise TagsError(f"nie można wczytać {path.name}: {error}") from error
    try:
        config = TagsConfig.model_validate(data)
    except ValidationError as error:
        details = "; ".join(
            f"{'.'.join(map(str, e['loc'])) or '(plik)'}: {e['msg']}" for e in error.errors()
        )
        raise TagsError(f"niepoprawny {path.name}: {details}") from error

    category_codes = {category.code for category in categories.categories}
    subcategory_codes = {
        sub.code for category in categories.categories for sub in category.subcategories
    }
    problems = []
    for code, rule in _rules(config):
        problems += [
            f"{code}: nieznana kategoria {c!r}" for c in rule.categories if c not in category_codes
        ]
        problems += [
            f"{code}: nieznana podkategoria {c!r}"
            for c in rule.subcategories
            if c not in subcategory_codes
        ]
    if problems:
        raise TagsError(f"niepoprawny {path.name}: {'; '.join(problems)}")
    return config


@dataclass(frozen=True)
class UsdaRecord:
    """Rekord USDA przypisany wariantowi produktu."""

    category: str
    description: str


@dataclass(frozen=True)
class Food:
    """Produkt podstawowy z danymi potrzebnymi do propozycji tagów."""

    food_id: int
    name_pl: str
    category: str
    subcategory: str
    category_code: str
    subcategory_code: str
    usda: tuple[UsdaRecord, ...] = field(default=())


def _search(patterns: Iterable[str], text: str) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def rule_sources(rule: Rule, food: Food) -> list[str]:
    """Źródła trafienia reguły dla produktu (`kategoria`, `nazwa`, `USDA`); pusta = brak."""
    if _search(rule.except_name_patterns, food.name_pl):
        return []
    sources = []
    if food.category_code in rule.categories or food.subcategory_code in rule.subcategories:
        sources.append("kategoria")
    if _search(rule.name_patterns, food.name_pl):
        sources.append("nazwa")
    for record in food.usda:
        if _search(rule.except_usda_patterns, record.description):
            continue
        if record.category in rule.usda_categories or _search(
            rule.usda_patterns, record.description
        ):
            sources.append("USDA")
            break
    return sources


def propose(food: Food, config: TagsConfig) -> tuple[dict[str, bool], str]:
    """Proponowane tagi produktu i uwagi do przeglądu (źródła tagów, wątpliwości)."""
    tags: dict[str, bool] = {}
    notes: list[str] = []
    for tag in config.tags:
        if tag.kind != "exclusion" or tag.match is None:
            continue
        sources = rule_sources(tag.match, food)
        tags[tag.code] = bool(sources)
        if sources:
            notes.append(f"{tag.code}: {', '.join(sources)}")
    # Tagi diet po wykluczeniach; `requires` sprawdzane w kolejności zależności
    diet = [tag for tag in config.tags if tag.kind == "diet"]
    pending = list(diet)
    while pending:
        progress = False
        for tag in list(pending):
            if any(code not in tags for code in tag.requires):
                continue
            pending.remove(tag)
            progress = True
            blocking = [code for code in tag.excluded_by_tags if tags[code]]
            blocking += [code for code in tag.requires if not tags[code]]
            sources = rule_sources(tag.excluded_by, food) if tag.excluded_by else []
            tags[tag.code] = not blocking and not sources
            if sources and not blocking:
                notes.append(f"nie {tag.code}: {', '.join(sources)}")
        if not progress:
            raise TagsError(f"cykl w `requires` tagów: {', '.join(t.code for t in pending)}")
    if not food.usda:
        notes.append("bez rekordu USDA – tylko kategoria i nazwa")
    notes += [
        note.note for note in config.review_notes if _search([note.name_pattern], food.name_pl)
    ]
    return {code: tags[code] for code in config.codes}, "; ".join(notes)


@dataclass(frozen=True)
class TagRow:
    """Wiersz `product_tags.csv`."""

    food_id: int
    name_pl: str
    category: str
    subcategory: str
    tags: dict[str, bool]
    status: Status
    notes: str = ""

    def cells(self, codes: Sequence[str]) -> list[object]:
        flags = ["true" if self.tags[code] else "false" for code in codes]
        return [
            self.food_id,
            self.name_pl,
            self.category,
            self.subcategory,
            *flags,
            self.status,
            self.notes,
        ]


def _parse_bool(value: str, column: str) -> bool:
    if value not in ("true", "false"):
        raise ValueError(f"{column}: dozwolone wartości true, false (jest {value!r})")
    return value == "true"


def load_product_tags(path: Path, config: TagsConfig) -> list[TagRow]:
    """Wczytuje `product_tags.csv` (typy pól i kolumny; spójność sprawdza `check_rows`)."""
    columns = config.columns()
    try:
        with path.open(encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != columns:
                raise TagsError(f"{path.name}: kolumny {reader.fieldnames}, oczekiwane {columns}")
            raw = list(reader)
    except OSError as error:
        raise TagsError(f"nie można wczytać {path.name}: {error}") from error
    rows = []
    errors = []
    for line, row in enumerate(raw, start=2):
        try:
            if row["status"] not in ("auto", "zweryfikowany"):
                raise ValueError(f"status: dozwolone auto, zweryfikowany (jest {row['status']!r})")
            status: Status = "auto" if row["status"] == "auto" else "zweryfikowany"
            rows.append(
                TagRow(
                    food_id=int(row["food_id"]),
                    name_pl=row["name_pl"],
                    category=row["category"],
                    subcategory=row["subcategory"],
                    tags={code: _parse_bool(row[code], code) for code in config.codes},
                    status=status,
                    notes=row["notes"],
                )
            )
        except ValueError as error:
            errors.append(f"wiersz {line} (food_id {row.get('food_id')}): {error}")
    if errors:
        raise TagsError(f"niepoprawny {path.name}:\n" + "\n".join(errors))
    return rows


def consistency_problems(row: TagRow, config: TagsConfig) -> list[str]:
    """Sprzeczne tagi wiersza, np. `vegan` bez `vegetarian` albo `vegetarian` z `meat`."""
    problems = []
    for tag in config.tags:
        if not row.tags[tag.code]:
            continue
        problems += [f"{tag.code} bez {code}" for code in tag.requires if not row.tags[code]]
        problems += [
            f"{tag.code} razem z {code}" for code in tag.excluded_by_tags if row.tags[code]
        ]
    return problems


def check_rows(
    rows: Sequence[TagRow], variants: Sequence[FoodVariant], config: TagsConfig
) -> list[str]:
    """Problemy pliku względem listy produktów i słownika; pusta lista = poprawny."""
    problems = []
    foods = {variant.food_id: variant for variant in variants}
    ids = [row.food_id for row in rows]
    duplicates = sorted(food_id for food_id, count in Counter(ids).items() if count > 1)
    if duplicates:
        problems.append(f"powtórzone food_id: {', '.join(map(str, duplicates))}")
    missing = sorted(set(foods) - set(ids))
    if missing:
        problems.append(f"produkty bez tagów (food_id): {', '.join(map(str, missing))}")
    unknown = sorted(set(ids) - set(foods))
    if unknown:
        problems.append(f"food_id spoza listy produktów: {', '.join(map(str, unknown))}")
    if ids != sorted(ids):
        problems.append("wiersze nie są posortowane według food_id")
    for row in rows:
        food = foods.get(row.food_id)
        prefix = f"food_id {row.food_id}"
        if food is not None:
            for column in ("name_pl", "category", "subcategory"):
                if getattr(row, column) != getattr(food, column):
                    problems.append(
                        f"{prefix}: {column} {getattr(row, column)!r} różni się od listy "
                        f"produktów ({getattr(food, column)!r})"
                    )
        problems += [f"{prefix}: {problem}" for problem in consistency_problems(row, config)]
    return problems


def foods_from(
    variants: Sequence[FoodVariant],
    categories: Categories,
    usda_by_food: dict[int, list[UsdaRecord]],
) -> list[Food]:
    """Produkty podstawowe (po `food_id`) z kodami kategorii i rekordami USDA."""
    by_name = categories.by_name()
    foods: dict[int, Food] = {}
    for variant in variants:
        if variant.food_id in foods:
            continue
        category = by_name[variant.category]
        subcategory = next(s for s in category.subcategories if s.name_pl == variant.subcategory)
        foods[variant.food_id] = Food(
            food_id=variant.food_id,
            name_pl=variant.name_pl,
            category=variant.category,
            subcategory=variant.subcategory,
            category_code=category.code,
            subcategory_code=subcategory.code,
            usda=tuple(usda_by_food.get(variant.food_id, [])),
        )
    return sorted(foods.values(), key=lambda food: food.food_id)


def build_rows(
    foods: Sequence[Food], config: TagsConfig, previous: dict[int, TagRow]
) -> list[TagRow]:
    """Wiersze pliku: `zweryfikowany` bez zmian tagów (nazwa i kategoria z listy produktów),
    pozostałe z propozycji automatycznej.
    """
    rows = []
    for food in foods:
        old = previous.get(food.food_id)
        if old is not None and old.status == "zweryfikowany":
            rows.append(
                TagRow(
                    food.food_id,
                    food.name_pl,
                    food.category,
                    food.subcategory,
                    {code: old.tags.get(code, False) for code in config.codes},
                    "zweryfikowany",
                    old.notes,
                )
            )
            continue
        tags, notes = propose(food, config)
        rows.append(
            TagRow(food.food_id, food.name_pl, food.category, food.subcategory, tags, "auto", notes)
        )
    return rows


def load_previous(path: Path, config: TagsConfig) -> dict[int, TagRow]:
    """Dotychczasowe wiersze (`food_id` → wiersz); pusty słownik, gdy pliku nie ma.

    Plik ze starym zestawem kolumn (zmiana słownika) jest czytany tylko z kolumn, które zostały;
    nowy tag w wierszu `zweryfikowany` dostaje `false` i trzeba go sprawdzić ręcznie.
    """
    if not path.exists():
        return {}
    with path.open(encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        fields = set(reader.fieldnames or [])
        rows = {}
        for row in reader:
            codes = [code for code in config.codes if code in fields]
            rows[int(row["food_id"])] = TagRow(
                food_id=int(row["food_id"]),
                name_pl=row["name_pl"],
                category=row["category"],
                subcategory=row["subcategory"],
                tags={code: row[code] == "true" for code in codes},
                status="zweryfikowany" if row.get("status") == "zweryfikowany" else "auto",
                notes=row.get("notes", ""),
            )
    return rows


def write_product_tags(path: Path, rows: Sequence[TagRow], config: TagsConfig) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(config.columns())
        writer.writerows(row.cells(config.codes) for row in rows)


def usda_records(mapping_fdc: dict[int, list[int]]) -> dict[int, list[UsdaRecord]]:
    """Rekordy USDA (kategoria, opis) dla `food_id` → lista `fdc_id` z mapowania."""
    problems = verify_dir(RAW_DIR, read_manifest(MANIFEST_PATH))
    if problems:
        raise TagsError(f"{problems[0]}; odtwórz surowe dane: make fetch-usda")
    usda = load_foods(RAW_DIR)
    by_fdc = {
        fdc_id: UsdaRecord(category or "", description)
        for fdc_id, description, category in usda.select(
            "fdc_id", "description", "food_category"
        ).iter_rows()
    }
    result: dict[int, list[UsdaRecord]] = {}
    for food_id, fdc_ids in mapping_fdc.items():
        unknown = [fdc_id for fdc_id in fdc_ids if fdc_id not in by_fdc]
        if unknown:
            raise TagsError(f"food_id {food_id}: fdc_id spoza SR Legacy: {unknown}")
        result[food_id] = [by_fdc[fdc_id] for fdc_id in fdc_ids]
    return result


def generate(previous_path: Path = PRODUCT_TAGS_FILE) -> tuple[TagsConfig, list[TagRow]]:
    """Liczy wiersze `product_tags.csv` z danych w repo (bez zapisu)."""
    try:
        categories = load_categories()
        variants = load_variants(categories=categories)
        mapping = load_mapping()
    except (CategoriesError, ProductListError, MappingError) as error:
        raise TagsError(str(error)) from error
    config = load_tags(categories=categories)
    mapping_fdc: dict[int, list[int]] = {}
    for row in mapping.values():
        if row.fdc_id is not None and row.fdc_id not in mapping_fdc.get(row.food_id, []):
            mapping_fdc.setdefault(row.food_id, []).append(row.fdc_id)
    foods = foods_from(variants, categories, usda_records(mapping_fdc))
    rows = build_rows(foods, config, load_previous(previous_path, config))
    problems = check_rows(rows, variants, config)
    if problems:
        raise TagsError("propozycja niespójna:\n" + "\n".join(problems))
    return config, rows


def check(path: Path = PRODUCT_TAGS_FILE) -> list[str]:
    """Walidacja pliku `product_tags.csv` bez danych USDA; pusta lista = poprawny."""
    try:
        categories = load_categories()
        variants = load_variants(categories=categories)
        config = load_tags(categories=categories)
        rows = load_product_tags(path, config)
    except (CategoriesError, ProductListError, TagsError) as error:
        return [str(error)]
    return check_rows(rows, variants, config)


def summary(rows: Sequence[TagRow], config: TagsConfig) -> list[str]:
    """Podsumowanie: liczba produktów z każdym tagiem, statusy, wiersze z uwagami."""
    statuses = Counter(row.status for row in rows)
    lines = [
        f"Produkty: {len(rows)} – auto {statuses['auto']}, "
        f"zweryfikowany {statuses['zweryfikowany']}"
    ]
    for tag in config.tags:
        count = sum(row.tags[tag.code] for row in rows)
        lines.append(f"  {tag.code} ({tag.name_pl}): {count}")
    no_usda = sum("bez rekordu USDA" in row.notes for row in rows if row.status == "auto")
    lines.append(f"  bez rekordu USDA (tylko kategoria i nazwa): {no_usda}")
    return lines


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Tagi wykluczeń i diet produktów podstawowych (S-108): propozycja "
        "automatyczna i walidacja tags/product_tags.csv."
    )
    parser.add_argument(
        "--check", action="store_true", help="tylko walidacja pliku, bez danych USDA i bez zapisu"
    )
    args = parser.parse_args(argv)
    if args.check:
        problems = check()
        for problem in problems:
            print(problem, file=sys.stderr)
        if not problems:
            print(f"OK: {PRODUCT_TAGS_FILE.name} poprawny")
        return 1 if problems else 0
    try:
        config, rows = generate()
    except TagsError as error:
        print(f"Błąd: {error}", file=sys.stderr)
        return 1
    write_product_tags(PRODUCT_TAGS_FILE, rows, config)
    print("\n".join(summary(rows, config)))
    print(f"Zapisano {PRODUCT_TAGS_FILE.relative_to(PIPELINE_DIR.parent)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
