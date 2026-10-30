from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from basirah.classification import classify
from basirah.io import extract_text
from basirah.models.categories import CATEGORIES
from basirah.utils.helpers import file_hash

if TYPE_CHECKING:  # pragma: no cover
    from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=1)
def get_embedding_model() -> "SentenceTransformer":
    # الاستيراد المتأخر يمنع تحميل torch عند استيراد الوحدة (يُحمّل عند أول استخدام فعلي)
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


__all__ = [
    "get_embedding_model",
    "CATEGORIES",
    "classify",
    "extract_text",
    "file_hash",
]
