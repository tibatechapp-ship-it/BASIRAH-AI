"""
محرك القواعد الدينية الثابتة (Fixed Religious Rules Engine)
يحتوي على قواعد قطعية لتحديد نوع النص الديني بدقة 100% قبل اللجوء للتصنيف الاحتمالي.
"""
import re
import logging
from typing import Optional, Tuple, List

logger = logging.getLogger(__name__)

# أنماط قطعية للقرآن الكريم
QURAN_PATTERNS = [
    r'\bآية\s+\d+\b',  # آية 10
    r'\bسورة\s+\w+',  # سورة البقرة
    r'\(\d+:\d+\)',  # (2:185) تنسيق شائع للآية
    r'^\{\s*.*?\s*\}$',  # نص محاط بأقواس معقوفة { }
    r'بسم\s+الله\s+الرحمن\s+الرحيم',  # البسملة (بدون تشكيل)
    r'^بِسْمِ\s+اللَّهِ\s+الرَّحْمَٰنِ\s+الرَّحِيمِ',  # البسملة الكاملة (بتشكيل)
    r'\bقل\s+هو\s+الله\s+أحد',  # سورة الإخلاص
    r'\bالحمد\s+لله\s+رب\s+العالمين',  # الفاتحة
    r'\bالرحمن\s+الرحيم',  # من الفاتحة
]

# أنماط قطعية للحديث الشريف (أسانيد)
HADITH_PATTERNS = [
    r'\bحدثنا\s+',  # حدثنا فلان
    r'\bأخبرنا\s+',  # أخبرنا فلان
    r'\bحدّثني\s+',  # حدثني فلان
    r'\bقال\s+رسول\s+الله\s+(صلى الله عليه وسلم|ﷺ)',  # قال رسول الله...
    r'\bعن\s+\w+\s+عن\s+\w+\s+عن\s+',  # سلسلة رواة (عن X عن Y عن Z)
    r'\(صحيح\s+البخاري\)|\(صحيح\s+مسلم\)',  # تخريج صحيح
    r'\bرقم\s+الحديث\s+\d+',  # رقم الحديث
]

# أنماط قطعية للفقه (أبواب ومسائل)
FIQH_PATTERNS = [
    r'\bباب\s+\w+',  # باب الوضوء
    r'\bكتاب\s+\w+',  # كتاب الصلاة
    r'\bفصل\s+في\s+',  # فصل في الزكاة
    r'\bمسألة\s+:?',  # مسألة: كذا
    r'\bالقول\s+الراجح\s+',  # القول الراجح
    r'\bذهب\s+أبو\s+حنيفة\s+إلى\s+',  # نسب الأقوال للمذاهب
    r'\bذهب\s+مالك\s+إلى\s+',
    r'\bذهب\s+الشافعي\s+إلى\s+',
    r'\bذهب\s+أحمد\s+إلى\s+',
]

# أنماط قطعية للسيرة والتاريخ
SEERAH_PATTERNS = [
    r'\bغزوة\s+\w+',  # غزوة بدر
    r'\bمولد\s+النبي\s+',  # مولد النبي
    r'\bوفاة\s+\w+\s+سنة\s+\d+',  # وفاة فلان سنة كذا
    r'\bفي\s+عام\s+\d+\s+من\s+الهجرة',  # في عام كذا من الهجرة
    r'\bأسماء\s+الرجال\s+',  # أسماء الرجال (كتب التراجم)
    r'\bطبقات\s+',  # طبقات ابن سعد
]

# أنماط قطعية للعقيدة
AQEEDAH_PATTERNS = [
    r'\bأصول\s+الدين\s+',
    r'\bصفات\s+الله\s+',
    r'\bأسماء\s+الله\s+الحسنى',
    r'\bالإيمان\s+بالقدر',
    r'\bالشرك\s+الأكبر',
]


def check_fixed_rules(text: str) -> Optional[Tuple[str, float]]:
    """
    تفحص النص ضد القواعد الثابتة القطعية.
    
    Args:
        text: النص المراد فحصه.
        
    Returns:
        Tuple(category, confidence) إذا تطابقت قاعدة ثابتة.
        None إذا لم تتطابق أي قاعدة ثابتة (يجب اللجوء للتصنيف الاحتمالي).
        
    Confidence: 1.0 (100%) للقواعد القطعية.
    """
    if not text or len(text.strip()) < 5:
        return None

    # تنظيف بسيط للنص للفحص (إزالة مسافات زائدة فقط)
    clean_text = " ".join(text.split())

    rules_checks = [
        ("القرآن الكريم", QURAN_PATTERNS),
        ("الحديث الشريف", HADITH_PATTERNS),
        ("الفقه الإسلامي", FIQH_PATTERNS),
        ("السيرة والتاريخ", SEERAH_PATTERNS),
        ("العقيدة", AQEEDAH_PATTERNS),
    ]

    for category, patterns in rules_checks:
        for pattern in patterns:
            try:
                if re.search(pattern, clean_text, re.IGNORECASE | re.UNICODE):
                    logger.debug(f"تم تطبيق قاعدة ثابتة: '{pattern}' -> الفئة: {category}")
                    return (category, 1.0)  # دقة 100%
            except re.error as e:
                logger.error(f"خطأ في تعبير نمطي '{pattern}': {e}")
                continue

    return None


def get_rule_explanation(text: str) -> List[str]:
    """
    ترجع قائمة بالأسباب (القواعد) التي طابقت النص.
    مفيد للتوضيح للمستخدم لماذا تم تصنيف النص بهذه الطريقة.
    """
    explanations = []
    clean_text = " ".join(text.split())
    
    rules_map = {
        "القرآن الكريم": QURAN_PATTERNS,
        "الحديث الشريف": HADITH_PATTERNS,
        "الفقه الإسلامي": FIQH_PATTERNS,
        "السيرة والتاريخ": SEERAH_PATTERNS,
        "العقيدة": AQEEDAH_PATTERNS,
    }

    for category, patterns in rules_map.items():
        for pattern in patterns:
            if re.search(pattern, clean_text, re.IGNORECASE | re.UNICODE):
                explanations.append(f"وجود نمط '{pattern}' يشير إلى {category}")
    
    return explanations
