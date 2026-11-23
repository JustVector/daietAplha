"""Testy przeliczeń wariantów po obróbce termicznej (cooking.py) – S-106.

Pięć przypadków referencyjnych liczonych ręcznie (opis w docs/data/cooking_calc.md), testy doboru
wydajności i procesu R6 na sztucznych danych, a na końcu porównanie z wariantami zmierzonymi w USDA
i aktualność plików w repo (REQUIRE_USDA=1: brak danych to błąd, nie pominięcie).
"""

import os
from pathlib import Path

import polars as pl
import pytest

import cooking
from cooking import (
    CookingError,
    Methods,
    Pair,
    RetentionRule,
    Variant,
    YieldChoice,
    YieldEntry,
    cook,
    load_methods,
    load_retention,
    load_yields,
    pair_yield,
    resolve_retention,
    resolve_yield,
)
from fetch_usda import RETENTION_DIR, RETENTION_MANIFEST_PATH, read_manifest, verify_dir

# --- Przypadki referencyjne (wartości na 100 g; wyniki policzone ręcznie) ---


def test_reference_1_vegetable_baked() -> None:
    """Warzywo pieczone: Y = 80%, witamina C R = 75%, wapń R = 100%."""
    base = {"water_g": 88.0, "protein_g": 1.0, "total_lipid_fat_g": 0.2,
            "carbohydrate_by_difference_g": 10.0, "energy_kcal": 45.0,
            "vitamin_c_total_ascorbic_acid_mg": 10.0, "calcium_ca_mg": 30.0}  # fmt: skip
    result = cook(base, {"vitamin_c_total_ascorbic_acid_mg": 75.0, "calcium_ca_mg": 100.0}, 80)
    # woda: 80 − (100 − 88) = 68 g na 100 g surowego → 68 / 0,8 = 85 g na 100 g pieczonego
    assert result["water_g"] == pytest.approx(85.0)
    assert result["protein_g"] == pytest.approx(1.25)
    assert result["energy_kcal"] == pytest.approx(56.25)
    # 10 × 0,75 / 0,8
    assert result["vitamin_c_total_ascorbic_acid_mg"] == pytest.approx(9.375)
    assert result["calcium_ca_mg"] == pytest.approx(37.5)


def test_reference_2_meat_grilled() -> None:
    """Mięso grillowane: Y = 75%, tiamina R = 70%."""
    base = {"water_g": 74.0, "protein_g": 22.0, "total_lipid_fat_g": 3.0, "energy_kcal": 120.0,
            "thiamin_mg": 0.1}  # fmt: skip
    result = cook(base, {"thiamin_mg": 70.0}, 75)
    assert result["water_g"] == pytest.approx((75 - 26) / 0.75)  # 65,33
    assert result["protein_g"] == pytest.approx(22 / 0.75)  # 29,33
    assert result["total_lipid_fat_g"] == pytest.approx(4.0)
    assert result["energy_kcal"] == pytest.approx(160.0)
    assert result["thiamin_mg"] == pytest.approx(0.1 * 0.7 / 0.75)  # 0,0933


def test_reference_3_fish_fried_with_oil() -> None:
    """Ryba smażona: Y = 80%, 2 g oleju wchłonięte na 100 g surowej ryby."""
    base = {"water_g": 80.0, "protein_g": 18.0, "total_lipid_fat_g": 1.0, "energy_kcal": 80.0,
            "fatty_acids_total_saturated_g": 0.2}  # fmt: skip
    oil = {"water_g": 0.0, "protein_g": 0.0, "total_lipid_fat_g": 100.0, "energy_kcal": 884.0,
           "fatty_acids_total_saturated_g": 7.0}  # fmt: skip
    result = cook(base, {}, 80, oil=oil, oil_g=2.0)
    # woda: 80 − 20 (sucha masa ryby) − 2 (sucha masa oleju) = 58 g → 72,5 g
    assert result["water_g"] == pytest.approx(72.5)
    assert result["total_lipid_fat_g"] == pytest.approx(3.75)  # (1 + 2) / 0,8
    assert result["energy_kcal"] == pytest.approx((80 + 17.68) / 0.8)  # 122,1
    assert result["fatty_acids_total_saturated_g"] == pytest.approx((0.2 + 0.14) / 0.8)
    assert result["protein_g"] == pytest.approx(22.5)


