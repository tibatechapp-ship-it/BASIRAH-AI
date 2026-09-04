"""BASIRAH AI - منصة ذكية لفهرسة وتصنيف وتنظيم المكتبات الرقمية."""

from basirah.classification.classifier import classify, TextClassifier
from basirah.io.file_handler import extract_text, read_pdf, read_txt
from basirah.io.mover import move_file
from basirah.organizer import organize_library
from basirah.utils.helpers import normalize_arabic_text

__version__ = "0.1.0"
__all__ = [
    "classify",
    "TextClassifier",
    "extract_text",
    "read_pdf",
    "read_txt",
    "move_file",
    "organize_library",
    "normalize_arabic_text",
]
