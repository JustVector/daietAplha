"""Testy miar domowych (build_portions.py) – S-109.

Testy jednostkowe działają na sztucznych porcjach; ostatnie testy liczą przykładowe przeliczenia na
prawdziwych porcjach USDA i sprawdzają, czy wygenerowane pliki w repo są aktualne
(REQUIRE_USDA=1: brak danych to błąd, nie pominięcie).
"""

import os
from pathlib import Path

import pytest

import build_portions
from build_portions import (
    Measures,
    ParsedPortion,
    PortionRow,
    PortionsError,
    SkippedPortion,
    UsdaPortion,
    load_measures,
    load_usda_portions,
    modifier_words,
    parse_modifier,
    render_report,
    variant_portions,
)
from build_sr_wide import RAW_DIR
from fetch_usda import MANIFEST_PATH, read_manifest, verify_dir
from map_products import MappingRow


@pytest.fixture(scope="module")
def measures() -> Measures:
    return load_measures()


def _variant(variant_id: int = 1, fdc_id: int | None = 100) -> MappingRow:
    return MappingRow(
        variant_id=variant_id,
        food_id=1,
        name_pl="produkt",
        preparation="surowy",
        fdc_id=fdc_id,
        status="auto",
        usda_description="Product, raw",
        score=100.0,
    )


def _portion(modifier: str, gram_weight: float, amount: float = 1.0) -> UsdaPortion:
    return UsdaPortion(fdc_id=100, amount=amount, modifier=modifier, gram_weight=gram_weight)


def _by_measure(rows: list[PortionRow]) -> dict[tuple[str, str, str], PortionRow]:
    return {(r.measure, r.size, r.form): r for r in rows}


# --- Słownik miar ---


def test_project_measures(measures: Measures) -> None:
    assert measures.glass_ml == 250
    assert measures.volume["tbsp"].measure == "łyżka"
    assert measures.volume["cup"].measure is None
    assert measures.count["slice"] == "plaster"
    assert "oz" in measures.ignored


def test_measures_overlapping_heads(tmp_path: Path) -> None:
    path = tmp_path / "measures.yaml"
    path.write_text(
        "glass_ml: 250\nvolume: {cup: {ml: 236.6}}\ncount: {cup: sztuka}\n"
        "sizes: {}\nforms: {}\nnoise: []\nignored: []\n",
        encoding="utf-8",
    )
    with pytest.raises(PortionsError, match="kilku listach"):
        load_measures(path)


def test_measures_bad_phrase(tmp_path: Path) -> None:
    path = tmp_path / "measures.yaml"
    path.write_text(
        "glass_ml: 250\nvolume: {}\ncount: {Slice: plaster}\n"
        "sizes: {}\nforms: {}\nnoise: []\nignored: []\n",
        encoding="utf-8",
    )
    with pytest.raises(PortionsError, match="małych liter"):
        load_measures(path)


# --- Rozbiór opisu porcji ---


def test_modifier_words_drop_parentheses_with_numbers() -> None:
    assert modifier_words('cup, chopped (1/2" pieces)') == ["cup", "chopped"]
    assert modifier_words("cup (not packed)") == ["cup", "not", "packed"]
    assert modifier_words('Potato large (3" to 4-1/4" dia)') == ["potato", "large"]


@pytest.mark.parametrize(
    ("modifier", "expected"),
    [
        ("tbsp", ParsedPortion("volume", "tbsp", "łyżka")),
        ("cup, chopped", ParsedPortion("volume", "cup", None, form="posiekane")),
        ("cup elbows not packed", ParsedPortion("volume", "cup", None, form="kolanka, luźno")),
        ("fl oz", ParsedPortion("volume", "fl oz", None)),
        ('large (3-1/4" dia)', ParsedPortion("count", "large", "sztuka", size="duży")),
        ("head, small (4\" dia)", ParsedPortion("count", "head", "główka", size="mały")),
        ("breast, bone and skin removed", ParsedPortion("count", "breast", "pierś",
                                                        form="bez kości i skóry")),
        ("cup, large curd (not packed)", ParsedPortion("volume", "cup", None,
                                                       form="duże ziarna, luźno")),
        ("chop, excluding refuse (yield from 1 raw chop, with refuse, weighing 113 g)",
         ParsedPortion("count", "chop", "kotlet")),
    ],
)  # fmt: skip
def test_parse_modifier(measures: Measures, modifier: str, expected: ParsedPortion) -> None:
    assert parse_modifier(modifier, measures) == expected


@pytest.mark.parametrize(
    ("modifier", "expected"),
    [
        ("oz", SkippedPortion("miara pominięta", "oz")),
        ("NLEA serving", SkippedPortion("miara pominięta", "nlea serving")),
        ("cup, dry, yields", SkippedPortion("wydajność", "cup dry yields")),
        ("cup, cooked", SkippedPortion("nieznane słowa", "cooked")),
        ("gizmo", SkippedPortion("nieznana miara", "gizmo")),
    ],
)
def test_parse_modifier_skipped(
    measures: Measures, modifier: str, expected: SkippedPortion
) -> None:
    assert parse_modifier(modifier, measures) == expected


# --- Miary wariantu ---


