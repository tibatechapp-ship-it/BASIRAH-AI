"""المنظم الرئيسي للمكتبة."""

from pathlib import Path
from typing import Tuple

from basirah.classification.classifier import classify
from basirah.io.file_handler import extract_text
from basirah.io.mover import move_file


def organize_library(library_path: str) -> Tuple[int, int]:
    """تنظيم الملفات المدعومة في مسار مكتبة.

    Args:
        library_path: مسار المكتبة المراد تنظيمها.

    Returns:
        tuple: (إجمالي الملفات، عدد الملفات المصنفة).

    Raises:
        ValueError: إذا كان المسار غير صالح.
    """
    base = Path(library_path)
    if not base.exists() or not base.is_dir():
        raise ValueError("مسار المكتبة غير صالح")

    total_files = 0
    classified_files = 0

    for entry in base.iterdir():
        if not entry.is_file() or entry.suffix.lower() not in {".pdf", ".txt"}:
            continue

        total_files += 1
        text = extract_text(str(entry))
        category = classify(text)
        target_folder = base / category
        move_file(str(entry), str(target_folder))
        classified_files += 1

    return total_files, classified_files
