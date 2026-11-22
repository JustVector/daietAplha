"""Miary domowe wariantów produktów: łyżka, szklanka, sztuka → gramy (S-109).

Dla każdego zmapowanego wariantu produktu (`mapping/mapping.csv`, S-104) narzędzie czyta porcje
USDA SR Legacy (`food_portion.csv`), rozpoznaje miarę w opisie porcji słownikiem `measures.yaml`
i zapisuje gramy na jedną polską miarę:

- łyżka, łyżeczka i miary sztukowe (sztuka, plaster, liść…) – wprost z USDA, flaga `measured`;
- gęstość produktu (g/ml) z miar objętości USDA (cup, tbsp, tsp, fl oz, pint, quart), z niej
  miara `ml` (gramy w 1 ml) i polska szklanka 250 ml – flaga `calculated` z opisem przeliczenia.

Wyjście:
- `portions/portions.csv` – miary wariantów produktów,
- `docs/data/portions_coverage.md` – pokrycie miarami i opisy porcji USDA pominięte przy rozbiorze.

Uruchomienie: `make portions` (wymaga danych z `make fetch-usda`).
"""

from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import polars as pl
import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from build_sr_wide import RAW_DIR
from fetch_usda import MANIFEST_PATH, REPO_ROOT, read_manifest, verify_dir
from map_products import MAPPING_FILE, MappingError, MappingRow, load_mapping

PIPELINE_DIR = Path(__file__).resolve().parent
MEASURES_FILE = PIPELINE_DIR / "measures.yaml"
PORTIONS_FILE = PIPELINE_DIR / "portions" / "portions.csv"
COVERAGE_REPORT = REPO_ROOT / "docs" / "data" / "portions_coverage.md"

PORTION_COLUMNS = [
    "variant_id",
    "food_id",
    "name_pl",
    "preparation",
    "measure",
    "size",
    "form",
    "grams",
    "flag",
    "fdc_id",
    "usda_modifier",
    "usda_amount",
    "usda_gram_weight",
    "calculation",
]

MEASURE_ML = "ml"
MEASURE_GLASS = "szklanka"
PIECE = "sztuka"
# Kolejność miar w pliku wynikowym: objętościowe, potem sztukowe alfabetycznie
VOLUME_ORDER = {MEASURE_ML: 0, "łyżeczka": 1, "łyżka": 2, MEASURE_GLASS: 3}
SIZE_ORDER = {"": 0, "bardzo mały": 1, "mały": 2, "średni": 3, "duży": 4, "bardzo duży": 5}

Flag = Literal["measured", "calculated"]
SkipReason = Literal["miara pominięta", "nieznana miara", "nieznane słowa", "wydajność"]

_PHRASE_RE = re.compile(r"[a-z]+( [a-z]+)*")
_WORD_RE = re.compile(r"[a-z]+")
_PAREN_RE = re.compile(r"\(([^()]*)\)")
_DIGIT_RE = re.compile(r"\d")
_YIELD_WORDS = frozenset({"yield", "yields"})


class PortionsError(Exception):
    """Słownik miar albo dane wejściowe są niepoprawne."""


# --- Słownik miar ---


class VolumeUnit(BaseModel):
    """Miara objętości USDA: ml jednostki i polska miara wpisywana wprost (łyżka, łyżeczka)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    ml: float = Field(gt=0)
    measure: str | None = None


class Measures(BaseModel):
    """Słownik `measures.yaml`: opis porcji USDA → polska miara, rozmiar i postać."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    glass_ml: float = Field(gt=0)
    volume: dict[str, VolumeUnit]
    count: dict[str, str]
    sizes: dict[str, str]
    forms: dict[str, str]
    noise: frozenset[str]
    ignored: frozenset[str]

    @field_validator("volume", "count", "sizes", "forms", "noise", "ignored")
    @classmethod
    def _plain_phrases(cls, value: Iterable[str]) -> Iterable[str]:
        wrong = sorted(key for key in value if not _PHRASE_RE.fullmatch(key))
        if wrong:
            raise ValueError(f"frazy muszą składać się z małych liter a–z: {wrong}")
        return value

    @model_validator(mode="after")
    def _disjoint(self) -> Measures:
        heads = [set(self.volume), set(self.count), set(self.sizes), set(self.ignored)]
        qualifiers = [set(self.sizes), set(self.forms), set(self.noise)]
        for group, name in ((heads, "miar"), (qualifiers, "rozmiarów, postaci i słów pomijanych")):
            seen: set[str] = set()
            for phrases in group:
                if seen & phrases:
                    raise ValueError(f"frazy w kilku listach {name}: {sorted(seen & phrases)}")
                seen |= phrases
        empty = [key for key, value in {**self.count, **self.forms}.items() if not value.strip()]
        if empty:
            raise ValueError(f"puste polskie nazwy: {empty}")
        return self


