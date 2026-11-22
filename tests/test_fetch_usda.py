"""Testy fetch_usda.py – bez sieci, na małych plikach tworzonych w teście."""

import hashlib
import zipfile
from pathlib import Path

import fetch_usda
import pytest
from fetch_usda import (
    DataIntegrityError,
    extract_archive,
    fetch,
    read_env_file,
    read_manifest,
    verify_dir,
    write_manifest,
)

FILES = {"food.csv": b"id,name\n1,ziemniak\n", "nutrient.csv": b"id,name\n1,bialko\n"}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def manifest() -> dict[str, str]:
    return {name: _sha(data) for name, data in FILES.items()}


@pytest.fixture
def source_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "zrodlo"
    directory.mkdir()
    for name, data in FILES.items():
        (directory / name).write_bytes(data)
    return directory


def _make_zip(path: Path, members: dict[str, bytes]) -> Path:
    with zipfile.ZipFile(path, "w") as zf:
        for name, data in members.items():
            zf.writestr(name, data)
    return path


def test_manifest_roundtrip(tmp_path: Path, manifest: dict[str, str]) -> None:
    path = tmp_path / "sumy.sha256"
    write_manifest(path, manifest)
    assert read_manifest(path) == manifest


def test_verify_dir_reports_missing_and_mismatch(
    tmp_path: Path, source_dir: Path, manifest: dict[str, str]
) -> None:
    assert verify_dir(source_dir, manifest) == []
    (source_dir / "food.csv").write_bytes(b"zmienione")
    (source_dir / "nutrient.csv").unlink()
    assert verify_dir(source_dir, manifest) == [
        "niezgodna suma SHA-256: food.csv",
        "brak pliku: nutrient.csv",
    ]


def test_fetch_copies_from_local_source(
    tmp_path: Path, source_dir: Path, manifest: dict[str, str]
) -> None:
    dest = tmp_path / "raw"
    action = fetch(dest, manifest, source_dir)
    assert "katalogu lokalnego" in action
    assert verify_dir(dest, manifest) == []


def test_fetch_skips_when_data_is_current(
    tmp_path: Path, source_dir: Path, manifest: dict[str, str]
) -> None:
    assert fetch(source_dir, manifest, source=None) == "dane są aktualne – nic do zrobienia"


def test_fetch_rejects_corrupted_local_copy(
    tmp_path: Path, source_dir: Path, manifest: dict[str, str]
) -> None:
    (source_dir / "food.csv").write_bytes(b"uszkodzone")
    with pytest.raises(DataIntegrityError, match="food.csv"):
        fetch(tmp_path / "raw", manifest, source_dir)


def test_fetch_downloads_and_extracts_archive(
    tmp_path: Path, manifest: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = _make_zip(tmp_path / "src.zip", {f"katalog/{n}": d for n, d in FILES.items()})

    def fake_download(url: str, target: Path) -> None:
        target.write_bytes(archive.read_bytes())

    monkeypatch.setattr(fetch_usda, "download", fake_download)
    dest = tmp_path / "raw"
    fetch(
        dest, manifest, None, archive_url="http://test", archive_sha256=_sha(archive.read_bytes())
    )
    assert verify_dir(dest, manifest) == []


def test_fetch_rejects_archive_with_wrong_checksum(
    tmp_path: Path, manifest: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(fetch_usda, "download", lambda url, target: target.write_bytes(b"x"))
    with pytest.raises(DataIntegrityError, match="archiwum"):
        fetch(tmp_path / "raw", manifest, None, archive_url="http://test", archive_sha256="0" * 64)


@pytest.mark.parametrize("bad_name", ["../poza.csv", "/abs/food.csv", "C:/food.csv"])
def test_extract_rejects_unsafe_paths(
    tmp_path: Path, manifest: dict[str, str], bad_name: str
) -> None:
    archive = _make_zip(tmp_path / "zly.zip", {**FILES, bad_name: b"x"})
    with pytest.raises(DataIntegrityError, match="niebezpieczna"):
        extract_archive(archive, tmp_path / "raw", manifest)
    assert not (tmp_path / "poza.csv").exists()


def test_read_env_file(tmp_path: Path) -> None:
    env = tmp_path / ".env"
    env.write_text('INNY=1\nUSDA_SOURCE_DIR="C:\\dane projektu"\n', encoding="utf-8")
    assert read_env_file(env, "USDA_SOURCE_DIR") == "C:\\dane projektu"
    assert read_env_file(env, "BRAK") is None
    assert read_env_file(tmp_path / "nie_ma", "USDA_SOURCE_DIR") is None
