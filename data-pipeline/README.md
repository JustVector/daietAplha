# data-pipeline

Przygotowanie bazy żywności v1: pobranie surowych danych, przetworzenie, walidacja i eksport.

Etapy (backlog E1):
- pobranie USDA FoodData Central SR Legacy do `data/raw/` (S-006),
- import do tabeli szerokiej (S-102, opis niżej) i wybór składników odżywczych (S-103),
- lista produktów podstawowych (S-101, opis niżej),
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

## Tabela szeroka SR Legacy (S-102)

```
make sr-wide
```

Skrypt [`build_sr_wide.py`](build_sr_wide.py) sprawdza sumy SHA-256 danych w `data/raw/usda_sr_legacy/`, łączy
`sr_legacy_food` + `food` + `food_category` z `food_nutrient` + `nutrient` i zapisuje do `data/interim/`
(poza git, odtwarzane tą komendą):

| Plik | Zawartość |
| --- | --- |
| `sr_wide.parquet` | 1 wiersz = produkt SR Legacy (7793). Kolumny: `fdc_id`, `ndb_number`, `description`, `food_category_id`, `food_category`, potem po jednej kolumnie na składnik odżywczy (149) |
| `sr_wide_nutrients.csv` | słownik kolumn składników: `column`, `nutrient_id`, `nutrient_nbr`, `name`, `unit`, `rank`, `food_count` (liczba produktów z wartością) |

- Nazwa kolumny składnika: nazwa USDA w `snake_case` + jednostka, np. `protein_g`, `energy_kcal`,
  `potassium_k_mg`, `vitamin_d_d2_d3_international_units_iu`. Jednostki: `g`, `mg`, `ug` (µg), `iu`, `kcal`, `kj`.
  Skrypt przerywa pracę, gdy dwie nazwy dałyby tę samą kolumnę albo pojawi się nieznana jednostka.
- Kolejność kolumn składników: `rank` z USDA (kolejność prezentacji w FDC).
- Wartości na 100 g części jadalnej, wprost z `food_nutrient.amount`. Brak wartości w źródle = `null`, nigdy 0.
- Informacja o pochodzeniu wartości (`derivation_id`) zostaje w danych surowych; flagi `measured` / `calculated`
  dochodzą przy eksporcie bazy (S-111). Wybór składników do bazy v1: S-103 (niżej).

## Składniki odżywcze bazy v1 (S-103)

```
make nutrient-coverage
```

| Plik | Zawartość |
| --- | --- |
| [`nutrients.yaml`](nutrients.yaml) | składniki bazy v1 (38): `usda_nutrient_id`, `usda_column` (kolumna tabeli szerokiej), `name_pl`, `unit` (`g`, `mg`, `ug`, `kcal`), `order` |
| [`nutrients.py`](nutrients.py) | wczytanie i walidacja `nutrients.yaml` (Pydantic) oraz sprawdzenie zgodności ze słownikiem tabeli szerokiej |
| [`nutrient_coverage.py`](nutrient_coverage.py) | raport pokrycia [`docs/data/nutrient_coverage.md`](../docs/data/nutrient_coverage.md) (w git) |

- Jednostki jak w USDA, bez przeliczeń. Pominięte warianty w IU (witaminy A i D) oraz energia w kJ.
- Skrypt buduje tabelę szeroką w pamięci z `data/raw/` (wymaga `make fetch-usda`, nie wymaga `make sr-wide`)
  i przerywa pracę, gdy `nutrients.yaml` nie zgadza się z danymi USDA (id, kolumna, jednostka).
- Po zmianie `nutrients.yaml` wygeneruj raport ponownie – test na prawdziwych danych sprawdza, czy raport w repo
  jest aktualny.

## Lista produktów podstawowych (S-101)

```
make product-list
```

Plik [`input/product_list.csv`](input/product_list.csv) (UTF-8, w git) – produkty podstawowe, które trafią do bazy v1.
1 wiersz = produkt podstawowy; warianty produktu (produkt + wariant obróbki) powstają z kolumny `preparations`.

| Kolumna | Zawartość |
| --- | --- |
| `product_id` | stały identyfikator (`snake_case`, ASCII), klucz dla mapowania do `fdc_id` (S-104) |
| `name_pl` | nazwa polska, unikalna |
| `category` | grupa: warzywa, owoce, zboża i kasze, nabiał, mięso, ryby i owoce morza, jaja, rośliny strączkowe, orzechy i nasiona, tłuszcze, inne. Podkategorie: S-105 |
| `preparations` | warianty obróbki rozdzielone `\|`: `surowy`, `gotowy`, `gotowany`, `gotowany na parze`, `pieczony`, `smażony`, `duszony`, `grillowany` |
| `polish_specific` | `true` – produkt typowy dla polskiej kuchni lub rynku, którego może brakować w USDA SR Legacy (kandydat do uzupełnienia z Ciqual/Fineli w S-104) |
| `notes` | uwagi, np. czym różni się najbliższy odpowiednik w USDA |

- `surowy` przy kaszach, ryżu, makaronie, mąkach i strączkach oznacza produkt suchy, przed ugotowaniem.
- `gotowy` – produkt jedzony bez obróbki w domu (chleb, ser, jogurt, wędlina, olej, konserwa).
- Formy przetworzone (kiszony, wędzony, suszony, konserwowy, mrożony) to osobne produkty, nie warianty obróbki –
  mają inny skład i w USDA osobne rekordy.
- Flagę `polish_specific` ustalono przez przeszukanie opisów SR Legacy; to wskazówka dla S-104, nie wynik mapowania.

[`product_list.py`](product_list.py) waliduje plik (Pydantic): kolumny, dozwolone kategorie i warianty, unikalność
`product_id` i `name_pl`, liczbę produktów 300–500 i obecność wszystkich grup poza „inne”. Test
`tests/test_product_list.py` sprawdza prawdziwy plik w CI.
