# ADR-0001 – Baza żywności: poziom danych, format i źródła

Status: przyjęta | Data: 2026-11-14 (uzupełniona 2026-11-22) | Decyduje: Piotr | Story: S-005

## Kontekst
dAIet układa przepisy przez LLM, ale wszystkie liczby (wartości odżywcze, IG, ŁG) muszą pochodzić z lokalnej bazy
żywności – LLM wskazuje tylko składniki i gramatury. Potrzebna jest baza, którą da się zbudować powtarzalnie
z otwartych źródeł, z jawnym pochodzeniem każdej wartości.

Źródło: dokument „Baza żywności dla dAIet – decyzje i źródła” z 2026-11-14
([kopia](../data/food_db_decisions_2026-11-14.md)) oraz decyzje z 2026-11-21 w
[backlog/README.md](../../backlog/README.md).

## Decyzja

**Poziom danych**
- Baza obejmuje **produkty podstawowe** – generyczne, bez marki (np. „ziemniak, gotowany”).
  Produkty handlowe (EAN) są poza zakresem.
- Zakres v1: ok. 300–500 produktów podstawowych z wariantami obróbki termicznej (S-101).
- Na start **mini-baza** 30–50 produktów w tym samym formacie (`foods_v0.1`, S-113), żeby odblokować model danych
  (E2) i przepisy LLM (E3) przed akceptacją pełnej bazy v1. Pełną bazą zastępuje ją ten sam loader.

**Format**
- **CSV szeroki**: 1 wiersz = produkt + wariant obróbki, kolumny = składniki odżywcze; wartości na 100 g części jadalnej.
- **Słownik `.md`** obok CSV: kolumny, jednostki, źródła, flagi.
- Baza ma **numer wersji** (np. `foods_v1.0.csv`, `foods_v1.0_dictionary.md`); build odtwarzalny jedną komendą
  `make data` (S-111).
- CSV ładuje do PostgreSQL idempotentny loader (S-202); backend czyta wyłącznie z bazy danych.

**Pochodzenie wartości**
- Każda wartość ma **źródło** i flagę **`measured`** (zmierzona, wprost ze źródła) albo **`calculated`**
  (wyliczona, np. współczynnikiem retencji lub wydajności – z odwołaniem do współczynnika).
- Brak wartości to jawne `null`, nigdy zero (np. produkt bez IG, S-107).

**Źródła**

| Rola | Źródło | Uwagi |
| --- | --- | --- |
| Szkielet: makro, minerały, witaminy, warianty po obróbce | USDA FoodData Central – SR Legacy (2018-04) | CC0, wydanie końcowe; S-006, S-102 |
| Indeks glikemiczny | International Tables of GI and GL Values 2021 (Atkinson i in., AJCN), tabela uzupełniająca 1 | tylko wartości zgodne z ISO; z metodą obróbki; S-107 |
| Przeliczenia po obróbce, gdy brak danych zmierzonych | USDA Table of Nutrient Retention Factors R6 (2007) | S-106 |
| Uzupełnienie | ANSES Ciqual 2025, Fineli | produkty europejskie, zwłaszcza polskie luki w USDA (np. twaróg, kasza gryczana, kiszonki); z oznaczeniem źródła |

## Konsekwencje
- Silnik więzów i kalkulator przepisu (E3) liczą wszystko z bazy; LLM nie podaje liczb (CLAUDE.md).
- Pipeline danych (`data-pipeline/`) musi zapisywać źródło i flagę przy każdej wartości, a walidacja (S-110)
  sprawdza spójność, np. kcal względem makro.
- Polskie produkty spoza USDA wymagają drugiego źródła i ręcznej weryfikacji mapowania (S-104).
- Publiczne udostępnienie bazy zależy od licencji źródeł (S-505).

## Odrzucone opcje
- Produkty handlowe z kodami EAN – poza zakresem v1 (dokument z 2026-11-14, roadmapa).

## Otwarte sprawy (rozbieżności z dokumentem z 2026-11-14)
1. **Wartości współczynników retencji R6 nie są w pobranych danych.** Plik `retention_factor.csv` z paczki
   SR Legacy (270 wierszy: `id`, `code`, `food_group_id`, `description`) zawiera tylko listę procesów obróbki,
   bez wartości współczynników. Pełną tabelę R6 trzeba pobrać osobno – do rozwiązania w S-106.
2. **Brak źródła współczynników wydajności** (zmiana masy przy obróbce). Dokument je wymienia, ale nie wskazuje
   źródła – do ustalenia w S-106.
3. **Licencje.** Dokument podaje tylko CC0 dla USDA. Do sprawdzenia: warunki publicznego użycia tabel IG,
   licencje Ciqual i Fineli oraz własna licencja bazy v1 – S-505.
4. **Rola Ciqual/Fineli** w dokumencie jest opcjonalna; roadmapa traktuje je jako uzupełnienie polskich produktów.
   Decyzja, czy i które produkty z nich brać, przy mapowaniu listy (S-104).
