"""Buduje tabelę szeroką z USDA SR Legacy (S-102): 1 wiersz = produkt, kolumny = składniki odżywcze.

Wejście: znormalizowane pliki CSV w data/raw/usda_sr_legacy/ (S-006, sprawdzane sumą SHA-256).
Łączy `sr_legacy_food` + `food` + `food_category` z `food_nutrient` + `nutrient`.

Wyjście w data/interim/ (poza git, odtwarzane tym skryptem):
- `sr_wide.parquet` – kolumny `fdc_id`, `ndb_number`, `description`, `food_category_id`,
  `food_category`, potem po jednej kolumnie na składnik odżywczy, np. `protein_g`, `energy_kcal`;
  wartości na 100 g części jadalnej, brak wartości = null (nigdy 0),
- `sr_wide_nutrients.csv` – słownik kolumn składników: id USDA, nazwa, jednostka, liczba produktów
  z wartością.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from pathlib import Path

import polars as pl

from fetch_usda import DEST_DIR, MANIFEST_PATH, REPO_ROOT, read_manifest, verify_dir

RAW_DIR = DEST_DIR
INTERIM_DIR = REPO_ROOT / "data" / "interim"
WIDE_FILE = "sr_wide.parquet"
DICTIONARY_FILE = "sr_wide_nutrients.csv"

FOOD_COLUMNS = ["fdc_id", "ndb_number", "description", "food_category_id", "food_category"]
DICTIONARY_COLUMNS = ["column", "nutrient_id", "nutrient_nbr", "name", "unit", "rank", "food_count"]

# Jednostki USDA → przyrostek kolumny (UG = mikrogram, IU = jednostka międzynarodowa)
UNIT_SUFFIXES = {"G": "g", "MG": "mg", "UG": "ug", "IU": "iu", "KCAL": "kcal", "KJ": "kj"}


class WideTableError(Exception):
    """Danych nie da się zamienić na tabelę szeroką (np. nieznana jednostka, kolizja nazw)."""


def column_name(nutrient_name: str, unit_name: str) -> str:
    """Nazwa kolumny składnika: nazwa USDA w snake_case + jednostka, np. `protein_g`."""
    unit = UNIT_SUFFIXES.get(unit_name.upper())
    if unit is None:
        raise WideTableError(f"nieznana jednostka składnika {nutrient_name!r}: {unit_name!r}")
    slug = re.sub(r"[^a-z0-9]+", "_", nutrient_name.lower()).strip("_")
    if not slug or not slug[0].isalpha():
        raise WideTableError(f"nazwa składnika nie daje poprawnej nazwy kolumny: {nutrient_name!r}")
    return f"{slug}_{unit}"


def _read_csv(path: Path, schema: dict[str, pl.DataType]) -> pl.DataFrame:
    """Czyta wybrane kolumny CSV USDA (wszystkie pola w cudzysłowach, puste pole = null)."""
    return pl.read_csv(
        path,
        columns=list(schema),
        schema_overrides=schema,
        encoding="utf8",
    )


def load_foods(raw_dir: Path) -> pl.DataFrame:
    """Produkty SR Legacy z opisem i kategorią – po jednym wierszu na `fdc_id`."""
    sr_foods = _read_csv(
        raw_dir / "sr_legacy_food.csv", {"fdc_id": pl.Int64(), "NDB_number": pl.Int64()}
    ).rename({"NDB_number": "ndb_number"})
    foods = _read_csv(
        raw_dir / "food.csv",
        {"fdc_id": pl.Int64(), "description": pl.String(), "food_category_id": pl.Int64()},
    )
    categories = _read_csv(
        raw_dir / "food_category.csv", {"id": pl.Int64(), "description": pl.String()}
    ).rename({"id": "food_category_id", "description": "food_category"})
    # Lewe złączenia: liczba wierszy = liczba produktów w sr_legacy_food.csv
    return (
        sr_foods.join(foods, on="fdc_id", how="left", validate="1:1")
        .join(categories, on="food_category_id", how="left", validate="m:1")
        .select(FOOD_COLUMNS)
        .sort("fdc_id")
    )


def load_food_nutrients(raw_dir: Path, fdc_ids: pl.Series) -> pl.DataFrame:
    """Wartości składników (na 100 g) tylko dla produktów SR Legacy."""
    values = _read_csv(
        raw_dir / "food_nutrient.csv",
        {"fdc_id": pl.Int64(), "nutrient_id": pl.Int64(), "amount": pl.Float64()},
    )
    values = values.filter(pl.col("fdc_id").is_in(fdc_ids.implode()))
    duplicates = values.group_by("fdc_id", "nutrient_id").len().filter(pl.col("len") > 1)
    if duplicates.height:
        raise WideTableError(
            f"{duplicates.height} par (fdc_id, nutrient_id) ma więcej niż jedną wartość"
        )
    return values


def build_dictionary(raw_dir: Path, values: pl.DataFrame) -> pl.DataFrame:
    """Słownik kolumn dla składników, które mają co najmniej jedną wartość.

    Kolejność kolumn: `rank` z USDA (kolejność prezentacji w FDC), potem id składnika.
    """
    nutrients = _read_csv(
        raw_dir / "nutrient.csv",
        {
            "id": pl.Int64(),
            "name": pl.String(),
            "unit_name": pl.String(),
            "nutrient_nbr": pl.String(),
            "rank": pl.Float64(),
        },
    ).rename({"id": "nutrient_id", "unit_name": "unit"})
    counts = values.filter(pl.col("amount").is_not_null()).group_by("nutrient_id").len("food_count")
    used = values.select("nutrient_id").unique()
    unknown = used.join(nutrients, on="nutrient_id", how="anti")
    if unknown.height:
        ids = ", ".join(str(i) for i in unknown["nutrient_id"].sort())
        raise WideTableError(f"składniki bez opisu w nutrient.csv: {ids}")
    dictionary = (
        nutrients.join(used, on="nutrient_id", how="semi")
        .join(counts, on="nutrient_id", how="left")
        .with_columns(
            pl.col("food_count").fill_null(0),
            pl.struct("name", "unit")
            .map_elements(lambda r: column_name(r["name"], r["unit"]), return_dtype=pl.String())
            .alias("column"),
        )
        .sort("rank", "nutrient_id", nulls_last=True)
        .select(DICTIONARY_COLUMNS)
    )
    clashes = dictionary.group_by("column").len().filter(pl.col("len") > 1)
    if clashes.height:
        raise WideTableError(f"kolizja nazw kolumn: {', '.join(clashes['column'].sort())}")
    if set(dictionary["column"]) & set(FOOD_COLUMNS):
        raise WideTableError("nazwa składnika pokrywa się z kolumną opisu produktu")
    return dictionary


def build(raw_dir: Path) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Zwraca (tabela szeroka, słownik kolumn składników) z plików CSV w `raw_dir`."""
    foods = load_foods(raw_dir)
    values = load_food_nutrients(raw_dir, foods["fdc_id"])
    dictionary = build_dictionary(raw_dir, values)
    names = dict(zip(dictionary["nutrient_id"], dictionary["column"], strict=True))
    wide_values = (
        values.with_columns(pl.col("nutrient_id").replace_strict(names, return_dtype=pl.String()))
        .pivot(on="nutrient_id", index="fdc_id", values="amount")
        .select("fdc_id", *[pl.col(c).cast(pl.Float64()) for c in dictionary["column"]])
    )
    # Brak wiersza w food_nutrient → null w kolumnie (nie zero)
    wide = foods.join(wide_values, on="fdc_id", how="left", validate="1:1")
    return wide, dictionary