def test_reference_4_groats_boiled() -> None:
    """Kasza gotowana: masa rośnie (Y = 300%), tiamina R = 80%."""
    base = {"water_g": 10.0, "protein_g": 12.0, "total_lipid_fat_g": 2.0, "thiamin_mg": 0.4,
            "carbohydrate_by_difference_g": 70.0, "energy_kcal": 340.0}  # fmt: skip
    result = cook(base, {"thiamin_mg": 80.0}, 300)
    assert result["water_g"] == pytest.approx(70.0)  # (300 − 90) / 3
    assert result["protein_g"] == pytest.approx(4.0)
    assert result["energy_kcal"] == pytest.approx(340 / 3)
    assert result["thiamin_mg"] == pytest.approx(0.4 * 0.8 / 3)


def test_reference_5_ready_product_keeps_missing_values() -> None:
    """Produkt gotowy (kiełbasa) smażony bez tłuszczu: Y = 90%; brak wartości zostaje brakiem."""
    base = {
        "water_g": 55.0,
        "protein_g": 12.0,
        "total_lipid_fat_g": 28.0,
        "vitamin_d_d2_d3_ug": None,
    }
    result = cook(base, {}, 90)
    assert result["water_g"] == pytest.approx(50.0)  # (90 − 45) / 0,9
    assert result["total_lipid_fat_g"] == pytest.approx(28 / 0.9)
    assert result["vitamin_d_d2_d3_ug"] is None


def test_cook_rejects_yield_below_dry_matter() -> None:
    with pytest.raises(CookingError, match="ujemna"):
        cook({"water_g": 50.0, "protein_g": 20.0}, {}, 40)


def test_cook_requires_water() -> None:
    with pytest.raises(CookingError, match="wody"):
        cook({"water_g": None, "protein_g": 20.0}, {}, 80)


# --- Pary USDA ---


def test_pair_yield_from_fat_free_dry_matter() -> None:
    # surowy: woda 75, tłuszcz 5 → sucha masa bez tłuszczu 20; po obróbce: woda 65, tłuszcz 10 → 25
    pair = pair_yield(
        {"water_g": 75.0, "total_lipid_fat_g": 5.0}, {"water_g": 65.0, "total_lipid_fat_g": 10.0}
    )
    assert pair is not None
    yield_pct, fat = pair
    assert yield_pct == pytest.approx(80.0)
    assert fat == pytest.approx(10 * 0.8 - 5)  # 3 g wchłoniętego tłuszczu
    assert pair_yield({"water_g": None, "total_lipid_fat_g": 1.0}, {"water_g": 1.0}) is None


# --- Dobór wydajności i procesu R6 ---


def _variant(preparation: str = "pieczony", food_id: int = 7) -> Variant:
    return Variant(1, food_id, "produkt", preparation, "vegetables", "root_vegetables", None)


def _pair(scope_sub: str, preparation: str, yield_pct: float, fat: float = 0.0) -> Pair:
    return Pair(2, "inny", "vegetables", scope_sub, preparation, yield_pct, fat)


def _entry(scope: str, preparation: str, yield_pct: float | None, fat: float | None = None,
           source: str = "bognar_2002") -> YieldEntry:  # fmt: skip
    return YieldEntry.model_validate(
        {
            "scope": scope,
            "preparation": preparation,
            "yield_pct": yield_pct,
            "fat_uptake_g": fat,
            "source": source,
            "reference": "test",
        }  # fmt: skip
    )


