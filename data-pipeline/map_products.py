"""Mapowanie listy produktów podstawowych do rekordów USDA SR Legacy – `fdc_id` (S-104).

Półautomat: dla każdego wariantu produktu z `input/product_list.csv` (S-101) narzędzie szuka
kandydatów w opisach SR Legacy przez dopasowanie przybliżone (rapidfuzz) angielskiego zapytania
z `input/search_terms.csv` i doliczenie premii lub kary za słowa obróbki z `preparations.yaml`.
Wyniki sprawdza Piotr, poprawiając `mapping/mapping.csv`.

Wyjście:
- `mapping/mapping_candidates.csv` – top-5 kandydatów na wariant z wynikiem 0–100,
- `mapping/mapping.csv` – wybrany `fdc_id` i status: `auto` (najlepszy kandydat z wynikiem
  od progu), `brak` (żaden kandydat nie osiąga progu), `zweryfikowany` (sprawdzony ręcznie –
  nigdy nie jest nadpisywany; pusty `fdc_id` = potwierdzony brak odpowiednika w USDA),
- `docs/data/missing_in_usda.md` – warianty bez odpowiednika: produkty do uzupełnienia z Ciqual
  lub Fineli i brakujące warianty obróbki (do wyliczenia w S-106).

Uruchomienie: `make map-products` (wymaga danych z `make fetch-usda`).
"""

from __future__ import annotations

import csv
import re
import sys
from collections import Counter
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, get_args

import numpy as np
import numpy.typing as npt
import polars as pl
import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator
from rapidfuzz import fuzz, process, utils

from build_sr_wide import RAW_DIR, load_foods
from fetch_usda import MANIFEST_PATH, REPO_ROOT, read_manifest, verify_dir
from product_list import FoodVariant, Preparation, ProductListError, load_variants

PIPELINE_DIR = Path(__file__).resolve().parent
SEARCH_TERMS_FILE = PIPELINE_DIR / "input" / "search_terms.csv"
PREPARATIONS_FILE = PIPELINE_DIR / "preparations.yaml"
MAPPING_DIR = PIPELINE_DIR / "mapping"
MAPPING_FILE = MAPPING_DIR / "mapping.csv"
CANDIDATES_FILE = MAPPING_DIR / "mapping_candidates.csv"
MISSING_REPORT = REPO_ROOT / "docs" / "data" / "missing_in_usda.md"

SEARCH_TERMS_COLUMNS = ["food_id", "name_pl", "query_en"]
MAPPING_COLUMNS = [
    "variant_id",
    "food_id",
    "name_pl",
    "preparation",
    "fdc_id",
    "status",
    "usda_description",
    "score",
]
CANDIDATE_COLUMNS = [
    "variant_id",
    "name_pl",
    "preparation",
    "rank",
    "fdc_id",
    "score",
    "usda_description",
    "usda_category",
]

Status = Literal["auto", "zweryfikowany", "brak"]

TOP_N = 5
# Najniższy wynik najlepszego kandydata, przy którym wariant dostaje status `auto`
AUTO_THRESHOLD = 85.0

# Kategorie USDA pomijane przy szukaniu kandydatów (dania gotowe i żywność dla niemowląt);
# ręcznie można wskazać dowolny rekord SR Legacy
EXCLUDED_CATEGORIES = frozenset({"Baby Foods", "Fast Foods", "Restaurant Foods"})

