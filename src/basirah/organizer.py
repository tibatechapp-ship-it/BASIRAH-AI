"""تنظيم الملفات في المكتبة الرقمية."""

import logging
from pathlib import Path
from typing import Tuple, Optional, List

from basirah.classification.classifier import classify
from basirah.io.file_handler import extract_text
from basirah.io.mover import move_file
from basirah.models.categories import SUPPORTED_EXTENSIONS

# إعداد المسجل (Logger)
logger = logging.getLogger(__name__)


def organize_library(
    library_path: str,
    encodings: Optional[List[str]] = None,
    normalize_text: bool = True
) -> Tuple[int, int]:
    """تنظيم الملفات المدعومة في مسار مكتبة.

    Args:
        library_path: مسار المكتبة المراد تنظيمها.
        encodings: قائمة الترميزات لقراءة ملفات النص.
        normalize_text: ما إذا كان يجب تطبيع النص قبل التصنيف.

    Returns:
        tuple: (إجمالي الملفات، عدد الملفات المصنفة).

    Raises:
        ValueError: إذا كان المسار غير صالح.
    """
    base = Path(library_path)
    
    if not base.exists():
        logger.error(f"المسار غير موجود: {library_path}")
        raise ValueError("المسار غير موجود")
    
    if not base.is_dir():
        logger.error(f"المسار ليس مجلداً: {library_path}")
        raise ValueError("المسار ليس مجلداً")
    
    logger.info(f"بدء تنظيم المكتبة: {library_path}")
    
    total_files = 0
    classified_files = 0

    for entry in base.iterdir():
        if not entry.is_file() or entry.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        total_files += 1
        logger.debug(f"معالجة الملف: {entry.name}")
        
        try:
            text = extract_text(str(entry), encodings=encodings)
            
            if not text:
                logger.warning(f"لم يتم استخراج أي نص من الملف: {entry.name}")
                continue
            
            category, score = classify(text, normalized=normalize_text)
            
            if category == "غير_مصنف":
                logger.warning(f"تعذر تصنيف الملف: {entry.name}")
                continue
            
            target_folder = base / category
            move_file(str(entry), str(target_folder))
            classified_files += 1
            logger.info(f"تم نقل الملف {entry.name} إلى {category} (الدرجة: {score})")
        
        except Exception as e:
            logger.error(f"حدث خطأ أثناء معالجة الملف {entry.name}: {e}", exc_info=True)
            continue

    logger.info(f"اكتمل التنظيم: {classified_files}/{total_files} ملف تم تصنيفه")
    return total_files, classified_files
