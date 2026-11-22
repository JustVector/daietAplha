# data

Dane lokalne projektu.

- `raw/` – surowe dane źródłowe (np. `raw/usda_sr_legacy/`). **Nie trafiają do git**
  (wpis w `.gitignore`); odtwarza je `make fetch-usda` z weryfikacją SHA-256 – opis źródła, wersji i licencji:
  [`data-pipeline/README.md`](../data-pipeline/README.md#dane-źródłowe-usda-s-006).

Nie commituj tu danych surowych ani niczego z danymi osobowymi.
