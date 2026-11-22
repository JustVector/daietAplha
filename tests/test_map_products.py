"""Testy mapowania listy produktów do fdc_id USDA (map_products.py) – S-104.

Testy jednostkowe działają na małej sztucznej tabeli USDA; ostatnie testy sprawdzają pliki
projektu i – gdy są dane USDA w data/raw – czy wygenerowane pliki w repo są aktualne
(REQUIRE_USDA=1: brak danych to błąd, nie pominięcie).
"""

import os
from pathlib import Path

import polars as pl
import pytest

import map_products
from build_sr_wide import RAW_DIR
from fetch_usda import MANIFEST_PATH, read_manifest, verify_dir
from map_products import (
    AUTO_THRESHOLD,
    Candidate,
    MappingError,
    MappingRow,
    PreparationRule,
    Scorer,
    build_mapping,
    contains_any,
    load_mapping,
    load_preparations,
    load_search_terms,
    normalized,
    render_report,
    words,
    write_mapping,
)
from product_list import FoodVariant, load_variants

USDA = pl.DataFrame(
    {
        "fdc_id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        "description": [
            "Potatoes, flesh and skin, raw",
            "Potatoes, boiled, cooked without skin, flesh, without salt",
            "Potatoes, boiled, cooked without skin, flesh, with salt",
            "Potatoes, flesh and skin, raw, KROGER",
            "Turkey, whole, neck, meat only, cooked, simmered",
            "Turkey, whole, breast, meat only, cooked, braised",
            "Buckwheat groats, roasted, dry",
            "Buckwheat groats, roasted, cooked",
            "Fish, cod, Atlantic, cooked, dry heat",
            "Fish, cod, Atlantic, raw",
        ],
        "food_category": ["Vegetables"] * 4 + ["Poultry"] * 2 + ["Grains"] * 2 + ["Fish"] * 2,
    }
)
QUERIES = {
    1: "Potatoes, flesh and skin",
    2: "Turkey, breast, meat only",
    3: "Buckwheat groats, roasted",
    4: "Fish, cod, Atlantic",
}
DESCRIPTIONS = dict(zip(USDA["fdc_id"].to_list(), USDA["description"].to_list(), strict=True))


def _variant(variant_id: int, food_id: int, preparation: str, name: str = "") -> FoodVariant:
    return FoodVariant(
        variant_id=variant_id,
        food_id=food_id,
        name_pl=name or f"produkt {food_id}",
        preparation=preparation,  # type: ignore[arg-type]
        category="warzywa",
        subcategory="korzeniowe i bulwiaste",
        polish_specific=False,
    )


@pytest.fixture(scope="module")
def scorer() -> Scorer:
    return Scorer(USDA, QUERIES, load_preparations())


def _top_ids(scorer: Scorer, food_id: int, preparation: str) -> list[int]:
    return [candidate.fdc_id for candidate in scorer.top(food_id, preparation)]


# --- Pomocnicze ---


def test_words_and_phrases() -> None:
    assert words("Chicken, liver, pan-fried") == {"chicken", "liver", "pan", "fried"}
    text = normalized("Fish, cod, cooked, dry heat")
    assert text == " fish cod cooked dry heat "
    assert contains_any(text, frozenset({"dry heat"}))
    assert not contains_any(text, frozenset({"moist heat", "co"}))


# --- Słownik obróbki ---


def test_project_preparations_cover_all_preparations() -> None:
    rules = load_preparations()
    assert set(rules) == {
        "surowy",
        "gotowy",
        "gotowany",
        "gotowany na parze",
        "pieczony",
        "smażony",
        "duszony",
        "grillowany",
    }
    assert "boiled" in rules["gotowany"].include
    assert rules["pieczony"].required
    assert not rules["surowy"].required


def test_preparations_missing_variant(tmp_path: Path) -> None:
    path = tmp_path / "prep.yaml"
    path.write_text("surowy:\n  include: [raw]\n  exclude: []\n", encoding="utf-8")
    with pytest.raises(MappingError, match="oczekiwane"):
        load_preparations(path)


