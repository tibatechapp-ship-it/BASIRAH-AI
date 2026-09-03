"""نقل الملفات مع معالجة التصادم في الأسماء."""

import logging
import shutil
from pathlib import Path

# إعداد المسجل (Logger)
logger = logging.getLogger(__name__)


def ensure_folder(path: str) -> None:
    """إنشاء مجلد إذا لزم الأمر.

    Args:
        path: مسار المجلد.
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        logger.debug(f"تم التحقق من المجلد أو إنشاؤه: {path}")
    except Exception as e:
        logger.error(f"فشل إنشاء المجلد {path}: {e}", exc_info=True)
        raise


def move_file(source: str, target_folder: str) -> str:
    """نقل ملف إلى مجلد مع إعادة تسمية آمنة في حالة التصادم.

    Args:
        source: مسار الملف المصدر.
        target_folder: مسار المجلد الهدف.

    Returns:
        المسار الجديد للملف المنقول.
        
    Raises:
        FileNotFoundError: إذا كان الملف المصدر غير موجود.
        Exception: في حالة فشل عملية النقل.
    """
    source_path = Path(source)
    
    if not source_path.exists():
        logger.error(f"الملف المصدر غير موجود: {source}")
        raise FileNotFoundError(f"الملف غير موجود: {source}")
    
    ensure_folder(target_folder)
    destination = Path(target_folder) / source_path.name

    counter = 1
    original_name = source_path.stem
    
    while destination.exists():
        destination = (
            Path(target_folder) / f"{original_name}_{counter}{source_path.suffix}"
        )
        counter += 1
        if counter > 1000:  # حد أقصى لتجنب الحلقات اللانهائية
            logger.error("تم تجاوز الحد الأقصى لمحاولات إعادة التسمية")
            raise Exception("فشل إنشاء اسم فريد للملف")

    try:
        shutil.move(str(source_path), str(destination))
        logger.info(f"تم نقل الملف من {source} إلى {destination}")
        return str(destination)
    except Exception as e:
        logger.error(f"فشل نقل الملف من {source} إلى {destination}: {e}", exc_info=True)
        raise
