"""وحدة توليد التقارير والإحصائيات المتقدمة."""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json

from basirah.models.categories import CategoryType

logger = logging.getLogger(__name__)


@dataclass
class FileStats:
    """إحصائيات ملف واحد."""
    file_path: str
    category: str
    confidence: float
    file_size_bytes: int
    word_count: int
    char_count: int
    classification_method: str


@dataclass
class CategoryStats:
    """إحصائيات فئة واحدة."""
    category_name: str
    file_count: int
    total_words: int
    total_chars: int
    avg_confidence: float
    files: List[str]


@dataclass
class LibraryReport:
    """تقرير شامل للمكتبة."""
    generated_at: str
    total_files: int
    classified_files: int
    unclassified_files: int
    total_words: int
    total_chars: int
    overall_avg_confidence: float
    categories: Dict[str, CategoryStats]
    file_details: List[FileStats]
    processing_time_seconds: float


class ReportGenerator:
    """مولد التقارير والإحصائيات المتقدمة."""

    def __init__(self):
        self.file_stats: List[FileStats] = []
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def start_processing(self) -> None:
        """بدء عملية المعالجة."""
        self.start_time = datetime.now()
        self.file_stats = []

    def add_file_stat(self, stat: FileStats) -> None:
        """إضافة إحصائيات ملف."""
        self.file_stats.append(stat)

    def end_processing(self) -> None:
        """إنهاء عملية المعالجة."""
        self.end_time = datetime.now()

    def _get_processing_time(self) -> float:
        """الحصول على وقت المعالجة بالثواني."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    def generate_category_stats(self) -> Dict[str, CategoryStats]:
        """توليد إحصائيات الفئات."""
        category_data: Dict[str, Dict[str, Any]] = {}

        for stat in self.file_stats:
            cat = stat.category
            if cat not in category_data:
                category_data[cat] = {
                    'files': [],
                    'total_words': 0,
                    'total_chars': 0,
                    'confidences': [],
                }
            
            category_data[cat]['files'].append(stat.file_path)
            category_data[cat]['total_words'] += stat.word_count
            category_data[cat]['total_chars'] += stat.char_count
            category_data[cat]['confidences'].append(stat.confidence)

        result: Dict[str, CategoryStats] = {}
        for cat_name, data in category_data.items():
            avg_conf = sum(data['confidences']) / len(data['confidences']) if data['confidences'] else 0.0
            result[cat_name] = CategoryStats(
                category_name=cat_name,
                file_count=len(data['files']),
                total_words=data['total_words'],
                total_chars=data['total_chars'],
                avg_confidence=avg_conf,
                files=[Path(f).name for f in data['files']],
            )

        return result

    def generate_report(self) -> LibraryReport:
        """توليد تقرير شامل للمكتبة."""
        category_stats = self.generate_category_stats()

        total_files = len(self.file_stats)
        classified_files = sum(1 for s in self.file_stats if s.category != CategoryType.UNSPECIFIED.value)
        unclassified_files = total_files - classified_files
        total_words = sum(s.word_count for s in self.file_stats)
        total_chars = sum(s.char_count for s in self.file_stats)
        
        confidences = [s.confidence for s in self.file_stats if s.is_classified]
        overall_avg_conf = sum(confidences) / len(confidences) if confidences else 0.0

        return LibraryReport(
            generated_at=datetime.now().isoformat(),
            total_files=total_files,
            classified_files=classified_files,
            unclassified_files=unclassified_files,
            total_words=total_words,
            total_chars=total_chars,
            overall_avg_confidence=overall_avg_conf,
            categories={k: asdict(v) for k, v in category_stats.items()},
            file_details=[asdict(f) for f in self.file_stats],
            processing_time_seconds=self._get_processing_time(),
        )

    def save_report_json(self, output_path: str) -> bool:
        """حفظ التقرير كملف JSON."""
        try:
            report = self.generate_report()
            report_dict = asdict(report)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, ensure_ascii=False, indent=2)
            
            logger.info(f"تم حفظ التقرير في: {output_path}")
            return True
        except Exception as e:
            logger.error(f"فشل حفظ التقرير JSON: {e}", exc_info=True)
            return False

    def save_report_text(self, output_path: str) -> bool:
        """حفظ التقرير كملف نصي."""
        try:
            report = self.generate_report()
            
            lines = [
                "=" * 60,
                "تقرير مكتبة BASIRAH-AI",
                "=" * 60,
                f"تاريخ التوليد: {report.generated_at}",
                f"وقت المعالجة: {report.processing_time_seconds:.2f} ثانية",
                "",
                "ملخص عام:",
                "-" * 40,
                f"إجمالي الملفات: {report.total_files}",
                f"الملفات المصنفة: {report.classified_files}",
                f"الملفات غير المصنفة: {report.unclassified_files}",
                f"إجمالي الكلمات: {report.total_words:,}",
                f"إجمالي الأحرف: {report.total_chars:,}",
                f"متوسط الثقة العام: {report.overall_avg_confidence:.2%}",
                "",
                "التفاصيل حسب الفئة:",
                "-" * 40,
            ]

            for cat_name, cat_data in report.categories.items():
                lines.extend([
                    f"\n{cat_name}:",
                    f"  عدد الملفات: {cat_data['file_count']}",
                    f"  إجمالي الكلمات: {cat_data['total_words']:,}",
                    f"  متوسط الثقة: {cat_data['avg_confidence']:.2%}",
                    f"  الملفات: {', '.join(cat_data['files'][:5])}" + 
                    (f" و{len(cat_data['files']) - 5} أخرى" if len(cat_data['files']) > 5 else ""),
                ])

            lines.extend([
                "",
                "=" * 60,
                "نهاية التقرير",
                "=" * 60,
            ])

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            
            logger.info(f"تم حفظ التقرير النصي في: {output_path}")
            return True
        except Exception as e:
            logger.error(f"فشل حفظ التقرير النصي: {e}", exc_info=True)
            return False

    def print_summary(self) -> None:
        """طباعة ملخص سريع للتقرير."""
        report = self.generate_report()
        
        print("\n" + "=" * 60)
        print("📊 ملخص مكتبة BASIRAH-AI")
        print("=" * 60)
        print(f"📁 إجمالي الملفات: {report.total_files}")
        print(f"✅ الملفات المصنفة: {report.classified_files} ({report.classified_files/max(report.total_files, 1)*100:.1f}%)")
        print(f"❌ الملفات غير المصنفة: {report.unclassified_files}")
        print(f"📝 إجمالي الكلمات: {report.total_words:,}")
        print(f"🔤 إجمالي الأحرف: {report.total_chars:,}")
        print(f"🎯 متوسط الثقة: {report.overall_avg_confidence:.2%}")
        print(f"⏱️ وقت المعالجة: {report.processing_time_seconds:.2f} ثانية")
        print("\n📂 التوزيع حسب الفئة:")
        
        for cat_name, cat_data in report.categories.items():
            emoji = "📖" if cat_name == "القرآن" else "🕌" if cat_name == "الحديث" else "⚖️" if cat_name == "الفقه" else "📜" if cat_name == "السيرة" else "💡" if cat_name == "العقيدة" else "❓"
            print(f"  {emoji} {cat_name}: {cat_data['file_count']} ملفات")
        
        print("=" * 60 + "\n")
