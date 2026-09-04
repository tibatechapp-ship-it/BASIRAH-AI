"""نماذج التصنيف والثوابت."""

from typing import Dict, List, TypedDict, Optional
from enum import Enum


class CategoryType(str, Enum):
    """أنواع الفئات المعتمدة في النظام."""
    QURAN = "القرآن"
    AQEEDAH = "العقيدة"
    FIQH = "الفقه"
    SEERAH = "السيرة"
    HADITH = "الحديث"
    UNSPECIFIED = "غير_مصنف"


# حد أقصى لعدد الأحرف في النص للمعالجة
MAX_TEXT_CHARS: int = 50_000

# حد أدنى للدرجة لتصنيف النص كفئة معينة
MIN_CONFIDENCE_THRESHOLD: float = 0.1

# الكلمات المفتاحية مطبعة مسبقاً لتتناسب مع النص المطبع
CATEGORIES: Dict[CategoryType, List[str]] = {
    CategoryType.QURAN: ["تفسير", "اسباب النزول", "الاية", "السورة", "القراءات", "وحي", "تنزيل"],
    CategoryType.AQEEDAH: ["العقيدة", "التوحيد", "الايمان", "الاسماء والصفات", "القدر", "الشرك"],
    CategoryType.FIQH: ["الطهارة", "الصلاة", "الزكاة", "الصيام", "الحج", "البيع", "النكاح", "الحدود"],
    CategoryType.SEERAH: ["السيرة", "الغزوات", "الهجرة", "رسول الله", "الصحابة", "التراجم"],
    CategoryType.HADITH: ["الحديث", "الاسناد", "الرواية", "المتن", "الصحيح", "السنن"],
}

# فئات القواعد الثابتة
FIXED_RULE_CATEGORIES: Dict[str, CategoryType] = {
    "القرآن الكريم": CategoryType.QURAN,
    "الحديث الشريف": CategoryType.HADITH,
    "الفقه الإسلامي": CategoryType.FIQH,
    "السيرة والتاريخ": CategoryType.SEERAH,
    "العقيدة": CategoryType.AQEEDAH,
}


class ClassificationResult(TypedDict):
    """نتيجة عملية التصنيف."""
    category: str
    score: float
    all_scores: Dict[str, int]
    is_classified: bool
    method: str  # "fixed_rules" أو "keywords"
    explanations: List[str]


class FileFormat(str, Enum):
    """صيغ الملفات المدعومة."""
    PDF = ".pdf"
    TXT = ".txt"
    DOCX = ".docx"
    UNSUPPORTED = ""
    
    @classmethod
    def from_extension(cls, ext: str) -> 'FileFormat':
        """إنشاء FileFormat من امتداد الملف."""
        ext_lower = ext.lower()
        for fmt in cls:
            if fmt.value == ext_lower:
                return fmt
        return cls.UNSUPPORTED
    
    @property
    def is_supported(self) -> bool:
        """التحقق مما إذا كانت الصيغة مدعومة."""
        return self != self.UNSUPPORTED


SUPPORTED_EXTENSIONS: List[str] = [fmt.value for fmt in FileFormat if fmt.is_supported]