def load_measures(path: Path = MEASURES_FILE) -> Measures:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return Measures.model_validate(data)
    except (OSError, yaml.YAMLError) as error:
        raise PortionsError(f"nie można wczytać {path.name}: {error}") from error
    except ValidationError as error:
        raise PortionsError(f"niepoprawny {path.name}: {error}") from error


# --- Rozbiór opisu porcji ---


@dataclass(frozen=True)
class ParsedPortion:
    """Rozpoznana miara porcji USDA: `unit` – fraza USDA, `measure` – polska miara (przy
    objętości tylko łyżka i łyżeczka; pozostałe jednostki służą do gęstości)."""

    kind: Literal["volume", "count"]
    unit: str
    measure: str | None
    size: str = ""
    form: str = ""


@dataclass(frozen=True)
class SkippedPortion:
    """Opis porcji pominięty przy rozbiorze; `key` – miara lub słowa, które go wykluczyły."""

    reason: SkipReason
    key: str


def _longest_match(words: Sequence[str], start: int, phrases: Iterable[str]) -> str | None:
    """Najdłuższa fraza ze zbioru, od której zaczynają się wyrazy `words[start:]`."""
    best: str | None = None
    for phrase in phrases:
        parts = phrase.split(" ")
        if list(words[start : start + len(parts)]) == parts and (
            best is None or len(parts) > len(best.split(" "))
        ):
            best = phrase
    return best


def modifier_words(modifier: str) -> list[str]:
    """Wyrazy opisu porcji: małe litery, bez nawiasów z liczbami (wymiary, masa w oz)."""

    def paren(match: re.Match[str]) -> str:
        inner = match.group(1)
        return " " if _DIGIT_RE.search(inner) else f" {inner} "

    return _WORD_RE.findall(_PAREN_RE.sub(paren, modifier.lower()))


def parse_modifier(modifier: str, measures: Measures) -> ParsedPortion | SkippedPortion:
    """Rozbiór opisu porcji USDA, np. „cup, chopped” → szklanka (objętość), postać „posiekane”."""
    words = modifier_words(modifier)
    if not words:
        return SkippedPortion("nieznana miara", modifier)
    if _YIELD_WORDS & set(words):
        return SkippedPortion("wydajność", " ".join(words))
    heads = [*measures.volume, *measures.count, *measures.sizes, *measures.ignored]
    head = _longest_match(words, 0, heads)
    if head is None:
        return SkippedPortion("nieznana miara", words[0])
    if head in measures.ignored:
        return SkippedPortion("miara pominięta", head)

    size = measures.sizes.get(head, "")
    forms: list[str] = []
    qualifiers = [*measures.sizes, *measures.forms, *measures.noise]
    position = len(head.split(" "))
    while position < len(words):
        phrase = _longest_match(words, position, qualifiers)
        if phrase is None:
            return SkippedPortion("nieznane słowa", " ".join(words[position:]))
        if phrase in measures.sizes:
            size = measures.sizes[phrase]
        elif phrase in measures.forms and measures.forms[phrase] not in forms:
            forms.append(measures.forms[phrase])
        position += len(phrase.split(" "))

    form = ", ".join(forms)
    if head in measures.volume:
        return ParsedPortion("volume", head, measures.volume[head].measure, form=form)
    measure = measures.count.get(head, PIECE)
    return ParsedPortion("count", head, measure, size=size, form=form)


