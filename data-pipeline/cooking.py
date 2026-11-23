"""Warianty po obróbce termicznej: wartości zmierzone z USDA, brakujące wyliczone (S-106).

Wariant produktu z rekordem USDA (`fdc_id` w `mapping/mapping.csv`, S-104) ma wartości zmierzone
(flaga `measured`). Wariant obróbki termicznej bez rekordu USDA jest wyliczany z wariantu bazowego
tego samego produktu (`surowy`, a gdy go nie ma – `gotowy`):

    ilość składnika = wartość bazowa × R/100 (+ składnik wchłoniętego oleju przy smażeniu)
    wartość na 100 g po obróbce = ilość × 100 / Y

R – współczynnik retencji z tabeli USDA R6 (`data/raw/usda_retention/`), Y – wydajność w % masy
produktu wyjściowego (`cooking/yields.csv` albo mediana par USDA). Woda wynika z bilansu masy.
Szczegóły i założenia: `docs/data/cooking_calc.md`.

Wyjście:
- `cooking/cooked_variants.csv` – wyliczone warianty z parametrami przeliczenia (w git),
- `docs/data/cooking_coverage.md` – raport: co wyliczono, z jakich parametrów, czego brakuje,
- `data/interim/variant_nutrients.parquet` – wartości wszystkich wariantów z flagą `measured`
  / `calculated`, źródłem i odwołaniem do współczynnika (poza git; eksport bazy – S-111).

Uruchomienie: `make cooked-variants` (wymaga danych z `make fetch-usda` i `mapping.csv`).
"""

from __future__ import annotations

import csv
import statistics
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, get_args

import polars as pl
import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from build_sr_wide import INTERIM_DIR, RAW_DIR, build
from categories import load_categories
from fetch_usda import (
    MANIFEST_PATH,
    REPO_ROOT,
    RETENTION_DIR,
    RETENTION_FILE,
    RETENTION_MANIFEST_PATH,
    read_manifest,
    verify_dir,
)
from map_products import MAPPING_FILE, MappingError, MappingRow, load_mapping
from nutrients import Nutrient, NutrientConfigError, load_nutrients
from product_list import FoodVariant, ProductListError, load_variants

PIPELINE_DIR = Path(__file__).resolve().parent
COOKING_DIR = PIPELINE_DIR / "cooking"
METHODS_FILE = COOKING_DIR / "methods.yaml"
YIELDS_FILE = COOKING_DIR / "yields.csv"
COOKED_FILE = COOKING_DIR / "cooked_variants.csv"
COVERAGE_REPORT = REPO_ROOT / "docs" / "data" / "cooking_coverage.md"
VALUES_FILE = INTERIM_DIR / "variant_nutrients.parquet"

CookedPreparation = Literal[
    "gotowany", "gotowany na parze", "pieczony", "smażony", "duszony", "grillowany"
]
COOKED_PREPARATIONS: tuple[str, ...] = get_args(CookedPreparation)
# Warianty bazowe w kolejności wyboru: surowy, a dla produktów jedzonych bez obróbki – gotowy
BASE_PREPARATIONS = ("surowy", "gotowy")
FRYING = "smażony"

WATER = "water_g"
FAT = "total_lipid_fat_g"

YIELD_COLUMNS = ["scope", "preparation", "yield_pct", "fat_uptake_g", "source", "reference"]
YieldSource = Literal["usda_meat_yields_2012", "bognar_2002", "brak"]
PAIRS_SOURCE = "usda_sr_pairs"
FOOD_SCOPE_PREFIX = "food:"

Flag = Literal["measured", "calculated"]


class CookingError(Exception):
    """Konfiguracja przeliczeń albo dane wejściowe są niepoprawne."""


# --- Konfiguracja ---


