# dAIet

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

Wymagania: Python 3.13, Docker z Docker Compose, Git, `make`.

```
git clone https://github.com/JustVector/daietAplha.git
cd daietAplha
cp .env.example .env    # uzupełnij wartości
make up                 # PostgreSQL (+ backend od S-007)
make test
```

> Pliki `.env.example`, `Makefile` i `docker-compose` dochodzą w [S-003](backlog/S-003.md),
> backend w [S-007](backlog/S-007.md). Do tego czasu powyższe komendy jeszcze nie działają.

## Licencja

Kod: GNU AGPL-3.0 ([`LICENSE`](LICENSE)); dane – osobna licencja ([`docs/data/licenses.md`](docs/data/licenses.md)).