# --- Miary wariantów ---


@dataclass(frozen=True)
class UsdaPortion:
    """Porcja z `food_portion.csv`: `amount` miar o opisie `modifier` waży `gram_weight` g."""

    fdc_id: int
    amount: float
    modifier: str
    gram_weight: float


@dataclass(frozen=True)
class PortionRow:
    variant_id: int
    food_id: int
    name_pl: str
    preparation: str
    measure: str
    size: str
    form: str
    grams: float
    flag: Flag
    source: UsdaPortion
    calculation: str = ""


@dataclass
class PortionsResult:
    rows: list[PortionRow]
    mapping: list[MappingRow]
    # (fdc_id, opis porcji) → powód pominięcia; tylko rekordy USDA z mapowania
    skipped: dict[tuple[int, str], SkippedPortion] = field(default_factory=dict)
    # Porcje odrzucone jako powtórzenie tej samej miary, rozmiaru i postaci
    duplicates: int = 0
    report: str = ""


def load_usda_portions(raw_dir: Path = RAW_DIR) -> dict[int, list[UsdaPortion]]:
    """Porcje SR Legacy według `fdc_id`, w kolejności z pliku USDA (`seq_num`)."""
    try:
        frame = pl.read_csv(
            raw_dir / "food_portion.csv",
            columns=["fdc_id", "seq_num", "amount", "modifier", "gram_weight"],
            schema_overrides={
                "fdc_id": pl.Int64(),
                "seq_num": pl.Int64(),
                "amount": pl.Float64(),
                "modifier": pl.String(),
                "gram_weight": pl.Float64(),
            },
        )
    except (OSError, pl.exceptions.PolarsError) as error:
        raise PortionsError(f"nie można wczytać food_portion.csv: {error}") from error
    portions: dict[int, list[UsdaPortion]] = {}
    for fdc_id, _, amount, modifier, gram_weight in frame.sort(["fdc_id", "seq_num"]).iter_rows():
        if amount is None or amount <= 0 or gram_weight is None or gram_weight <= 0:
            continue
        portions.setdefault(fdc_id, []).append(
            UsdaPortion(fdc_id, amount, (modifier or "").strip(), gram_weight)
        )
    return portions


def _number(value: float) -> str:
    """Liczba bez zbędnych zer: 13.60 → „13.6”, 250.0 → „250”."""
    return f"{value:.3f}".rstrip("0").rstrip(".")


def variant_portions(
    variant: MappingRow,
    portions: Sequence[UsdaPortion],
    measures: Measures,
    skipped: dict[tuple[int, str], SkippedPortion] | None = None,
) -> tuple[list[PortionRow], int]:
    """Miary jednego wariantu produktu i liczba odrzuconych powtórzeń.

    Gęstość (g/ml) liczona osobno dla każdej postaci („szklanka, posiekane” ≠ „szklanka”) z porcji
    o największej objętości – przy większej objętości zaokrąglenia USDA ważą mniej.
    """
    rows: list[PortionRow] = []
    seen: set[tuple[str, str, str]] = set()
    duplicates = 0
    densest: dict[str, tuple[float, UsdaPortion, str]] = {}

    def add(row: PortionRow) -> None:
        nonlocal duplicates
        key = (row.measure, row.size, row.form)
        if key in seen:
            duplicates += 1
            return
        seen.add(key)
        rows.append(row)

    def row(measure: str, size: str, form: str, grams: float, flag: Flag, source: UsdaPortion,
            calculation: str = "") -> PortionRow:  # fmt: skip
        return PortionRow(
            variant.variant_id,
            variant.food_id,
            variant.name_pl,
            variant.preparation,
            measure,
            size,
            form,
            grams,
            flag,
            source,
            calculation,
        )

    for portion in portions:
        parsed = parse_modifier(portion.modifier, measures)
        if isinstance(parsed, SkippedPortion):
            if skipped is not None:
                skipped[(portion.fdc_id, portion.modifier)] = parsed
            continue
        per_unit = portion.gram_weight / portion.amount
        if parsed.kind == "volume":
            volume_ml = portion.amount * measures.volume[parsed.unit].ml
            if parsed.form not in densest or volume_ml > densest[parsed.form][0]:
                densest[parsed.form] = (volume_ml, portion, parsed.unit)
        if parsed.measure is not None:
            add(row(parsed.measure, parsed.size, parsed.form, per_unit, "measured", portion))

    for form, (volume_ml, portion, unit) in densest.items():
        density = portion.gram_weight / volume_ml
        basis = (
            f"gęstość {_number(density)} g/ml z USDA: {_number(portion.amount)} {unit} "
            f"({_number(volume_ml)} ml) = {_number(portion.gram_weight)} g"
        )
        if not form:
            add(row(MEASURE_ML, "", "", density, "calculated", portion, basis))
        glass = f"{basis}; × {_number(measures.glass_ml)} ml"
        add(row(MEASURE_GLASS, "", form, density * measures.glass_ml, "calculated", portion, glass))

    rows.sort(
        key=lambda r: (
            VOLUME_ORDER.get(r.measure, len(VOLUME_ORDER)),
            r.measure,
            SIZE_ORDER.get(r.size, len(SIZE_ORDER)),
            r.form,
        )
    )
    return rows, duplicates


