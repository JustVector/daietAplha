"""Testy konfiguracji składników (nutrients.py) i raportu pokrycia (nutrient_coverage.py) – S-103.

Testy jednostkowe działają na małych danych tworzonych w teście. Testy na prawdziwych danych
wymagają data/raw/usda_sr_legacy/ (`make fetch-usda`); bez danych są pomijane, a w CI
(REQUIRE_USDA=1) brak danych to błąd, nie pominięcie.
"""

import os
from pathlib import Path
from typing import Any

import polars as pl
import pytest

import nutrient_coverage
from build_sr_wide import RAW_DIR
from fetch_usda import MANIFEST_PATH, read_manifest, verify_dir
from nutrient_coverage import category_coverage, percent, render_report, unit_label
from nutrients import (
    NUTRIENTS_FILE,
    Nutrient,
    NutrientConfigError,
    check_against_dictionary,
    load_nutrients,
)

PROTEIN: dict[str, Any] = {
    "usda_nutrient_id": 1003,
    "usda_column": "protein_g",
    "name_pl": "Białko",
    "unit": "g",
    "order": 1,
}
POTASSIUM: dict[str, Any] = {
    "usda_nutrient_id": 1092,
    "usda_column": "potassium_k_mg",
    "name_pl": "Potas",
    "unit": "mg",
    "order": 2,
}


def _write_yaml(path: Path, entries: list[dict[str, Any]]) -> Path:
    lines = ["nutrients:"]
    for entry in entries:
        lines.append(f"  - usda_nutrient_id: {entry['usda_nutrient_id']}")
        lines += [
            f"    {key}: {value}" for key, value in entry.items() if key != "usda_nutrient_id"
        ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _dictionary() -> pl.DataFrame:
    """Słownik tabeli szerokiej w formacie sr_wide_nutrients.csv (S-102)."""
    return pl.DataFrame(
        {
            "column": ["energy_kj", "protein_g", "potassium_k_mg"],
            "nutrient_id": [1062, 1003, 1092],
            "nutrient_nbr": ["268", "203", "306"],
            "name": ["Energy", "Protein", "Potassium, K"],
            "unit": ["kJ", "G", "MG"],
            "rank": [400.0, 600.0, 5700.0],
            "food_count": [1, 4, 2],
        }
    )


def _wide() -> pl.DataFrame:
    """4 produkty w 2 kategoriach; potas tylko w warzywach."""
    return pl.DataFrame(
        {
            "fdc_id": [1, 2, 3, 4],
            "description": ["Potatoes, raw", "Carrots, raw", "Egg, raw", "Milk"],
            "food_category": ["Vegetables", "Vegetables", "Dairy", "Dairy"],
            "energy_kj": [322.0, None, None, None],
            "protein_g": [2.05, 0.93, 12.56, 3.3],
            "potassium_k_mg": [425.0, 0.0, None, None],
        }
    )


# --- Plik konfiguracji ---


def test_load_valid_config(tmp_path: Path) -> None:
    nutrients = load_nutrients(_write_yaml(tmp_path / "n.yaml", [PROTEIN, POTASSIUM]))
    assert [n.name_pl for n in nutrients] == ["Białko", "Potas"]
    assert nutrients[1] == Nutrient(**POTASSIUM)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"unit": "iu"}, "unit"),
        ({"usda_nutrient_id": 1003}, "powtórzone usda_nutrient_id: 1003"),
        ({"name_pl": "Białko"}, "powtórzone name_pl: Białko"),
        ({"order": 3}, "order muszą mieć wartości 1..N"),
        ({"usda_column": "potassium_k_g"}, "nie kończy się jednostką mg"),
        ({"usda_column": "Potassium"}, "usda_column"),
        ({"extra": "x"}, "extra"),
    ],
)
def test_invalid_config_is_rejected(tmp_path: Path, change: dict[str, Any], message: str) -> None:
    path = _write_yaml(tmp_path / "n.yaml", [PROTEIN, {**POTASSIUM, **change}])
    with pytest.raises(NutrientConfigError, match=message):
        load_nutrients(path)


def test_empty_or_missing_config_is_rejected(tmp_path: Path) -> None:
    empty = tmp_path / "empty.yaml"
    empty.write_text("nutrients: []\n", encoding="utf-8")
    with pytest.raises(NutrientConfigError):
        load_nutrients(empty)
    with pytest.raises(NutrientConfigError, match="nie można wczytać"):
        load_nutrients(tmp_path / "brak.yaml")


