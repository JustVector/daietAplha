# CLAUDE.md – dAIet

Planer posiłków dla domu. LLM (Claude API) proponuje przepisy z dozwolonych składników, a silnik więzów
przelicza je i weryfikuje na danych z bazy żywności. Wynik: plan na N dni i lista zakupów.

## Architektura

- **PostgreSQL** – baza żywności, użytkownicy, profile, plany, oceny.
- **backend/** – REST API w FastAPI, w docker compose. Jedyne miejsce logiki biznesowej i jedyny dostęp do bazy.
- **Klienci API** – bot Discord (domownicy, S-405), CLI (insiderzy, S-404), przyszły WebApp (`web/`, E5).
  Rozmawiają wyłącznie z REST API, nigdy bezpośrednio z bazą.
- **Claude API** – wołane tylko z backendu, przez warstwę adaptera (S-305).
- **data-pipeline/** – przygotowanie bazy żywności v1 (USDA SR Legacy → CSV → loader do bazy).

| Katalog | Zawartość |
| --- | --- |
| `backend/` | REST API |
| `data-pipeline/` | import, mapowanie, walidacja i eksport bazy żywności |
| `data/raw/` | surowe dane źródłowe, poza git |
| `docs/` | ADR, słownik pojęć, licencje danych, specyfikacje |
| `backlog/` | stories (`S-XXX.md`) i tabela statusów (`README.md`) |
| `web/` | przyszły WebApp |

Diagram: `DietAi.drawio`.

## Środowisko i komendy

- Python **3.13** (gałąź 3.13, nie konkretna łatka). Sprawdzenie: `python --version`.
  Ta sama gałąź w czterech miejscach: `.python-version`, `requires-python` w `pyproject.toml`,
  obraz Dockera `python:3.13-slim-trixie` (S-007) i CI `python-version: "3.13"` (S-004).
- Zależności: **uv** (`pyproject.toml` + `uv.lock`). Nowa zależność: `uv add <pakiet>` (dev: `uv add --dev`).
  Komendy Pythona uruchamiaj przez `uv run`.
- Wymagane narzędzia: uv, make, Docker z Docker Compose.

| Komenda | Działanie |
| --- | --- |
| `make install` | `uv sync` i instalacja hooków pre-commit |
| `make up` / `make down` | start / stop PostgreSQL (od S-007 także backendu) w docker compose |
| `make test` | testy (pytest) |
| `make lint` | ruff check, ruff format --check, mypy (strict) |
| `make format` | formatowanie i automatyczne poprawki ruff |

- Konfiguracja tylko z `.env`; wzór zmiennych w `.env.example`.
- pre-commit uruchamia się przy każdym commicie (ruff, mypy, podstawowe hooki). Nie omijaj go `--no-verify`.
- CI (GitHub Actions, `.github/workflows/ci.yml`) uruchamia na każdym PR to samo: `make lint`, `make test` i hooki pre-commit.
  PR scalamy tylko z zielonym CI.

## Konwencje kodu

- Nazwy w kodzie **po angielsku**, zgodnie z **PEP 8**: `snake_case` dla zmiennych, funkcji i modułów,
  `PascalCase` dla klas, `UPPER_CASE` dla stałych.
- **Po polsku**: komentarze, docstringi, `--help` w CLI, komunikaty dla użytkownika (bot, CLI).
- Typowanie wszędzie (mypy); modele danych w Pydantic.

## Konwencje bazy danych

- Wszystkie nazwy **małymi literami** (`snake_case`), bez cudzysłowów w SQL.
- Tabele: pełna angielska nazwa w liczbie mnogiej – `users`, `plans`. Rzeczowniki niepoliczalne
  w formie pojedynczej – `feedback`.
- Kolumny: `akronim_nazwa`, akronim tabeli zawsze 3 litery – `usr_id`, `usr_name`.
- Klucze obce: akronim tabeli, potem nazwa kolumny docelowej – `pln_usr_id` w tabeli `plans`.
- Akronim wybiera się przy tworzeniu tabeli i dopisuje do listy poniżej.
- Ta konwencja ma pierwszeństwo przed nazwami w opisach starszych story (np. `user_id`, `food_variant_id`) –
  dopasuj nazwy przy realizacji danej story.

| Tabela | Akronim |
| --- | --- |
| `users` | `usr` |
| `plans` | `pln` |

## Zasady danych

- **LLM nigdy nie podaje wartości odżywczych.** Wszystkie liczby (kcal, makro, IG, ŁG itd.) pochodzą z bazy
  i są liczone w kodzie.
- Przepis od LLM wskazuje tylko składniki z bazy (identyfikator wariantu produktu) i ich gramaturę (S-304);
  wszystko inne liczy backend.
- Każda wartość odżywcza ma **źródło** i flagę **`measured` / `calculated`**.
- Terminologia z `docs/glossary.md` (S-005): produkt podstawowy, składnik odżywczy, wariant obróbki.

## Sposób pracy

- Jedna story = jedna sesja = jeden branch `s-XXX-krotki-opis` = jeden PR do `main`.
- Start: `Zrealizuj backlog/S-XXX.md zgodnie z CLAUDE.md` – **najpierw plan**, implementacja po akceptacji Piotra.
- Po realizacji: zaznacz spełnione kryteria w `backlog/S-XXX.md` i zaktualizuj status tam oraz w
  `backlog/README.md`. Kryteria typu „Piotr zatwierdził” zaznacza Piotr.
- Statusy: `todo` → `ready` → `in-progress` → `done`; `odłożone` = poza v1.
- Decyzje Piotra wpisuj do sekcji „Decyzje” w story, z datą.
- Commity i opisy PR po polsku.

## Czego nie robić

- Nie commituj `data/raw/`, `.env`, sekretów ani danych osobowych.
- Nie wpisuj kluczy API ani tokenów w kod – tylko `.env`.
- Nie łącz się z bazą z klientów API (bot, CLI, web) – tylko przez REST API.
- Nie generuj ani nie zgaduj wartości odżywczych modelem językowym.
- Nie zmieniaj decyzji zapisanych w backlogu bez pytania Piotra.
- Nie commituj bezpośrednio na `main`.
- Nie dodawaj zakresu spoza story – zapisz pomysł jako propozycję nowej story.
