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
    Product,
    ProductListError,
    check_scope,
    load_products,
)

HEADER = ",".join(COLUMNS)
POTATO = "potato,ziemniak,warzywa,surowy|gotowany,false,"
QUARK = "quark_lean,twaróg chudy,nabiał,gotowy,true,brak w USDA"


def _write_csv(path: Path, *rows: str, header: str = HEADER) -> Path:
    path.write_text("\n".join([header, *rows]) + "\n", encoding="utf-8")
    return path


def _product(product_id: str, category: str) -> Product:
    return Product(
        product_id=product_id,
        name_pl=product_id,
        category=category,  # type: ignore[arg-type]
        preparations=("surowy",),
        polish_specific=False,
    )


def test_load_products_parses_rows(tmp_path: Path) -> None:
    products = load_products(_write_csv(tmp_path / "list.csv", POTATO, QUARK))

    assert [p.product_id for p in products] == ["potato", "quark_lean"]
    assert products[0].preparations == ("surowy", "gotowany")
    assert products[0].polish_specific is False
    assert products[0].notes == ""
    assert products[1].polish_specific is True
    assert products[1].notes == "brak w USDA"


def test_quoted_name_with_comma(tmp_path: Path) -> None:
    row = 'milk_skimmed,"mleko 0,5%",nabiał,gotowy,false,'
    products = load_products(_write_csv(tmp_path / "list.csv", row))

    assert products[0].name_pl == "mleko 0,5%"


@pytest.mark.parametrize(
    ("row", "message"),
    [
        ("Potato,ziemniak,warzywa,surowy,false,", "product_id"),
        ("potato,ziemniak,słodycze,surowy,false,", "category"),
        ("potato,ziemniak,warzywa,surowy|wędzony,false,", "preparations"),
        ("potato,ziemniak,warzywa,surowy|surowy,false,", "powtórzony wariant"),
        ("potato,ziemniak,warzywa,,false,", "preparations"),
        ("potato,ziemniak,warzywa,surowy,tak,", "polish_specific"),
        ("potato, ziemniak,warzywa,surowy,false,", "name_pl"),
    ],
)
def test_invalid_row(tmp_path: Path, row: str, message: str) -> None:
    with pytest.raises(ProductListError, match=message):
        load_products(_write_csv(tmp_path / "list.csv", row))


def test_wrong_columns(tmp_path: Path) -> None:
    path = _write_csv(tmp_path / "list.csv", POTATO, header="id,name,category,preps,pl,notes")

    with pytest.raises(ProductListError, match="kolumny"):
        load_products(path)


@pytest.mark.parametrize(
    ("second_row", "field"),
    [
        ("potato,ziemniak młody,warzywa,surowy,false,", "product_id"),
        ("new_potato,ziemniak,warzywa,surowy,false,", "name_pl"),
    ],
)
def test_duplicates(tmp_path: Path, second_row: str, field: str) -> None:
    with pytest.raises(ProductListError, match=f"powtórzone {field}"):
        load_products(_write_csv(tmp_path / "list.csv", POTATO, second_row))


def test_check_scope_too_few_and_missing_groups() -> None:
    problems = check_scope([_product("potato", "warzywa")])

    assert any("liczba produktów 1" in p for p in problems)
    assert any("brak produktów w grupach" in p and "owoce" in p for p in problems)


def test_check_scope_ok() -> None:
    categories = sorted(REQUIRED_CATEGORIES)
    products = [_product(f"p{i}", categories[i % len(categories)]) for i in range(300)]

    assert check_scope(products) == []


def test_real_product_list_is_valid() -> None:
    products = load_products(PRODUCT_LIST_FILE)

    assert check_scope(products) == []
    assert any(p.polish_specific for p in products)
