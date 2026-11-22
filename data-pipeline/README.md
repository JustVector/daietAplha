# data-pipeline

Przygotowanie bazy żywności v1: pobranie surowych danych, przetworzenie, walidacja i eksport.

Etapy (backlog E1):
- pobranie USDA FoodData Central SR Legacy do `data/raw/` (S-006),
- import do tabeli szerokiej i wybór składników odżywczych (S-102, S-103),
- mapowanie listy produktów podstawowych, polskie nazwy, warianty obróbki, IG, tagi, miary (S-104 – S-109),
- walidacja i eksport bazy v1 (S-110, S-111).

Zasada: każda wartość odżywcza ma źródło i flagę `measured` / `calculated`.
Wynik eksportu ładuje do bazy backend (S-202).

## Dane źródłowe USDA (S-006)

| | |
| --- | --- |
| Źródło | USDA FoodData Central – SR Legacy, format CSV |
| Wersja | 2018-04 (wydanie końcowe SR Legacy; archiwum na serwerze z 2023-10-25) |
| Adres | https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_csv_2018-04.zip |
| Licencja | CC0 1.0 Universal – domena publiczna; USDA prosi o podanie FoodData Central jako źródła ([api-guide, „Licensing”](https://fdc.nal.usda.gov/api-guide)) |
| Zawartość | 18 plików (17 CSV + opis pól `.xlsx`), ok. 40 MB po rozpakowaniu |
| Miejsce | `data/raw/usda_sr_legacy/` – poza git |

Odtworzenie danych:

```
make fetch-usda
```

Skrypt [`fetch_usda.py`](fetch_usda.py) bierze pliki z lokalnej kopii, jeśli wskazuje ją `USDA_SOURCE_DIR`
(w `.env` albo w środowisku) lub opcja `--source`; w przeciwnym razie pobiera archiwum z USDA. W obu przypadkach
każdy plik jest sprawdzany sumą SHA-256 z manifestu [`checksums/usda_sr_legacy.sha256`](checksums/usda_sr_legacy.sha256)
(format `sha256sum`, w git). Gdy dane w `data/raw/` są już zgodne z manifestem, skrypt nic nie robi.

- `uv run python data-pipeline/fetch_usda.py --verify` – tylko sprawdzenie plików, bez sieci.
- `--update-checksums` – przepisanie manifestu; tylko przy świadomej zmianie wersji danych.

Uwaga: `retention_factor.csv` zawiera tylko listę procesów obróbki, bez wartości współczynników retencji –
pełna tabela USDA R6 jest osobnym źródłem (S-106, [ADR-0001](../docs/adr/0001-food-database.md)).
