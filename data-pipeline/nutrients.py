"""Konfiguracja składników odżywczych bazy v1 (S-103): wczytanie i walidacja `nutrients.yaml`.

Plik wskazuje składniki z USDA SR Legacy (id i kolumna tabeli szerokiej z S-102) wraz
z polską nazwą, jednostką i kolejnością prezentacji. Walidacja ma dwa poziomy:
- sam plik (`load_nutrients`): typy pól, dozwolone jednostki, unikalność, kolejność 1..N,
- zgodność ze słownikiem tabeli szerokiej (`check_against_dictionary`): id, kolumna
  i jednostka USDA.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import polars as pl
import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from build_sr_wide import UNIT_SUFFIXES

NUTRIENTS_FILE = Path(__file__).resolve().parent / "nutrients.yaml"

# Jednostki bazy v1 – tylko te, w których USDA podaje wybrane składniki (bez IU i kJ)
Unit = Literal["g", "mg", "ug", "kcal"]


class NutrientConfigError(Exception):
    """Plik `nutrients.yaml` jest niepoprawny albo niezgodny z danymi USDA."""


class Nutrient(BaseModel):
    """Składnik odżywczy bazy v1."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    usda_nutrient_id: int = Field(gt=0)
    usda_column: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    name_pl: str = Field(min_length=1)
    unit: Unit
    order: int = Field(ge=1)


class NutrientList(BaseModel):
    """Zawartość `nutrients.yaml`: lista składników w kolejności prezentacji."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    nutrients: list[Nutrient] = Field(min_length=1)

    @model_validator(mode="after")
    def _check_unique_and_ordered(self) -> NutrientList:
        for field in ("usda_nutrient_id", "usda_column", "name_pl"):
            values = [getattr(n, field) for n in self.nutrients]
            duplicates = sorted({str(v) for v in values if values.count(v) > 1})
            if duplicates:
                raise ValueError(f"powtórzone {field}: {', '.join(duplicates)}")
        orders = [n.order for n in self.nutrients]
        if orders != list(range(1, len(orders) + 1)):
            raise ValueError("pola order muszą mieć wartości 1..N w kolejności wpisów")
        for nutrient in self.nutrients:
            if not nutrient.usda_column.endswith(f"_{nutrient.unit}"):
                raise ValueError(
                    f"kolumna {nutrient.usda_column} nie kończy się jednostką {nutrient.unit}"
                )
        return self


def load_nutrients(path: Path = NUTRIENTS_FILE) -> list[Nutrient]:
    """Wczytuje i waliduje listę składników z pliku YAML."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return NutrientList.model_validate(data).nutrients
    except (OSError, yaml.YAMLError) as error:
        raise NutrientConfigError(f"nie można wczytać {path.name}: {error}") from error
    except ValidationError as error:
        raise NutrientConfigError(f"niepoprawny {path.name}:\n{error}") from error


def check_against_dictionary(nutrients: list[Nutrient], dictionary: pl.DataFrame) -> list[str]:
    """Problemy zgodności ze słownikiem tabeli szerokiej (`sr_wide_nutrients.csv`, S-102).

    Każdy składnik musi istnieć w słowniku pod tym samym id, z tą samą kolumną i jednostką.
    Pusta lista = konfiguracja zgodna.
    """
    rows = {row["nutrient_id"]: row for row in dictionary.iter_rows(named=True)}
    problems = []
    for nutrient in nutrients:
        row = rows.get(nutrient.usda_nutrient_id)
        if row is None:
            problems.append(
                f"{nutrient.name_pl}: brak id {nutrient.usda_nutrient_id} w danych USDA"
            )
            continue
        if row["column"] != nutrient.usda_column:
            problems.append(
                f"{nutrient.name_pl}: id {nutrient.usda_nutrient_id} to kolumna {row['column']}, "
                f"nie {nutrient.usda_column}"
            )
        usda_unit = UNIT_SUFFIXES.get(str(row["unit"]).upper())
        if usda_unit != nutrient.unit:
            problems.append(
                f"{nutrient.name_pl}: jednostka USDA {row['unit']}, w konfiguracji {nutrient.unit}"
            )
    return problems