def test_preparation_rule_rejects_bad_words() -> None:
    with pytest.raises(ValueError, match="małych liter"):
        PreparationRule(include=frozenset({"Raw"}), exclude=frozenset())
    rule = PreparationRule(include=frozenset({"dry heat"}), exclude=frozenset({"raw"}))
    assert rule.words() == {"dry", "heat", "raw"}


# --- Zapytania ---


def _terms(tmp_path: Path, *rows: str, header: str = "food_id,name_pl,query_en") -> Path:
    path = tmp_path / "terms.csv"
    path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")
    return path


def test_load_search_terms(tmp_path: Path) -> None:
    variants = [_variant(1, 1, "surowy", "ziemniak"), _variant(2, 1, "gotowany", "ziemniak")]
    path = _terms(tmp_path, '1,ziemniak,"Potatoes, flesh and skin"')
    assert load_search_terms(variants, path) == {1: "Potatoes, flesh and skin"}


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        ((), "brak zapytania dla food_id: \\[1\\]"),
        (("1,ziemniak,Potatoes", "2,x,Carrots"), "spoza listy"),
        (("1,ziemniak,Potatoes", "1,ziemniak,Potato"), "powtórzone food_id"),
        (("1,kartofel,Potatoes",), "name_pl 'kartofel'"),
        (("1,ziemniak,",), "query_en"),
    ],
)
def test_load_search_terms_errors(tmp_path: Path, rows: tuple[str, ...], message: str) -> None:
    variants = [_variant(1, 1, "surowy", "ziemniak")]
    with pytest.raises(MappingError, match=message):
        load_search_terms(variants, _terms(tmp_path, *rows))


def test_load_search_terms_wrong_columns(tmp_path: Path) -> None:
    path = _terms(tmp_path, "1,ziemniak,Potatoes", header="id,name,query")
    with pytest.raises(MappingError, match="kolumny"):
        load_search_terms([_variant(1, 1, "surowy", "ziemniak")], path)


# --- Punktacja ---


def test_raw_variant_prefers_raw_record_without_brand(scorer: Scorer) -> None:
    top = scorer.top(1, "surowy")
    assert top[0].fdc_id == 1
    assert top[0].score == 100.0
    # Rekord markowy (KROGER) niżej niż ten sam opis bez marki
    assert _top_ids(scorer, 1, "surowy").index(4) > 0


def test_boiled_variant_prefers_without_salt(scorer: Scorer) -> None:
    assert _top_ids(scorer, 1, "gotowany")[:2] == [2, 3]


def test_missing_preparation_falls_below_threshold(scorer: Scorer) -> None:
    # W danych nie ma ziemniaka pieczonego – najlepszy kandydat nie może dostać statusu auto
    assert scorer.top(1, "pieczony")[0].score < AUTO_THRESHOLD


def test_query_word_is_not_penalized_as_preparation(scorer: Scorer) -> None:
    # „roasted” jest w zapytaniu (kasza palona), więc nie karze opisu przy wariancie surowym
    best = scorer.top(3, "surowy")[0]
    assert best.fdc_id == 7
    assert best.score >= AUTO_THRESHOLD


def test_missing_query_word_lowers_score(scorer: Scorer) -> None:
    assert scorer.top(2, "duszony")[0].fdc_id == 6
    neck = scorer.score_of(2, "duszony", 5)
    breast = scorer.score_of(2, "duszony", 6)
    assert neck is not None and breast is not None
    assert neck < breast


def test_fish_dry_heat_counts_as_baked_not_boiled(scorer: Scorer) -> None:
    assert scorer.top(4, "pieczony")[0].fdc_id == 9
    assert scorer.top(4, "pieczony")[0].score >= AUTO_THRESHOLD
    assert scorer.top(4, "gotowany")[0].score < AUTO_THRESHOLD


