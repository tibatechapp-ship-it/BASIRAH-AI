"""مصنف النصوص بناءً على تكرار الكلمات المفتاحية والقواعد الثابتة."""

import logging
from typing import Dict, Tuple, List, Optional

from basirah.models.categories import (
    CATEGORIES, 
    CategoryType, 
    ClassificationResult,
    MIN_CONFIDENCE_THRESHOLD
)
from basirah.utils.helpers import normalize_arabic_text
from basirah.rules.fixed_rules import check_fixed_rules

# إعداد المسجل (Logger)
logger = logging.getLogger(__name__)


class TextClassifier:
    """مصنف النصوص العربية الهجين (قواعد ثابتة + كلمات مفتاحية)."""
    
    def __init__(self, use_fixed_rules: bool = True, min_confidence: float = MIN_CONFIDENCE_THRESHOLD):
        """تهيئة المصنف.
        
        Args:
            use_fixed_rules: استخدام القواعد الثابتة للتحقق الأولي (افتراضي: True).
            min_confidence: الحد الأدنى للدرجة لتصنيف النص (افتراضي: 0.1).
        """
        self.categories = CATEGORIES
        self.use_fixed_rules = use_fixed_rules
        self.min_confidence = min_confidence
        logger.info(f"تم تهيئة مصنف النصوص (استخدام القواعد الثابتة: {use_fixed_rules}, الحد الأدنى للثقة: {min_confidence})")
    
    def classify(self, text: str, normalized: bool = True) -> Tuple[str, float]:
        """تصنيف النص إلى فئة معروفة.
        
        Args:
            text: النص المراد تصنيفه.
            normalized: ما إذا كان يجب تطبيع النص قبل التصنيف.
            
        Returns:
            tuple: (اسم الفئة، درجة التطابق).
        """
        return classify(text, normalized, self.use_fixed_rules, self.min_confidence)
    
    def classify_with_details(self, text: str, normalized: bool = True) -> ClassificationResult:
        """تصنيف النص مع إرجاع تفاصيل كاملة.
        
        Args:
            text: النص المراد تصنيفه.
            normalized: ما إذا كان يجب تطبيع النص قبل التصنيف.
            
        Returns:
            dict: يحتوي على الفئة، الدرجة، وجميع الدرجات التفصيلية.
        """
        return classify_with_details(text, normalized, self.use_fixed_rules, self.min_confidence)


def _normalize_keywords(keywords: List[str]) -> List[str]:
    """تطبيع قائمة الكلمات المفتاحية."""
    return [normalize_arabic_text(kw) for kw in keywords]


def classify(
    text: str, 
    normalized: bool = True, 
    use_fixed_rules: bool = True,
    min_confidence: float = MIN_CONFIDENCE_THRESHOLD,
    return_details: bool = False,
) -> Tuple[str, float] | ClassificationResult:
    """تصنيف النص إلى فئة معروفة باستخدام القواعد الثابتة ثم الكلمات المفتاحية.
    
    الاستراتيجية:
    1. التحقق من القواعد الثابتة القطعية (دقة 100%).
    2. إذا لم تطبق القواعد الثابتة، نستخدم طريقة الكلمات المفتاحية.

    Args:
        text: النص المراد تصنيفه.
        normalized: ما إذا كان يجب تطبيع النص قبل التصنيف (افتراضي: True).
        use_fixed_rules: استخدام القواعد الثابتة أولاً (افتراضي: True).
        min_confidence: الحد الأدنى للدرجة لتصنيف النص (افتراضي: 0.1).
        return_details: إرجاع تفاصيل كاملة بدلاً من مجرد الفئة والدرجة (افتراضي: False).

    Returns:
        tuple أو dict: 
            - إذا كانت return_details=False: (اسم الفئة أو 'غير_مصنف', درجة التطابق).
            - إذا كانت return_details=True: dict يحتوي على التفاصيل الكاملة.
            الدرجة تكون 1.0 للقواعد الثابتة، أو عدد التطابقات للكلمات المفتاحية.
    """
    if return_details:
        return classify_with_details(text, normalized, use_fixed_rules, min_confidence)
    
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
        scores: Dict[CategoryType, int] = {}
        for category, keywords in CATEGORIES.items():
            normalized_keywords = _normalize_keywords(keywords) if normalized else keywords
            score = sum(text.count(keyword) for keyword in normalized_keywords)
            scores[category] = score
        
        # إيجاد أفضل فئة
        best_category = max(scores, key=scores.get)
        best_score = scores[best_category]
        
        logger.info(f"نتائج التصنيف بالكلمات المفتاحية: {best_category.value} بدرجة {best_score}")
        logger.debug(f"جميع الدرجات: {scores}")
        
        if best_score == 0:
            logger.info("لم يتم العثور على أي تطابق للكلمات المفتاحية")
            return ("غير_مصنف", 0.0)
        
        # التحقق من الحد الأدنى للثقة
        confidence_score = min(best_score / 10.0, 1.0)
        if confidence_score < min_confidence:
            logger.info(f"الدرجة {confidence_score} أقل من الحد الأدنى {min_confidence}")
            return ("غير_مصنف", confidence_score)
        
        return (best_category.value, confidence_score)
    
    except Exception as e:
        logger.error(f"حدث خطأ أثناء تصنيف النص: {e}", exc_info=True)
        return ("غير_مصنف", 0.0)


def classify_with_details(
    text: str, 
    normalized: bool = True, 
    use_fixed_rules: bool = True,
    min_confidence: float = MIN_CONFIDENCE_THRESHOLD
) -> ClassificationResult:
    """تصنيف النص مع إرجاع تفاصيل كاملة عن النتائج.

    Args:
        text: النص المراد تصنيفه.
        normalized: ما إذا كان يجب تطبيع النص قبل التصنيف.
        use_fixed_rules: استخدام القواعد الثابتة أولاً.
        min_confidence: الحد الأدنى للدرجة لتصنيف النص.

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
        
        result: ClassificationResult = {
            "category": category,
            "score": confidence,
            "all_scores": {cat.value: 0 for cat in CATEGORIES.keys()},
            "is_classified": True,
            "method": "fixed_rules",
            "explanations": explanations
        }
        logger.debug(f"تفاصيل التصنيف (قواعد ثابتة): {result}")
        return result
    
    # استخدام الكلمات المفتاحية
    category, score = classify(text, normalized, use_fixed_rules=False, min_confidence=min_confidence)
    
    # إعادة حساب جميع الدرجات للعرض
    if normalized:
        text = normalize_arabic_text(text)
    
    all_scores: Dict[CategoryType, int] = {}
    for cat, keys in CATEGORIES.items():
        normalized_keys = _normalize_keywords(keys) if normalized else keys
        all_scores[cat] = sum(text.count(kw) for kw in normalized_keys)
    
    result = {
        "category": category,
        "score": score,
        "all_scores": {cat.value: sc for cat, sc in all_scores.items()},
        "is_classified": category != "غير_مصنف",
        "method": "keywords",
        "explanations": []
    }
    
    logger.debug(f"تفاصيل التصنيف (كلمات مفتاحية): {result}")
    return result