# Wagi wyniku podstawowego (suma 1): zbiór słów, kolejność słów, początek opisu (przed przecinkiem)
WEIGHT_TOKEN_SET = 0.5
WEIGHT_TOKEN_SORT = 0.25
WEIGHT_HEAD = 0.25
# Premia za słowo obróbki z `include`, kara za słowo z `exclude` i za brak słowa z `include`
# (gdy reguła ma `required: true`)
PREPARATION_BONUS = 10.0
PREPARATION_PENALTY = 30.0
PREPARATION_MISSING_PENALTY = 25.0
# Kary za cechy opisu, których nie ma w zapytaniu: produkt markowy, dodatek soli, forma handlowa
BRAND_PENALTY = 10.0
SALT_PENALTY = 5.0
FORM_PENALTY = 5.0
FORM_WORDS = ("canned", "frozen", "sweetened", "dehydrated")
# Słowa pomijane w porównaniu kolejności słów (obok słów obróbki z `preparations.yaml`), żeby
# opis „Broccoli, cooked, boiled, drained, without salt” był bliżej „Broccoli” niż
# „Broccoli, chinese, cooked”
NOISE_WORDS = frozenset({"drained", "without", "with", "salt", "added", "no", "solids", "liquids"})
# Kara za każde słowo zapytania (poza słowami pomijanymi), którego nie ma w opisie USDA –
# odróżnia np. „Turkey, breast” od „Turkey, neck” mimo podobnego zapisu
MISSING_WORD_PENALTY = 15.0
STOP_WORDS = frozenset({"and", "or", "of", "the", "in", "to", "a"})

# Słowo pisane wielkimi literami (min. 3 znaki) = nazwa marki, np. „KELLOGG'S”, „LIFEWAY”;
# poza „USDA” z dopisku „(Includes foods for USDA's Food Distribution Program)”
_BRAND_RE = re.compile(r"\b(?!USDA\b)[A-Z][A-Z'&]{2,}\b")
_SALT_RE = re.compile(r"\bwith salt\b")
_WORD_RE = re.compile(r"[a-z]+")


class MappingError(Exception):
    """Pliki wejściowe mapowania są niepoprawne albo niespójne z listą produktów lub USDA."""


def words(text: str) -> frozenset[str]:
    """Wyrazy tekstu małymi literami, bez interpunkcji: „pan-fried” → {„pan”, „fried”}."""
    return frozenset(_WORD_RE.findall(text.lower()))


def normalized(text: str) -> str:
    """Tekst jako wyrazy małymi literami rozdzielone spacją, ze spacją na początku i końcu –
    do szukania fraz: „ dry heat ” w „Fish, cod, cooked, dry heat”."""
    return " " + " ".join(_WORD_RE.findall(text.lower())) + " "


def contains_any(text: str, terms: frozenset[str]) -> bool:
    """Czy znormalizowany tekst zawiera którekolwiek słowo lub frazę."""
    return any(f" {term} " in text for term in terms)


# --- Wejście: słownik obróbki i zapytania ---


class PreparationRule(BaseModel):
    """Słowa w opisie USDA wskazujące wariant obróbki (`include`) albo inny wariant (`exclude`)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    include: frozenset[str]
    exclude: frozenset[str]
    required: bool = False

    @field_validator("include", "exclude")
    @classmethod
    def _plain_words(cls, value: frozenset[str]) -> frozenset[str]:
        wrong = sorted(term for term in value if not re.fullmatch(r"[a-z]+( [a-z]+)*", term))
        if wrong:
            raise ValueError(f"słowa lub frazy muszą składać się z małych liter a–z: {wrong}")
        return value

    def words(self) -> frozenset[str]:
        """Wszystkie pojedyncze słowa reguły (także z fraz)."""
        return frozenset(w for term in self.include | self.exclude for w in term.split())


def load_preparations(path: Path = PREPARATIONS_FILE) -> dict[str, PreparationRule]:
    """Wczytuje `preparations.yaml`; wymaga reguły dla każdego wariantu obróbki z S-101."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise MappingError(f"nie można wczytać {path.name}: {error}") from error
    if not isinstance(data, dict):
        raise MappingError(f"{path.name}: oczekiwany słownik wariant → reguła")
    expected = set(get_args(Preparation))
    if set(data) != expected:
        raise MappingError(
            f"{path.name}: warianty {sorted(map(str, data))}, oczekiwane {sorted(expected)}"
        )
    try:
        return {name: PreparationRule.model_validate(rule) for name, rule in data.items()}
    except ValidationError as error:
        raise MappingError(f"niepoprawny {path.name}: {error}") from error


