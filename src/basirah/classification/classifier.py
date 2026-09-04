"""مصنف النصوص بناءً على تكرار الكلمات المفتاحية."""

import logging
from typing import Dict, Tuple, List

from basirah.models.categories import CATEGORIES
from basirah.utils.helpers import normalize_arabic_text

# إعداد المسجل (Logger)
logger = logging.getLogger(__name__)


class TextClassifier:
    """مصنف النصوص العربية."""
    
    def __init__(self):
        """تهيئة المصنف."""
        self.categories = CATEGORIES
        logger.info("تم تهيئة مصنف النصوص")
    
    def classify(self, text: str, normalized: bool = True) -> Tuple[str, int]:
        """تصنيف النص إلى فئة معروفة.
        
        Args:
            text: النص المراد تصنيفه.
            normalized: ما إذا كان يجب تطبيع النص قبل التصنيف.
            
        Returns:
            tuple: (اسم الفئة، درجة التطابق).
        """
        return classify(text, normalized)
    
    def classify_with_details(self, text: str, normalized: bool = True) -> Dict:
        """تصنيف النص مع إرجاع تفاصيل كاملة.
        
        Args:
            text: النص المراد تصنيفه.
            normalized: ما إذا كان يجب تطبيع النص قبل التصنيف.
            
        Returns:
            dict: يحتوي على الفئة، الدرجة، وجميع الدرجات التفصيلية.
        """
        return classify_with_details(text, normalized)


def _normalize_keywords(keywords: List[str]) -> List[str]:
    """تطبيع قائمة الكلمات المفتاحية."""
    return [normalize_arabic_text(kw) for kw in keywords]


def classify(text: str, normalized: bool = True) -> Tuple[str, int]:
    """تصنيف النص إلى فئة معروفة باستخدام تكرار الكلمات المفتاحية.

    Args:
        text: النص المراد تصنيفه.
        normalized: ما إذا كان يجب تطبيع النص قبل التصنيف (افتراضي: True).

    Returns:
        tuple: (اسم الفئة أو 'غير_مصنف', درجة التطابق).
    """
    if not text or not isinstance(text, str):
        logger.warning("تم استلام نص فارغ أو غير صالح للتصنيف")
        return ("غير_مصنف", 0)
    
    try:
        # تطبيع النص إذا لزم الأمر
        if normalized:
            text = normalize_arabic_text(text)
            logger.debug("تم تطبيع النص قبل التصنيف")
        
        # حساب درجات كل فئة مع تطبيع الكلمات المفتاحية
        scores: Dict[str, int] = {}
        for category, keywords in CATEGORIES.items():
            normalized_keywords = _normalize_keywords(keywords) if normalized else keywords
            score = sum(text.count(keyword) for keyword in normalized_keywords)
            scores[category] = score
        
        # إيجاد أفضل فئة
        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]
        
        logger.info(f"نتائج التصنيف: {best_category} بدرجة {best_score}")
        logger.debug(f"جميع الدرجات: {scores}")
        
        if best_score == 0:
            logger.info("لم يتم العثور على أي تطابق للكلمات المفتاحية")
            return ("غير_مصنف", 0)
        
        return (best_category, best_score)
    
    except Exception as e:
        logger.error(f"حدث خطأ أثناء تصنيف النص: {e}", exc_info=True)
        return ("غير_مصنف", 0)


def classify_with_details(text: str, normalized: bool = True) -> Dict:
    """تصنيف النص مع إرجاع تفاصيل كاملة عن النتائج.

    Args:
        text: النص المراد تصنيفه.
        normalized: ما إذا كان يجب تطبيع النص قبل التصنيف.

    Returns:
        dict: يحتوي على الفئة، الدرجة، وجميع الدرجات التفصيلية.
    """
    category, score = classify(text, normalized)
    
    # إعادة حساب جميع الدرجات للعرض
    if normalized:
        text = normalize_arabic_text(text)
    
    all_scores: Dict[str, int] = {}
    for cat, keys in CATEGORIES.items():
        normalized_keys = _normalize_keywords(keys) if normalized else keys
        all_scores[cat] = sum(text.count(kw) for kw in normalized_keys)
    
    result = {
        "category": category,
        "score": score,
        "all_scores": all_scores,
        "is_classified": category != "غير_مصنف"
    }
    
    logger.debug(f"تفاصيل التصنيف: {result}")
    return result