def test_resolve_yield_prefers_narrow_scope() -> None:
    yields = {
        ("food:7", "pieczony"): _entry("food:7", "pieczony", 70),
        ("root_vegetables", "pieczony"): _entry("root_vegetables", "pieczony", 80),
    }
    choice = resolve_yield(_variant(), yields, [], min_pairs=3)
    assert isinstance(choice, YieldChoice)
    assert choice.yield_pct == 70


def test_resolve_yield_pairs_before_wider_table_entry() -> None:
    pairs = [_pair("root_vegetables", "pieczony", y) for y in (60, 70, 90)]
    yields = {("vegetables", "pieczony"): _entry("vegetables", "pieczony", 85)}
    choice = resolve_yield(_variant(), yields, pairs, min_pairs=3)
    assert isinstance(choice, YieldChoice)
    assert (choice.yield_pct, choice.source) == (70, "usda_sr_pairs")
    # Za mało par w podkategorii → wpis kategorii
    choice = resolve_yield(_variant(), yields, pairs[:2], min_pairs=3)
    assert isinstance(choice, YieldChoice)
    assert choice.yield_pct == 85


def test_resolve_yield_explicit_no_data_stops_search() -> None:
    yields = {
        ("root_vegetables", "pieczony"): _entry("root_vegetables", "pieczony", None, source="brak"),
        ("vegetables", "pieczony"): _entry("vegetables", "pieczony", 85),
    }
    assert not isinstance(resolve_yield(_variant(), yields, [], min_pairs=3), YieldChoice)
    assert not isinstance(resolve_yield(_variant(), {}, [], min_pairs=3), YieldChoice)


def test_resolve_yield_frying_fat_from_pairs() -> None:
    pairs = [_pair("other_vegetables", "smażony", 90, fat) for fat in (10.0, 12.0, -1.0)]
    yields = {("root_vegetables", "smażony"): _entry("root_vegetables", "smażony", 80)}
    choice = resolve_yield(_variant("smażony"), yields, pairs, min_pairs=3)
    assert isinstance(choice, YieldChoice)
    # Tabela daje wydajność, tłuszcz – mediana par kategorii
    assert (choice.yield_pct, choice.fat_uptake_g) == (80, 10.0)
    # Ujemna mediana (wytapianie tłuszczu) → 0
    lean = [_pair("other_vegetables", "smażony", 90, fat) for fat in (-2.0, -1.0, 1.0)]
    choice = resolve_yield(_variant("smażony"), yields, lean, min_pairs=3)
    assert isinstance(choice, YieldChoice)
    assert choice.fat_uptake_g == 0.0


def test_yield_entry_validation() -> None:
    with pytest.raises(ValueError, match="źródło"):
        _entry("vegetables", "pieczony", None)
    with pytest.raises(ValueError, match="smażony"):
        _entry("vegetables", "pieczony", 80, fat=2.0)


def _methods(rules: list[RetentionRule]) -> Methods:
    return Methods(
        frying_fat_variant_id=1, min_pairs=3, fatty_fish_fat_g=5.0, r6_nutrients={},
        retention=tuple(rules),
    )  # fmt: skip


def test_resolve_retention_most_specific_rule_and_fatty_fish() -> None:
    methods = _methods(
        [
            RetentionRule(category="vegetables", codes={"pieczony": 3771, "duszony": 3776}),
            RetentionRule(subcategory="root_vegetables", codes={"pieczony": 3451}),
            RetentionRule(food_id=9, codes={"duszony": 2401}, fatty={"duszony": 2551}),
        ]
    )
    assert resolve_retention(_variant("pieczony"), None, methods) == 3451
    assert resolve_retention(_variant("duszony"), None, methods) == 3776
    assert resolve_retention(_variant("duszony", food_id=9), 2.0, methods) == 2401
    assert resolve_retention(_variant("duszony", food_id=9), 12.0, methods) == 2551
    assert resolve_retention(_variant("smażony"), None, methods) is None


