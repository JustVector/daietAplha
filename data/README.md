# data

Dane lokalne projektu.

- `raw/` – surowe dane źródłowe (np. `raw/usda_sr_legacy/`). **Nie trafiają do git**
  (wpis w `.gitignore`); odtwarza je skrypt `data-pipeline/fetch_usda.py` z weryfikacją SHA-256 (S-006).

Nie commituj tu danych surowych ani niczego z danymi osobowymi.
