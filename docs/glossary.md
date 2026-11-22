# Słownik pojęć

Wspólne pojęcia projektu dAIet. Używaj ich w kodzie (angielskie odpowiedniki w nawiasach), dokumentacji i
rozmowach z Claude Code. Nowe pojęcie dopisz tutaj w tym samym PR, w którym się pojawia.

## Baza żywności

| Pojęcie | Znaczenie |
| --- | --- |
| **produkt podstawowy** (food) | Generyczny produkt spożywczy bez marki, np. „ziemniak”. Poziom danych bazy – [ADR-0001](adr/0001-food-database.md). |
| **wariant obróbki** (preparation) | Stan produktu po obróbce: surowy, gotowy, gotowany, gotowany na parze, pieczony, smażony, duszony, grillowany (S-101). Formy przetworzone (kiszony, wędzony, suszony) to osobne produkty. |
| **lista produktów** (product list) | Warianty produktów bazy v1 (`variant_id`, `food_id`) z kategorią: `data-pipeline/input/product_list.csv` (S-101). |
| **wariant produktu** (food variant) | Para produkt podstawowy + wariant obróbki, np. „ziemniak, gotowany”. Jeden wiersz CSV bazy; na niego wskazuje przepis od LLM (S-304). |
| **składnik odżywczy** (nutrient) | Mierzona cecha produktu: białko, tłuszcz, magnez, błonnik, IG itd. Kolumna CSV bazy. |
| **źródło** (source) | Pochodzenie wartości, np. USDA SR Legacy (z `fdc_id`) albo pozycja w tabeli IG. Każda wartość je ma. |
| **measured / calculated** | Flaga wartości: zmierzona (wprost ze źródła) albo wyliczona, np. współczynnikiem retencji lub wydajności. |
| **współczynnik retencji** (retention factor) | Część składnika, która zostaje po obróbce; USDA R6 (S-106). |
| **współczynnik wydajności** (yield factor) | Zmiana masy produktu przy obróbce, np. utrata wody (S-106). |
| **IG** – indeks glikemiczny (GI) | Jak szybko produkt podnosi glukozę we krwi względem glukozy; brak danych = `null` (S-107). |
| **ŁG** – ładunek glikemiczny (GL) | IG × węglowodany przyswajalne w porcji / 100; liczony w kodzie (S-302). |
| **pokrycie składnika** (nutrient coverage) | Odsetek produktów, które mają wartość składnika odżywczego (`null` = brak, zero ze źródła to wartość). Raport: `docs/data/nutrient_coverage.md` (S-103). |
| **tabela szeroka** (wide table) | Układ danych: 1 wiersz = produkt, 1 kolumna = składnik odżywczy (przeciwieństwo układu wąskiego USDA: 1 wiersz = produkt + składnik). Pośrednia `sr_wide.parquet` (S-102), docelowo CSV bazy (ADR-0001). |
| **`fdc_id`** | Identyfikator produktu w USDA FoodData Central. |
| **mini-baza** | Baza startowa 30–50 produktów (`foods_v0.1`) w formacie v1 (S-113). |
| **baza v1** | Pełna baza 300–500 produktów (`foods_v1.0`) po akceptacji (S-112). |

## Planer

| Pojęcie | Znaczenie |
| --- | --- |
| **więzy** (constraints) | Reguły, które musi spełnić przepis i plan: wykluczenia, próg IG, limit ŁG, różnorodność 7 dni (S-301). |
| **tag wykluczenia** (exclusion tag) | Cecha produktu używana przez więzy, np. laktoza, gluten, mięso (S-108). |
| **profil** (profile) | Ustawienia domownika: wykluczenia, tryb niskiego IG, posiłki dziennie (S-203). |
| **tryb niskiego IG** | Ustawienie profilu ograniczające IG/ŁG posiłków; dane o zdrowiu w rozumieniu RODO (S-504). |
| **przepis** (recipe) | Propozycja LLM: warianty produktów z gramaturą, kroki, porcje; liczby dolicza backend (S-304). |
| **plan** (plan) | Posiłki na N dni; zapisane plany to historia do reguły różnorodności (S-206, S-401). |
| **lista zakupów** (shopping list) | Suma składników planu (S-402). |
| **ocena dania** (feedback) | Ocena 1–5 wystawiona przez domownika (S-308). |

## Praca nad projektem

| Pojęcie | Znaczenie |
| --- | --- |
| **story** | Jednostka pracy w `backlog/S-XXX.md`: jedna story = jedna sesja = jeden branch i PR. |
| **CC / P / CC+P** | Kto realizuje story: Claude Code (review Piotra) / Piotr / Piotr decyduje, Claude Code implementuje. |
| **ADR** | Zapis decyzji architektonicznej w `docs/adr/` (szablon: `0000-template.md`). |
