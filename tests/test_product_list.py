"""Testy listy produktów podstawowych (product_list.py) – S-101.

Testy jednostkowe działają na małych plikach tworzonych w teście; ostatni test sprawdza
prawdziwy plik `data-pipeline/input/product_list.csv` (w git, bez danych USDA).
"""

from pathlib import Path

import pytest

from product_list import (
    COLUMNS,
    PRODUCT_LIST_FILE,
    REQUIRED_CATEGORIES,
    FoodVariant,
    ProductListError,
    check_scope,
    load_variants,
)

HEADER = ",".join(COLUMNS)
POTATO_RAW = "1,1,ziemniak,surowy,warzywa,false,"
POTATO_BOILED = "2,1,ziemniak,gotowany,warzywa,false,"
QUARK = "3,2,twaróg chudy,gotowy,nabiał,true,brak w USDA"


def _write_csv(path: Path, *rows: str, header: str = HEADER) -> Path:
    path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")
    return path


def _variant(variant_id: int, food_id: int, category: str) -> FoodVariant:
    return FoodVariant(
        variant_id=variant_id,
        food_id=food_id,
        name_pl=f"produkt {food_id}",
        preparation="surowy",
        category=category,  # type: ignore[arg-type]
        polish_specific=False,
    )


def test_load_variants_parses_rows(tmp_path: Path) -> None:
    variants = load_variants(_write_csv(tmp_path / "list.csv", POTATO_RAW, POTATO_BOILED, QUARK))

    assert [(v.variant_id, v.food_id) for v in variants] == [(1, 1), (2, 1), (3, 2)]
    assert [v.preparation for v in variants] == ["surowy", "gotowany", "gotowy"]
    assert variants[0].polish_specific is False
    assert variants[0].notes == ""
    assert variants[2].polish_specific is True
    assert variants[2].notes == "brak w USDA"


def test_quoted_name_with_comma(tmp_path: Path) -> None:
    row = '1,1,"mleko 0,5%",gotowy,nabiał,false,'
    variants = load_variants(_write_csv(tmp_path / "list.csv", row))

    assert variants[0].name_pl == "mleko 0,5%"


@pytest.mark.parametrize(
    ("row", "message"),
    [
        ("x,1,ziemniak,surowy,warzywa,false,", "variant_id"),
        ("0,1,ziemniak,surowy,warzywa,false,", "variant_id"),
        ("1,-1,ziemniak,surowy,warzywa,false,", "food_id"),
        ("1,1,ziemniak,surowy,słodycze,false,", "category"),
        ("1,1,ziemniak,wędzony,warzywa,false,", "preparation"),
        ("1,1,ziemniak,surowy,warzywa,tak,", "polish_specific"),
        ("1,1, ziemniak,surowy,warzywa,false,", "name_pl"),
    ],
)
def test_invalid_row(tmp_path: Path, row: str, message: str) -> None:
    with pytest.raises(ProductListError, match=message):
        load_variants(_write_csv(tmp_path / "list.csv", row))


def test_wrong_columns(tmp_path: Path) -> None:
    path = _write_csv(tmp_path / "list.csv", POTATO_RAW, header="id,food,name,prep,cat,pl,notes")

    with pytest.raises(ProductListError, match="kolumny"):
        load_variants(path)


@pytest.mark.parametrize(
    ("second_row", "message"),
    [
        ("1,1,ziemniak,gotowany,warzywa,false,", "powtórzone variant_id"),
        ("2,1,ziemniak,surowy,warzywa,false,", "powtórzony wariant obróbki"),
        ("2,1,ziemniak młody,gotowany,warzywa,false,", "różne name_pl"),
        ("2,1,ziemniak,gotowany,owoce,false,", "różne category"),
        ("2,1,ziemniak,gotowany,warzywa,true,", "różne polish_specific"),
        ("2,2,ziemniak,gotowany,warzywa,false,", "ta sama name_pl"),
    ],
)
def test_list_consistency(tmp_path: Path, second_row: str, message: str) -> None:
    with pytest.raises(ProductListError, match=message):
        load_variants(_write_csv(tmp_path / "list.csv", POTATO_RAW, second_row))


def test_check_scope_counts_foods_not_variants() -> None:
    variants = [_variant(i, 1, "warzywa") for i in range(1, 400)]
    problems = check_scope(variants)

    assert any("liczba produktów 1" in p for p in problems)
    assert any("brak produktów w grupach" in p and "owoce" in p for p in problems)


def test_check_scope_ok() -> None:
    categories = sorted(REQUIRED_CATEGORIES)
    variants = [_variant(i, i, categories[i % len(categories)]) for i in range(1, 301)]

    assert check_scope(variants) == []


def test_real_product_list_is_valid() -> None:
    variants = load_variants(PRODUCT_LIST_FILE)

    assert check_scope(variants) == []
    assert any(v.polish_specific for v in variants)