class RetentionRule(BaseModel):
    """Reguła doboru procesu R6: zakres (kategoria, podkategoria albo produkt) → kody procesów."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    category: str | None = None
    subcategory: str | None = None
    food_id: int | None = Field(default=None, gt=0)
    codes: dict[CookedPreparation, int]
    # Ryby: kody dla produktu wyjściowego z tłuszczem powyżej progu `fatty_fish_fat_g`
    fatty: dict[CookedPreparation, int] | None = None

    @model_validator(mode="after")
    def _one_scope(self) -> RetentionRule:
        scopes = [s for s in (self.category, self.subcategory, self.food_id) if s is not None]
        if len(scopes) != 1:
            raise ValueError("reguła musi mieć dokładnie jedno z: category, subcategory, food_id")
        if self.fatty is not None and set(self.fatty) != set(self.codes):
            raise ValueError("`fatty` musi mieć te same warianty obróbki co `codes`")
        return self

    @property
    def scope(self) -> str:
        if self.food_id is not None:
            return f"{FOOD_SCOPE_PREFIX}{self.food_id}"
        return self.subcategory or self.category or ""


class Methods(BaseModel):
    """Zawartość `cooking/methods.yaml`."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    frying_fat_variant_id: int = Field(gt=0)
    min_pairs: int = Field(ge=1)
    fatty_fish_fat_g: float = Field(ge=0)
    r6_nutrients: dict[int, int]
    retention: tuple[RetentionRule, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def _unique_scopes(self) -> Methods:
        scopes = [rule.scope for rule in self.retention]
        duplicates = sorted({s for s in scopes if scopes.count(s) > 1})
        if duplicates:
            raise ValueError(f"kilka reguł retencji dla zakresu: {duplicates}")
        return self


def load_methods(path: Path = METHODS_FILE) -> Methods:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return Methods.model_validate(data)
    except (OSError, yaml.YAMLError) as error:
        raise CookingError(f"nie można wczytać {path.name}: {error}") from error
    except ValidationError as error:
        raise CookingError(f"niepoprawny {path.name}: {error}") from error


class YieldEntry(BaseModel):
    """Wiersz `cooking/yields.csv`: wydajność wariantu obróbki w zakresie produktów.

    `scope` – kod kategorii lub podkategorii (categories.yaml) albo `food:<food_id>`.
    Pusta wydajność ze źródłem `brak` = świadomy brak danych: zakres nie jest wyliczany.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    scope: str = Field(min_length=1)
    preparation: CookedPreparation
    yield_pct: float | None = Field(default=None, gt=0)
    fat_uptake_g: float | None = Field(default=None, ge=0)
    source: YieldSource
    reference: str = Field(min_length=1)

    @field_validator("yield_pct", "fat_uptake_g", mode="before")
    @classmethod
    def _empty_is_none(cls, value: object) -> object:
        return None if value == "" else value

    @model_validator(mode="after")
    def _source_matches_value(self) -> YieldEntry:
        if (self.source == "brak") != (self.yield_pct is None):
            raise ValueError("pusta wydajność wtedy i tylko wtedy, gdy źródło to `brak`")
        if self.fat_uptake_g is not None and self.preparation != FRYING:
            raise ValueError("wchłonięty tłuszcz podaje się tylko dla wariantu `smażony`")
        return self


def load_yields(path: Path = YIELDS_FILE) -> dict[tuple[str, str], YieldEntry]:
    try:
        with path.open(encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != YIELD_COLUMNS:
                raise CookingError(
                    f"{path.name}: kolumny {reader.fieldnames}, oczekiwane {YIELD_COLUMNS}"
                )
            entries = [YieldEntry.model_validate(row) for row in reader]
    except OSError as error:
        raise CookingError(f"nie można wczytać {path.name}: {error}") from error
    except ValidationError as error:
        raise CookingError(f"niepoprawny {path.name}: {error}") from error
    by_key: dict[tuple[str, str], YieldEntry] = {(e.scope, e.preparation): e for e in entries}
    if len(by_key) != len(entries):
        raise CookingError(f"{path.name}: powtórzona para (scope, preparation)")
    return by_key


# --- Tabela retencji R6 ---


@dataclass(frozen=True)
class RetentionProcess:
    """Proces obróbki z tabeli R6: opis i współczynniki (numer składnika R6 → %)."""

    code: int
    description: str
    factors: dict[int, float]


def load_retention(path: Path = RETENTION_DIR / RETENTION_FILE) -> dict[int, RetentionProcess]:
    """Czyta `retn06.txt`: pola rozdzielone `^`, tekst w `~`; kolumny: kod procesu, grupa,
    opis, numer składnika, nazwa składnika, współczynnik (%), data."""
    processes: dict[int, RetentionProcess] = {}
    try:
        lines = path.read_text(encoding="latin-1").splitlines()
    except OSError as error:
        raise CookingError(f"nie można wczytać {path.name}: {error}") from error
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        fields = [f.strip("~") for f in line.split("^")]
        try:
            code, description, nutrient = int(fields[0]), fields[2].strip(), int(fields[3])
            # Pusty współczynnik (np. część procesów z alkoholem) = brak współczynnika
            value = float(fields[5]) if fields[5] else None
        except (IndexError, ValueError) as error:
            raise CookingError(f"{path.name}, wiersz {number}: {error}") from error
        process = processes.setdefault(code, RetentionProcess(code, description, {}))
        if value is not None:
            process.factors[nutrient] = value
    return processes


# --- Warianty produktów ---


@dataclass(frozen=True)
class Variant:
    """Wariant produktu z listy (S-101) z kodami kategorii i rekordem USDA z mapowania (S-104)."""

    variant_id: int
    food_id: int
    name_pl: str
    preparation: str
    category: str
    subcategory: str
    fdc_id: int | None

    @property
    def scopes(self) -> tuple[str, str, str]:
        """Zakresy od najbardziej szczegółowego: produkt, podkategoria, kategoria."""
        return (f"{FOOD_SCOPE_PREFIX}{self.food_id}", self.subcategory, self.category)


def join_variants(
    variants: Sequence[FoodVariant], mapping: Mapping[int, MappingRow]
) -> list[Variant]:
    """Łączy listę produktów z mapowaniem; kategorie zamienia na kody z categories.yaml."""
    by_name = load_categories().by_name()
    result: list[Variant] = []
    for v in variants:
        category = by_name[v.category]
        subcategory = next(s.code for s in category.subcategories if s.name_pl == v.subcategory)
        row = mapping.get(v.variant_id)
        result.append(
            Variant(
                v.variant_id,
                v.food_id,
                v.name_pl,
                v.preparation,
                category.code,
                subcategory,
                row.fdc_id if row is not None else None,
            )
        )
    return result


def base_variant(variant: Variant, by_food: Mapping[int, Sequence[Variant]]) -> Variant | None:
    """Wariant bazowy produktu z rekordem USDA: `surowy`, a gdy go nie ma – `gotowy`."""
    for preparation in BASE_PREPARATIONS:
        for other in by_food.get(variant.food_id, ()):
            if other.preparation == preparation and other.fdc_id is not None:
                return other
    return None


def group_by_food(variants: Iterable[Variant]) -> dict[int, list[Variant]]:
    by_food: dict[int, list[Variant]] = {}
    for v in variants:
        by_food.setdefault(v.food_id, []).append(v)
    return by_food


# --- Wydajność i wchłonięty tłuszcz ---


@dataclass(frozen=True)
class Pair:
    """Para wariantów zmierzonych w USDA: bazowy i po obróbce tego samego produktu.

    Wydajność z bilansu suchej masy bez tłuszczu (białko, węglowodany, popiół nie znikają przy
    obróbce): Y = (100 − woda_b − tłuszcz_b) / (100 − woda_o − tłuszcz_o) × 100,
    wchłonięty tłuszcz (g na 100 g produktu wyjściowego) = tłuszcz_o × Y/100 − tłuszcz_b.
    """

    variant_id: int
    name_pl: str
    category: str
    subcategory: str
    preparation: str
    yield_pct: float
    fat_uptake_g: float


def pair_yield(
    base: Mapping[str, float | None], cooked: Mapping[str, float | None]
) -> tuple[float, float] | None:
    """(wydajność %, wchłonięty tłuszcz g) z wartości na 100 g; None bez wody lub tłuszczu."""
    values = (base.get(WATER), base.get(FAT), cooked.get(WATER), cooked.get(FAT))
    if any(v is None for v in values):
        return None
    water_b, fat_b, water_c, fat_c = (float(v) for v in values if v is not None)
    solids_b, solids_c = 100 - water_b - fat_b, 100 - water_c - fat_c
    if solids_b <= 0 or solids_c <= 0:
        return None
    yield_pct = solids_b / solids_c * 100
    return yield_pct, fat_c * yield_pct / 100 - fat_b


def measured_pairs(
    variants: Sequence[Variant], values: Mapping[int, Mapping[str, float | None]]
) -> list[Pair]:
    """Pary (bazowy, obrobiony) dla wariantów obróbki termicznej zmierzonych w USDA."""
    by_food = group_by_food(variants)
    pairs: list[Pair] = []
    for v in variants:
        if v.preparation not in COOKED_PREPARATIONS or v.fdc_id is None:
            continue
        base = base_variant(v, by_food)
        if base is None or base.fdc_id is None:
            continue
        result = pair_yield(values[base.fdc_id], values[v.fdc_id])
        if result is not None:
            pairs.append(
                Pair(v.variant_id, v.name_pl, v.category, v.subcategory, v.preparation, *result)
            )
    return pairs


@dataclass(frozen=True)
class YieldChoice:
    """Wydajność i wchłonięty tłuszcz dla wariantu z opisem pochodzenia."""

    yield_pct: float
    fat_uptake_g: float
    source: str
    reference: str
    fat_reference: str = ""


@dataclass(frozen=True)
class NoYield:
    reason: str


def _pairs_at(pairs: Sequence[Pair], scope: str, preparation: str) -> list[Pair]:
    return [
        p for p in pairs if preparation == p.preparation and scope in (p.category, p.subcategory)
    ]


def _fat_from_pairs(
    pairs: Sequence[Pair], scopes: Sequence[str], min_pairs: int
) -> tuple[float, str]:
    """Wchłonięty tłuszcz przy smażeniu: mediana par od najwęższego zakresu, potem wszystkie
    pary smażenia; ujemna mediana (wytopienie tłuszczu) = 0."""
    for scope in scopes:
        group = _pairs_at(pairs, scope, FRYING)
        if len(group) >= min_pairs:
            fat = max(0.0, statistics.median(p.fat_uptake_g for p in group))
            return fat, f"mediana {len(group)} par USDA ({scope}, smażony)"
    group = [p for p in pairs if p.preparation == FRYING]
    if len(group) >= min_pairs:
        fat = max(0.0, statistics.median(p.fat_uptake_g for p in group))
        return fat, f"mediana {len(group)} par USDA (wszystkie, smażony)"
    return 0.0, "brak danych – przyjęto 0"


def resolve_yield(
    variant: Variant,
    yields: Mapping[tuple[str, str], YieldEntry],
    pairs: Sequence[Pair],
    min_pairs: int,
) -> YieldChoice | NoYield:
    """Wydajność wariantu: od najwęższego zakresu (produkt, podkategoria, kategoria) najpierw
    wpis z `yields.csv`, potem mediana co najmniej `min_pairs` par USDA."""
    prep = variant.preparation
    scopes = variant.scopes
    for level, scope in enumerate(scopes):
        entry = yields.get((scope, prep))
        if entry is not None:
            if entry.yield_pct is None:
                return NoYield(f"brak danych ({scope}): {entry.reference}")
            fat, fat_reference = 0.0, ""
            if prep == FRYING:
                if entry.fat_uptake_g is not None:
                    fat, fat_reference = entry.fat_uptake_g, entry.source
                else:
                    fat, fat_reference = _fat_from_pairs(pairs, scopes[1:], min_pairs)
            return YieldChoice(
                entry.yield_pct, fat, entry.source, f"{scope}: {entry.reference}", fat_reference
            )
        if level == 0:
            continue  # par na poziomie produktu nie ma – wariant nie ma rekordu USDA
        group = _pairs_at(pairs, scope, prep)
        if len(group) >= min_pairs:
            names = ", ".join(sorted(p.name_pl for p in group))
            fat, fat_reference = 0.0, ""
            if prep == FRYING:
                fat = max(0.0, statistics.median(p.fat_uptake_g for p in group))
                fat_reference = f"mediana {len(group)} par USDA ({scope}, smażony)"
            return YieldChoice(
                statistics.median(p.yield_pct for p in group),
                fat,
                PAIRS_SOURCE,
                f"{scope}: mediana {len(group)} par USDA ({names})",
                fat_reference,
            )
    return NoYield("brak wydajności dla wariantu obróbki w grupie produktu")


# --- Retencja ---


def resolve_retention(variant: Variant, base_fat_g: float | None, methods: Methods) -> int | None:
    """Kod procesu R6 z najbardziej szczegółowej reguły (produkt, podkategoria, kategoria)."""
    rules = {rule.scope: rule for rule in methods.retention}
    for scope in variant.scopes:
        rule = rules.get(scope)
        if rule is None or variant.preparation not in rule.codes:
            continue
        prep = variant.preparation
        if (
            rule.fatty is not None
            and base_fat_g is not None
            and base_fat_g > methods.fatty_fish_fat_g
        ):
            return rule.fatty[prep]
        return rule.codes[prep]
    return None


# --- Przeliczenie ---


def cook(
    base: Mapping[str, float | None],
    retention: Mapping[str, float],
    yield_pct: float,
    oil: Mapping[str, float | None] | None = None,
    oil_g: float = 0.0,
) -> dict[str, float | None]:
    """Wartości na 100 g produktu po obróbce.

    `base` – wartości na 100 g produktu wyjściowego (kolumny tabeli szerokiej), `retention` –
    współczynnik retencji w % dla kolumny (brak = 100), `yield_pct` – masa po obróbce w % masy
    wyjściowej, `oil` i `oil_g` – wchłonięty olej (wartości na 100 g oleju, gramy oleju na 100 g
    produktu wyjściowego). Woda: Y − sucha masa produktu − sucha masa oleju. Brak wartości bazowej
    zostaje brakiem (None).
    """
    if yield_pct <= 0:
        raise CookingError("wydajność musi być dodatnia")
    water_base = base.get(WATER)
    if water_base is None:
        raise CookingError("brak wody w produkcie wyjściowym – nie da się policzyć bilansu masy")
    oil_water = (oil or {}).get(WATER) or 0.0
    water = yield_pct - (100 - water_base) - oil_g * (100 - oil_water) / 100
    if water < -1e-9:
        raise CookingError(
            f"wydajność {yield_pct:g}% poniżej suchej masy produktu – ujemna ilość wody"
        )
    result: dict[str, float | None] = {}
    for column, value in base.items():
        if column == WATER:
            amount: float | None = max(water, 0.0)
        elif value is None:
            amount = None
        else:
            amount = value * retention.get(column, 100.0) / 100
            oil_value = (oil or {}).get(column)
            if oil_g and oil_value is not None:
                amount += oil_value * oil_g / 100
        result[column] = None if amount is None else amount * 100 / yield_pct
    return result


# --- Budowa wyniku ---


@dataclass(frozen=True)
class CookedVariant:
    variant: Variant
    base: Variant
    r6_code: int
    r6_description: str
    choice: YieldChoice
    oil_g: float
    values: dict[str, float | None]
    # kolumna → współczynnik retencji (%); brak klucza = brak współczynnika w R6 (100%)
    retention: dict[str, float]


@dataclass(frozen=True)
class SkippedVariant:
    variant: Variant
    base: Variant | None
    reason: str


@dataclass
class CookingResult:
    cooked: list[CookedVariant]
    skipped: list[SkippedVariant]
    pairs: list[Pair]
    variants: list[Variant]
    nutrients: list[Nutrient]
    report: str = ""
    measured: int = field(default=0)


def retention_by_column(
    process: RetentionProcess, nutrients: Sequence[Nutrient], methods: Methods
) -> dict[str, float]:
    """Współczynniki procesu R6 dla kolumn bazy v1 (tylko składniki obecne w R6)."""
    result: dict[str, float] = {}
    for nutrient in nutrients:
        number = methods.r6_nutrients.get(nutrient.usda_nutrient_id)
        if number is not None and number in process.factors:
            result[nutrient.usda_column] = process.factors[number]
    return result


def build_cooked(
    variants: Sequence[Variant],
    values: Mapping[int, Mapping[str, float | None]],
    nutrients: Sequence[Nutrient],
    methods: Methods,
    yields: Mapping[tuple[str, str], YieldEntry],
    retention: Mapping[int, RetentionProcess],
) -> CookingResult:
    """Wylicza warianty obróbki termicznej bez rekordu USDA."""
    _check_config(variants, methods, yields, retention)
    by_food = group_by_food(variants)
    pairs = measured_pairs(variants, values)
    columns = [n.usda_column for n in nutrients]
    oil_variant = next(v for v in variants if v.variant_id == methods.frying_fat_variant_id)
    if oil_variant.fdc_id is None:
        raise CookingError(f"wariant tłuszczu do smażenia {oil_variant.variant_id} bez fdc_id")
    oil = values[oil_variant.fdc_id]
    oil_fat = oil.get(FAT)
    if not oil_fat:
        raise CookingError("tłuszcz do smażenia bez zawartości tłuszczu")

    result = CookingResult([], [], pairs, list(variants), list(nutrients))
    result.measured = sum(1 for v in variants if v.fdc_id is not None)
    for v in variants:
        if v.preparation not in COOKED_PREPARATIONS or v.fdc_id is not None:
            continue
        base = base_variant(v, by_food)
        if base is None or base.fdc_id is None:
            result.skipped.append(SkippedVariant(v, None, "brak wariantu bazowego w USDA"))
            continue
        base_values = {c: values[base.fdc_id].get(c) for c in columns}
        code = resolve_retention(v, base_values.get(FAT), methods)
        if code is None:
            result.skipped.append(SkippedVariant(v, base, "brak procesu R6 dla grupy produktu"))
            continue
        choice = resolve_yield(v, yields, pairs, methods.min_pairs)
        if isinstance(choice, NoYield):
            result.skipped.append(SkippedVariant(v, base, choice.reason))
            continue
        oil_g = choice.fat_uptake_g * 100 / float(oil_fat)
        factors = retention_by_column(retention[code], nutrients, methods)
        try:
            cooked = cook(base_values, factors, choice.yield_pct, oil, oil_g)
        except CookingError as error:
            result.skipped.append(SkippedVariant(v, base, str(error)))
            continue
        result.cooked.append(
            CookedVariant(
                v, base, code, retention[code].description, choice, oil_g, cooked, factors
            )
        )
    return result


def _check_config(
    variants: Sequence[Variant],
    methods: Methods,
    yields: Mapping[tuple[str, str], YieldEntry],
    retention: Mapping[int, RetentionProcess],
) -> None:
    """Zakresy w konfiguracji muszą istnieć na liście produktów, kody procesów – w R6."""
    scopes = {s for v in variants for s in v.scopes}
    problems: list[str] = []
    for rule in methods.retention:
        if rule.scope not in scopes:
            problems.append(f"methods.yaml: nieznany zakres {rule.scope}")
        codes = [*rule.codes.values(), *(rule.fatty or {}).values()]
        problems += [f"methods.yaml: brak procesu R6 {c}" for c in codes if c not in retention]
    problems += [f"yields.csv: nieznany zakres {s}" for s, _ in yields if s not in scopes]
    if not any(v.variant_id == methods.frying_fat_variant_id for v in variants):
        problems.append(f"methods.yaml: brak wariantu {methods.frying_fat_variant_id} na liście")
    if problems:
        raise CookingError("; ".join(problems))


# --- Zapis ---


def _number(value: float | None, digits: int = 3) -> str:
    """Liczba bez zbędnych zer; brak wartości = pusty tekst."""
    if value is None:
        return ""
    text = f"{value:.{digits}f}".rstrip("0").rstrip(".")
    return "0" if text in ("-0", "") else text


COOKED_HEADER = [
    "variant_id",
    "food_id",
    "name_pl",
    "preparation",
    "base_variant_id",
    "base_fdc_id",
    "r6_code",
    "yield_pct",
    "yield_source",
    "fat_uptake_g",
    "oil_g",
]


def write_cooked(path: Path, result: CookingResult) -> None:
    columns = [n.usda_column for n in result.nutrients]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow([*COOKED_HEADER, *columns])
        for c in result.cooked:
            writer.writerow(
                [
                    c.variant.variant_id,
                    c.variant.food_id,
                    c.variant.name_pl,
                    c.variant.preparation,
                    c.base.variant_id,
                    c.base.fdc_id,
                    c.r6_code,
                    _number(c.choice.yield_pct, 1),
                    c.choice.source,
                    _number(c.choice.fat_uptake_g, 2),
                    _number(c.oil_g, 2),
                    *[_number(c.values[col]) for col in columns],
                ]
            )


def variant_values(
    result: CookingResult, values: Mapping[int, Mapping[str, float | None]]
) -> pl.DataFrame:
    """Wartości wszystkich wariantów w formacie długim z flagą, źródłem i odwołaniem."""
    rows: list[dict[str, object]] = []
    for v in result.variants:
        if v.fdc_id is None:
            continue
        for n in result.nutrients:
            rows.append(
                {
                    "variant_id": v.variant_id,
                    "nutrient": n.usda_column,
                    "unit": n.unit,
                    "value": values[v.fdc_id].get(n.usda_column),
                    "flag": "measured",
                    "source": f"usda_sr_legacy:{v.fdc_id}",
                    "factor_ref": "",
                }
            )
    for c in result.cooked:
        for n in result.nutrients:
            column = n.usda_column
            if column == WATER:
                factor = "bilans masy"
            elif column in c.retention:
                factor = f"R6:{c.r6_code} {_number(c.retention[column], 1)}%"
            else:
                factor = f"R6:{c.r6_code} brak współczynnika – 100%"
            factor += f"; Y {_number(c.choice.yield_pct, 1)}% ({c.choice.source})"
            if c.oil_g:
                factor += f"; olej {_number(c.oil_g, 2)} g"
            rows.append(
                {
                    "variant_id": c.variant.variant_id,
                    "nutrient": column,
                    "unit": n.unit,
                    "value": c.values[column],
                    "flag": "calculated",
                    "source": f"usda_sr_legacy:{c.base.fdc_id}",
                    "factor_ref": factor,
                }
            )
    schema = {
        "variant_id": pl.Int64(),
        "nutrient": pl.String(),
        "unit": pl.String(),
        "value": pl.Float64(),
        "flag": pl.String(),
        "source": pl.String(),
        "factor_ref": pl.String(),
    }
    return pl.DataFrame(rows, schema=schema).sort(["variant_id", "nutrient"])


def _cell(text: str) -> str:
    return text.replace("|", "\\|")


def render_report(result: CookingResult) -> str:
    """Raport Markdown: wyliczone warianty, braki i mediany par USDA."""
    targets = [
        v for v in result.variants if v.preparation in COOKED_PREPARATIONS and v.fdc_id is None
    ]
    by_source: dict[str, int] = {}
    for c in result.cooked:
        by_source[c.choice.source] = by_source.get(c.choice.source, 0) + 1
    pair_groups: dict[tuple[str, str], list[Pair]] = {}
    for p in result.pairs:
        pair_groups.setdefault((p.subcategory, p.preparation), []).append(p)
        pair_groups.setdefault((p.category, p.preparation), []).append(p)

    lines = [
        "# Warianty po obróbce termicznej – pokrycie",
        "",
        "Wygenerowane przez `make cooked-variants` (S-106) z `data-pipeline/mapping/mapping.csv`, "
        "`data-pipeline/cooking/` i tabeli retencji USDA R6 – nie edytuj ręcznie. "
        "Logika przeliczenia: [cooking_calc.md](cooking_calc.md).",
        "",
        "## Podsumowanie",
        "",
        "| Warianty produktów | Liczba |",
        "| --- | --- |",
        f"| na liście | {len(result.variants)} |",
        f"| z wartościami zmierzonymi (`measured`, rekord USDA) | {result.measured} |",
        f"| obróbki termicznej bez rekordu USDA | {len(targets)} |",
        f"| wyliczone (`calculated`) | {len(result.cooked)} |",
        f"| bez wartości | {len(result.skipped)} |",
        "",
        "| Źródło wydajności | Wyliczone warianty |",
        "| --- | --- |",
        *[f"| `{source}` | {count} |" for source, count in sorted(by_source.items())],
        "",
        f"## Wyliczone warianty ({len(result.cooked)})",
        "",
        "Y – wydajność (masa po obróbce w % masy produktu wyjściowego); olej – gramy oleju "
        "wchłoniętego na 100 g produktu wyjściowego.",
        "",
        "| variant_id | Produkt | Wariant | Baza (variant_id, fdc_id) | Proces R6 | Y % | Źródło Y "
        "| Olej g |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
        *[
            f"| {c.variant.variant_id} | {_cell(c.variant.name_pl)} | {c.variant.preparation} | "
            f"{c.base.preparation} ({c.base.variant_id}, {c.base.fdc_id}) | "
            f"{c.r6_code} {_cell(c.r6_description)} | {_number(c.choice.yield_pct, 1)} | "
            f"{_cell(c.choice.reference)} | {_number(c.oil_g, 2) if c.oil_g else '–'} |"
            for c in result.cooked
        ],
        "",
        f"## Warianty bez wartości ({len(result.skipped)})",
        "",
        "Do uzupełnienia z drugiego źródła (Ciqual, Fineli) albo po weryfikacji mapowania (S-104).",
        "",
        "| variant_id | Produkt | Wariant | Powód |",
        "| --- | --- | --- | --- |",
        *[
            f"| {s.variant.variant_id} | {_cell(s.variant.name_pl)} | {s.variant.preparation} | "
            f"{_cell(s.reason)} |"
            for s in result.skipped
        ],
        "",
        "## Pary USDA (wariant bazowy i po obróbce, oba zmierzone)",
        "",
        "Wydajność z bilansu suchej masy bez tłuszczu; mediana grupy jest używana od "
        "co najmniej `min_pairs` par (methods.yaml), gdy `yields.csv` nie ma wpisu.",
        "",
        "| Grupa | Wariant | Pary | Mediana Y % | Mediana tłuszczu g |",
        "| --- | --- | --- | --- | --- |",
        *[
            f"| {scope} | {prep} | {len(group)} | "
            f"{_number(statistics.median(p.yield_pct for p in group), 1)} | "
            f"{_number(statistics.median(p.fat_uptake_g for p in group), 1)} |"
            for (scope, prep), group in sorted(pair_groups.items())
        ],
    ]
    return "\n".join(lines) + "\n"


# --- Uruchomienie ---


def generate(mapping_path: Path = MAPPING_FILE) -> tuple[CookingResult, pl.DataFrame]:
    """Liczy warianty, raport i tabelę wartości z danych w repo (bez zapisu plików)."""
    for directory, manifest in ((RAW_DIR, MANIFEST_PATH), (RETENTION_DIR, RETENTION_MANIFEST_PATH)):
        problems = verify_dir(directory, read_manifest(manifest))
        if problems:
            raise CookingError(f"{problems[0]}; odtwórz surowe dane: make fetch-usda")
    try:
        mapping = load_mapping(mapping_path)
        variants = join_variants(load_variants(), mapping)
        nutrients = load_nutrients()
    except (MappingError, ProductListError, NutrientConfigError) as error:
        raise CookingError(str(error)) from error
    if not mapping:
        raise CookingError(f"brak {mapping_path.name}; uruchom make map-products")
    wide, _ = build(RAW_DIR)
    columns = [n.usda_column for n in nutrients]
    fdc_ids = {v.fdc_id for v in variants if v.fdc_id is not None}
    values: dict[int, dict[str, float | None]] = {
        row["fdc_id"]: {c: row[c] for c in columns}
        for row in wide.filter(pl.col("fdc_id").is_in(list(fdc_ids)))
        .select("fdc_id", *columns)
        .iter_rows(named=True)
    }
    result = build_cooked(
        variants, values, nutrients, load_methods(), load_yields(), load_retention()
    )
    result.report = render_report(result)
    return result, variant_values(result, values)


def main() -> int:
    """Zapisuje wyliczone warianty, raport i tabelę wartości; kod wyjścia 1 przy błędach."""
    try:
        result, table = generate()
    except CookingError as error:
        print(f"Błąd: {error}", file=sys.stderr)
        return 1
    write_cooked(COOKED_FILE, result)
    COVERAGE_REPORT.write_text(result.report, encoding="utf-8", newline="\n")
    VALUES_FILE.parent.mkdir(parents=True, exist_ok=True)
    table.write_parquet(VALUES_FILE)
    print(
        f"OK: wyliczono {len(result.cooked)} wariantów, bez wartości {len(result.skipped)}; "
        f"zapisano {COOKED_FILE.name}, {COVERAGE_REPORT.name} i {VALUES_FILE.name} "
        f"({table.height} wartości)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
