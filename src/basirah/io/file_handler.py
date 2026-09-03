"""قراءة النصوص من ملفات PDF و TXT."""

from pathlib import Path
from typing import List

from basirah.models.categories import MAX_TEXT_CHARS


def read_pdf(pdf_path: str) -> str:
    """قراءة النص من ملف PDF مع حد أقصى للحجم.

    Args:
        pdf_path: مسار ملف PDF.

    Returns:
        النص المستخرج أو سلسلة فارغة في حالة الخطأ.
    """
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
    """قراءة محتوى نصي UTF-8 من ملف .txt.

    Args:
        file_path: مسار ملف النص.

    Returns:
        محتوى الملف أو سلسلة فارغة في حالة الخطأ.
    """
    try:
        return Path(file_path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def extract_text(file_path: str) -> str:
    """استخراج النص بناءً على امتداد الملف.

    Args:
        file_path: مسار الملف.

    Returns:
        النص المستخرج أو سلسلة فارغة إذا كان الامتداد غير مدعوم.
    """
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return read_pdf(file_path)
    if ext == ".txt":
        return read_txt(file_path)
    return ""
