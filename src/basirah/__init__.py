"""BASIRAH AI - منصة ذكية لفهرسة وتصنيف وتنظيم المكتبات الرقمية."""

from basirah.classification.classifier import classify, TextClassifier, classify_with_details
from basirah.io.file_handler import extract_text, read_pdf, read_txt
from basirah.io.mover import move_file
from basirah.organizer import organize_library
from basirah.utils.helpers import normalize_arabic_text
from basirah.rules.fixed_rules import check_fixed_rules, get_rule_explanation

__version__ = "0.2.0"
__all__ = [
    "classify",
    "classify_with_details",
    "TextClassifier",
    "extract_text",
    "read_pdf",
    "read_txt",
    "move_file",
    "organize_library",
    "normalize_arabic_text",
    "check_fixed_rules",
    "get_rule_explanation",
]
