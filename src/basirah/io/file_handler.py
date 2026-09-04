"""قراءة النصوص من ملفات PDF و TXT و DOCX والصور (OCR)."""

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


def read_docx(file_path: str) -> str:
    """قراءة النص من ملف DOCX (Word).

    Args:
        file_path: مسار ملف DOCX.

    Returns:
        النص المستخرج أو سلسلة فارغة في حالة الخطأ.
    """
    try:
        from docx import Document

        if not Path(file_path).exists():
            logger.error(f"ملف DOCX غير موجود: {file_path}")
            return ""

        doc = Document(file_path)
        paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
        result = "\n".join(paragraphs)
        
        if len(result) > MAX_TEXT_CHARS:
            result = result[:MAX_TEXT_CHARS]
            logger.warning(f"تم قص النص إلى الحد الأقصى ({MAX_TEXT_CHARS} حرف).")
        
        logger.info(f"تم قراءة ملف DOCX بنجاح: {file_path}. عدد الأحرف: {len(result)}")
        return result
    
    except ImportError:
        logger.error("مكتبة python-docx غير مثبتة. قم بتثبيتها باستخدام: pip install python-docx")
        return ""
    except Exception as e:
        logger.error(f"حدث خطأ أثناء قراءة ملف DOCX {file_path}: {e}", exc_info=True)
        return ""


def read_image_ocr(image_path: str, lang: str = "ara+eng") -> str:
    """استخراج النص من صورة باستخدام OCR (Tesseract).

    Args:
        image_path: مسار ملف الصورة (PNG, JPG, JPEG, TIFF, BMP).
        lang: لغة OCR (افتراضي: 'ara+eng' للعربية والإنجليزية).

    Returns:
        النص المستخرج أو سلسلة فارغة في حالة الخطأ.
    """
    try:
        import pytesseract
        from PIL import Image

        if not Path(image_path).exists():
            logger.error(f"ملف الصورة غير موجود: {image_path}")
            return ""

        # فتح الصورة واستخراج النص
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img, lang=lang)
        
        # تطبيق الحد الأقصى للحجم
        if len(text) > MAX_TEXT_CHARS:
            text = text[:MAX_TEXT_CHARS]
            logger.warning(f"تم قص النص إلى الحد الأقصى ({MAX_TEXT_CHARS} حرف).")
        
        logger.info(f"تم استخراج النص من الصورة بنجاح: {image_path}. عدد الأحرف: {len(text)}")
        return text
    
    except ImportError as e:
        logger.error(f"مكتبة مطلوبة غير مثبتة: {e}. قم بتثبيت pytesseract و Pillow وتثبيت Tesseract على النظام.")
        return ""
    except Exception as e:
        logger.error(f"حدث خطأ أثناء استخراج النص من الصورة {image_path}: {e}", exc_info=True)
        return ""


def extract_text(file_path: str, encodings: Optional[List[str]] = None, ocr_lang: str = "ara+eng") -> str:
    """استخراج النص بناءً على امتداد الملف.

    Args:
        file_path: مسار الملف.
        encodings: قائمة الترميزات لقراءة ملفات النص.
        ocr_lang: لغة OCR لملفات الصور (افتراضي: 'ara+eng').

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
    elif ext == ".docx":
        return read_docx(file_path)
    elif ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".gif"]:
        return read_image_ocr(file_path, lang=ocr_lang)
    else:
        logger.warning(f"امتداد الملف غير مدعوم: {ext}")
        return ""