def write_outputs(wide: pl.DataFrame, dictionary: pl.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    wide.write_parquet(out_dir / WIDE_FILE)
    dictionary.write_csv(out_dir / DICTIONARY_FILE, line_terminator="\n")


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Buduje tabelę szeroką z USDA SR Legacy (1 wiersz = produkt, kolumny = składniki "
            f"odżywcze) i zapisuje {WIDE_FILE} oraz słownik {DICTIONARY_FILE}."
        ),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=INTERIM_DIR,
        help="katalog wyjściowy (domyślnie data/interim/)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        problems = verify_dir(RAW_DIR, read_manifest(MANIFEST_PATH))
        if problems:
            for problem in problems:
                print(f"Błąd: {problem}", file=sys.stderr)
            print("Odtwórz surowe dane: make fetch-usda", file=sys.stderr)
            return 1
        wide, dictionary = build(RAW_DIR)
        write_outputs(wide, dictionary, args.out_dir)
    except (WideTableError, OSError, pl.exceptions.PolarsError) as error:
        print(f"Błąd: {error}", file=sys.stderr)
        return 1
    print(
        # Bez znaków spoza cp1250 (konsola Windows): zapis do pliku, nie strzałki
        f"OK: {wide.height} produktów, {dictionary.height} składników; zapisano "
        f"{args.out_dir / WIDE_FILE} i słownik {args.out_dir / DICTIONARY_FILE}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
