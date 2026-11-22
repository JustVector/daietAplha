# Ustawienia repozytorium GitHub

Repo: `JustVector/daietAplha` (publiczne). Ustawienia poniżej żyją na GitHubie, nie w git – ten plik
i [`.github/rulesets/main.json`](../.github/rulesets/main.json) opisują ich stan, żeby dało się je sprawdzić i odtworzyć.

## Ochrona `main` (S-008)

Ruleset **„main – ochrona”** (id 27844202), cel: gałąź domyślna, egzekwowanie: aktywne.
Włączony 2026-11-22.

| Reguła | Ustawienie | Po co |
| --- | --- | --- |
| Zmiany przez pull request | wymagane; 0 wymaganych zatwierdzeń | do `main` trafia tylko kod z PR; review nie jest wymagany, bo jest jedna osoba, a GitHub nie pozwala zatwierdzić własnego PR |
| Wymagany status check | `lint i testy` (GitHub Actions), branch aktualny względem `main` | scalenie tylko z zielonym CI na kodzie zgodnym z aktualnym `main` |
| Zakaz force push | włączony | historia `main` nie da się przepisać |
| Zakaz usunięcia | włączony | `main` nie da się skasować |
| Wyjątek (bypass) | rola Admin, tylko w PR | admin może świadomie scalić PR mimo czerwonego CI (opcja „bypass” przy scalaniu); push prosto na `main` jest zablokowany także dla admina |

Decyzje Piotra (2026-11-22): bez wymaganego review; wyjątek dla admina tylko w PR – patrz [S-008](../backlog/S-008.md).

Sprawdzone 2026-11-22:
- `git push origin HEAD:main` → `remote rejected … push declined due to repository rule violations`
  („Changes must be made through a pull request”, „Required status check "lint i testy" is expected”),
- PR z czerwonym CI ma stan „zablokowany” (`mergeStateStatus: BLOCKED`).

## Jak zmienić

**Przez stronę:** Settings → Rules → Rulesets → „main – ochrona”.

**Przez `gh`** (po zmianie zaktualizuj `main.json` w tym samym PR):

```
# podgląd reguł obowiązujących na main
gh api repos/JustVector/daietAplha/rules/branches/main

# zastosowanie zmian z pliku
gh api -X PUT repos/JustVector/daietAplha/rulesets/27844202 --input .github/rulesets/main.json

# odtworzenie od zera (np. po usunięciu rulesetu)
gh api -X POST repos/JustVector/daietAplha/rulesets --input .github/rulesets/main.json
```

Typowe zmiany:
- **Do repo dołącza druga osoba** – `required_approving_review_count` na 1, żeby każdy PR przechodził review.
- **Awaria CI blokuje pilną poprawkę** – scal PR z opcją „bypass” jako admin albo czasowo ustaw
  `enforcement` na `disabled`; po wszystkim przywróć `active`.
- **Zmiana nazwy joba CI** (`name:` w `.github/workflows/ci.yml`) – zmień też `context` w `main.json`,
  inaczej żaden PR nie będzie mógł zostać scalony.
