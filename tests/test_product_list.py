"""Testy listy produktów podstawowych (product_list.py) – S-101, S-105.

Testy jednostkowe działają na małych plikach tworzonych w teście i słowniku kategorii
z `categories.yaml`; ostatni test sprawdza prawdziwy plik `data-pipeline/input/product_list.csv`
(w git, bez danych USDA).
"""

from pathlib import Path

import pytest
from categories import Categories, Category, Subcategory, load_categories

from product_list import (
    COLUMNS,
    PRODUCT_LIST_FILE,
    FoodVariant,
    ProductListError,
    check_scope,
    load_variants,
    name_key,
)

HEADER = ",".join(COLUMNS)
ROOT = "korzeniowe i bulwiaste"
POTATO_RAW = f"1,1,ziemniak,surowy,warzywa,{ROOT},false,"
POTATO_BOILED = f"2,1,ziemniak,gotowany,warzywa,{ROOT},false,"
QUARK = "3,2,twaróg chudy,gotowy,nabiał,twarogi i serki,true,brak w USDA"

# Mały słownik do testów zakresu listy: dwie wymagane kategorie i jedna opcjonalna
SMALL_CATEGORIES = Categories(
    categories=(
        Category(
            code="vegetables",
            name_pl="warzywa",
            required=True,
            subcategories=(
                Subcategory(code="root_vegetables", name_pl="korzeniowe"),
                Subcategory(code="leafy_vegetables", name_pl="liściaste"),
            ),
        ),
        Category(
            code="fruits",
            name_pl="owoce",
            required=True,
            subcategories=(Subcategory(code="berries", name_pl="jagodowe"),),
        ),
        Category(
            code="other",
            name_pl="inne",
            required=False,
            subcategories=(Subcategory(code="spices", name_pl="przyprawy"),),
        ),
    )
)


def _write_csv(path: Path, *rows: str, header: str = HEADER) -> Path:
    path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")
    return path


def _variant(variant_id: int, food_id: int, category: str, subcategory: str) -> FoodVariant:
    return FoodVariant(
        variant_id=variant_id,
        food_id=food_id,
        name_pl=f"produkt {food_id}",
        preparation="surowy",
        category=category,
        subcategory=subcategory,
        polish_specific=False,
    )


def test_load_variants_parses_rows(tmp_path: Path) -> None:
    variants = load_variants(_write_csv(tmp_path / "list.csv", POTATO_RAW, POTATO_BOILED, QUARK))

    assert [(v.variant_id, v.food_id) for v in variants] == [(1, 1), (2, 1), (3, 2)]
    assert [v.preparation for v in variants] == ["surowy", "gotowany", "gotowy"]
    assert [v.subcategory for v in variants] == [ROOT, ROOT, "twarogi i serki"]
    assert variants[0].polish_specific is False
    assert variants[0].notes == ""
    assert variants[2].polish_specific is True
    assert variants[2].notes == "brak w USDA"


def test_quoted_name_with_comma(tmp_path: Path) -> None:
    row = '1,1,"mleko 0,5%",gotowy,nabiał,mleko i napoje mleczne,false,'
    variants = load_variants(_write_csv(tmp_path / "list.csv", row))

    assert variants[0].name_pl == "mleko 0,5%"


@pytest.mark.parametrize(
    ("row", "message"),
    [
        (f"x,1,ziemniak,surowy,warzywa,{ROOT},false,", "variant_id"),
        (f"0,1,ziemniak,surowy,warzywa,{ROOT},false,", "variant_id"),
        (f"1,-1,ziemniak,surowy,warzywa,{ROOT},false,", "food_id"),
        (f"1,1,ziemniak,surowy,słodycze,{ROOT},false,", "category: nieznana kategoria"),
        ("1,1,ziemniak,surowy,warzywa,,false,", "subcategory"),
        ("1,1,ziemniak,surowy,warzywa,bulwy,false,", "subcategory: 'bulwy' nie jest"),
        ("1,1,ziemniak,surowy,warzywa,jagodowe,false,", "subcategory: 'jagodowe' nie jest"),
        (f"1,1,ziemniak,wędzony,warzywa,{ROOT},false,", "preparation"),
        (f"1,1,ziemniak,surowy,warzywa,{ROOT},tak,", "polish_specific"),
        (f"1,1, ziemniak,surowy,warzywa,{ROOT},false,", "name_pl"),
        (f"1,1,ziemniak,surowy,warzywa,{ROOT} ,false,", "subcategory"),
    ],
)
def test_invalid_row(tmp_path: Path, row: str, message: str) -> None:
    with pytest.raises(ProductListError, match=message):
        load_variants(_write_csv(tmp_path / "list.csv", row))


