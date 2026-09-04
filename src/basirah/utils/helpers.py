"""دوال مساعدة عامة."""

import logging
import re
from pathlib import Path
from typing import Optional

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


def normalize_arabic_text(text: str) -> str:
    """
    تطبيع النص العربي لمعالجة الاختلافات في الكتابة.
    
    العمليات:
    - توحيد الألف (أ، إ، آ -> ا)
    - توحيد الياء والهاء (ى -> ي، ة -> ه)
    - إزالة التشكيل
    - إزالة المسافات الزائدة
    
    Args:
        text: النص المراد تطبيعه
        
    Returns:
        النص المطبع
    """
    if not text or not isinstance(text, str):
        logger.warning("تم استلام نص فارغ أو غير صالح للتطبيع")
        return ""
    
    try:
        normalized = text
        
        # توحيد الألف
        normalized = re.sub(r'[أإآ]', 'ا', normalized)
        
        # توحيد الياء
        normalized = re.sub(r'ى', 'ي', normalized)
        
        # توحيد التاء المربوطة والهاء
        normalized = re.sub(r'ة', 'ه', normalized)
        
        # إزالة التشكيل (الفتحة، الضمة، الكسرة، التنوين، إلخ)
        normalized = re.sub(r'[\u064B-\u065F]', '', normalized)
        
        # إزالة المسافات الزائدة
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        logger.debug(f"تم تطبيع النص بنجاح. الطول الأصلي: {len(text)}, الطول الجديد: {len(normalized)}")
        return normalized
        
    except Exception as e:
        logger.error(f"حدث خطأ أثناء تطبيع النص: {e}", exc_info=True)
        return text  # إرجاع النص الأصلي في حالة الفشل بدلاً من سلسلة فارغة

