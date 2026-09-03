"""مصنف النصوص بناءً على تكرار الكلمات المفتاحية."""

from typing import Dict

from basirah.models.categories import CATEGORIES


def classify(text: str) -> str:
    """تصنيف النص إلى فئة معروفة باستخدام تكرار الكلمات المفتاحية.

    Args:
        text: النص المراد تصنيفه.

    Returns:
        اسم الفئة أو 'غير_مصنف' إذا لم يتم العثور على تطابق.
    """
    scores: Dict[str, int] = {
        category: sum(text.count(keyword) for keyword in keywords)
        for category, keywords in CATEGORIES.items()
    }
    best_category = max(scores, key=scores.get)
    if scores[best_category] == 0:
        return "غير_مصنف"
    return best_category
