from pathlib import Path

import pytest

from src.organizer import classify, move_file, organize_library


def test_classify_known_category():
    text = "الصلاة الصلاة الزكاة"
    assert classify(text) == "الفقه"


def test_classify_unknown_category():
    assert classify("hello world") == "غير_مصنف"


def test_move_file_handles_name_collision(tmp_path: Path):
    source_dir1 = tmp_path / "s1"
    source_dir2 = tmp_path / "s2"
    source_dir1.mkdir()
    source_dir2.mkdir()

    source1 = source_dir1 / "a.txt"
    source2 = source_dir2 / "a.txt"
    source1.write_text("x", encoding="utf-8")
    source2.write_text("y", encoding="utf-8")

    target = tmp_path / "dest"
    first_dest = Path(move_file(str(source1), str(target)))
    second_dest = Path(move_file(str(source2), str(target)))

    assert first_dest != second_dest
    assert first_dest.exists()
    assert second_dest.exists()
    assert first_dest.read_text(encoding="utf-8") == "x"
    assert second_dest.read_text(encoding="utf-8") == "y"
    assert not source1.exists()
    assert not source2.exists()


def test_organize_library_moves_txt(tmp_path: Path):
    file_path = tmp_path / "book.txt"
    file_path.write_text("العقيدة والتوحيد", encoding="utf-8")

    total, classified = organize_library(str(tmp_path))

    assert total == 1
    assert classified == 1
    assert (tmp_path / "العقيدة" / "book.txt").exists()


def test_organize_library_rejects_invalid_path(tmp_path: Path):
    invalid = tmp_path / "missing"
    with pytest.raises(ValueError):
        organize_library(str(invalid))
