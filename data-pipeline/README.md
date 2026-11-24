# data-pipeline

Przygotowanie bazy żywności v1: pobranie surowych danych, przetworzenie, walidacja i eksport.

Etapy (backlog E1):
- pobranie USDA FoodData Central SR Legacy do `data/raw/` (S-006),
- import do tabeli szerokiej (S-102, opis niżej) i wybór składników odżywczych (S-103),
- lista produktów podstawowych (S-101) z polskimi nazwami i kategoriami (S-105), opis niżej,
- mapowanie listy produktów podstawowych, warianty obróbki, IG, tagi, miary (S-104, S-106 – S-109;
  tagi wykluczeń i diet opis niżej),
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
pełną tabelę USDA R6 pobiera ta sama komenda (niżej, S-106).

**Tabela retencji USDA R6** (S-106): `make fetch-usda` pobiera też *USDA Table of Nutrient Retention Factors,
Release 6* (2007, domena publiczna) – plik `retn06.txt` z
https://www.ars.usda.gov/ARSUserFiles/80400525/Data/retn/ do `data/raw/usda_retention/` (poza git), sprawdzany
sumą z [`checksums/usda_retention.sha256`](checksums/usda_retention.sha256). Gdy `USDA_SOURCE_DIR` zawiera
`retn06.txt`, plik jest kopiowany zamiast pobierania.

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
1 wiersz = wariant produktu (produkt podstawowy + wariant obróbki), np. „ziemniak, gotowany” – jak w CSV bazy
([ADR-0001](../docs/adr/0001-food-database.md)).

| Kolumna | Zawartość |
| --- | --- |
| `variant_id` | identyfikator wariantu produktu (int > 0, unikalny); na wariant wskazuje przepis od LLM (S-304) |
| `food_id` | identyfikator produktu podstawowego (int > 0); wspólny dla wszystkich wariantów produktu |
| `name_pl` | nazwa polska produktu podstawowego; jedna nazwa = jeden `food_id` |
| `preparation` | wariant obróbki: `surowy`, `gotowy`, `gotowany`, `gotowany na parze`, `pieczony`, `smażony`, `duszony`, `grillowany` |
| `category` | kategoria (grupa): warzywa, owoce, zboża i kasze, nabiał, mięso, ryby i owoce morza, jaja, rośliny strączkowe, orzechy i nasiona, tłuszcze, inne – polska nazwa z [`categories.yaml`](categories.yaml) (S-105, niżej) |
| `subcategory` | podkategoria w obrębie kategorii, np. „korzeniowe i bulwiaste” – polska nazwa z [`categories.yaml`](categories.yaml) |
| `polish_specific` | `true` – produkt typowy dla polskiej kuchni lub rynku, którego może brakować w USDA SR Legacy (kandydat do uzupełnienia z Ciqual/Fineli w S-104) |
| `notes` | uwagi, np. czym różni się najbliższy odpowiednik w USDA |

- Identyfikatory są stałe: nowe warianty i produkty dostają kolejne wolne numery, usuniętych numerów nie używa się
  ponownie.
- `name_pl`, `category`, `subcategory` i `polish_specific` muszą być takie same we wszystkich wierszach jednego
  `food_id`.
- `surowy` przy kaszach, ryżu, makaronie, mąkach i strączkach oznacza produkt suchy, przed ugotowaniem.
- `gotowy` – produkt jedzony bez obróbki w domu (chleb, ser, jogurt, wędlina, olej, konserwa).
- Formy przetworzone (kiszony, wędzony, suszony, konserwowy, mrożony) to osobne produkty, nie warianty obróbki –
  mają inny skład i w USDA osobne rekordy.
- Flagę `polish_specific` ustalono przez przeszukanie opisów SR Legacy; to wskazówka dla S-104, nie wynik mapowania.