class SearchTerm(BaseModel):
    """Angielskie zapytanie do opisów USDA dla produktu podstawowego."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    food_id: int = Field(gt=0)
    name_pl: str = Field(min_length=1)
    query_en: str = Field(min_length=1)


def load_search_terms(
    variants: Sequence[FoodVariant], path: Path = SEARCH_TERMS_FILE
) -> dict[int, str]:
    """Zapytania `food_id` → `query_en`; każdy produkt z listy musi mieć dokładnie jedno."""
    try:
        with path.open(encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != SEARCH_TERMS_COLUMNS:
                raise MappingError(
                    f"{path.name}: kolumny {reader.fieldnames}, oczekiwane {SEARCH_TERMS_COLUMNS}"
                )
            terms = [SearchTerm.model_validate(row) for row in reader]
    except OSError as error:
        raise MappingError(f"nie można wczytać {path.name}: {error}") from error
    except ValidationError as error:
        raise MappingError(f"niepoprawny {path.name}: {error}") from error

    problems = []
    counts = Counter(term.food_id for term in terms)
    duplicates = sorted(food_id for food_id, count in counts.items() if count > 1)
    if duplicates:
        problems.append(f"powtórzone food_id: {duplicates}")
    names = {variant.food_id: variant.name_pl for variant in variants}
    missing = sorted(set(names) - set(counts))
    if missing:
        problems.append(f"brak zapytania dla food_id: {missing}")
    unknown = sorted(set(counts) - set(names))
    if unknown:
        problems.append(f"food_id spoza listy produktów: {unknown}")
    problems += [
        f"food_id {term.food_id}: name_pl {term.name_pl!r}, na liście {names[term.food_id]!r}"
        for term in terms
        if term.food_id in names and term.name_pl != names[term.food_id]
    ]
    if problems:
        raise MappingError(f"niepoprawny {path.name}:\n" + "\n".join(problems))
    return {term.food_id: term.query_en for term in terms}


# --- Punktacja kandydatów ---


@dataclass(frozen=True)
class Candidate:
    """Rekord USDA zaproponowany dla wariantu produktu."""

    fdc_id: int
    score: float
    description: str
    category: str


Scores = npt.NDArray[np.float64]


class Scorer:
    """Wyniki dopasowania (0–100) zapytań do wszystkich rekordów USDA.

    Wynik = wynik podstawowy (podobieństwo nazw) + premia lub kara za obróbkę
    + kary za markę, sól, formę handlową i słowa zapytania nieobecne w opisie,
    przycięty do 0–100 i zaokrąglony do 0,1.
    """

    def __init__(
        self,
        usda: pl.DataFrame,
        queries: dict[int, str],
        preparations: dict[str, PreparationRule],
    ) -> None:
        self.fdc_ids: npt.NDArray[np.int64] = usda["fdc_id"].to_numpy()
        self.descriptions: list[str] = usda["description"].to_list()
        self.categories: list[str] = usda["food_category"].fill_null("").to_list()
        self._index = {int(fdc_id): i for i, fdc_id in enumerate(self.fdc_ids)}
        self._food_ids = list(queries)
        self._row = {food_id: i for i, food_id in enumerate(self._food_ids)}
        self._vocabulary = [rule.words() for rule in preparations.values()]
        self._base = self._base_scores([queries[food_id] for food_id in self._food_ids])
        self._form = self._form_penalties([queries[food_id] for food_id in self._food_ids])
        self._form += self._missing_word_penalties(
            [queries[food_id] for food_id in self._food_ids],
            [words(description) for description in self.descriptions],
        )
        self._queries = queries
        self._preparations = preparations
        texts = [normalized(description) for description in self.descriptions]
        # Dla każdego słowa lub frazy z reguł: czy występuje w opisie (wektor po rekordach USDA)
        self._term_hits = {
            term: np.array([f" {term} " in text for text in texts], dtype=bool)
            for rule in preparations.values()
            for term in rule.include | rule.exclude
        }

    def _base_scores(self, queries: list[str]) -> Scores:
        def matrix(scorer: Callable[..., float], left: list[str], right: list[str]) -> Scores:
            return np.asarray(
                process.cdist(
                    left, right, scorer=scorer, processor=utils.default_process, workers=-1
                ),
                dtype=np.float64,
            )

        noise = NOISE_WORDS.union(*self._vocabulary)

        def clean(text: str) -> str:
            return " ".join(w for w in _WORD_RE.findall(text.lower()) if w not in noise)

        heads = [query.split(",")[0] for query in queries]
        description_heads = [description.split(",")[0] for description in self.descriptions]
        return (
            WEIGHT_TOKEN_SET * matrix(fuzz.token_set_ratio, queries, self.descriptions)
            + WEIGHT_TOKEN_SORT
            * matrix(
                fuzz.token_sort_ratio,
                [clean(q) for q in queries],
                [clean(d) for d in self.descriptions],
            )
            + WEIGHT_HEAD * matrix(fuzz.ratio, heads, description_heads)
        )

    def _form_penalties(self, queries: list[str]) -> Scores:
        brand = np.array([bool(_BRAND_RE.search(d)) for d in self.descriptions], dtype=np.float64)
        salt = np.array([bool(_SALT_RE.search(d.lower())) for d in self.descriptions], np.float64)
        penalties = np.tile(-(BRAND_PENALTY * brand + SALT_PENALTY * salt), (len(queries), 1))
        description_words = [words(description) for description in self.descriptions]
        for form in FORM_WORDS:
            has_form = np.array([form in w for w in description_words], dtype=np.float64)
            for row, query in enumerate(queries):
                if form not in words(query):
                    penalties[row] -= FORM_PENALTY * has_form
        return penalties

    @staticmethod
    def _missing_word_penalties(
        queries: list[str], description_words: list[frozenset[str]]
    ) -> Scores:
        penalties = np.zeros((len(queries), len(description_words)), dtype=np.float64)
        for row, query in enumerate(queries):
            query_words = words(query) - NOISE_WORDS - STOP_WORDS
            penalties[row] = [
                -MISSING_WORD_PENALTY * len(query_words - w) for w in description_words
            ]
        return penalties

    def _any_hit(self, terms: Iterable[str]) -> npt.NDArray[np.bool_]:
        hits = np.zeros(len(self.descriptions), dtype=bool)
        for term in terms:
            hits |= self._term_hits[term]
        return hits

    def _preparation_scores(self, food_id: int, preparation: str) -> Scores:
        """Premie i kary za obróbkę. Słowa obecne w samym zapytaniu (np. „roasted” w „Buckwheat
        groats, roasted”) opisują produkt, nie obróbkę – nie są karane."""
        rule = self._preparations[preparation]
        query = normalized(self._queries[food_id])
        included = self._any_hit(rule.include)
        excluded = self._any_hit(t for t in rule.exclude if not contains_any(query, frozenset({t})))
        scores: Scores = PREPARATION_BONUS * included - PREPARATION_PENALTY * excluded
        if rule.required:
            scores -= PREPARATION_MISSING_PENALTY * ~included
        return scores

    def _raw(self, food_id: int, preparation: str) -> Scores:
        row = self._row[food_id]
        total: Scores = (
            self._base[row] + self._form[row] + self._preparation_scores(food_id, preparation)
        )
        return total

    def scores(self, food_id: int, preparation: str) -> Scores:
        """Wyniki wariantu produktu dla wszystkich rekordów USDA (kolejność jak w `fdc_ids`)."""
        return np.round(np.clip(self._raw(food_id, preparation), 0.0, 100.0), 1)

    def score_of(self, food_id: int, preparation: str, fdc_id: int) -> float | None:
        """Wynik konkretnego rekordu; None, gdy rekord jest poza przeszukiwanym zbiorem."""
        index = self._index.get(fdc_id)
        if index is None:
            return None
        return float(self.scores(food_id, preparation)[index])

    def top(self, food_id: int, preparation: str, n: int = TOP_N) -> list[Candidate]:
        """Najlepsze rekordy: malejąco po wyniku przed przycięciem do 100 (premie rozróżniają
        rekordy z wynikiem 100), przy remisie rosnąco po `fdc_id`."""
        raw = np.round(self._raw(food_id, preparation), 1)
        scores = self.scores(food_id, preparation)
        order = np.lexsort((self.fdc_ids, -raw))[:n]
        return [
            Candidate(
                fdc_id=int(self.fdc_ids[i]),
                score=float(scores[i]),
                description=self.descriptions[i],
                category=self.categories[i],
            )
            for i in order
        ]


# --- Plik mapowania ---


class MappingRow(BaseModel):
    """Wiersz `mapping.csv`: wariant produktu i przypisany rekord USDA."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    variant_id: int = Field(gt=0)
    food_id: int = Field(gt=0)
    name_pl: str
    preparation: Preparation
    fdc_id: int | None
    status: Status
    usda_description: str = ""
    # Wynik przypisanego rekordu; przy statusie `brak` – wynik najlepszego kandydata
    score: float | None = None

    @field_validator("fdc_id", "score", mode="before")
    @classmethod
    def _empty_is_none(cls, value: object) -> object:
        return None if value == "" else value


