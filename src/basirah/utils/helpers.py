"""دوال مساعدة عامة."""

from pathlib import Path


def ensure_folder(path: str) -> None:
    """إنشاء مجلد إذا لزم الأمر.

    Args:
        path: مسار المجلد.
    """
    Path(path).mkdir(parents=True, exist_ok=True)