def test_check_against_dictionary() -> None:
    nutrients = [Nutrient(**PROTEIN), Nutrient(**POTASSIUM)]
    assert check_against_dictionary(nutrients, _dictionary()) == []

    wrong = [
        Nutrient(**{**PROTEIN, "usda_nutrient_id": 9999}),
        Nutrient(**{**POTASSIUM, "usda_column": "potassium_mg"}),
    ]
    problems = check_against_dictionary(wrong, _dictionary())
    assert problems == [
        "Białko: brak id 9999 w danych USDA",
        "Potas: id 1092 to kolumna potassium_k_mg, nie potassium_mg",
    ]

    other_unit = [Nutrient(**{**POTASSIUM, "usda_column": "potassium_k_g", "unit": "g"})]
    problems = check_against_dictionary(other_unit, _dictionary())
    assert "Potas: jednostka USDA MG, w konfiguracji g" in problems


# --- Raport pokrycia ---


def test_formatting_helpers() -> None:
    assert percent(0.5) == "50,0%"
    assert percent(1 / 3) == "33,3%"
    assert [unit_label(u) for u in ("ug", "UG", "MG", "kJ", "IU", "KCAL")] == [
        "µg",
        "µg",
        "mg",
        "kJ",
        "IU",
        "kcal",
    ]


def test_category_coverage_counts_zero_as_value() -> None:
    nutrients = [Nutrient(**PROTEIN), Nutrient(**POTASSIUM)]
    rows = {
        r["food_category"]: r for r in category_coverage(_wide(), nutrients).iter_rows(named=True)
    }
    assert rows["Vegetables"] == {
        "food_category": "Vegetables",
        "food_count": 2,
        "protein_g": 1.0,
        "potassium_k_mg": 1.0,  # 0.0 ze źródła to wartość
    }
    assert rows["Dairy"]["potassium_k_mg"] == 0.0


def test_render_report() -> None:
    nutrients = [Nutrient(**PROTEIN), Nutrient(**POTASSIUM)]
    report = render_report(_wide(), _dictionary(), nutrients)
    assert report.endswith("|\n")
    assert "## Składniki bazy v1 (2)" in report
    assert "| 1 | Białko | g | `protein_g` | 1003 | 4 | 100,0% |" in report
    assert "| 2 | Potas | mg | `potassium_k_mg` | 1092 | 2 | 50,0% |" in report
    # Kategorie alfabetycznie; w nabiale potas poniżej progu
    assert "| Dairy | 2 | 50,0% | Potas |" in report
    assert "| Vegetables | 2 | 100,0% | – |" in report
    assert report.index("| Dairy |") < report.index("| Vegetables |")
    # Wszystkie składniki: także spoza v1, z pustą kolumną „Baza v1”
    assert "| `energy_kj` | 1062 | Energy | kJ | 1 | 25,0% |  |" in report
    assert "| `protein_g` | 1003 | Protein | g | 4 | 100,0% | Białko |" in report
    assert not any(line != line.rstrip() for line in report.splitlines())


# --- Prawdziwe dane USDA SR Legacy ---


@pytest.fixture(scope="module")
def real_report() -> str:
    problems = verify_dir(RAW_DIR, read_manifest(MANIFEST_PATH))
    if problems:
        message = f"brak danych USDA w data/raw ({problems[0]}); uruchom make fetch-usda"
        if os.environ.get("REQUIRE_USDA") == "1":
            pytest.fail(f"REQUIRE_USDA=1, ale {message}")
        pytest.skip(message)
    # generate() sprawdza też zgodność nutrients.yaml z danymi USDA (id, kolumna, jednostka)
    return nutrient_coverage.generate()


def test_project_config_is_valid() -> None:
    nutrients = load_nutrients(NUTRIENTS_FILE)
    assert len(nutrients) == 38
    assert nutrients[0].usda_column == "energy_kcal"
    assert {n.unit for n in nutrients} == {"g", "mg", "ug", "kcal"}


def test_committed_report_is_up_to_date(real_report: str) -> None:
    committed = nutrient_coverage.REPORT_PATH.read_text(encoding="utf-8").replace("\r\n", "\n")
    assert committed == real_report, "raport nieaktualny – uruchom make nutrient-coverage"
    assert "| 1 | Energia | kcal | `energy_kcal` | 1008 | 7793 | 100,0% |" in real_report
