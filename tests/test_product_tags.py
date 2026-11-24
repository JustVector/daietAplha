"""Testy tagów wykluczeń i diet (product_tags.py) – S-108.

Testy jednostkowe sprawdzają reguły z prawdziwego `tags.yaml` na produktach referencyjnych
i walidację spójności; ostatnie testy sprawdzają plik `product_tags.csv` w repo (bez danych USDA)
i – gdy są dane USDA w data/raw – czy plik jest aktualny (REQUIRE_USDA=1: brak danych to błąd,
nie pominięcie).
"""

import os
from dataclasses import replace
from pathlib import Path

import pytest

import product_tags
from build_sr_wide import RAW_DIR
from categories import load_categories
from fetch_usda import MANIFEST_PATH, read_manifest, verify_dir
from product_list import FoodVariant, load_variants
from product_tags import (
    Food,
    TagRow,
    TagsConfig,
    TagsError,
    UsdaRecord,
    build_rows,
    check_rows,
    consistency_problems,
    foods_from,
    load_product_tags,
    load_tags,
    propose,
    write_product_tags,
)


@pytest.fixture(scope="module")
def config() -> TagsConfig:
    return load_tags()


def _food(
    name: str,
    category: str,
    subcategory: str,
    usda: list[tuple[str, str]] | None = None,
) -> Food:
    """Produkt testowy; kategoria i podkategoria podane polskimi nazwami z categories.yaml."""
    variants = [
        FoodVariant(
            variant_id=1,
            food_id=1,
            name_pl=name,
            preparation="gotowy",
            category=category,
            subcategory=subcategory,
            polish_specific=False,
        )
    ]
    records = [UsdaRecord(c, d) for c, d in usda or []]
    return foods_from(variants, load_categories(), {1: records})[0]


def _true_tags(food: Food, config: TagsConfig) -> set[str]:
    tags, _ = propose(food, config)
    return {code for code, value in tags.items() if value}


REFERENCE = [
    (
        _food(
            "chleb pszenny",
            "zboża i kasze",
            "pieczywo",
            [("Baked Products", "Bread, white, commercially prepared")],
        ),
        {"contains_gluten", "vegan", "vegetarian"},
    ),
    (
        _food(
            "ser gouda",
            "nabiał",
            "sery żółte i twarde",
            [("Dairy and Egg Products", "Cheese, gouda")],
        ),
        {"contains_lactose", "vegetarian"},
    ),
    (
        _food("masło", "tłuszcze", "tłuszcze zwierzęce", []),
        {"contains_lactose", "vegetarian"},
    ),
    (
        _food(
            "łosoś",
            "ryby i owoce morza",
            "ryby morskie",
            [("Finfish and Shellfish Products", "Fish, salmon, Atlantic, farmed, raw")],
        ),
        {"fish"},
    ),
    (
        _food(
            "krewetki",
            "ryby i owoce morza",
            "owoce morza",
            [("Finfish and Shellfish Products", "Crustaceans, shrimp, raw")],
        ),
        {"seafood"},
    ),
    (
        _food(
            "jajo kurze",
            "jaja",
            "jaja i ich części",
            [("Dairy and Egg Products", "Egg, whole, raw, fresh")],
        ),
        {"eggs", "vegetarian"},
    ),
    (
        _food(
            "migdały", "orzechy i nasiona", "orzechy", [("Nut and Seed Products", "Nuts, almonds")]
        ),
        {"nuts", "vegan", "vegetarian"},
    ),
    (
        _food(
            "wiórki kokosowe",
            "orzechy i nasiona",
            "orzechy",
            [("Nut and Seed Products", "Nuts, coconut meat, dried (desiccated)")],
        ),
        {"vegan", "vegetarian"},
    ),
    (
        _food("miód", "inne", "cukry i słodziki", [("Sweets", "Honey")]),
        {"vegetarian"},
    ),
    (
        _food(
            "żelatyna",
            "inne",
            "dodatki do pieczenia",
            [("Sweets", "Gelatins, dry powder, unsweetened")],
        ),
        {"meat"},
    ),
    (
        _food(
            "tofu naturalne",
            "rośliny strączkowe",
            "przetwory strączkowe",
            [("Legumes and Legume Products", "Tofu, firm, prepared with calcium sulfate")],
        ),
        {"vegan", "vegetarian"},
    ),
    (
        _food(
            "sos sojowy",
            "inne",
            "sosy i przyprawy",
            [("Legumes and Legume Products", "Soy sauce made from soy and wheat (shoyu)")],
        ),
        {"contains_gluten", "vegan", "vegetarian"},
    ),
    (
        _food(
            "płatki owsiane",
            "zboża i kasze",
            "płatki i otręby",
            [("Breakfast Cereals", "Cereals, oats, regular and quick, not fortified, dry")],
        ),
        {"contains_gluten", "vegan", "vegetarian"},
    ),
    (
        _food(
            "kasza gryczana palona",
            "zboża i kasze",
            "kasze i ziarna",
            [("Cereal Grains and Pasta", "Buckwheat groats, roasted, dry")],
        ),
        {"vegan", "vegetarian"},
    ),
    (
        _food(
            "drożdże świeże",
            "inne",
            "dodatki do pieczenia",
            [("Baked Products", "Leavening agents, yeast, baker's, compressed")],
        ),
        {"vegan", "vegetarian"},
    ),
    (
        _food(
            "orzeszki ziemne",
            "orzechy i nasiona",
            "orzechy",
            [("Legumes and Legume Products", "Peanuts, all types, raw")],
        ),
        {"nuts", "vegan", "vegetarian"},
    ),
]


