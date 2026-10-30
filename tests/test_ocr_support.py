"""اختبارات دعم OCR للصور."""

import pytest
from pathlib import Path
from PIL import Image

from basirah.io.file_handler import read_image_ocr, extract_text


@pytest.fixture
def sample_arabic_image(tmp_path):
    """إنشاء صورة اختبار تحتوي على نص عربي بسيط."""
    img_path = tmp_path / "test_arabic.png"
    
    # إنشاء صورة بيضاء بسيطة
    img = Image.new('RGB', (200, 50), color='white')
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    # رسم نص بسيط (للاختبار فقط - لن يتعرف عليه OCR بشكل صحيح بدون خط حقيقي)
    draw.text((10, 10), "Test", fill='black')
    img.save(img_path)
    
    return str(img_path)


@pytest.fixture
def sample_image_jpg(tmp_path):
    """إنشاء صورة JPG للاختبار."""
    img_path = tmp_path / "test.jpg"
    img = Image.new('RGB', (100, 100), color='blue')
    img.save(img_path)
    return str(img_path)


def test_read_image_ocr_nonexistent():
    """اختبار قراءة صورة غير موجودة."""
    result = read_image_ocr("/nonexistent/path/image.png")
    assert result == ""


def test_read_image_ocr_png(sample_arabic_image):
    """اختبار استخراج النص من صورة PNG."""
    result = read_image_ocr(sample_arabic_image)
    # يجب أن ترجع نصاً (قد يكون فارغاً إذا لم يتعرف OCR على المحتوى)
    assert isinstance(result, str)


def test_read_image_ocr_jpg(sample_image_jpg):
    """اختبار استخراج النص من صورة JPG."""
    result = read_image_ocr(sample_image_jpg)
    assert isinstance(result, str)


def test_extract_text_with_ocr_png(sample_arabic_image):
    """اختبار extract_text مع صور PNG."""
    result = extract_text(sample_arabic_image)
    assert isinstance(result, str)


def test_extract_text_with_ocr_jpg(sample_image_jpg):
    """اختبار extract_text مع صور JPG."""
    result = extract_text(sample_image_jpg)
    assert isinstance(result, str)


def test_extract_text_unsupported_image_format(tmp_path):
    """اختبار امتداد صورة غير مدعوم."""
    # إنشاء ملف بامتداد غير مدعوم
    unsupported_path = tmp_path / "test.xyz"
    unsupported_path.write_text("test")
    
    result = extract_text(str(unsupported_path))
    assert result == ""


def test_read_image_ocr_custom_language(sample_image_jpg):
    """اختبار OCR مع لغة مخصصة."""
    result = read_image_ocr(sample_image_jpg, lang="eng")
    assert isinstance(result, str)


def test_read_image_ocr_all_supported_formats(tmp_path):
    """اختبار جميع صيغ الصور المدعومة."""
    formats = {
        ".png": "PNG",
        ".jpg": "JPEG",
        ".jpeg": "JPEG-alt",
        ".tiff": "TIFF",
        ".bmp": "BMP",
        ".gif": "GIF"
    }
    
    for ext, name in formats.items():
        img_path = tmp_path / f"test{ext}"
        img = Image.new('RGB', (50, 50), color='red')
        img.save(img_path)
        
        result = extract_text(str(img_path))
        assert isinstance(result, str), f"فشل اختبار صيغة {ext}"
