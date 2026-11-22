# dAIet

[![CI](https://github.com/JustVector/daietAplha/actions/workflows/ci.yml/badge.svg)](https://github.com/JustVector/daietAplha/actions/workflows/ci.yml)

Planer posiłków dla domu: układa plan na kilka dni i listę zakupów z przepisów generowanych przez LLM,
pilnując celów i ograniczeń żywieniowych domowników. Wartości odżywcze **zawsze pochodzą z bazy żywności**
(USDA SR Legacy + własne opracowanie), nigdy z modelu językowego – LLM proponuje przepis, a silnik więzów
go przelicza i weryfikuje.

## Architektura

- **PostgreSQL** – baza żywności, użytkownicy, zapisane plany.
- **backend** – REST API w FastAPI (Docker); cała logika, w tym silnik więzów i wywołania Claude API.
- **Klienci API** – bot Discord dla domowników, CLI dla insiderów, w przyszłości WebApp.

Diagram: [`DietAi.drawio`](DietAi.drawio).

## Struktura repozytorium

| Katalog | Zawartość |
| --- | --- |
| [`data-pipeline/`](data-pipeline/README.md) | Przygotowanie bazy żywności v1 (import, mapowanie, walidacja, eksport) |
| [`backend/`](backend/README.md) | REST API (FastAPI) |
| [`web/`](web/README.md) | Przyszły WebApp (E5) |
| [`docs/`](docs/README.md) | Dokumentacja, ADR, słownik pojęć, licencje danych |
| [`data/`](data/README.md) | Dane lokalne; `data/raw/` poza git |
| [`backlog/`](backlog/README.md) | Stories i roadmapa |

## Uruchomienie środowiska

Wymagania: Python 3.13, [uv](https://docs.astral.sh/uv/), `make`, Docker z Docker Compose, Git.
Na Windows: `winget install astral-sh.uv` i `winget install ezwinports.make`.

Pierwsze uruchomienie (w nowym katalogu, poza istniejącą kopią repo):

```
git clone https://github.com/JustVector/daietAplha.git
cd daietAplha
cp .env.example .env    # uzupełnij wartości
make install            # zależności (uv) i hooki pre-commit
make up                 # PostgreSQL (+ backend od S-007)
make test
```

Pozostałe komendy: `make lint`, `make format`, `make down`.

## Licencja

Kod: GNU AGPL-3.0 ([`LICENSE`](LICENSE)); dane – osobna licencja ([`docs/data/licenses.md`](docs/data/licenses.md)).