[`product_list.py`](product_list.py) waliduje plik (Pydantic): kolumny, dozwolone warianty obróbki, kategorie
i podkategorie ze słownika, unikalność `variant_id` i pary (`food_id`, `preparation`), unikalność nazw (także prawie
identycznych), spójność wierszy jednego produktu, liczbę produktów podstawowych 300–500, obecność wszystkich grup
poza „inne” i użycie każdej podkategorii. Test `tests/test_product_list.py` sprawdza prawdziwy plik w CI.

## Polskie nazwy i kategorie (S-105)

```
make product-list
```

Wypisuje liczbę produktów podstawowych w każdej kategorii i podkategorii albo błędy.

| Plik | Zawartość |
| --- | --- |
| [`categories.yaml`](categories.yaml) | słownik kategorii: kategoria (`code`, `name_pl`, `required`) → lista podkategorii (`code`, `name_pl`); kolejność w pliku = kolejność prezentacji |
| [`categories.py`](categories.py) | wczytanie i walidacja słownika (Pydantic) |

- W `product_list.csv` kategoria i podkategoria są zapisane polską nazwą (`name_pl`), żeby plik dało się czytać
  i poprawiać ręcznie. `code` to stały identyfikator angielski (`snake_case`, unikalny w całym słowniku) dla bazy
  i API; nie zmienia się przy zmianie polskiej nazwy.
- `required: true` – na liście muszą być produkty z tej kategorii (kryterium S-101); `false` ma tylko „inne”.
- Każda podkategoria musi mieć co najmniej jeden produkt; nazwa podkategorii jest unikalna w swojej kategorii.
- **Nazwy produktów**: jedna `name_pl` = jeden `food_id`. Nazwy różniące się tylko wielkością liter, polskimi
  znakami, spacjami albo interpunkcją (np. „kasza manna” i „Kasza-Manna”) walidator traktuje jak duplikat.
  Nazwa wariantu produktu to nazwa produktu podstawowego + wariant obróbki („ziemniak, gotowany”), więc jest
  unikalna, gdy unikalne są nazwy produktów i pary (`food_id`, `preparation`).
- Konwencja nazw: liczba pojedyncza („ziemniak”, „jabłko”), mnoga tylko w zwyczajowej formie handlowej
  („winogrona”, „krewetki”, „płatki owsiane”); w nawiasie – synonim albo doprecyzowanie części lub formy
  („borowik (prawdziwek)”, „cielęcina (udziec)”, „orkisz (ziarno)”).
- Zmiana `name_pl` wymaga tej samej zmiany w [`input/search_terms.csv`](input/search_terms.csv) (S-104) –
  inaczej `make map-products` i test mapowania zgłoszą rozbieżność.

## Mapowanie produktów do `fdc_id` (S-104)

```
make map-products
```

Półautomat: [`map_products.py`](map_products.py) proponuje rekordy USDA SR Legacy dla każdego wariantu produktu
z listy (S-101), Piotr weryfikuje wynik w `mapping/mapping.csv`. Wymaga danych z `make fetch-usda` (sprawdzane sumą
SHA-256), nie wymaga `make sr-wide`.

| Plik | Zawartość |
| --- | --- |
| [`input/search_terms.csv`](input/search_terms.csv) | `food_id`, `name_pl`, `query_en` – angielskie zapytanie w stylu opisów USDA (np. „Beef, chuck, arm pot roast, separable lean only”), jedno na produkt podstawowy; `name_pl` musi zgadzać się z listą |
| [`preparations.yaml`](preparations.yaml) | wariant obróbki → słowa lub frazy w opisach USDA: `include` (pasuje), `exclude` (inna obróbka), `required` (brak słowa z `include` obniża wynik) |
| [`mapping/mapping_candidates.csv`](mapping/mapping_candidates.csv) | wynik: top-5 kandydatów na wariant – `variant_id`, `rank`, `fdc_id`, `score` (0–100), opis i kategoria USDA |
| [`mapping/mapping.csv`](mapping/mapping.csv) | wynik: `variant_id`, `food_id`, `name_pl`, `preparation`, `fdc_id`, `status`, `usda_description`, `score` |
| [`../docs/data/missing_in_usda.md`](../docs/data/missing_in_usda.md) | wynik: produkty bez odpowiednika (do Ciqual/Fineli) i brakujące warianty obróbki (do S-106) |

