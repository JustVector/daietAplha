# data-pipeline

Przygotowanie bazy żywności v1: pobranie surowych danych, przetworzenie, walidacja i eksport.

Etapy (backlog E1):
- pobranie USDA FoodData Central SR Legacy do `data/raw/` (S-006),
- import do tabeli szerokiej i wybór składników odżywczych (S-102, S-103),
- mapowanie listy produktów podstawowych, polskie nazwy, warianty obróbki, IG, tagi, miary (S-104 – S-109),
- walidacja i eksport bazy v1 (S-110, S-111).

Zasada: każda wartość odżywcza ma źródło i flagę `measured` / `calculated`.
Wynik eksportu ładuje do bazy backend (S-202).
