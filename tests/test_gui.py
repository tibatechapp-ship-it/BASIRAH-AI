"""Tests for the BASIRAH AI GUI helpers."""

from pathlib import Path

from src.gui import _count_supported_files, _is_supported_file


def test_is_supported_file_accepts_supported_extensions(tmp_path: Path):
    for ext in (".pdf", ".txt", ".docx", ".PDF", ".TXT", ".DOCX"):
        file_path = tmp_path / f"book{ext}"
        file_path.write_text("x", encoding="utf-8")
        assert _is_supported_file(file_path) is True


def test_is_supported_file_rejects_unsupported_extensions(tmp_path: Path):
    file_path = tmp_path / "book.xyz"
    file_path.write_text("x", encoding="utf-8")
    assert _is_supported_file(file_path) is False


def test_count_supported_files_counts_recursively(tmp_path: Path):
    nested = tmp_path / "nested"
    nested.mkdir()
    (tmp_path / "a.txt").write_text("x", encoding="utf-8")
    (tmp_path / "b.pdf").write_text("x", encoding="utf-8")
    (nested / "c.docx").write_text("x", encoding="utf-8")
    (tmp_path / "d.png").write_text("x", encoding="utf-8")

    assert _count_supported_files(tmp_path) == 3
