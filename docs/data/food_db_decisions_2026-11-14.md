> Kopia dokumentu z plików projektu dAIet (Claude Cowork), stan na 2026-11-14, przeniesiona do repo 2026-11-22.
> Treść poniżej bez zmian. Aktualne, obowiązujące decyzje: [ADR-001](../adr/0001-food-database.md),
> rozbieżności z późniejszymi ustaleniami są opisane w sekcji „Rozbieżności” ADR-001.

# Baza żywności dla dAIet – decyzje i źródła

## Decyzje (2026-11-14)
- Poziom danych: **produkty podstawowe** (np. „ziemniak, gotowany”). Produkty handlowe (EAN) są poza zakresem.
- Zakres v1: ok. 300–500 produktów podstawowych z wariantami obróbki termicznej.
- Format: **CSV szeroki** (1 wiersz = produkt + wariant obróbki, kolumny = składniki odżywcze) + **słownik .md** (kolumny, jednostki, źródła).
- Każda wartość ma źródło; wartości wyliczone (współczynniki retencji/wydajności) są oznaczane osobno od zmierzonych.

## Terminologia
- produkt podstawowy – generyczny produkt spożywczy bez marki
- składnik odżywczy – białko, magnez, IG itd.
- wariant obróbki – surowy, gotowany, pieczony, smażony…

## Źródła
| Rola | Źródło | Uwagi |
|---|---|---|
| Szkielet (makro, minerały, witaminy, warianty po obróbce) | USDA FoodData Central – SR Legacy (2018-04) | CC0, wydanie końcowe |
| Indeks glikemiczny | International Tables of GI and GL Values 2021 (Atkinson i in., AJCN), tabela uzupełniająca 1 | tylko wartości zgodne z ISO; zawiera metodę obróbki |
| Przeliczenia po obróbce (gdy brak danych zmierzonych) | USDA Table of Nutrient Retention Factors R6 (2007) | |
| Uzupełnienie (opcjonalnie) | ANSES Ciqual 2025, Fineli | produkty europejskie |