def test_measured_per_unit(measures: Measures) -> None:
    rows, _ = variant_portions(
        _variant(), [_portion("tbsp", 13.5), _portion("raspberries", 19, amount=10)], measures
    )
    by = _by_measure(rows)
    assert by[("łyżka", "", "")].grams == 13.5
    assert by[("łyżka", "", "")].flag == "measured"
    # 10 malin = 19 g → 1,9 g na sztukę
    assert by[("sztuka", "", "")].grams == pytest.approx(1.9)


def test_density_glass_and_ml(measures: Measures) -> None:
    rows, _ = variant_portions(
        _variant(), [_portion("tbsp", 15), _portion("cup", 244), _portion("fl oz", 30.5)], measures
    )
    by = _by_measure(rows)
    # Gęstość z porcji o największej objętości – cup (236,59 ml), nie tbsp ani fl oz
    assert by[("ml", "", "")].grams == pytest.approx(244 / 236.5882)
    assert by[("szklanka", "", "")].grams == pytest.approx(244 / 236.5882 * 250)
    assert by[("szklanka", "", "")].flag == "calculated"
    assert "1 cup (236.588 ml) = 244 g" in by[("szklanka", "", "")].calculation
    assert [r.measure for r in rows] == ["ml", "łyżka", "szklanka"]


def test_density_per_form(measures: Measures) -> None:
    rows, _ = variant_portions(
        _variant(), [_portion("cup, chopped", 120), _portion("tbsp chopped", 8)], measures
    )
    by = _by_measure(rows)
    # Bez porcji bez postaci nie ma miary `ml`; szklanka i łyżka z postacią „posiekane”
    assert ("ml", "", "") not in by
    assert by[("szklanka", "", "posiekane")].grams == pytest.approx(120 / 236.5882 * 250)
    assert by[("łyżka", "", "posiekane")].grams == 8


def test_duplicates_and_skipped(measures: Measures) -> None:
    skipped: dict[tuple[int, str], SkippedPortion] = {}
    rows, duplicates = variant_portions(
        _variant(),
        [_portion("medium", 180), _portion('medium (3" dia)', 182), _portion("oz", 28.35)],
        measures,
        skipped,
    )
    assert [(r.measure, r.size, r.grams) for r in rows] == [("sztuka", "średni", 180)]
    assert duplicates == 1
    assert skipped == {(100, "oz"): SkippedPortion("miara pominięta", "oz")}


def test_build_and_report(measures: Measures) -> None:
    mapping = [_variant(1, 100), _variant(2, None), _variant(3, 200)]
    result = build_portions.build_portions(
        mapping, {100: [_portion("cup", 240), _portion("oz", 28.35)]}, measures
    )
    assert {r.variant_id for r in result.rows} == {1}
    report = render_report(result)
    assert "| z `fdc_id` | 2 |" in report
    assert "| ze szklanką i `ml` (gęstość) | 1 |" in report
    assert "## Warianty z `fdc_id` bez miar (1)" in report
    assert "| 3 | produkt | surowy | 200 |" in report
    assert "| miara pominięta | oz | 1 |" in report
    assert not any(line != line.rstrip() for line in report.splitlines())


# --- Prawdziwe dane USDA ---


@pytest.fixture(scope="module")
def usda_portions() -> dict[int, list[UsdaPortion]]:
    problems = verify_dir(RAW_DIR, read_manifest(MANIFEST_PATH))
    if problems:
        message = f"brak danych USDA w data/raw ({problems[0]}); uruchom make fetch-usda"
        if os.environ.get("REQUIRE_USDA") == "1":
            pytest.fail(f"REQUIRE_USDA=1, ale {message}")
        pytest.skip(message)
    return load_usda_portions()


@pytest.mark.parametrize(
    ("fdc_id", "key", "grams"),
    [
        # Oil, olive, salad or cooking: 1 tablespoon = 13,5 g
        (171413, ("łyżka", "", ""), 13.5),
        # Milk, fluid, nonfat: 1 cup = 247 g → szklanka 250 ml = 261 g
        (169868, ("szklanka", "", ""), 247 / 236.5882 * 250),
        # Apples, raw, without skin: 1 medium (3" dia) = 161 g
        (171689, ("sztuka", "średni", ""), 161),
    ],
)
def test_reference_conversions(
    usda_portions: dict[int, list[UsdaPortion]],
    measures: Measures,
    fdc_id: int,
    key: tuple[str, str, str],
    grams: float,
) -> None:
    rows, _ = variant_portions(_variant(fdc_id=fdc_id), usda_portions[fdc_id], measures)
    assert _by_measure(rows)[key].grams == pytest.approx(grams)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def test_committed_outputs_are_up_to_date(
    usda_portions: dict[int, list[UsdaPortion]], tmp_path: Path
) -> None:
    result = build_portions.generate()
    build_portions.write_portions(tmp_path / "portions.csv", result.rows)
    hint = "pliki miar nieaktualne – uruchom make portions"
    assert _read(build_portions.PORTIONS_FILE) == _read(tmp_path / "portions.csv"), hint
    assert _read(build_portions.COVERAGE_REPORT) == result.report, hint
