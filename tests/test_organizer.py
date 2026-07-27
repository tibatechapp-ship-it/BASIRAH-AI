from pathlib import Path

from src.organizer import classify, move_file, organize_library


def test_classify_known_category():
    text = "الصلاة الصلاة الزكاة"
    assert classify(text) == "الفقه"


def test_classify_unknown_category():
    assert classify("hello world") == "غير_مصنف"


def test_move_file_handles_name_collision(tmp_path: Path):
    source1 = tmp_path / "a.txt"
    source2 = tmp_path / "a.txt.copy"
    source1.write_text("x", encoding="utf-8")
    source2.write_text("y", encoding="utf-8")

    target = tmp_path / "dest"
    first_dest = move_file(str(source1), str(target))

    second_named_source = tmp_path / "a.txt"
    second_named_source.write_text("z", encoding="utf-8")
    second_dest = move_file(str(second_named_source), str(target))

    assert first_dest != second_dest
    assert Path(first_dest).exists()
    assert Path(second_dest).exists()


def test_organize_library_moves_txt(tmp_path: Path):
    file_path = tmp_path / "book.txt"
    file_path.write_text("العقيدة والتوحيد", encoding="utf-8")

    total, classified = organize_library(str(tmp_path))

    assert total == 1
    assert classified == 1
    assert (tmp_path / "العقيدة" / "book.txt").exists()
