"""Odtwarza surowe dane USDA SR Legacy (2018-04) w data/raw/usda_sr_legacy/ (S-006).

Źródło plików (w tej kolejności):
1. katalog lokalny z opcji --source albo zmiennej USDA_SOURCE_DIR (środowisko lub plik .env),
2. oficjalne archiwum ZIP z serwera USDA.

Każdy plik jest sprawdzany sumą SHA-256 z manifestu data-pipeline/checksums/usda_sr_legacy.sha256,
więc obie drogi dają dokładnie te same dane.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from collections.abc import Sequence
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parent.parent
DEST_DIR = REPO_ROOT / "data" / "raw" / "usda_sr_legacy"
MANIFEST_PATH = Path(__file__).resolve().parent / "checksums" / "usda_sr_legacy.sha256"
ENV_FILE = REPO_ROOT / ".env"
SOURCE_ENV_VAR = "USDA_SOURCE_DIR"

ARCHIVE_URL = (
    "https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_csv_2018-04.zip"
)
ARCHIVE_SHA256 = "b80817294b8850530aaedf2e515c02593b1824f763a0ff356e5c2081643e6fd0"

_CHUNK = 1024 * 1024


class DataIntegrityError(Exception):
    """Dane nie zgadzają się z manifestem albo archiwum jest niebezpieczne."""


def sha256_file(path: Path) -> str:
    """Suma SHA-256 pliku (czytanie porcjami – food_nutrient.csv ma ~36 MB)."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(_CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def read_manifest(path: Path) -> dict[str, str]:
    """Czyta manifest w formacie sha256sum: `<suma>  <nazwa pliku>`; `#` zaczyna komentarz."""
    entries: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        digest, name = line.split(maxsplit=1)
        entries[name.lstrip("*")] = digest.lower()
    return entries


def write_manifest(path: Path, entries: dict[str, str]) -> None:
    """Zapisuje manifest posortowany po nazwie pliku, z nagłówkiem o źródle."""
    header = [
        "# USDA FoodData Central – SR Legacy (2018-04), CC0 1.0",
        f"# Źródło: {ARCHIVE_URL}",
        "# Generuje: uv run python data-pipeline/fetch_usda.py --update-checksums",
    ]
    lines = [f"{digest}  {name}" for name, digest in sorted(entries.items())]
    path.parent.mkdir(parents=True, exist_ok=True)
    # newline="\n": ten sam plik na Windows i Linuksie (format sha256sum)
    path.write_text("\n".join([*header, *lines]) + "\n", encoding="utf-8", newline="\n")


def verify_dir(directory: Path, manifest: dict[str, str]) -> list[str]:
    """Zwraca listę problemów (brakujące pliki, niezgodne sumy); pusta lista = dane poprawne."""
    problems: list[str] = []
    for name, expected in sorted(manifest.items()):
        path = directory / name
        if not path.is_file():
            problems.append(f"brak pliku: {name}")
        elif sha256_file(path) != expected:
            problems.append(f"niezgodna suma SHA-256: {name}")
    return problems


def copy_from_dir(source: Path, dest: Path, manifest: dict[str, str]) -> None:
    """Kopiuje pliki z manifestu z katalogu lokalnego; brak pliku przerywa kopiowanie."""
    missing = [name for name in manifest if not (source / name).is_file()]
    if missing:
        raise DataIntegrityError(
            f"w katalogu {source} brakuje plików: {', '.join(sorted(missing))}"
        )
    dest.mkdir(parents=True, exist_ok=True)
    for name in manifest:
        shutil.copy2(source / name, dest / name)


def extract_archive(archive: Path, dest: Path, manifest: dict[str, str]) -> None:
    """Rozpakowuje pliki z manifestu do `dest` (bez katalogu nadrzędnego z ZIP-a).

    Odrzuca archiwum ze ścieżkami bezwzględnymi lub z `..` (ochrona przed zip slip).
    """
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        members = [info for info in zf.infolist() if not info.is_dir()]
        for info in members:
            member = PurePosixPath(info.filename.replace("\\", "/"))
            if member.is_absolute() or ".." in member.parts or ":" in info.filename:
                raise DataIntegrityError(f"niebezpieczna ścieżka w archiwum: {info.filename}")
        by_name = {PurePosixPath(info.filename).name: info for info in members}
        missing = [name for name in manifest if name not in by_name]
        if missing:
            raise DataIntegrityError(f"w archiwum brakuje plików: {', '.join(sorted(missing))}")
        for name in manifest:
            with zf.open(by_name[name]) as src, (dest / name).open("wb") as dst:
                shutil.copyfileobj(src, dst, _CHUNK)


