# Backlog dAIet

Roadmapa i opis faz: dokument 'dAIet – roadmapa i backlog' w projekcie dAIet.

CC = Claude Code realizuje, Piotr robi review · P = praca/decyzja Piotra · CC+P = Piotr decyduje, CC implementuje

Sposób pracy: jedna story = jedna sesja Claude Code = jeden branch i PR.
Polecenie startowe: `Zrealizuj backlog/S-XXX.md zgodnie z CLAUDE.md` (najpierw tryb planu).

Statusy: todo → ready (zależności zamknięte, decyzje wypełnione) → in-progress → done; odłożone = poza v1

## Decyzje 2026-11-21
- Produkt działa „od planu”: bez spiżarni (S-205, S-403 odłożone).
- Historia 7 dni = zapisane plany (S-206).
- Oceny jako luźna tabela `feedback` (user_id, danie, ocena 1–5) (S-308).
- Ankieta preferencji odłożona (S-208).
- Architektura: PostgreSQL + backend REST API (FastAPI) w Dockerze; LLM przez Claude API; interfejsy to klienci API: bot Discord dla domowników (S-405), CLI dla insiderów (S-404).
- Mini-baza 30–50 produktów (S-113) odblokowuje E2/E3 przed ukończeniem pełnej bazy v1.
- Python 3.13 w całym projekcie (lokalnie, Docker, CI). Na początku prac Piotr podnosi lokalny Python z 3.13.0 do 3.13.17 – ostatniego wydania z instalatorem na Windows; 3.13.18+ jest tylko źródłowe (S-003). Stos sprawdzony też pod 3.14 – ewentualna zmiana później.
- Licencja kodu: GNU AGPL-3.0 (użycie komercyjne dozwolone pod warunkiem udostępnienia źródeł, także dla usług online) – S-001. Licencja danych (baza żywności) osobno – S-505.

## E0 – Fundament repo (M0)

| ID | Story | Kto | Zależy od | Status |
| --- | --- | --- | --- | --- |
| [S-001](S-001.md) | Struktura repozytorium | CC | – | done |
| [S-002](S-002.md) | CLAUDE.md – zasady pracy z Claude Code | CC+P | S-001 | done |
| [S-003](S-003.md) | Środowisko developerskie | CC | S-001 | done |
| [S-004](S-004.md) | CI w GitHub Actions | CC | S-003 | done |
| [S-005](S-005.md) | Szablony story i ADR | CC | S-001 | done |
| [S-006](S-006.md) | Surowe dane USDA w repo (poza git) | CC | S-001 | done |
| [S-007](S-007.md) | Szkielet backendu FastAPI w Dockerze | CC | S-003 | done |
| [S-008](S-008.md) | Ochrona brancha main | CC+P | S-004 | done |

## E1 – Baza żywności v1 (M1)

| ID | Story | Kto | Zależy od | Status |
| --- | --- | --- | --- | --- |
| [S-101](S-101.md) | Lista docelowych produktów podstawowych | P | – | in-progress |
| [S-102](S-102.md) | Import SR Legacy do tabeli szerokiej | CC | S-006 | done |
| [S-103](S-103.md) | Wybór składników odżywczych i jednostek | CC+P | S-102 | in-progress |
| [S-104](S-104.md) | Mapowanie listy produktów do fdc_id | CC+P | S-101, S-102 | in-progress |
| [S-105](S-105.md) | Polskie nazwy i kategorie | CC+P | S-104 | done |
| [S-106](S-106.md) | Warianty po obróbce termicznej | CC | S-104 | todo |
| [S-107](S-107.md) | Indeks glikemiczny | CC+P | S-104 | todo |
| [S-108](S-108.md) | Tagi wykluczeń i diet | P | S-104 | todo |
| [S-109](S-109.md) | Miary domowe | CC | S-104 | done |
| [S-110](S-110.md) | Walidacja jakości danych | CC | S-106 | todo |
| [S-111](S-111.md) | Eksport bazy v1 | CC | S-110 | todo |
| [S-112](S-112.md) | Przegląd i akceptacja bazy v1 | P | S-111 | todo |
| [S-113](S-113.md) | Mini-baza startowa (30–50 produktów) | CC+P | S-102 | todo |

## E2 – Model danych i API (M2)

| ID | Story | Kto | Zależy od | Status |
| --- | --- | --- | --- | --- |
| [S-201](S-201.md) | Schemat bazy produktów | CC | S-007, S-113 | todo |
| [S-202](S-202.md) | Loader CSV → DB | CC | S-201 | todo |
| [S-203](S-203.md) | Encje użytkownika (multi-user od początku) | CC | S-201 | todo |
| [S-204](S-204.md) | API produktów | CC | S-202 | todo |
| [S-205](S-205.md) | API spiżarni | CC | S-203 | odłożone |
| [S-206](S-206.md) | Zapis planów jako historia | CC | S-203 | todo |
| [S-207](S-207.md) | Profile domowników | P | S-203 | todo |
| [S-208](S-208.md) | Ankieta preferencji smakowych | CC+P | S-203 | odłożone |

## E3 – Silnik więzów i przepisy LLM (M3)

| ID | Story | Kto | Zależy od | Status |
| --- | --- | --- | --- | --- |
| [S-301](S-301.md) | Specyfikacja więzów | P | – | todo |
| [S-302](S-302.md) | Kalkulator przepisu | CC | S-202 | todo |
| [S-303](S-303.md) | Silnik reguł | CC | S-301, S-302 | todo |
| [S-304](S-304.md) | Schemat JSON przepisu | CC+P | S-201 | todo |
| [S-305](S-305.md) | Adapter LLM i prompt | CC | S-304 | todo |
| [S-306](S-306.md) | Walidator i pętla naprawcza | CC | S-303, S-305 | todo |
| [S-307](S-307.md) | Zestaw ewaluacyjny | CC+P | S-306 | todo |
| [S-308](S-308.md) | Oceny dań (lean) | CC | S-203 | todo |

## E4 – Planer i pilot domowy (M4)

| ID | Story | Kto | Zależy od | Status |
| --- | --- | --- | --- | --- |
| [S-401](S-401.md) | Plan na N dni | CC | S-206, S-306 | todo |
| [S-402](S-402.md) | Lista zakupów | CC | S-401 | todo |
| [S-403](S-403.md) | Oznaczanie zjedzonych posiłków | CC | S-401 | odłożone |
| [S-404](S-404.md) | CLI (narzędzie dla insiderów) | CC | S-401 | todo |
| [S-405](S-405.md) | Bot Discord | CC | S-007, S-402 | todo |
| [S-406](S-406.md) | Pilot domowy | P | S-405 | todo |
| [S-407](S-407.md) | Poprawki po pilocie | CC+P | S-406 | todo |

## E5 – Gotowość na publiczny WebApp (M5)

| ID | Story | Kto | Zależy od | Status |
| --- | --- | --- | --- | --- |
| [S-501](S-501.md) | Uwierzytelnianie i izolacja danych | CC | S-407 | todo |
| [S-502](S-502.md) | Deploy | CC+P | S-501 | todo |
| [S-503](S-503.md) | Limity i koszty LLM | CC | S-501 | todo |
| [S-504](S-504.md) | RODO i dane o zdrowiu | P | – | todo |
| [S-505](S-505.md) | Licencje danych | P | – | todo |
| [S-506](S-506.md) | Disclaimer i onboarding | CC+P | S-504 | todo |
| [S-507](S-507.md) | Monitoring i logi | CC | S-502 | todo |