def load_mapping(path: Path = MAPPING_FILE) -> dict[int, MappingRow]:
    """Dotychczasowe mapowanie (`variant_id` → wiersz); pusty słownik, gdy pliku nie ma."""
    if not path.exists():
        return {}
    try:
        with path.open(encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            if reader.fieldnames != MAPPING_COLUMNS:
                raise MappingError(
                    f"{path.name}: kolumny {reader.fieldnames}, oczekiwane {MAPPING_COLUMNS}"
                )
            rows = [MappingRow.model_validate(row) for row in reader]
    except OSError as error:
        raise MappingError(f"nie można wczytać {path.name}: {error}") from error
    except ValidationError as error:
        raise MappingError(f"niepoprawny {path.name}: {error}") from error
    mapping = {row.variant_id: row for row in rows}
    if len(mapping) != len(rows):
        raise MappingError(f"{path.name}: powtórzone variant_id")
    return mapping


def build_mapping(
    variants: Sequence[FoodVariant],
    candidates: dict[int, list[Candidate]],
    previous: dict[int, MappingRow],
    scorer: Scorer,
    usda_descriptions: dict[int, str],
    threshold: float = AUTO_THRESHOLD,
) -> tuple[list[MappingRow], list[str]]:
    """Nowe mapowanie i lista ostrzeżeń.

    Wiersze `zweryfikowany` z poprzedniego mapowania zostają bez zmian (poza opisem i wynikiem),
    o ile wariant ma ten sam `food_id` i obróbkę. Pozostałe liczone są od nowa z kandydatów.
    `usda_descriptions` obejmuje wszystkie rekordy SR Legacy, także spoza przeszukiwanych kategorii.
    """
    rows = []
    warnings = []
    for variant in variants:
        old = previous.get(variant.variant_id)
        if old is not None and old.status == "zweryfikowany":
            if (old.food_id, old.preparation) == (variant.food_id, variant.preparation):
                if old.fdc_id is not None and old.fdc_id not in usda_descriptions:
                    raise MappingError(
                        f"variant_id {variant.variant_id}: fdc_id {old.fdc_id} nie istnieje "
                        "w USDA SR Legacy"
                    )
                fdc_id = old.fdc_id
                rows.append(
                    MappingRow(
                        variant_id=variant.variant_id,
                        food_id=variant.food_id,
                        name_pl=variant.name_pl,
                        preparation=variant.preparation,
                        fdc_id=fdc_id,
                        status="zweryfikowany",
                        usda_description="" if fdc_id is None else usda_descriptions[fdc_id],
                        score=None
                        if fdc_id is None
                        else scorer.score_of(variant.food_id, variant.preparation, fdc_id),
                    )
                )
                continue
            warnings.append(
                f"variant_id {variant.variant_id}: zmienił się produkt lub obróbka – "
                "weryfikacja usunięta, wariant zmapowany od nowa"
            )
        best = candidates[variant.variant_id][0]
        matched = best.score >= threshold
        rows.append(
            MappingRow(
                variant_id=variant.variant_id,
                food_id=variant.food_id,
                name_pl=variant.name_pl,
                preparation=variant.preparation,
                fdc_id=best.fdc_id if matched else None,
                status="auto" if matched else "brak",
                usda_description=best.description if matched else "",
                score=best.score,
            )
        )
    dropped = sorted(set(previous) - {variant.variant_id for variant in variants})
    if dropped:
        warnings.append(f"usunięte z mapowania warianty spoza listy: {dropped}")
    return rows, warnings


# --- Zapis ---


def _score(value: float | None) -> str:
    return "" if value is None else f"{value:.1f}"


def _write_csv(path: Path, header: list[str], rows: Iterable[list[object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def write_candidates(
    path: Path, variants: Sequence[FoodVariant], candidates: dict[int, list[Candidate]]
) -> None:
    _write_csv(
        path,
        CANDIDATE_COLUMNS,
        (
            [
                v.variant_id,
                v.name_pl,
                v.preparation,
                rank,
                c.fdc_id,
                _score(c.score),
                c.description,
                c.category,
            ]  # fmt: skip
            for v in variants
            for rank, c in enumerate(candidates[v.variant_id], start=1)
        ),
    )


def write_mapping(path: Path, rows: Sequence[MappingRow]) -> None:
    _write_csv(
        path,
        MAPPING_COLUMNS,
        (
            [
                r.variant_id,
                r.food_id,
                r.name_pl,
                r.preparation,
                "" if r.fdc_id is None else r.fdc_id,
                r.status,
                r.usda_description,
                _score(r.score),
            ]  # fmt: skip
            for r in rows
        ),
    )


def load_candidates(path: Path = CANDIDATES_FILE) -> dict[int, list[Candidate]]:
    """Kandydaci z `mapping_candidates.csv` (`variant_id` → lista według rangi)."""
    candidates: dict[int, list[Candidate]] = {}
    try:
        with path.open(encoding="utf-8", newline="") as file:
            for row in csv.DictReader(file):
                candidates.setdefault(int(row["variant_id"]), []).append(
                    Candidate(
                        fdc_id=int(row["fdc_id"]),
                        score=float(row["score"]),
                        description=row["usda_description"],
                        category=row["usda_category"],
                    )
                )
    except (OSError, KeyError, ValueError) as error:
        raise MappingError(f"nie można wczytać {path.name}: {error}") from error
    return candidates


def _cell(text: str) -> str:
    return text.replace("|", "\\|")


def render_report(
    variants: Sequence[FoodVariant],
    rows: Sequence[MappingRow],
    candidates: dict[int, list[Candidate]],
) -> str:
    """Raport Markdown: podsumowanie mapowania i warianty bez odpowiednika w USDA.

    Dwie listy: produkty podstawowe bez żadnego zmapowanego wariantu (do uzupełnienia z Ciqual
    lub Fineli) oraz brakujące warianty obróbki produktów, które mają w USDA inny wariant
    (do wyliczenia współczynnikami w S-106 albo uzupełnienia z drugiego źródła).
    """
    by_id = {variant.variant_id: variant for variant in variants}
    statuses = Counter(row.status for row in rows)
    missing = [row for row in rows if row.fdc_id is None]
    mapped_foods = {row.food_id for row in rows if row.fdc_id is not None}
    whole = [row for row in missing if row.food_id not in mapped_foods]
    partial = [row for row in missing if row.food_id in mapped_foods]

    def table(selected: list[MappingRow]) -> list[str]:
        lines = [
            "| variant_id | Produkt | Wariant | Typowo polski | Status | "
            "Najlepszy kandydat USDA | Wynik | Uwagi z listy |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for row in selected:
            variant = by_id[row.variant_id]
            found = candidates.get(row.variant_id)
            best = found[0] if found else None
            lines.append(
                f"| {row.variant_id} | {_cell(variant.name_pl)} | {variant.preparation} | "
                f"{'tak' if variant.polish_specific else 'nie'} | `{row.status}` | "
                f"{_cell(best.description) if best else '–'} | "
                f"{_score(best.score) if best else '–'} | {_cell(variant.notes) or '–'} |"
            )
        return lines

    return (
        "\n".join(
            [
                "# Produkty bez odpowiednika w USDA SR Legacy",
                "",
                "Wygenerowane przez `make map-products` (S-104) z "
                "`data-pipeline/mapping/mapping.csv` – nie edytuj ręcznie.",
                "",
                "## Podsumowanie",
                "",
                "| Status | Warianty |",
                "| --- | --- |",
                *[f"| `{status}` | {statuses.get(status, 0)} |" for status in get_args(Status)],
                f"| razem | {len(rows)} |",
                "",
                f"Status `brak` = najlepszy kandydat poniżej progu {AUTO_THRESHOLD:.0f} "
                "(pozostali w `mapping_candidates.csv`); `zweryfikowany` z pustym `fdc_id` = "
                "brak potwierdzony ręcznie.",
                "",
                f"## Produkty do uzupełnienia z Ciqual lub Fineli ({len(whole)} wariantów, "
                f"{len({row.food_id for row in whole})} produktów)",
                "",
                "Żaden wariant produktu nie ma odpowiednika w USDA – potrzebne drugie źródło "
                "([ADR-0001](../adr/0001-food-database.md)).",
                "",
                *table(whole),
                "",
                f"## Brakujące warianty obróbki ({len(partial)} wariantów, "
                f"{len({row.food_id for row in partial})} produktów)",
                "",
                "Produkt ma w USDA inny wariant obróbki – brakujący wariant do wyliczenia "
                "współczynnikami retencji i wydajności (S-106) albo z Ciqual lub Fineli.",
                "",
                *table(partial),
            ]
        )
        + "\n"
    )


# --- Uruchomienie ---


@dataclass(frozen=True)
class MappingResult:
    variants: list[FoodVariant]
    candidates: dict[int, list[Candidate]]
    rows: list[MappingRow]
    warnings: list[str]
    report: str


def generate(previous_path: Path = MAPPING_FILE) -> MappingResult:
    """Liczy kandydatów, mapowanie i raport z danych w repo (bez zapisu plików)."""
    problems = verify_dir(RAW_DIR, read_manifest(MANIFEST_PATH))
    if problems:
        raise MappingError(f"{problems[0]}; odtwórz surowe dane: make fetch-usda")
    try:
        variants = load_variants()
    except ProductListError as error:
        raise MappingError(str(error)) from error
    queries = load_search_terms(variants)
    preparations = load_preparations()

    usda_all = load_foods(RAW_DIR)
    usda_descriptions = dict(
        zip(usda_all["fdc_id"].to_list(), usda_all["description"].to_list(), strict=True)
    )
    searched = usda_all.filter(~pl.col("food_category").is_in(list(EXCLUDED_CATEGORIES)))
    scorer = Scorer(searched, queries, preparations)
    candidates = {v.variant_id: scorer.top(v.food_id, v.preparation) for v in variants}
    rows, warnings = build_mapping(
        variants, candidates, load_mapping(previous_path), scorer, usda_descriptions
    )
    return MappingResult(
        variants, candidates, rows, warnings, render_report(variants, rows, candidates)
    )


def main() -> int:
    """Zapisuje kandydatów, mapowanie i raport braków; kod wyjścia 1 przy błędach."""
    try:
        result = generate()
    except MappingError as error:
        print(f"Błąd: {error}", file=sys.stderr)
        return 1
    write_candidates(CANDIDATES_FILE, result.variants, result.candidates)
    write_mapping(MAPPING_FILE, result.rows)
    MISSING_REPORT.write_text(result.report, encoding="utf-8", newline="\n")
    for warning in result.warnings:
        print(f"Uwaga: {warning}", file=sys.stderr)
    statuses = Counter(row.status for row in result.rows)
    print(
        f"OK: {len(result.rows)} wariantów – auto {statuses['auto']}, zweryfikowany "
        f"{statuses['zweryfikowany']}, brak {statuses['brak']}; zapisano {MAPPING_FILE.name}, "
        f"{CANDIDATES_FILE.name} i {MISSING_REPORT.name}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
