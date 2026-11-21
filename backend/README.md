# backend

REST API (FastAPI) na PostgreSQL, uruchamiane w Dockerze. Jedyne miejsce logiki i dostępu do danych –
bot Discord, CLI i przyszły WebApp są wyłącznie klientami tego API.

Zakres:
- szkielet, `GET /health`, konfiguracja z `.env` (S-007),
- schemat bazy produktów i loader CSV → DB (S-201, S-202),
- encje użytkownika, historia planów, oceny dań (S-203, S-206, S-308),
- silnik więzów, kalkulator przepisu, adapter Claude API (E3),
- planer na N dni i lista zakupów (S-401, S-402).

Zasada: LLM nigdy nie podaje wartości odżywczych – liczby pochodzą z bazy.
