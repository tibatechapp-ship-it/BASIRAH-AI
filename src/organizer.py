"""BASIRAH AI v0.1 - simple digital library organizer."""

from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Dict, List

MAX_TEXT_CHARS = 50_000


def normalize_arabic(text: str) -> str:
    """Normalize Arabic text for consistent matching."""
    text = re.sub(r"[\u064B-\u065F\u0670\u0640]", "", text)  # remove tashkeel & tatweel
    text = text.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
    text = text.replace("ة", "ه")  # unify taa marbuta
    text = text.replace("ى", "ي")  # unify alif maksura
    return text


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
        total_len = 0
        with fitz.open(pdf_path) as document:
            for page in document:
                part = page.get_text()
                text_parts.append(part)
                total_len += len(part)
                if total_len > MAX_TEXT_CHARS:
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
    normalized = normalize_arabic(text)
    scores = {
        category: sum(normalized.count(normalize_arabic(keyword)) for keyword in keywords)
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

    target_names = set(CATEGORIES.keys()) | {"غير_مصنف"}

    def _is_in_category_folder(path: Path) -> bool:
        return path.parent != base and path.parent.name in target_names

    entries = [
        entry for entry in base.rglob("*")
        if entry.is_file() and entry.suffix.lower() in {".pdf", ".txt"} and not _is_in_category_folder(entry)
    ]

    for entry in entries:
        total_files += 1
        text = extract_text(str(entry))
        category = classify(text)
        target_folder = base / category
        if entry.resolve().parent == target_folder.resolve():
            continue
        move_file(str(entry), str(target_folder))
        classified_files += 1

    return total_files, classified_files


if __name__ == "__main__":
    print("\nBASIRAH AI v0.1\n")
    library = input("أدخل مسار المكتبة: ").strip()
    try:
        total, classified = organize_library(library)
    except ValueError as exc:
        print(f"\nخطأ: {exc}")
        raise SystemExit(1) from exc
    print("\n" + "=" * 40)
    print("انتهى التصنيف")
    print("=" * 40)
    print(f"عدد الملفات: {total}")
    print(f"عدد الملفات المصنفة: {classified}")
