"""Testy słownika kategorii (categories.py) – S-105.

Testy jednostkowe działają na małych plikach YAML tworzonych w teście; ostatni test sprawdza
prawdziwy plik `data-pipeline/categories.yaml`.
"""

from pathlib import Path

import pytest
from categories import CATEGORIES_FILE, CategoriesError, load_categories

VALID = """
categories:
  - code: vegetables
    name_pl: warzywa
    required: true
    subcategories:
      - {code: root_vegetables, name_pl: korzeniowe}
      - {code: leafy_vegetables, name_pl: liściaste}
  - code: other
    name_pl: inne
    required: false
    subcategories:
      - {code: spices, name_pl: przyprawy}
"""


def _write_yaml(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_load_categories(tmp_path: Path) -> None:
    categories = load_categories(_write_yaml(tmp_path / "c.yaml", VALID))

    assert [c.code for c in categories.categories] == ["vegetables", "other"]
    assert categories.required_names() == {"warzywa"}
    assert categories.by_name()["warzywa"].subcategory_names() == {"korzeniowe", "liściaste"}


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("code: leafy_vegetables", "code: spices", "powtórzone kody: spices"),
        ("code: other", "code: vegetables", "powtórzone kody: vegetables"),
        ("name_pl: inne", "name_pl: warzywa", "powtórzone nazwy kategorii"),
        ("name_pl: liściaste", "name_pl: korzeniowe", "powtórzone nazwy podkategorii"),
        ("code: root_vegetables", "code: Root-Vegetables", "code"),
        ("required: false", "required: może", "required"),
        ("name_pl: przyprawy}", "name_pl: przyprawy, color: red}", "color"),
        (
            "    subcategories:\n      - {code: spices, name_pl: przyprawy}\n",
            "    subcategories: []\n",
            "subcategories",
        ),
    ],
)
def test_invalid_categories(tmp_path: Path, old: str, new: str, message: str) -> None:
    assert old in VALID
    path = _write_yaml(tmp_path / "c.yaml", VALID.replace(old, new))

    with pytest.raises(CategoriesError, match=message):
        load_categories(path)


def test_broken_yaml(tmp_path: Path) -> None:
    with pytest.raises(CategoriesError, match="nie można wczytać"):
        load_categories(_write_yaml(tmp_path / "c.yaml", "categories: [\n"))


def test_real_categories_file() -> None:
    categories = load_categories(CATEGORIES_FILE)

    assert "inne" not in categories.required_names()
    assert len(categories.required_names()) == 10
    assert all(category.subcategories for category in categories.categories)
