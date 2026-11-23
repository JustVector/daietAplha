# Przeliczenie wariantów po obróbce termicznej

Story: [S-106](../../backlog/S-106.md) · kod: [`data-pipeline/cooking.py`](../../data-pipeline/cooking.py) ·
komenda: `make cooked-variants` · wynik: [`cooking_coverage.md`](cooking_coverage.md)

Dokument opisuje, skąd pochodzą wartości odżywcze wariantów obróbki termicznej (gotowany, gotowany na parze,
pieczony, smażony, duszony, grillowany) i jak backend może je odtworzyć. LLM nie podaje żadnej z tych liczb.

## Wartości zmierzone i wyliczone

| Sytuacja | Wartości | Flaga | Źródło | Odwołanie do współczynnika |
| --- | --- | --- | --- | --- |
| Wariant ma rekord USDA (`fdc_id` w `mapping.csv`, S-104) | wprost z SR Legacy | `measured` | `usda_sr_legacy:<fdc_id>` | – |
| Wariant obróbki termicznej bez rekordu USDA, a produkt ma wariant bazowy z rekordem | wyliczone z wariantu bazowego | `calculated` | `usda_sr_legacy:<fdc_id bazy>` | proces R6, wydajność i jej źródło, ewentualnie olej |
| Brak wariantu bazowego albo parametrów | brak (`null`) | – | – | powód w raporcie |

**Wariant bazowy** to wariant tego samego produktu podstawowego z rekordem USDA: `surowy`, a gdy go nie ma –
`gotowy` (kiełbasy, tofu, sery jedzone bez obróbki).

Wynik: `data/interim/variant_nutrients.parquet` (poza git) – jeden wiersz na wariant i składnik:
`variant_id`, `nutrient`, `unit`, `value`, `flag`, `source`, `factor_ref`. Wyliczone warianty z parametrami
są też w [`data-pipeline/cooking/cooked_variants.csv`](../../data-pipeline/cooking/cooked_variants.csv) (w git).
Eksport bazy v1 (S-111) bierze stąd flagi i źródła.

## Wzory

Dla 100 g produktu wyjściowego (wariantu bazowego):

1. **Ilość składnika po obróbce** = wartość bazowa × R / 100 + wartość oleju × olej / 100
   - R – współczynnik retencji składnika w procesie R6 (%); składnik bez współczynnika w R6 – 100%,
   - olej – gramy oleju wchłoniętego przy smażeniu (tylko `smażony`), wartości oleju z wariantu
     `frying_fat_variant_id` (olej rzepakowy).
2. **Woda** = Y − (100 − woda bazowa) − olej × (100 − woda oleju) / 100. Cała sucha masa produktu zostaje, masa
   zmienia się przez wodę i wchłonięty olej.
3. **Wartość na 100 g po obróbce** = ilość × 100 / Y.

Y – **wydajność**: masa po obróbce w % masy produktu wyjściowego (80 = traci 20% masy, 300 = kasza wchłania wodę).
Energia, makroskładniki, kwasy tłuszczowe i cholesterol mają R = 100% – zmienia je tylko masa i olej.
Brak wartości w produkcie bazowym zostaje brakiem (`null`, nigdy 0). Wydajność poniżej suchej masy (ujemna woda)
przerywa wyliczenie wariantu (raport podaje powód).

## Współczynniki retencji – USDA R6

- Źródło: *USDA Table of Nutrient Retention Factors, Release 6* (2007),
  `https://www.ars.usda.gov/ARSUserFiles/80400525/Data/retn/retn06.txt`, domena publiczna. Pobiera go
  `make fetch-usda` do `data/raw/usda_retention/` (suma SHA-256 w `data-pipeline/checksums/usda_retention.sha256`).
  `retention_factor.csv` z paczki SR Legacy ma tylko listę 270 procesów, bez wartości.
- Proces dobiera [`cooking/methods.yaml`](../../data-pipeline/cooking/methods.yaml) (`retention`): reguły dla
  kategorii, podkategorii albo produktu podstawowego (kody z `categories.yaml`); wygrywa najbardziej
  szczegółowa reguła z danym wariantem obróbki. Ryby: powyżej `fatty_fish_fat_g` (5 g tłuszczu w produkcie
  wyjściowym) procesy dla ryb tłustych.
- Składniki bazy v1 ze współczynnikiem R6 (`r6_nutrients`): Ca, Fe, Mg, P, K, Na, Zn, Cu, witaminy C, B1, B2,
  B3, B6, B12, alkohol; witamina A (RAE) bierze współczynnik „Vitamin A, RE”, foliany (DFE) – „Folate, total”.
- **Bez współczynnika w R6 – retencja 100%** (decyzja Piotra z 2026-11-23, jak w praktyce USDA): Mn, Se,
  witaminy D, E, K, kwasy tłuszczowe, cholesterol, kofeina. `factor_ref` mówi wtedy „brak współczynnika – 100%”.

## Wydajność

Kolejność szukania (od najwęższego zakresu: produkt podstawowy, podkategoria, kategoria):

1. wpis w [`cooking/yields.csv`](../../data-pipeline/cooking/yields.csv) dla zakresu i wariantu obróbki,
2. mediana co najmniej `min_pairs` (3) **par USDA** w zakresie (poza poziomem produktu),
3. następny, szerszy zakres.

Wpis z pustą wydajnością i źródłem `brak` zatrzymuje szukanie – świadomy brak danych (np. smażony boczek).

