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
| `backend/` | REST API – pakiet `daiet-backend` (`src/daiet_backend/`), migracje Alembic, Dockerfile |
| `data-pipeline/` | import, mapowanie, walidacja i eksport bazy żywności |
| `data/raw/` | surowe dane źródłowe, poza git |
| `docs/` | ADR, słownik pojęć, licencje danych, specyfikacje |
| `backlog/` | stories (`S-XXX.md`) i tabela statusów (`README.md`) |
| `web/` | przyszły WebApp |

Diagram: `DietAi.drawio`.

## Środowisko i komendy

- Python **3.13** (gałąź 3.13, nie konkretna łatka). Sprawdzenie: `python --version`.
  Ta sama gałąź w czterech miejscach: `.python-version`, `requires-python` w `pyproject.toml`,
  obraz Dockera `python:3.13-slim-trixie` (`backend/Dockerfile`) i CI `python-version: "3.13"`.
- Zależności: **uv**, workspace z jednym `uv.lock`; członkowie: `backend/` (pakiet `daiet-backend`).
  Zależność backendu: `uv add --package daiet-backend <pakiet>`; narzędzia dev: `uv add --dev <pakiet>`.
  Komendy Pythona uruchamiaj przez `uv run`.
- Wymagane narzędzia: uv, make, Docker z Docker Compose.

| Komenda | Działanie |
| --- | --- |
| `make install` | `uv sync` i instalacja hooków pre-commit |
| `make up` / `make down` | start (z budowaniem obrazu) / stop bazy i backendu w docker compose |
| `make logs` / `make migrate` | logi backendu / migracje Alembic w kontenerze |
| `make run` | backend lokalnie z przeładowaniem kodu – http://localhost:8000/docs |
| `make test` | testy (pytest); test z bazą wymaga `make up` i `DATABASE_URL`, inaczej jest pomijany |
| `make lint` | ruff check, ruff format --check, mypy (strict) |
| `make format` | formatowanie i automatyczne poprawki ruff |
| `make fetch-usda` | surowe dane USDA do `data/raw/` z weryfikacją SHA-256 |

- Konfiguracja tylko z `.env`; wzór zmiennych w `.env.example`.
- pre-commit uruchamia się przy każdym commicie (ruff, mypy, podstawowe hooki). Nie omijaj go `--no-verify`.
- CI (GitHub Actions, `.github/workflows/ci.yml`) uruchamia na każdym PR to samo: `make lint`, `make test`
  (z PostgreSQL i `REQUIRE_DB=1`), hooki pre-commit i budowanie obrazu backendu.
  PR scalamy tylko z zielonym CI – wymusza to ruleset na `main` (push prosto na `main` jest odrzucany);
  opis i zmiana reguł: `docs/repo-settings.md`. Nie zmieniaj nazwy joba CI bez aktualizacji rulesetu.

## Konwencje kodu

- Nazwy w kodzie **po angielsku**, zgodnie z **PEP 8**: `snake_case` dla zmiennych, funkcji i modułów,
  `PascalCase` dla klas, `UPPER_CASE` dla stałych.
- **Po polsku**: komentarze, docstringi, `--help` w CLI, komunikaty dla użytkownika (bot, CLI).
- Typowanie wszędzie (mypy); modele danych w Pydantic.
- Backend: endpointy jako routery w `daiet_backend/api/`; błędy przez wyjątki FastAPI, nie własne odpowiedzi –
  format `{"detail", "error"}` nadaje `errors.py`. Logi przez `logging.getLogger(__name__)`, nie `print`.
- Zmiana schematu bazy = migracja Alembic w `backend/migrations/` w tym samym PR.

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
- Terminologia z `docs/glossary.md`: produkt podstawowy, wariant obróbki, składnik odżywczy i in.
  Nowe pojęcie dopisz do słownika w tym samym PR.
- Decyzje o bazie żywności (poziom danych, format, źródła): `docs/adr/0001-food-database.md`.

## Sposób pracy

- Jedna story = jedna sesja = jeden branch `s-XXX-krotki-opis` = jeden PR do `main`.
- Start: `Zrealizuj backlog/S-XXX.md zgodnie z CLAUDE.md` – **najpierw plan**, implementacja po akceptacji Piotra.
- Po realizacji: zaznacz spełnione kryteria w `backlog/S-XXX.md` i zaktualizuj status tam oraz w
  `backlog/README.md`. Kryteria typu „Piotr zatwierdził” zaznacza Piotr.
- Statusy: `todo` → `ready` → `in-progress` → `done`; `odłożone` = poza v1.
- Decyzje Piotra wpisuj do sekcji „Decyzje” w story, z datą.
- Decyzje architektoniczne zapisuj jako ADR w `docs/adr/` (szablon `0000-template.md`, kolejny numer).
- Commity i opisy PR po polsku.

## Czego nie robić

- Nie commituj `data/raw/`, `.env`, sekretów ani danych osobowych.
- Nie wpisuj kluczy API ani tokenów w kod – tylko `.env`.
- Nie łącz się z bazą z klientów API (bot, CLI, web) – tylko przez REST API.
- Nie publikuj portów w `docker-compose.yml` poza `127.0.0.1` – wystawienie usługi w sieci tylko po decyzji Piotra
  (repo jest publiczne, a domyślne hasła w nim jawne).
- Nie generuj ani nie zgaduj wartości odżywczych modelem językowym.
- Nie zmieniaj decyzji zapisanych w backlogu bez pytania Piotra.
- Nie commituj bezpośrednio na `main`.
- Nie dodawaj zakresu spoza story – zapisz pomysł jako propozycję nowej story.