def download(url: str, target: Path) -> None:
    """Pobiera plik z sieci (certyfikaty z magazynu systemowego)."""
    with urllib.request.urlopen(url, timeout=120) as response, target.open("wb") as out:
        shutil.copyfileobj(response, out, _CHUNK)


def read_env_file(path: Path, key: str) -> str | None:
    """Odczytuje jedną zmienną `KLUCZ=wartość` z pliku .env (bez interpretacji reszty pliku)."""
    if not path.is_file():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        name, sep, value = line.partition("=")
        if sep and name.strip() == key:
            return value.strip().strip('"').strip("'") or None
    return None


def resolve_source(cli_value: str | None, env_file: Path) -> Path | None:
    """Katalog lokalny: --source, potem zmienna środowiskowa, potem plik .env."""
    value = cli_value or os.environ.get(SOURCE_ENV_VAR) or read_env_file(env_file, SOURCE_ENV_VAR)
    return Path(value) if value else None


def fetch(
    dest: Path,
    manifest: dict[str, str],
    source: Path | None,
    archive_url: str = ARCHIVE_URL,
    archive_sha256: str = ARCHIVE_SHA256,
) -> str:
    """Doprowadza `dest` do stanu zgodnego z manifestem. Zwraca opis wykonanej akcji."""
    if not verify_dir(dest, manifest):
        return "dane są aktualne – nic do zrobienia"
    if source is not None:
        copy_from_dir(source, dest, manifest)
        action = f"skopiowano z katalogu lokalnego {source}"
    else:
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "sr_legacy.zip"
            download(archive_url, archive)
            if sha256_file(archive) != archive_sha256:
                raise DataIntegrityError("niezgodna suma SHA-256 pobranego archiwum")
            extract_archive(archive, dest, manifest)
        action = f"pobrano i rozpakowano {archive_url}"
    problems = verify_dir(dest, manifest)
    if problems:
        raise DataIntegrityError("; ".join(problems))
    return action


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Odtwarza surowe dane USDA SR Legacy (2018-04) w data/raw/usda_sr_legacy/ "
            "i sprawdza sumy SHA-256."
        ),
    )
    parser.add_argument(
        "--source",
        help=(
            "katalog z lokalną kopią plików CSV (zamiast pobierania); "
            f"domyślnie zmienna {SOURCE_ENV_VAR} ze środowiska lub .env"
        ),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--verify",
        action="store_true",
        help="tylko sprawdź pliki w data/raw, bez kopiowania i sieci",
    )
    mode.add_argument(
        "--update-checksums",
        action="store_true",
        help="przepisz manifest sum z plików w data/raw (tylko przy świadomej zmianie danych)",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.update_checksums:
            files = (
                sorted(p for p in DEST_DIR.iterdir() if p.is_file()) if DEST_DIR.is_dir() else []
            )
            if not files:
                print(f"Błąd: brak plików w {DEST_DIR}", file=sys.stderr)
                return 1
            write_manifest(MANIFEST_PATH, {p.name: sha256_file(p) for p in files})
            print(f"Zapisano manifest: {MANIFEST_PATH} ({len(files)} plików)")
            return 0

        manifest = read_manifest(MANIFEST_PATH)
        if args.verify:
            problems = verify_dir(DEST_DIR, manifest)
            for problem in problems:
                print(f"Błąd: {problem}", file=sys.stderr)
            if not problems:
                print(f"OK: {len(manifest)} plików zgodnych z manifestem")
            return 1 if problems else 0

        action = fetch(DEST_DIR, manifest, resolve_source(args.source, ENV_FILE))
        print(f"OK: {action}; {len(manifest)} plików zgodnych z manifestem")
        return 0
    except (DataIntegrityError, OSError) as error:
        print(f"Błąd: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
