"""BASIRAH AI - منصة ذكية لفهرسة وتصنيف وتنظيم المكتبات الرقمية."""

from basirah.classification.classifier import classify
from basirah.io.file_handler import extract_text, read_pdf, read_txt
from basirah.io.mover import move_file
from basirah.organizer import organize_library

__version__ = "0.1.0"
__all__ = [
    "classify",
    "extract_text",
    "read_pdf",
    "read_txt",
    "move_file",
    "organize_library",
]