**Pary USDA** to warianty tego samego produktu zmierzone w SR Legacy przed obróbką i po niej (oba zmapowane
w S-104). Wydajność z bilansu suchej masy bez tłuszczu (białko, węglowodany i popiół nie znikają):

    Y = (100 − woda_bazowy − tłuszcz_bazowy) / (100 − woda_obrobiony − tłuszcz_obrobiony) × 100
    wchłonięty tłuszcz = tłuszcz_obrobiony × Y / 100 − tłuszcz_bazowy   (g na 100 g produktu wyjściowego)

Mediany par każdej grupy są w raporcie pokrycia. Rekordy surowe i po obróbce USDA pochodzą często z różnych
próbek, więc pojedyncza para bywa myląca (np. marchew gotowana > 100%) – stąd mediana i minimum 3 par.

Źródła wpisów w `yields.csv` (kolumna `source`, odwołanie do tabeli w `reference`):

| `source` | Dokument | Zakres w bazie v1 |
| --- | --- | --- |
| `usda_meat_yields_2012` | *USDA Table of Cooking Yields for Meat and Poultry* (Showell i in., 2012), [PDF](https://www.ars.usda.gov/ARSUserFiles/80400525/Data/retn/USDA_CookingYields_MeatPoultry.pdf) – mediany rekordów gatunku i metody z tabeli danych | wieprzowina, wołowina i cielęcina, drób (gotowany, pieczony), podroby (gotowany) |
| `bognar_2002` | A. Bognár, *Tables on weight yield of food and retention factors of food constituents for the calculation of nutrient composition of cooked foods (dishes)*, BFE-R--02-03, Bundesforschungsanstalt für Ernährung, Karlsruhe 2002, [PDF (KIT)](https://publikationen.bibliothek.kit.edu/9642002/1928) – tabele wydajności części 1 | ryby (gotowane, na parze, smażone), kiełbasy i wyroby podrobowe, jajo gotowane, kasza gryczana, płatki owsiane, warzywa i grzyby duszone |
| `usda_sr_pairs` | pary USDA (wyżej), liczone w kodzie | pozostałe grupy z co najmniej 3 parami, np. warzywa smażone, drób grillowany i duszony |

Decyzja Piotra z 2026-11-23: dla warzyw najpierw pary USDA, potem Bognár. Tabele USDA (AH-102 z 1975 r. i tabela
mięsa z 2012 r.) nie mają warzyw pieczonych, grillowanych ani smażonych; Bognár ma dla warzyw głównie gotowanie,
gotowanie na parze i duszenie. **Warzywa pieczone i grillowane, jabłko pieczone, tofu i tempeh zostają bez
wartości** – do uzupełnienia z Ciqual lub Fineli.

## Tłuszcz przy smażeniu

Decyzja Piotra z 2026-11-23: wariant `smażony` zawiera wchłonięty tłuszcz (tak jak zmierzone rekordy USDA
„fried”), więc olej do smażenia nie jest osobnym składnikiem przepisu (S-304).

- Ilość tłuszczu: z `yields.csv` (kolumna `fat_uptake_g`), a gdy jej brak – mediana par USDA smażenia
  (podkategoria, kategoria, wszystkie pary); ujemna mediana (tłuszcz wytopiony) = 0.
- Olej: wariant `frying_fat_variant_id` (615, olej rzepakowy); gramy oleju = tłuszcz × 100 / tłuszcz oleju.
  Olej wnosi wszystkie swoje składniki (energię, kwasy tłuszczowe, witaminy E i K).

## Założenia i ograniczenia

- Tłuszcz produktu zostaje w całości (R = 100%) – wytapianie tłuszczu z mięsa przy pieczeniu i duszeniu nie jest
  odejmowane, więc tłuste mięso duszone może mieć zawyżony tłuszcz.
- Wydajność grupy, nie produktu: wynik dla konkretnego kawałka mięsa może różnić się o ok. 10–15% (test
  porównuje wyliczoną pieczoną pierś z kurczaka z rekordem USDA).
- Sucha masa nie przechodzi do wody (np. przy gotowaniu z odlewaniem) – straty składników rozpuszczalnych
  ujmują tylko współczynniki R6.
- Wyniki zależą od mapowania (S-104): po weryfikacji `mapping.csv` trzeba ponownie uruchomić
  `make cooked-variants`; test sprawdza, czy pliki w repo są aktualne.

## Przypadki referencyjne

Testy jednostkowe (`tests/test_cooking.py`) liczą 5 przypadków na sztucznych wartościach, z wynikami
policzonymi ręcznie:

| Przypadek | Dane | Wynik (na 100 g po obróbce) |
| --- | --- | --- |
| 1. warzywo pieczone | woda 88 g, witamina C 10 mg (R = 75%), wapń 30 mg (R = 100%), Y = 80% | woda 85 g, witamina C 9,375 mg, wapń 37,5 mg |
| 2. mięso grillowane | woda 74 g, białko 22 g, tiamina 0,1 mg (R = 70%), Y = 75% | woda 65,3 g, białko 29,3 g, tiamina 0,093 mg |
| 3. ryba smażona | woda 80 g, tłuszcz 1 g, 80 kcal, Y = 80%, 2 g oleju (884 kcal/100 g) | woda 72,5 g, tłuszcz 3,75 g, 122,1 kcal |
| 4. kasza gotowana | woda 10 g, białko 12 g, tiamina 0,4 mg (R = 80%), Y = 300% | woda 70 g, białko 4 g, tiamina 0,107 mg |
| 5. produkt gotowy smażony | kiełbasa: woda 55 g, tłuszcz 28 g, witamina D brak, Y = 90% | woda 50 g, tłuszcz 31,1 g, witamina D brak |
