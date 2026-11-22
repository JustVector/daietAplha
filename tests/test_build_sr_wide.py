"""Testy build_sr_wide.py (S-102).

Testy jednostkowe działają na małych plikach CSV tworzonych w teście.
Test na prawdziwych danych wymaga data/raw/usda_sr_legacy/ (`make fetch-usda`);
bez danych jest pomijany, a w CI (REQUIRE_USDA=1) brak danych to błąd, nie pominięcie.
"""

import csv
import os
from pathlib import Path

import polars as pl
import pytest

import build_sr_wide
from build_sr_wide import (
    DICTIONARY_COLUMNS,
    FOOD_COLUMNS,
    WideTableError,
    build,
    column_name,
    write_outputs,
)
from fetch_usda import MANIFEST_PATH, read_manifest, verify_dir


def _write_csv(path: Path, header: list[str], rows: list[list[object]]) -> None:
    """Zapisuje CSV w stylu USDA: wszystkie pola w cudzysłowach."""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, quoting=csv.QUOTE_ALL)
        writer.writerow(header)
        writer.writerows(rows)


@pytest.fixture
def raw_dir(tmp_path: Path) -> Path:
    """Mini-zestaw: 3 produkty SR Legacy (jeden bez żadnych wartości) i produkt spoza SR."""
    directory = tmp_path / "raw"
    directory.mkdir()
    _write_csv(
        directory / "sr_legacy_food.csv",
        ["fdc_id", "NDB_number"],
        [[30, 3003], [10, 1001], [20, 2002]],
    )
    _write_csv(
        directory / "food.csv",
        ["fdc_id", "data_type", "description", "food_category_id", "publication_date"],
        [
            [10, "sr_legacy_food", "Potatoes, raw", 11, "2019-04-01"],
            [20, "sr_legacy_food", "Egg, whole, raw", 1, "2019-04-01"],
            [30, "sr_legacy_food", "Water, tap", 14, "2019-04-01"],
            [99, "foundation_food", "Inny zbiór", 11, "2020-01-01"],
        ],
    )
    _write_csv(
        directory / "food_category.csv",
        ["id", "code", "description"],
        [[1, "0100", "Dairy and Egg Products"], [11, "1100", "Vegetables"], [14, "1400", "Bev"]],
    )
    _write_csv(
        directory / "nutrient.csv",
        ["id", "name", "unit_name", "nutrient_nbr", "rank"],
        [
            [1003, "Protein", "G", "203", "600.0"],
            [1008, "Energy", "KCAL", "208", "300.0"],
            [1062, "Energy", "kJ", "268", "400.0"],
            [1110, "Vitamin D (D2 + D3), International Units", "IU", "324", "8650.0"],
            [1092, "Potassium, K", "MG", "306", "5700.0"],
            [2000, "Nieużywany", "G", "999", "1.0"],
        ],
    )
    _write_csv(
        directory / "food_nutrient.csv",
        ["id", "fdc_id", "nutrient_id", "amount", "data_points", "derivation_id"],
        [
            [1, 10, 1003, "2.05", 1, 1],
            [2, 10, 1008, "77", 0, 49],
            [3, 10, 1062, "322", 0, 49],
            [4, 10, 1092, "425", 1, 1],
            [5, 20, 1003, "12.56", 1, 1],
            [6, 20, 1008, "143", 0, 49],
            [7, 20, 1110, "82", 1, 1],
            [8, 20, 1092, "0", 1, 1],
            [9, 99, 1003, "5", 1, 1],
        ],
    )
    return directory


def test_column_name_is_readable_snake_case_with_unit() -> None:
    assert column_name("Protein", "G") == "protein_g"
    assert column_name("Energy", "kJ") == "energy_kj"
    assert column_name("Total lipid (fat)", "G") == "total_lipid_fat_g"
    assert column_name("Vitamin D (D2 + D3), International Units", "IU") == (
        "vitamin_d_d2_d3_international_units_iu"
    )
    assert column_name("PUFA 18:2 n-6 c,c", "G") == "pufa_18_2_n_6_c_c_g"
    assert column_name("Vitamin B-12", "UG") == "vitamin_b_12_ug"