def test_scores_in_range_and_top_n(scorer: Scorer) -> None:
    for food_id in QUERIES:
        scores = scorer.scores(food_id, "gotowany")
        assert scores.min() >= 0.0
        assert scores.max() <= 100.0
        assert len(scorer.top(food_id, "gotowany")) == 5
    assert scorer.score_of(1, "surowy", 999) is None


# --- Mapowanie ---


def _candidates(variants: list[FoodVariant], scorer: Scorer) -> dict[int, list[Candidate]]:
    return {v.variant_id: scorer.top(v.food_id, v.preparation) for v in variants}


def _row(variant_id: int, food_id: int, preparation: str, fdc_id: int | None) -> MappingRow:
    return MappingRow(
        variant_id=variant_id,
        food_id=food_id,
        name_pl=f"produkt {food_id}",
        preparation=preparation,  # type: ignore[arg-type]
        fdc_id=fdc_id,
        status="zweryfikowany",
    )


def test_build_mapping_auto_and_missing(scorer: Scorer) -> None:
    variants = [_variant(1, 1, "surowy"), _variant(2, 1, "pieczony")]
    rows, warnings = build_mapping(
        variants, _candidates(variants, scorer), {}, scorer, DESCRIPTIONS
    )
    assert warnings == []
    assert (rows[0].fdc_id, rows[0].status, rows[0].score) == (1, "auto", 100.0)
    assert rows[0].usda_description == "Potatoes, flesh and skin, raw"
    assert (rows[1].fdc_id, rows[1].status, rows[1].usda_description) == (None, "brak", "")
    assert rows[1].score is not None and rows[1].score < AUTO_THRESHOLD


def test_build_mapping_keeps_verified_rows(scorer: Scorer) -> None:
    variants = [_variant(1, 1, "surowy"), _variant(2, 1, "pieczony"), _variant(3, 1, "gotowany")]
    previous = {
        1: _row(1, 1, "surowy", 4),  # ręcznie wybrany inny rekord niż najlepszy kandydat
        2: _row(2, 1, "pieczony", None),  # potwierdzony brak
        3: MappingRow(**{**_row(3, 1, "gotowany", 7).model_dump(), "status": "auto"}),
    }
    rows, _ = build_mapping(variants, _candidates(variants, scorer), previous, scorer, DESCRIPTIONS)
    assert (rows[0].fdc_id, rows[0].status) == (4, "zweryfikowany")
    assert rows[0].usda_description == "Potatoes, flesh and skin, raw, KROGER"
    assert (rows[1].fdc_id, rows[1].status, rows[1].score) == (None, "zweryfikowany", None)
    # Wiersz `auto` liczony od nowa
    assert (rows[2].fdc_id, rows[2].status) == (2, "auto")


def test_build_mapping_rejects_unknown_fdc_id(scorer: Scorer) -> None:
    variants = [_variant(1, 1, "surowy")]
    with pytest.raises(MappingError, match="fdc_id 999"):
        build_mapping(
            variants,
            _candidates(variants, scorer),
            {1: _row(1, 1, "surowy", 999)},
            scorer,
            DESCRIPTIONS,
        )


def test_build_mapping_resets_changed_variant(scorer: Scorer) -> None:
    variants = [_variant(1, 1, "gotowany")]
    previous = {1: _row(1, 1, "surowy", 1), 7: _row(7, 1, "pieczony", None)}
    rows, warnings = build_mapping(
        variants, _candidates(variants, scorer), previous, scorer, DESCRIPTIONS
    )
    assert (rows[0].fdc_id, rows[0].status) == (2, "auto")
    assert any("variant_id 1" in warning for warning in warnings)
    assert any("[7]" in warning for warning in warnings)


def test_mapping_roundtrip(tmp_path: Path) -> None:
    rows = [
        _row(1, 1, "surowy", 4),
        MappingRow(
            variant_id=2,
            food_id=1,
            name_pl="produkt 1",
            preparation="pieczony",
            fdc_id=None,
            status="brak",
            score=45.0,
        ),
    ]
    path = tmp_path / "mapping.csv"
    write_mapping(path, rows)
    assert list(load_mapping(path).values()) == rows
    assert load_mapping(tmp_path / "missing.csv") == {}


