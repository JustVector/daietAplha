"""Raport pokrycia składników odżywczych w USDA SR Legacy (S-103).

Pokrycie składnika = odsetek produktów SR Legacy, które mają jego wartość (null = brak wartości;
zero ze źródła to wartość). Raport opisuje składniki bazy v1 z `nutrients.yaml`, ich pokrycie
w kategoriach USDA i pokrycie wszystkich składników tabeli szerokiej (S-102).

Wejście: surowe dane w data/raw/usda_sr_legacy/ (sprawdzane sumą SHA-256), tabela szeroka liczona
w pamięci tak samo jak w `build_sr_wide.py`. Wyjście: docs/data/nutrient_coverage.md (w git).
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

import polars as pl

from build_sr_wide import RAW_DIR, UNIT_SUFFIXES, WideTableError, build
from fetch_usda import MANIFEST_PATH, REPO_ROOT, read_manifest, verify_dir
from nutrients import Nutrient, NutrientConfigError, check_against_dictionary, load_nutrients

REPORT_PATH = REPO_ROOT / "docs" / "data" / "nutrient_coverage.md"

# Próg „słabego” pokrycia w tabeli kategorii
LOW_COVERAGE = 0.5
UNIT_LABELS = {"ug": "µg", "kj": "kJ", "iu": "IU"}


def unit_label(unit: str) -> str:
    """Jednostka do wyświetlenia: `ug` → `µg`, jednostki USDA (`MG`, `kJ`) małymi literami."""
    suffix = UNIT_SUFFIXES.get(unit.upper(), unit.lower())
    return UNIT_LABELS.get(suffix, suffix)


def percent(share: float) -> str:
    """Odsetek z jednym miejscem po przecinku, np. `93,1%`."""
    return f"{share * 100:.1f}%".replace(".", ",")


def _table(header: list[str], rows: list[list[str]]) -> list[str]:
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join("---" for _ in header) + " |"]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    return lines


def category_coverage(wide: pl.DataFrame, nutrients: list[Nutrient]) -> pl.DataFrame:
    """Pokrycie składników v1 w każdej kategorii USDA: kolumny `food_category`, `food_count`
    i po jednej kolumnie udziału (0–1) na składnik."""
    columns = [n.usda_column for n in nutrients]
    return (
        wide.with_columns(pl.col("food_category").fill_null("(brak kategorii)"))
        .group_by("food_category")
        .agg(
            pl.len().alias("food_count"),
            *[pl.col(c).is_not_null().mean().alias(c) for c in columns],
        )
        .sort("food_category")
    )


def render_report(wide: pl.DataFrame, dictionary: pl.DataFrame, nutrients: list[Nutrient]) -> str:
    """Treść raportu w Markdown (deterministyczna – bez daty generowania)."""
    total = wide.height
    counts = dict(zip(dictionary["nutrient_id"], dictionary["food_count"], strict=True))
    v1_ids = {n.usda_nutrient_id: n for n in nutrients}

    lines = [
        "# Pokrycie składników odżywczych – USDA SR Legacy",
        "",
        "> Plik generowany przez `make nutrient-coverage` (S-103) – nie edytuj ręcznie.",
        "",
        f"Dane: USDA FoodData Central – SR Legacy (2018-04): {total} produktów, "
        f"{dictionary.height} składników z co najmniej jedną wartością "
        "(tabela szeroka, [S-102](../../backlog/S-102.md)).",
        "",
        "**Pokrycie** składnika to odsetek produktów, które mają jego wartość. Brak wartości "
        "w źródle to `null`; zero podane przez USDA liczy się jako wartość.",
        "",
        "Lista składników bazy v1: "
        "[`data-pipeline/nutrients.yaml`](../../data-pipeline/nutrients.yaml) "
        "(decyzje w [S-103](../../backlog/S-103.md)). Pokrycie liczone jest na całym SR Legacy; "
        "baza v1 obejmie 300–500 produktów podstawowych (S-101), więc ostateczne pokrycie "
        "będzie znane po mapowaniu (S-104).",
        "",
        f"## Składniki bazy v1 ({len(nutrients)})",
        "",
    ]
    rows = [
        [
            str(n.order),
            n.name_pl,
            unit_label(n.unit),
            f"`{n.usda_column}`",
            str(n.usda_nutrient_id),
            str(counts[n.usda_nutrient_id]),
            percent(counts[n.usda_nutrient_id] / total),
        ]
        for n in nutrients
    ]
    header = ["#", "Składnik", "Jedn.", "Kolumna USDA", "id USDA", "Produkty z wartością"]
    lines += _table([*header, "Pokrycie"], rows)

    by_category = category_coverage(wide, nutrients)
    columns = [n.usda_column for n in nutrients]
    lines += [
        "",
        "## Pokrycie składników v1 według kategorii USDA",
        "",
        "Średnie pokrycie = średnia z pokrycia wszystkich składników v1 w kategorii. "
        f"Ostatnia kolumna wymienia składniki v1 z pokryciem poniżej {percent(LOW_COVERAGE)} "
        "w danej kategorii.",
        "",
    ]
    rows = []
    for row in by_category.iter_rows(named=True):
        shares = [float(row[c]) for c in columns]
        low = [
            n.name_pl for n, share in zip(nutrients, shares, strict=True) if share < LOW_COVERAGE
        ]
        rows.append(
            [
                row["food_category"],
                str(row["food_count"]),
                percent(sum(shares) / len(shares)),
                ", ".join(low) if low else "–",
            ]
        )
    header = ["Kategoria USDA", "Produkty", "Średnie pokrycie"]
    lines += _table([*header, f"Pokrycie < {percent(LOW_COVERAGE)}"], rows)

    lines += [
        "",
        "## Wszystkie składniki SR Legacy",
        "",
        "Kolejność: `rank` z USDA (kolejność prezentacji w FoodData Central).",
        "",
    ]
    rows = [
        [
            f"`{row['column']}`",
            str(row["nutrient_id"]),
            row["name"],
            unit_label(row["unit"]),
            str(row["food_count"]),
            percent(row["food_count"] / total),
            v1_ids[row["nutrient_id"]].name_pl if row["nutrient_id"] in v1_ids else "",
        ]
        for row in dictionary.iter_rows(named=True)
    ]
    header = ["Kolumna", "id USDA", "Nazwa USDA", "Jedn.", "Produkty z wartością", "Pokrycie"]
    lines += _table([*header, "Baza v1"], rows)
    return "\n".join(lines) + "\n"


def generate(raw_dir: Path = RAW_DIR, nutrients_path: Path | None = None) -> str:
    """Buduje tabelę szeroką z `raw_dir`, sprawdza konfigurację składników i zwraca raport."""
    nutrients = load_nutrients() if nutrients_path is None else load_nutrients(nutrients_path)
    wide, dictionary = build(raw_dir)
    problems = check_against_dictionary(nutrients, dictionary)
    if problems:
        raise NutrientConfigError(
            "nutrients.yaml niezgodny z danymi USDA:\n" + "\n".join(f"- {p}" for p in problems)
        )
    return render_report(wide, dictionary, nutrients)


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generuje raport pokrycia składników odżywczych w USDA SR Legacy "
            "(docs/data/nutrient_coverage.md) i sprawdza nutrients.yaml z danymi USDA."
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=REPORT_PATH,
        help="plik raportu (domyślnie docs/data/nutrient_coverage.md)",
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
        report = generate()
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8", newline="\n")
    except (NutrientConfigError, WideTableError, OSError, pl.exceptions.PolarsError) as error:
        print(f"Błąd: {error}", file=sys.stderr)
        return 1
    print(f"OK: zapisano raport {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