def test_column_name_rejects_unknown_unit() -> None:
    with pytest.raises(WideTableError, match="nieznana jednostka"):
        column_name("Protein", "OZ")


def test_one_row_per_sr_legacy_food(raw_dir: Path) -> None:
    wide, _ = build(raw_dir)
    assert wide["fdc_id"].to_list() == [10, 20, 30]
    assert wide.columns[: len(FOOD_COLUMNS)] == FOOD_COLUMNS
    expected = {
        "fdc_id": 10,
        "ndb_number": 1001,
        "description": "Potatoes, raw",
        "food_category_id": 11,
        "food_category": "Vegetables",
    }
    assert expected.items() <= wide.row(0, named=True).items()


def test_nutrient_columns_ordered_by_usda_rank(raw_dir: Path) -> None:
    wide, dictionary = build(raw_dir)
    expected = [
        "energy_kcal",
        "energy_kj",
        "protein_g",
        "potassium_k_mg",
        "vitamin_d_d2_d3_international_units_iu",
    ]
    assert wide.columns[len(FOOD_COLUMNS) :] == expected
    assert dictionary["column"].to_list() == expected
    # Składnik bez żadnej wartości nie dostaje kolumny
    assert "nieuzywany_g" not in wide.columns


def test_missing_value_is_null_not_zero(raw_dir: Path) -> None:
    wide, _ = build(raw_dir)
    potato, egg, water = wide.iter_rows(named=True)
    assert potato["protein_g"] == pytest.approx(2.05)
    assert potato["vitamin_d_d2_d3_international_units_iu"] is None
    assert egg["energy_kj"] is None
    assert egg["potassium_k_mg"] == 0.0  # zero ze źródła zostaje zerem
    # Produkt bez wierszy w food_nutrient: wszystkie składniki null
    assert all(water[c] is None for c in wide.columns[len(FOOD_COLUMNS) :])


def test_dictionary_has_units_and_counts(raw_dir: Path) -> None:
    _, dictionary = build(raw_dir)
    assert dictionary.columns == DICTIONARY_COLUMNS
    rows = {row["column"]: row for row in dictionary.iter_rows(named=True)}
    expected = {"nutrient_id": 1003, "unit": "G", "food_count": 2}
    assert expected.items() <= rows["protein_g"].items()
    assert rows["energy_kj"]["unit"] == "kJ"
    assert rows["energy_kj"]["food_count"] == 1


def test_duplicate_values_are_rejected(raw_dir: Path) -> None:
    with (raw_dir / "food_nutrient.csv").open("a", encoding="utf-8", newline="") as handle:
        csv.writer(handle, quoting=csv.QUOTE_ALL).writerow([10, 10, 1003, "2.1", 1, 1])
    with pytest.raises(WideTableError, match="więcej niż jedną wartość"):
        build(raw_dir)


def test_column_name_clash_is_rejected(raw_dir: Path) -> None:
    with (raw_dir / "nutrient.csv").open("a", encoding="utf-8", newline="") as handle:
        csv.writer(handle, quoting=csv.QUOTE_ALL).writerow([1004, "Protein!", "G", "204", "700"])
    with (raw_dir / "food_nutrient.csv").open("a", encoding="utf-8", newline="") as handle:
        csv.writer(handle, quoting=csv.QUOTE_ALL).writerow([10, 10, 1004, "1", 1, 1])
    with pytest.raises(WideTableError, match="kolizja nazw kolumn: protein_g"):
        build(raw_dir)


def test_write_outputs_roundtrip(raw_dir: Path, tmp_path: Path) -> None:
    wide, dictionary = build(raw_dir)
    out_dir = tmp_path / "interim"
    write_outputs(wide, dictionary, out_dir)
    assert pl.read_parquet(out_dir / build_sr_wide.WIDE_FILE).equals(wide)
    saved = pl.read_csv(out_dir / build_sr_wide.DICTIONARY_FILE)
    assert saved["column"].to_list() == dictionary["column"].to_list()