@pytest.mark.parametrize(("food", "expected"), REFERENCE, ids=[f.name_pl for f, _ in REFERENCE])
def test_reference_products(food: Food, expected: set[str], config: TagsConfig) -> None:
    assert _true_tags(food, config) == expected


def test_notes_list_sources_and_review_hints(config: TagsConfig) -> None:
    _, notes = propose(_food("napój owsiany", "zboża i kasze", "napoje zbożowe"), config)
    assert "contains_gluten: nazwa" in notes
    assert "bez rekordu USDA" in notes
    assert "owies jak zboże glutenowe" in notes


def test_usda_category_alone_gives_tag(config: TagsConfig) -> None:
    # Produkt spoza kategorii mięso, ale z rekordem USDA mięsnym – tag z USDA
    food = _food("pasztet", "inne", "sosy i przyprawy", [("Sausages and Luncheon Meats", "Pate")])
    tags, notes = propose(food, config)
    assert tags["meat"] and not tags["vegetarian"]
    assert "meat: USDA" in notes


def _row(food_id: int = 1, **tags: bool) -> TagRow:
    codes = load_tags().codes
    return TagRow(
        food_id, "x", "inne", "sosy i przyprawy", {c: tags.get(c, False) for c in codes}, "auto"
    )


def test_consistency_problems(config: TagsConfig) -> None:
    assert consistency_problems(_row(vegan=True, vegetarian=True), config) == []
    assert consistency_problems(_row(vegan=True), config) == ["vegan bez vegetarian"]
    assert consistency_problems(_row(vegetarian=True, meat=True), config) == [
        "vegetarian razem z meat"
    ]
    assert consistency_problems(_row(vegan=True, vegetarian=True, eggs=True), config) == [
        "vegan razem z eggs"
    ]


def test_verified_rows_are_kept(config: TagsConfig) -> None:
    food = _food("miód", "inne", "cukry i słodziki", [("Sweets", "Honey")])
    verified = TagRow(
        1,
        "stara nazwa",
        "inne",
        "cukry i słodziki",
        {c: c in ("vegan", "vegetarian") for c in config.codes},
        "zweryfikowany",
        "sprawdzone",
    )
    [row] = build_rows([food], config, {1: verified})
    assert row.status == "zweryfikowany" and row.tags["vegan"] and row.notes == "sprawdzone"
    assert row.name_pl == "miód"  # nazwa zawsze z listy produktów
    [row] = build_rows([food], config, {1: replace(verified, status="auto")})
    assert row.status == "auto" and not row.tags["vegan"]


def test_csv_round_trip_and_validation(config: TagsConfig, tmp_path: Path) -> None:
    path = tmp_path / "product_tags.csv"
    rows = [_row(1, vegan=True, vegetarian=True), _row(2, meat=True)]
    write_product_tags(path, rows, config)
    assert load_product_tags(path, config) == rows

    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace(",auto,", ",tak,", 1), encoding="utf-8")
    with pytest.raises(TagsError, match="status"):
        load_product_tags(path, config)
    path.write_text(text.replace("true", "TAK", 1), encoding="utf-8")
    with pytest.raises(TagsError, match="true, false"):
        load_product_tags(path, config)


def test_check_rows_against_product_list(config: TagsConfig) -> None:
    variants = load_variants()
    problems = check_rows([_row(1), _row(1), _row(9999)], variants, config)
    text = "\n".join(problems)
    assert "powtórzone food_id: 1" in text
    assert "produkty bez tagów" in text
    assert "food_id spoza listy produktów: 9999" in text
    assert "name_pl 'x' różni się" in text


def test_invalid_config_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "tags.yaml"
    path.write_text(
        "tags:\n  - {code: meat, name_pl: mięso, kind: exclusion, match: {categories: [nope]}}\n",
        encoding="utf-8",
    )
    with pytest.raises(TagsError, match="nieznana kategoria 'nope'"):
        load_tags(path)
    path.write_text(
        "tags:\n  - {code: vegan, name_pl: w, kind: diet, excluded_by_tags: [vegan]}\n",
        encoding="utf-8",
    )
    with pytest.raises(TagsError, match="nie jest tagiem wykluczenia"):
        load_tags(path)


def test_committed_product_tags_are_valid() -> None:
    assert product_tags.check() == []


def test_committed_product_tags_are_up_to_date() -> None:
    problems = verify_dir(RAW_DIR, read_manifest(MANIFEST_PATH))
    if problems:
        message = f"brak danych USDA w data/raw ({problems[0]}); uruchom make fetch-usda"
        if os.environ.get("REQUIRE_USDA") == "1":
            pytest.fail(f"REQUIRE_USDA=1, ale {message}")
        pytest.skip(message)
    config, rows = product_tags.generate()
    committed = load_product_tags(product_tags.PRODUCT_TAGS_FILE, config)
    assert committed == rows, "product_tags.csv nieaktualny – uruchom make product-tags"
