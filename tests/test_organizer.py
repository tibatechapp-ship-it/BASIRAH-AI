from pathlib import Path

import pytest

from src.organizer import (
    classify,
    extract_text,
    file_hash,
    find_duplicates,
    move_file,
    organize_library,
)


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


def test_classify_normalizes_tashkeel_and_variant_forms():
    text = "التَّوْحِيدُ والإِيمَان"
    assert classify(text) == "العقيدة"


def test_organize_library_skips_files_already_in_target_category(tmp_path: Path):
    category_dir = tmp_path / "الفقه"
    category_dir.mkdir()
    file_path = category_dir / "book.txt"
    file_path.write_text("الصلاة", encoding="utf-8")

    total, classified = organize_library(str(tmp_path))

    assert total == 0
    assert classified == 0
    assert file_path.exists()


def test_organize_library_scans_recursively(tmp_path: Path):
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "book.txt").write_text("الصلاة والحج", encoding="utf-8")

    total, classified = organize_library(str(tmp_path))

    assert total == 1
    assert classified == 1
    assert (tmp_path / "الفقه" / "book.txt").exists()


def test_organize_library_respects_recursive_false(tmp_path: Path):
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "book.txt").write_text("الصلاة", encoding="utf-8")
    (tmp_path / "root.txt").write_text("الزكاة", encoding="utf-8")

    total, classified = organize_library(str(tmp_path), recursive=False)

    assert total == 1
    assert classified == 1
    assert (tmp_path / "الفقه" / "root.txt").exists()
    assert (nested / "book.txt").exists()


def test_file_hash_is_stable_and_distinguishes_content(tmp_path: Path):
    file_a = tmp_path / "a.txt"
    file_b = tmp_path / "b.txt"
    file_c = tmp_path / "c.txt"
    file_a.write_text("content", encoding="utf-8")
    file_b.write_text("content", encoding="utf-8")
    file_c.write_text("different", encoding="utf-8")

    hash_a = file_hash(str(file_a))
    hash_b = file_hash(str(file_b))
    hash_c = file_hash(str(file_c))

    assert hash_a == hash_b
    assert hash_a != hash_c


def test_find_duplicates_detects_duplicates(tmp_path: Path):
    (tmp_path / "file1.txt").write_text("same", encoding="utf-8")
    (tmp_path / "file2.txt").write_text("same", encoding="utf-8")
    (tmp_path / "file3.txt").write_text("unique", encoding="utf-8")

    duplicates = find_duplicates(str(tmp_path))

    assert len(duplicates) == 1
    duplicate_paths = list(duplicates.values())[0]
    assert len(duplicate_paths) == 2
    assert all("file1.txt" in path or "file2.txt" in path for path in duplicate_paths)


def test_extract_text_ignores_unsupported_extensions(tmp_path: Path):
    file_path = tmp_path / "book.xyz"
    file_path.write_text("الصلاة", encoding="utf-8")
    assert extract_text(str(file_path)) == ""
