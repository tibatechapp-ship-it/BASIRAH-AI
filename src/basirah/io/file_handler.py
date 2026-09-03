"""قراءة النصوص من ملفات PDF و TXT."""

import logging
from pathlib import Path
from typing import List, Optional

from basirah.models.categories import MAX_TEXT_CHARS

# إعداد المسجل (Logger)
logger = logging.getLogger(__name__)


def read_pdf(pdf_path: str, encoding: str = "utf-8") -> str:
    """قراءة النص من ملف PDF مع حد أقصى للحجم.

    Args:
        pdf_path: مسار ملف PDF.
        encoding: الترميز المستخدم (افتراضي: utf-8).

    Returns:
        النص المستخرج أو سلسلة فارغة في حالة الخطأ.
    """
    try:
        import fitz  # PyMuPDF

        if not Path(pdf_path).exists():
            logger.error(f"ملف PDF غير موجود: {pdf_path}")
            return ""

        text_parts: List[str] = []
        with fitz.open(pdf_path) as document:
            for page in document:
                text_parts.append(page.get_text())
                if sum(len(part) for part in text_parts) > MAX_TEXT_CHARS:
                    logger.warning(f"تم تجاوز الحد الأقصى للنص ({MAX_TEXT_CHARS} حرف). تم إيقاف القراءة.")
                    break
        
        result = "".join(text_parts)
        logger.info(f"تم قراءة ملف PDF بنجاح: {pdf_path}. عدد الأحرف: {len(result)}")
        return result
    
    except ImportError:
        logger.error("مكتبة PyMuPDF غير مثبتة. قم بتثبيتها باستخدام: pip install PyMuPDF")
        return ""
    except Exception as e:
        logger.error(f"حدث خطأ أثناء قراءة ملف PDF {pdf_path}: {e}", exc_info=True)
        return ""


def read_txt(file_path: str, encodings: Optional[List[str]] = None) -> str:
    """قراءة محتوى نصي من ملف .txt مع دعم ترميزات متعددة.

    Args:
        file_path: مسار ملف النص.
        encodings: قائمة الترميزات للتجربة (افتراضي: ['utf-8', 'cp1256', 'iso-8859-6']).

    Returns:
        محتوى الملف أو سلسلة فارغة في حالة الخطأ.
    """
    if encodings is None:
        encodings = ['utf-8', 'cp1256', 'iso-8859-6']
    
    if not Path(file_path).exists():
        logger.error(f"ملف النص غير موجود: {file_path}")
        return ""
    
    for encoding in encodings:
        try:
            content = Path(file_path).read_text(encoding=encoding)
            logger.info(f"تم قراءة ملف النص بنجاح: {file_path} باستخدام ترميز {encoding}. عدد الأحرف: {len(content)}")
            return content
        except UnicodeDecodeError:
            logger.debug(f"فشل قراءة الملف بالترميز {encoding}, جرب الترميز التالي.")
            continue
        except Exception as e:
            logger.error(f"حدث خطأ أثناء قراءة ملف النص {file_path} بالترميز {encoding}: {e}", exc_info=True)
            continue
    
    logger.error(f"فشل قراءة الملف بجميع الترميزات المتاحة: {file_path}")
    return ""


def extract_text(file_path: str, encodings: Optional[List[str]] = None) -> str:
    """استخراج النص بناءً على امتداد الملف.

    Args:
        file_path: مسار الملف.
        encodings: قائمة الترميزات لقراءة ملفات النص.

    Returns:
        النص المستخرج أو سلسلة فارغة إذا كان الامتداد غير مدعوم.
    """
    ext = Path(file_path).suffix.lower()
    
    if not Path(file_path).exists():
        logger.error(f"الملف غير موجود: {file_path}")
        return ""
    
    if ext == ".pdf":
        return read_pdf(file_path)
    elif ext == ".txt":
        return read_txt(file_path, encodings=encodings)
    else:
        logger.warning(f"امتداد الملف غير مدعوم: {ext}")
        return ""