# --- Prawdziwe dane USDA SR Legacy ---

# Wartości wzorcowe z FoodData Central (API FDC, /fdc/v1/food/{fdc_id}, odczyt 2026-11-22),
# niezależnie od plików CSV; widok w przeglądarce: https://fdc.nal.usda.gov/food-details/{fdc_id}
FDC_SAMPLES = {
    170026: {  # Potatoes, flesh and skin, raw
        "energy_kcal": 77.0,
        "protein_g": 2.05,
        "total_lipid_fat_g": 0.09,
        "fiber_total_dietary_g": 2.1,
        "calcium_ca_mg": 12.0,
        "potassium_k_mg": 425.0,
        "vitamin_c_total_ascorbic_acid_mg": 19.7,
    },
    171287: {  # Egg, whole, raw, fresh
        "energy_kcal": 143.0,
        "protein_g": 12.56,
        "total_lipid_fat_g": 9.51,
        "fiber_total_dietary_g": 0.0,
        "calcium_ca_mg": 56.0,
        "potassium_k_mg": 138.0,
        "vitamin_c_total_ascorbic_acid_mg": 0.0,
    },
    173944: {  # Bananas, raw
        "energy_kcal": 89.0,
        "protein_g": 1.09,
        "total_lipid_fat_g": 0.33,
        "fiber_total_dietary_g": 2.6,
        "calcium_ca_mg": 5.0,
        "potassium_k_mg": 358.0,
        "vitamin_c_total_ascorbic_acid_mg": 8.7,
    },
}
FDC_DESCRIPTIONS = {
    170026: "Potatoes, flesh and skin, raw",
    171287: "Egg, whole, raw, fresh",
    173944: "Bananas, raw",
}


@pytest.fixture(scope="module")
def real_tables() -> tuple[pl.DataFrame, pl.DataFrame]:
    problems = verify_dir(build_sr_wide.RAW_DIR, read_manifest(MANIFEST_PATH))
    if problems:
        message = f"brak danych USDA w data/raw ({problems[0]}); uruchom make fetch-usda"
        if os.environ.get("REQUIRE_USDA") == "1":
            pytest.fail(f"REQUIRE_USDA=1, ale {message}")
        pytest.skip(message)
    return build(build_sr_wide.RAW_DIR)


def test_real_food_count_matches_sr_legacy_food(
    real_tables: tuple[pl.DataFrame, pl.DataFrame],
) -> None:
    wide, _ = real_tables
    sr_foods = pl.read_csv(build_sr_wide.RAW_DIR / "sr_legacy_food.csv")
    assert wide.height == sr_foods.height == 7793
    assert wide["fdc_id"].n_unique() == wide.height
    assert wide.select(pl.col("description").null_count()).item() == 0


def test_real_values_match_fdc(real_tables: tuple[pl.DataFrame, pl.DataFrame]) -> None:
    wide, _ = real_tables
    for fdc_id, expected in FDC_SAMPLES.items():
        row = wide.filter(pl.col("fdc_id") == fdc_id).row(0, named=True)
        assert row["description"] == FDC_DESCRIPTIONS[fdc_id]
        for column, value in expected.items():
            assert row[column] == pytest.approx(value), f"{fdc_id} {column}"
    # Składnik niezmierzony dla ziemniaka to null, nie zero
    potato = wide.filter(pl.col("fdc_id") == 170026).row(0, named=True)
    assert potato["vitamin_d3_cholecalciferol_ug"] is None


def test_real_dictionary_covers_all_nutrient_columns(
    real_tables: tuple[pl.DataFrame, pl.DataFrame],
) -> None:
    wide, dictionary = real_tables
    assert wide.columns[len(FOOD_COLUMNS) :] == dictionary["column"].to_list()
    assert dictionary.height == 149
    assert set(dictionary["unit"]) == {"G", "MG", "UG", "IU", "KCAL", "kJ"}