**Wynik dopasowania** (0–100): podobieństwo zapytania do opisu USDA (rapidfuzz: zbiór słów, kolejność słów bez słów
obróbki, początek opisu do pierwszego przecinka) + premia za słowo obróbki z `include` − kary za słowo z `exclude`,
za brak obróbki (`required`), za słowa zapytania nieobecne w opisie, za markę (słowo wielkimi literami), dodatek soli
(„with salt”) i formę handlową (`canned`, `frozen`, `sweetened`, `dehydrated`), jeśli nie ma jej w zapytaniu.
Słowa obróbki obecne w samym zapytaniu (np. „roasted” w „Buckwheat groats, roasted”) nie są karane.
Pomijane kategorie USDA: Baby Foods, Fast Foods, Restaurant Foods. Wagi i kary – stałe na początku skryptu.

**Statusy** w `mapping.csv`:

| Status | Znaczenie |
| --- | --- |
| `auto` | najlepszy kandydat z wynikiem ≥ 85 – do weryfikacji |
| `brak` | żaden kandydat nie osiąga progu; `fdc_id` puste, `score` = wynik najlepszego kandydata |
| `zweryfikowany` | sprawdzony przez Piotra; pusty `fdc_id` = potwierdzony brak odpowiednika w USDA |

Weryfikacja: w `mapping.csv` popraw `fdc_id` (np. na innego kandydata z `mapping_candidates.csv` albo dowolny
rekord SR Legacy) i ustaw status `zweryfikowany`, potem uruchom `make map-products`. Wiersze `zweryfikowany` nie są
nadpisywane – skrypt odświeża w nich tylko opis i wynik, sprawdza, czy `fdc_id` istnieje w SR Legacy, a gdy wariant
zmienił na liście produkt lub obróbkę, usuwa weryfikację z ostrzeżeniem. Wiersze `auto` i `brak` są liczone od nowa
przy każdym uruchomieniu – sama zmiana `fdc_id` bez statusu `zweryfikowany` zostanie nadpisana.

Test `tests/test_map_products.py` sprawdza w CI (z danymi USDA), czy pliki wynikowe w repo są aktualne.

## Miary domowe (S-109)

```
make portions
```

[`build_portions.py`](build_portions.py) zamienia porcje USDA SR Legacy (`food_portion.csv`) zmapowanych wariantów
produktów ([`mapping/mapping.csv`](mapping/mapping.csv), S-104) na polskie miary domowe z gramami na jedną miarę.
Wymaga danych z `make fetch-usda` (sprawdzane sumą SHA-256). Po weryfikacji mapowania (`make map-products`)
uruchom ponownie.

| Plik | Zawartość |
| --- | --- |
| [`measures.yaml`](measures.yaml) | słownik opisów porcji USDA: miary objętości z ml (`volume`), miary sztukowe → polska nazwa (`count`), rozmiary (`sizes`), postaci (`forms`), słowa pomijane (`noise`) i miary pominięte (`ignored`) |
| [`portions/portions.csv`](portions/portions.csv) | wynik: `variant_id`, `food_id`, `name_pl`, `preparation`, `measure`, `size`, `form`, `grams` (gramy na 1 miarę), `flag`, `fdc_id`, `usda_modifier`, `usda_amount`, `usda_gram_weight`, `calculation` |
| [`../docs/data/portions_coverage.md`](../docs/data/portions_coverage.md) | wynik: pokrycie wariantów miarami i opisy porcji USDA pominięte przy rozbiorze |

