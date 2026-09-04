"""قراءة النصوص من ملفات PDF و TXT و DOCX."""

import logging
from pathlib import Path
from typing import List, Optional

from basirah.models.categories import MAX_TEXT_CHARS, FileFormat

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


def read_docx(docx_path: str) -> str:
    """قراءة النص من ملف DOCX.

    Args:
        docx_path: مسار ملف DOCX.

    Returns:
        النص المستخرج أو سلسلة فارغة في حالة الخطأ.
    """
    try:
        from docx import Document

        if not Path(docx_path).exists():
            logger.error(f"ملف DOCX غير موجود: {docx_path}")
            return ""

        doc = Document(docx_path)
        text_parts: List[str] = [paragraph.text for paragraph in doc.paragraphs]
        result = "\n".join(text_parts)
        
        if len(result) > MAX_TEXT_CHARS:
            result = result[:MAX_TEXT_CHARS]
            logger.warning(f"تم قص النص إلى {MAX_TEXT_CHARS} حرف لملف DOCX: {docx_path}")
        
        logger.info(f"تم قراءة ملف DOCX بنجاح: {docx_path}. عدد الأحرف: {len(result)}")
        return result
    
    except ImportError:
        logger.error("مكتبة python-docx غير مثبتة. قم بتثبيتها باستخدام: pip install python-docx")
        return ""
    except Exception as e:
        logger.error(f"حدث خطأ أثناء قراءة ملف DOCX {docx_path}: {e}", exc_info=True)
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
    file_format = FileFormat.from_extension(ext)
    
    if not Path(file_path).exists():
        logger.error(f"الملف غير موجود: {file_path}")
        return ""
    
    if not file_format.is_supported:
        logger.warning(f"امتداد الملف غير مدعوم: {ext}")
        return ""
    
    if file_format == FileFormat.PDF:
        return read_pdf(file_path)
    elif file_format == FileFormat.TXT:
        return read_txt(file_path, encodings=encodings)
    elif file_format == FileFormat.DOCX:
        return read_docx(file_path)
    else:
        logger.warning(f"امتداد الملف غير مدعوم: {ext}")
        return ""