def build_portions(
    mapping: Sequence[MappingRow],
    usda_portions: dict[int, list[UsdaPortion]],
    measures: Measures,
) -> PortionsResult:
    """Miary wszystkich zmapowanych wariantów (warianty bez `fdc_id` pomijane)."""
    result = PortionsResult(rows=[], mapping=list(mapping))
    for variant in mapping:
        if variant.fdc_id is None:
            continue
        rows, duplicates = variant_portions(
            variant, usda_portions.get(variant.fdc_id, []), measures, result.skipped
        )
        result.rows.extend(rows)
        result.duplicates += duplicates
    return result


# --- Zapis i raport ---


def _grams(row: PortionRow) -> str:
    """Gramy na miarę: przy `ml` trzy miejsca po przecinku (gęstość), poza tym dwa."""
    digits = 3 if row.measure == MEASURE_ML else 2
    return f"{row.grams:.{digits}f}".rstrip("0").rstrip(".")


def write_portions(path: Path, rows: Sequence[PortionRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(PORTION_COLUMNS)
        for r in rows:
            writer.writerow(
                [
                    r.variant_id,
                    r.food_id,
                    r.name_pl,
                    r.preparation,
                    r.measure,
                    r.size,
                    r.form,
                    _grams(r),
                    r.flag,
                    r.source.fdc_id,
                    r.source.modifier,
                    _number(r.source.amount),
                    _number(r.source.gram_weight),
                    r.calculation,
                ]
            )


def _cell(text: str) -> str:
    return text.replace("|", "\\|")


def render_report(result: PortionsResult) -> str:
    """Raport Markdown: pokrycie wariantów miarami, liczba miar i pominięte opisy porcji USDA."""
    mapped = [v for v in result.mapping if v.fdc_id is not None]
    measures_of: dict[int, set[str]] = {}
    for row in result.rows:
        measures_of.setdefault(row.variant_id, set()).add(row.measure)
    count_measures = {r.measure for r in result.rows} - set(VOLUME_ORDER)

    def having(predicate: set[str] | None) -> int:
        return sum(
            1
            for v in mapped
            if v.variant_id in measures_of
            and (predicate is None or measures_of[v.variant_id] & predicate)
        )

    without = [v for v in mapped if v.variant_id not in measures_of]
    per_measure = Counter(row.measure for row in result.rows)
    reasons = Counter(skip.reason for skip in result.skipped.values())
    keys = Counter((skip.reason, skip.key) for skip in result.skipped.values())

    lines = [
        "# Miary domowe – pokrycie",
        "",
        "Wygenerowane przez `make portions` (S-109) z `data-pipeline/mapping/mapping.csv` i porcji "
        "USDA SR Legacy – nie edytuj ręcznie.",
        "",
        "## Podsumowanie",
        "",
        "| Warianty produktów | Liczba |",
        "| --- | --- |",
        f"| na liście (`mapping.csv`) | {len(result.mapping)} |",
        f"| z `fdc_id` | {len(mapped)} |",
        f"| z co najmniej jedną miarą | {having(None)} |",
        f"| ze szklanką i `ml` (gęstość) | {having({MEASURE_GLASS})} |",
        f"| z łyżką | {having({'łyżka'})} |",
        f"| z łyżeczką | {having({'łyżeczka'})} |",
        f"| z miarą sztukową (sztuka, plaster, liść…) | {having(count_measures)} |",
        "",
        "Warianty bez `fdc_id` (status `brak`) nie mają porcji USDA. Szklanka (250 ml) i `ml` są "
        "wyliczane z gęstości (`calculated`), pozostałe miary pochodzą wprost z USDA (`measured`). "
        f"Powtórzenia tej samej miary, rozmiaru i postaci pominięte: {result.duplicates}.",
        "",
        "## Miary",
        "",
        "| Miara | Wiersze |",
        "| --- | --- |",
        *[f"| {measure} | {count} |" for measure, count in sorted(per_measure.items())],
        "",
        f"## Warianty z `fdc_id` bez miar ({len(without)})",
        "",
        "| variant_id | Produkt | Wariant | fdc_id | Opis USDA |",
        "| --- | --- | --- | --- | --- |",
        *[
            f"| {v.variant_id} | {_cell(v.name_pl)} | {v.preparation} | {v.fdc_id} | "
            f"{_cell(v.usda_description)} |"
            for v in without
        ],
        "",
        "## Pominięte opisy porcji USDA",
        "",
        "Liczone raz na rekord USDA i opis. „miara pominięta” – miara z listy `ignored` w "
        "`measures.yaml` (masa, opakowanie, porcja handlowa); „wydajność” – porcja z opakowania "
        "lub produktu przed obróbką; „nieznana miara” i „nieznane słowa” – do uzupełnienia "
        "słownika.",
        "",
        "| Powód | Opisy |",
        "| --- | --- |",
        *[f"| {reason} | {count} |" for reason, count in sorted(reasons.items())],
        "",
        "| Powód | Miara lub słowa | Opisy |",
        "| --- | --- | --- |",
        *[
            f"| {reason} | {_cell(key)} | {count} |"
            for (reason, key), count in sorted(
                keys.items(), key=lambda item: (item[0][0], -item[1], item[0][1])
            )
        ],
    ]
    return "\n".join(lines) + "\n"


# --- Uruchomienie ---


def generate(mapping_path: Path = MAPPING_FILE) -> PortionsResult:
    """Liczy miary i raport z danych w repo (bez zapisu plików)."""
    problems = verify_dir(RAW_DIR, read_manifest(MANIFEST_PATH))
    if problems:
        raise PortionsError(f"{problems[0]}; odtwórz surowe dane: make fetch-usda")
    try:
        mapping = list(load_mapping(mapping_path).values())
    except MappingError as error:
        raise PortionsError(str(error)) from error
    if not mapping:
        raise PortionsError(f"brak {mapping_path.name}; uruchom make map-products")
    result = build_portions(mapping, load_usda_portions(), load_measures())
    result.report = render_report(result)
    return result


def main() -> int:
    """Zapisuje `portions.csv` i raport pokrycia; kod wyjścia 1 przy błędach."""
    try:
        result = generate()
    except PortionsError as error:
        print(f"Błąd: {error}", file=sys.stderr)
        return 1
    write_portions(PORTIONS_FILE, result.rows)
    COVERAGE_REPORT.write_text(result.report, encoding="utf-8", newline="\n")
    variants = len({row.variant_id for row in result.rows})
    print(
        f"OK: {len(result.rows)} miar dla {variants} wariantów; zapisano {PORTIONS_FILE.name} "
        f"i {COVERAGE_REPORT.name}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
