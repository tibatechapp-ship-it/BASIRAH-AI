"""مصنف النصوص بناءً على تكرار الكلمات المفتاحية والقواعد الثابتة."""

import logging
from typing import Dict, Tuple, List, Optional

from basirah.models.categories import CATEGORIES
from basirah.utils.helpers import normalize_arabic_text, count_keyword_matches
from basirah.rules.fixed_rules import check_fixed_rules

# إعداد المسجل (Logger)
logger = logging.getLogger(__name__)


class TextClassifier:
    """مصنف النصوص العربية الهجين (قواعد ثابتة + كلمات مفتاحية)."""
    
    def __init__(self, use_fixed_rules: bool = True):
        """تهيئة المصنف.
        
        Args:
            use_fixed_rules: استخدام القواعد الثابتة للتحقق الأولي (افتراضي: True).
        """
        self.categories = CATEGORIES
        self.use_fixed_rules = use_fixed_rules
        logger.info(f"تم تهيئة مصنف النصوص (استخدام القواعد الثابتة: {use_fixed_rules})")
    
    def classify(self, text: str, normalized: bool = True) -> Tuple[str, float]:
        """تصنيف النص إلى فئة معروفة.
        
        Args:
            text: النص المراد تصنيفه.
            normalized: ما إذا كان يجب تطبيع النص قبل التصنيف.
            
        Returns:
            tuple: (اسم الفئة، درجة التطابق).
        """
        return classify(text, normalized, self.use_fixed_rules)
    
    def classify_with_details(self, text: str, normalized: bool = True) -> Dict:
        """تصنيف النص مع إرجاع تفاصيل كاملة.
        
        Args:
            text: النص المراد تصنيفه.
            normalized: ما إذا كان يجب تطبيع النص قبل التصنيف.
            
        Returns:
            dict: يحتوي على الفئة، الدرجة، وجميع الدرجات التفصيلية.
        """
        return classify_with_details(text, normalized, self.use_fixed_rules)


def _normalize_keywords(keywords: List[str]) -> List[str]:
    """تطبيع قائمة الكلمات المفتاحية."""
    return [normalize_arabic_text(kw) for kw in keywords]


def classify(text: str, normalized: bool = True, use_fixed_rules: bool = True) -> Tuple[str, float]:
    """تصنيف النص إلى فئة معروفة باستخدام القواعد الثابتة ثم الكلمات المفتاحية.
    
    الاستراتيجية:
    1. التحقق من القواعد الثابتة القطعية (دقة 100%).
    2. إذا لم تطبق القواعد الثابتة، نستخدم طريقة الكلمات المفتاحية.

    Args:
        text: النص المراد تصنيفه.
        normalized: ما إذا كان يجب تطبيع النص قبل التصنيف (افتراضي: True).
        use_fixed_rules: استخدام القواعد الثابتة أولاً (افتراضي: True).

    Returns:
        tuple: (اسم الفئة أو 'غير_مصنف', درجة التطابق).
              الدرجة تكون 1.0 للقواعد الثابتة، أو عدد التطابقات للكلمات المفتاحية.
    """
    if not text or not isinstance(text, str):
        logger.warning("تم استلام نص فارغ أو غير صالح للتصنيف")
        return ("غير_مصنف", 0.0)
    
    try:
        # الخطوة 1: التحقق من القواعد الثابتة القطعية
        if use_fixed_rules:
            fixed_result = check_fixed_rules(text)
            if fixed_result:
                category, confidence = fixed_result
                logger.info(f"تم التصنيف بواسطة القواعد الثابتة: {category} (دقة: {confidence*100}%)")
                return (category, confidence)
            logger.debug("لم تطبق أي قاعدة ثابتة، جاري استخدام الكلمات المفتاحية")
        
        # الخطوة 2: استخدام طريقة الكلمات المفتاحية
        # تطبيع النص إذا لزم الأمر
        if normalized:
            text = normalize_arabic_text(text)
            logger.debug("تم تطبيع النص قبل التصنيف")
        
        # حساب درجات كل فئة مع تطبيع الكلمات المفتاحية
        scores: Dict[str, int] = {}
        for category, keywords in CATEGORIES.items():
            normalized_keywords = _normalize_keywords(keywords) if normalized else keywords
            score = count_keyword_matches(text, normalized_keywords)
            scores[category] = score
        
        # إيجاد أفضل فئة
        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]
        
        logger.info(f"نتائج التصنيف بالكلمات المفتاحية: {best_category} بدرجة {best_score}")
        logger.debug(f"جميع الدرجات: {scores}")
        
        if best_score == 0:
            logger.info("لم يتم العثور على أي تطابق للكلمات المفتاحية")
            return ("غير_مصنف", 0.0)
        
        # تحويل الدرجة إلى نسبة مئوية تقريبية للتوحيد
        # نفترض أن 10 تطابقات فأكثر تعطي دقة عالية
        confidence_score = min(best_score / 10.0, 1.0)
        
        return (best_category, confidence_score)
    
    except Exception as e:
        logger.error(f"حدث خطأ أثناء تصنيف النص: {e}", exc_info=True)
        return ("غير_مصنف", 0.0)


def classify_with_details(text: str, normalized: bool = True, use_fixed_rules: bool = True) -> Dict:
    """تصنيف النص مع إرجاع تفاصيل كاملة عن النتائج.

    Args:
        text: النص المراد تصنيفه.
        normalized: ما إذا كان يجب تطبيع النص قبل التصنيف.
        use_fixed_rules: استخدام القواعد الثابتة أولاً.

    Returns:
        dict: يحتوي على الفئة، الدرجة، وجميع الدرجات التفصيلية، ومنهجية التصنيف.
    """
    # التحقق من القواعد الثابتة أولاً
    fixed_result = None
    if use_fixed_rules:
        fixed_result = check_fixed_rules(text)
    
    if fixed_result:
        category, confidence = fixed_result
        explanations = []
        if use_fixed_rules:
            from basirah.rules.fixed_rules import get_rule_explanation
            explanations = get_rule_explanation(text)
        
        result = {
            "category": category,
            "score": confidence,
            "all_scores": {cat: 0 for cat in CATEGORIES.keys()},
            "is_classified": True,
            "method": "fixed_rules",
            "explanations": explanations
        }
        logger.debug(f"تفاصيل التصنيف (قواعد ثابتة): {result}")
        return result
    
    # استخدام الكلمات المفتاحية
    category, score = classify(text, normalized, use_fixed_rules=False)
    
    # إعادة حساب جميع الدرجات للعرض
    if normalized:
        text = normalize_arabic_text(text)
    
    all_scores: Dict[str, int] = {}
    for cat, keys in CATEGORIES.items():
        normalized_keys = _normalize_keywords(keys) if normalized else keys
        all_scores[cat] = count_keyword_matches(text, normalized_keys)
    
    result = {
        "category": category,
        "score": score,
        "all_scores": all_scores,
        "is_classified": category != "غير_مصنف",
        "method": "keywords",
        "explanations": []
    }
    
    logger.debug(f"تفاصيل التصنيف (كلمات مفتاحية): {result}")
    return result
