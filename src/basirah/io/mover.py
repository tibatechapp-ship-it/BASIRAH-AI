"""نقل الملفات مع معالجة التصادم في الأسماء."""

import shutil
from pathlib import Path


def ensure_folder(path: str) -> None:
    """إنشاء مجلد إذا لزم الأمر.

    Args:
        path: مسار المجلد.
    """
    Path(path).mkdir(parents=True, exist_ok=True)


def move_file(source: str, target_folder: str) -> str:
    """نقل ملف إلى مجلد مع إعادة تسمية آمنة في حالة التصادم.

    Args:
        source: مسار الملف المصدر.
        target_folder: مسار المجلد الهدف.

    Returns:
        المسار الجديد للملف المنقول.
    """
    ensure_folder(target_folder)
    source_path = Path(source)
    destination = Path(target_folder) / source_path.name

    counter = 1
    while destination.exists():
        destination = (
            Path(target_folder) / f"{source_path.stem}_{counter}{source_path.suffix}"
        )
        counter += 1

    shutil.move(str(source_path), str(destination))
    return str(destination)