def test_load_retention_skips_empty_factor(tmp_path: Path) -> None:
    path = tmp_path / "retn06.txt"
    path.write_text(
        "~3451~^~11~^~VEG,ROOTS,ETC,BAKED~^~401~^~Vitamin C~^~75~^~09/1975~\n"
        "~5005~^~14~^~ALC BEV~^~301~^~Calcium, Ca~^^~09/1975~\n",
        encoding="latin-1",
    )
    processes = load_retention(path)
    assert processes[3451].factors == {401: 75.0}
    assert processes[3451].description == "VEG,ROOTS,ETC,BAKED"
    assert processes[5005].factors == {}


def test_project_config_is_valid() -> None:
    methods = load_methods()
    yields = load_yields()
    assert methods.frying_fat_variant_id == 615
    assert ("sea_fish", "smażony") in yields
    assert all(e.reference for e in yields.values())


# --- Prawdziwe dane USDA ---


@pytest.fixture(scope="module")
def generated() -> tuple[cooking.CookingResult, pl.DataFrame]:
    problems = verify_dir(RETENTION_DIR, read_manifest(RETENTION_MANIFEST_PATH))
    if problems:
        message = f"brak tabeli R6 w data/raw ({problems[0]}); uruchom make fetch-usda"
        if os.environ.get("REQUIRE_USDA") == "1":
            pytest.fail(f"REQUIRE_USDA=1, ale {message}")
        pytest.skip(message)
    try:
        return cooking.generate()
    except CookingError as error:
        if os.environ.get("REQUIRE_USDA") == "1":
            raise
        pytest.skip(str(error))


def test_flags_measured_and_calculated(
    generated: tuple[cooking.CookingResult, pl.DataFrame],
) -> None:
    result, table = generated
    flags = dict(table.group_by("flag").len().iter_rows())
    per_variant = len(result.nutrients)
    assert flags["measured"] == result.measured * per_variant
    assert flags["calculated"] == len(result.cooked) * per_variant
    calculated = table.filter(pl.col("flag") == "calculated")
    water = calculated["nutrient"] == "water_g"
    assert calculated.filter(~water)["factor_ref"].str.starts_with("R6:").all()
    assert calculated.filter(water)["factor_ref"].str.starts_with("bilans masy").all()
    assert calculated["factor_ref"].str.contains("; Y ").all()
    assert table.filter(pl.col("flag") == "measured")["factor_ref"].eq("").all()


def test_calculated_close_to_measured(
    generated: tuple[cooking.CookingResult, pl.DataFrame],
) -> None:
    """Sprawdzenie metody na wariancie zmierzonym w USDA: pierś z kurczaka pieczona wyliczona
    z surowej (wydajność drobiu z tabeli USDA 2012) a rekord USDA pieczonej piersi. Wydajność grupy
    (73%) różni się od wydajności samej piersi (ok. 66%), stąd tolerancja 15%."""
    result, table = generated
    variants = {(v.name_pl, v.preparation): v for v in result.variants}
    raw, roasted = (
        variants[("pierś z kurczaka", "surowy")],
        variants[("pierś z kurczaka", "pieczony")],
    )
    values = {
        row["variant_id"]: row
        for row in table.filter(pl.col("nutrient") == "protein_g").iter_rows(named=True)
    }
    yields = load_yields()
    computed = values[raw.variant_id]["value"] * 100 / yields[("poultry", "pieczony")].yield_pct
    measured = values[roasted.variant_id]["value"]
    assert computed == pytest.approx(measured, rel=0.15)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def test_committed_outputs_are_up_to_date(
    generated: tuple[cooking.CookingResult, pl.DataFrame], tmp_path: Path
) -> None:
    result, _ = generated
    cooking.write_cooked(tmp_path / "cooked_variants.csv", result)
    hint = "pliki wariantów po obróbce nieaktualne – uruchom make cooked-variants"
    assert _read(cooking.COOKED_FILE) == _read(tmp_path / "cooked_variants.csv"), hint
    assert _read(cooking.COVERAGE_REPORT) == result.report, hint