def test_wrong_columns(tmp_path: Path) -> None:
    header = "variant_id,food_id,name_pl,preparation,category,polish_specific,notes"
    path = _write_csv(tmp_path / "list.csv", "1,1,ziemniak,surowy,warzywa,false,", header=header)

    with pytest.raises(ProductListError, match="kolumny"):
        load_variants(path)


@pytest.mark.parametrize(
    ("second_row", "message"),
    [
        (f"1,1,ziemniak,gotowany,warzywa,{ROOT},false,", "powtórzone variant_id"),
        (f"2,1,ziemniak,surowy,warzywa,{ROOT},false,", "powtórzony wariant obróbki"),
        (f"2,1,ziemniak młody,gotowany,warzywa,{ROOT},false,", "różne name_pl"),
        ("2,1,ziemniak,gotowany,owoce,inne owoce,false,", "różne category"),
        ("2,1,ziemniak,gotowany,warzywa,psiankowate,false,", "różne subcategory"),
        (f"2,1,ziemniak,gotowany,warzywa,{ROOT},true,", "różne polish_specific"),
        (f"2,2,ziemniak,gotowany,warzywa,{ROOT},false,", "ta sama name_pl"),
        (f"2,2,Ziemniak,gotowany,warzywa,{ROOT},false,", "prawie identyczne name_pl"),
    ],
)
def test_list_consistency(tmp_path: Path, second_row: str, message: str) -> None:
    with pytest.raises(ProductListError, match=message):
        load_variants(_write_csv(tmp_path / "list.csv", POTATO_RAW, second_row))


@pytest.mark.parametrize(
    ("first", "second"),
    [
        ("kasza manna", "Kasza Manna"),
        ("kasza manna", "kasza-manna"),
        ("kasza manna", "kasza  manna"),
        ("łosoś", "losos"),
        ("żółtko", "zoltko"),
        ("mleko 0,5%", "mleko 05"),
    ],
)
def test_name_key_matches_spelling_variants(first: str, second: str) -> None:
    assert name_key(first) == name_key(second)


def test_name_key_keeps_different_names_apart() -> None:
    assert name_key("ser gouda") != name_key("ser edamski")
    assert name_key("mleko 2%") != name_key("mleko 3,2%")


def test_check_scope_counts_foods_not_variants() -> None:
    variants = [_variant(i, 1, "warzywa", "korzeniowe") for i in range(1, 400)]
    problems = check_scope(variants, SMALL_CATEGORIES)

    assert any("liczba produktów 1" in p for p in problems)
    assert any("brak produktów w grupach: owoce" in p for p in problems)


def test_check_scope_reports_unused_subcategories() -> None:
    subcategories = [("warzywa", "korzeniowe"), ("owoce", "jagodowe")]
    variants = [_variant(i, i, *subcategories[i % 2]) for i in range(1, 301)]
    problems = check_scope(variants, SMALL_CATEGORIES)

    assert problems == ["podkategorie bez produktów: warzywa / liściaste, inne / przyprawy"]


def test_check_scope_ok() -> None:
    subcategories = [
        ("warzywa", "korzeniowe"),
        ("warzywa", "liściaste"),
        ("owoce", "jagodowe"),
        ("inne", "przyprawy"),
    ]
    variants = [_variant(i, i, *subcategories[i % 4]) for i in range(1, 301)]

    assert check_scope(variants, SMALL_CATEGORIES) == []


def test_real_product_list_is_valid() -> None:
    categories = load_categories()
    variants = load_variants(PRODUCT_LIST_FILE, categories)

    assert check_scope(variants, categories) == []
    assert any(v.polish_specific for v in variants)