def test_load_mapping_errors(tmp_path: Path) -> None:
    path = tmp_path / "mapping.csv"
    write_mapping(path, [_row(1, 1, "surowy", 4), _row(1, 1, "surowy", 4)])
    with pytest.raises(MappingError, match="powtórzone"):
        load_mapping(path)
    path.write_text("variant_id,fdc_id\n1,4\n", encoding="utf-8")
    with pytest.raises(MappingError, match="kolumny"):
        load_mapping(path)
    write_mapping(path, [_row(1, 1, "surowy", 4)])
    path.write_text(path.read_text(encoding="utf-8").replace("zweryfikowany", "ok"), "utf-8")
    with pytest.raises(MappingError, match="status"):
        load_mapping(path)


def test_render_report_splits_missing_foods_and_variants(scorer: Scorer) -> None:
    variants = [_variant(1, 1, "surowy"), _variant(2, 1, "pieczony"), _variant(3, 2, "surowy")]
    rows = [
        MappingRow(**{**_row(1, 1, "surowy", 1).model_dump(), "status": "auto"}),
        MappingRow(**{**_row(2, 1, "pieczony", None).model_dump(), "status": "brak"}),
        _row(3, 2, "surowy", None),
    ]
    report = render_report(variants, rows, _candidates(variants, scorer))
    assert "| `auto` | 1 |" in report
    assert "| `brak` | 1 |" in report
    assert "| `zweryfikowany` | 1 |" in report
    whole = report.index("## Produkty do uzupełnienia z Ciqual lub Fineli (1 wariantów, 1 produkt")
    partial = report.index("## Brakujące warianty obróbki (1 wariantów, 1 produkt")
    assert whole < report.index("| 3 | produkt 2 | surowy |") < partial
    assert partial < report.index("| 2 | produkt 1 | pieczony |")
    assert not any(line != line.rstrip() for line in report.splitlines())


# --- Pliki projektu ---


def test_project_search_terms_cover_product_list() -> None:
    variants = load_variants()
    queries = load_search_terms(variants)
    assert len(queries) == len({v.food_id for v in variants})


@pytest.fixture(scope="module")
def real_result() -> map_products.MappingResult:
    problems = verify_dir(RAW_DIR, read_manifest(MANIFEST_PATH))
    if problems:
        message = f"brak danych USDA w data/raw ({problems[0]}); uruchom make fetch-usda"
        if os.environ.get("REQUIRE_USDA") == "1":
            pytest.fail(f"REQUIRE_USDA=1, ale {message}")
        pytest.skip(message)
    return map_products.generate()


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


def test_real_mapping_covers_all_variants(real_result: map_products.MappingResult) -> None:
    assert [row.variant_id for row in real_result.rows] == [
        v.variant_id for v in real_result.variants
    ]
    assert all(len(c) == 5 for c in real_result.candidates.values())
    assert real_result.warnings == []
    # „ziemniak, gotowany” (variant_id 2) – w top-5 ziemniak gotowany z USDA
    assert any(c.description.startswith("Potatoes, boiled") for c in real_result.candidates[2])


def test_committed_outputs_are_up_to_date(
    real_result: map_products.MappingResult, tmp_path: Path
) -> None:
    hint = "pliki mapowania nieaktualne – uruchom make map-products"
    map_products.write_candidates(
        tmp_path / "candidates.csv", real_result.variants, real_result.candidates
    )
    map_products.write_mapping(tmp_path / "mapping.csv", real_result.rows)
    assert _read(map_products.CANDIDATES_FILE) == _read(tmp_path / "candidates.csv"), hint
    assert _read(map_products.MAPPING_FILE) == _read(tmp_path / "mapping.csv"), hint
    assert _read(map_products.MISSING_REPORT) == real_result.report, hint
