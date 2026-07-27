"""BASIRAH AI v0.1 - simple digital library organizer."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Dict, List

MAX_TEXT_CHARS = 50_000

CATEGORIES: Dict[str, List[str]] = {
    "القرآن": ["تفسير", "أسباب النزول", "الآية", "السورة", "القراءات"],
    "العقيدة": ["العقيدة", "التوحيد", "الإيمان", "الأسماء والصفات"],
    "الفقه": ["الطهارة", "الصلاة", "الزكاة", "الصيام", "الحج", "البيع"],
    "السيرة": ["السيرة", "الغزوات", "الهجرة", "رسول الله"],
}


def read_pdf(pdf_path: str) -> str:
    """Read text from a PDF file with a size guard."""
    try:
        import fitz  # PyMuPDF

        text_parts: List[str] = []
        with fitz.open(pdf_path) as document:
            for page in document:
                text_parts.append(page.get_text())
                if sum(len(part) for part in text_parts) > MAX_TEXT_CHARS:
                    break
        return "".join(text_parts)
    except Exception:
        return ""


def read_txt(file_path: str) -> str:
    """Read UTF-8 text content from a .txt file."""
    try:
        return Path(file_path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def extract_text(file_path: str) -> str:
    """Extract text based on file extension."""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return read_pdf(file_path)
    if ext == ".txt":
        return read_txt(file_path)
    return ""


def classify(text: str) -> str:
    """Classify text into one known category using keyword frequency."""
    scores = {
        category: sum(text.count(keyword) for keyword in keywords)
        for category, keywords in CATEGORIES.items()
    }
    best_category = max(scores, key=scores.get)
    if scores[best_category] == 0:
        return "غير_مصنف"
    return best_category


def ensure_folder(path: str) -> None:
    """Create a folder if needed."""
    Path(path).mkdir(parents=True, exist_ok=True)


def move_file(source: str, target_folder: str) -> str:
    """Move file into folder with collision-safe rename. Returns destination path."""
    ensure_folder(target_folder)
    source_path = Path(source)
    destination = Path(target_folder) / source_path.name

    counter = 1
    while destination.exists():
        destination = Path(target_folder) / f"{source_path.stem}_{counter}{source_path.suffix}"
        counter += 1

    shutil.move(str(source_path), str(destination))
    return str(destination)


def organize_library(library_path: str) -> tuple[int, int]:
    """Organize supported files in a library path and return (total_files, classified_files)."""
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


if __name__ == "__main__":
    print("\nBASIRAH AI v0.1\n")
    library = input("أدخل مسار المكتبة: ").strip()
    total, classified = organize_library(library)
    print("\n" + "=" * 40)
    print("انتهى التصنيف")
    print("=" * 40)
    print(f"عدد الملفات: {total}")
    print(f"عدد الملفات المصنفة: {classified}")