- W SR Legacy jednostka porcji jest tylko w wolnym tekście (`modifier`, np. „cup, chopped”, „large (3" dia)”);
  `measure_unit_id` ma zawsze wartość 9999 („undetermined”). Rozbiór opisu – komentarz w `measures.yaml`.
- **`measured`** – wprost z USDA: łyżka (`tbsp`), łyżeczka (`tsp`) i miary sztukowe (sztuka, plaster, liść, filet…)
  z rozmiarem (`mały`, `średni`, `duży`…) i postacią (`posiekane`, `w plastrach`…). `grams` = `gram_weight / amount`
  (np. 10 malin = 19 g → 1,9 g na sztukę).
- **`calculated`** – z gęstości produktu (g/ml) liczonej z miary objętości USDA (cup, tbsp, tsp, fl oz, pint, quart)
  o największej objętości, osobno dla każdej postaci: `ml` (gramy w 1 ml, tylko bez postaci) i polska szklanka
  250 ml (amerykański `cup` ma 236,59 ml). Kolumna `calculation` opisuje przeliczenie.
- Pomijane: jednostki masy (oz, lb – gramy są w USDA wprost), opakowania i porcje handlowe (can, package,
  NLEA serving) oraz porcje z „yield(s)” (wydajność z opakowania lub produktu przed obróbką).
- Powtórzenia tej samej miary, rozmiaru i postaci w jednym rekordzie USDA: zostaje pierwsza porcja (`seq_num`).
- Warianty bez `fdc_id` (status `brak`) nie mają miar; przenoszenie miar między wariantami obróbki – poza S-109.

Test `tests/test_portions.py` sprawdza rozbiór opisów, przeliczenia (3 przykłady na prawdziwych danych: łyżka oliwy,
szklanka mleka, średnie jabłko) i czy pliki wynikowe w repo są aktualne.

## Warianty po obróbce termicznej (S-106)

```
make cooked-variants
```

[`cooking.py`](cooking.py) wylicza warianty obróbki termicznej bez rekordu USDA z wariantu bazowego tego samego
produktu (`surowy`, a gdy go nie ma – `gotowy`): współczynniki retencji USDA R6, wydajność (zmiana masy) i olej
wchłonięty przy smażeniu. Wymaga danych z `make fetch-usda` i `mapping/mapping.csv`. Logika, wzory i źródła:
[`docs/data/cooking_calc.md`](../docs/data/cooking_calc.md).

| Plik | Zawartość |
| --- | --- |
| [`cooking/methods.yaml`](cooking/methods.yaml) | parametry (olej do smażenia, minimum par, próg ryb tłustych), składniki z R6 i dobór procesu R6 dla kategorii, podkategorii lub produktu |
| [`cooking/yields.csv`](cooking/yields.csv) | wydajność (%) i wchłonięty tłuszcz (g) dla zakresu i wariantu obróbki: `scope`, `preparation`, `yield_pct`, `fat_uptake_g`, `source`, `reference` (tabela w źródle) |
| [`cooking/cooked_variants.csv`](cooking/cooked_variants.csv) | wynik: wyliczone warianty – baza, proces R6, wydajność, olej i wartości 38 składników |
| [`../docs/data/cooking_coverage.md`](../docs/data/cooking_coverage.md) | wynik: wyliczone warianty, warianty bez wartości z powodem, mediany par USDA |
| `data/interim/variant_nutrients.parquet` | wynik (poza git): wartości wszystkich wariantów – `measured` z USDA i `calculated` – ze źródłem i odwołaniem do współczynnika (`factor_ref`) |

- Wydajność: najpierw wpis `yields.csv`, potem mediana co najmniej 3 par USDA (warianty zmierzone przed obróbką
  i po niej), od najwęższego zakresu (produkt, podkategoria, kategoria). Wpis ze źródłem `brak` = świadomy brak.
- Kody kategorii i podkategorii jak w [`categories.yaml`](categories.yaml); produkt jako `food:<food_id>`.
- Po zmianie `mapping.csv`, `cooking/` albo listy produktów uruchom komendę ponownie – test
  `tests/test_cooking.py` sprawdza, czy pliki w repo są aktualne.

## Tagi wykluczeń i diet (S-108)

```
make product-tags
```

| Plik | Zawartość |
| --- | --- |
| [`tags.yaml`](tags.yaml) | słownik tagów: `code` (angielski, nazwa kolumny), `name_pl`, `kind` (`exclusion` / `diet`), zależności tagów diet i reguły automatycznej propozycji; uwagi do przeglądu (`review_notes`) |
| [`tags/product_tags.csv`](tags/product_tags.csv) | tagi produktów (w git): 1 wiersz = produkt podstawowy (`food_id`), kolumny `food_id`, `name_pl`, `category`, `subcategory`, po jednej kolumnie `true`/`false` na tag, `status`, `notes` |
| [`product_tags.py`](product_tags.py) | propozycja automatyczna i walidacja |

Tagi v1:

| Kod | Nazwa | Rodzaj |
| --- | --- | --- |
| `contains_lactose` | zawiera laktozę | wykluczenie |
| `contains_gluten` | zawiera gluten | wykluczenie |
| `meat` | mięso | wykluczenie |
| `fish` | ryby | wykluczenie |
| `seafood` | owoce morza | wykluczenie |
| `eggs` | jaja | wykluczenie |
| `nuts` | orzechy | wykluczenie |
| `vegan` | wegańskie | dieta |
| `vegetarian` | wegetariańskie | dieta |

- Tag wykluczenia = produkt **zawiera** składnik; profil domownika wyklucza produkty z tagiem (S-301).
  Tag diety = produkt **nadaje się** do diety.
- Tagi należą do produktu podstawowego, więc obowiązują wszystkie jego warianty (obróbka ich nie zmienia;
  wariant `smażony` zawiera olej rzepakowy – S-106).
- **Propozycja automatyczna** (`make product-tags`): reguły z `tags.yaml` sprawdzają kategorię i podkategorię
  produktu (`categories.yaml`), polską nazwę oraz kategorię i opis USDA rekordów przypisanych wariantom
  produktu w `mapping/mapping.csv` (S-104). Tag diety dostaje produkt bez wykluczających go tagów
  (`excluded_by_tags`) i bez trafienia reguły `excluded_by` (np. miód nie jest wegański).
  W `notes` generator zapisuje źródła każdego tagu (`kategoria`, `nazwa`, `USDA`), brak rekordu USDA
  i uwagi do przeglądu z `review_notes`.
- **Zasada ostrożności**: wątpliwy produkt dostaje tag wykluczenia – niepotrzebne wykluczenie szkodzi mniej
  niż pominięte (np. laktoza w serach dojrzewających i maśle klarowanym, gluten w kaszance i płatkach
  kukurydzianych).
- **Statusy**: `auto` – propozycja, nadpisywana przy każdym uruchomieniu; `zweryfikowany` – sprawdzone ręcznie,
  nigdy nienadpisywane (nazwa i kategoria odświeżane z listy produktów). Weryfikacja (praca Piotra):
  popraw `true`/`false`, ustaw `zweryfikowany`, opcjonalnie zmień `notes`.
- Walidacja (także w CI, bez danych USDA: `uv run python -X utf8 data-pipeline/product_tags.py --check`):
  kolumny zgodne ze słownikiem, każdy produkt z listy dokładnie raz i w kolejności `food_id`, nazwa i kategoria
  zgodne z listą produktów, wartości `true`/`false`, statusy, spójność tagów (`vegan` → `vegetarian`;
  `vegetarian` nie z `meat`, `fish`, `seafood`; `vegan` nie z `contains_lactose`, `eggs`).
  Test na prawdziwych danych sprawdza, czy plik w repo jest aktualny – po zmianie listy produktów, mapowania
  albo `tags.yaml` uruchom `make product-tags`.
