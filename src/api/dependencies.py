from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

from basirah.classification import classify
from basirah.io import extract_text
from basirah.models.categories import CATEGORIES
from basirah.utils.helpers import file_hash

if TYPE_CHECKING:  # pragma: no cover
    from sqlalchemy.orm import Session
    from sentence_transformers import SentenceTransformer

    from src.api.models import Document


@lru_cache(maxsize=1)
def get_embedding_model() -> "SentenceTransformer":
    # الاستيراد المتأخر يمنع تحميل torch عند استيراد الوحدة (يُحمّل عند أول استخدام فعلي)
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


def index_document_chunks(db: "Session", doc: "Document", text: str,
                          model: "SentenceTransformer") -> int:
    """فهرسة أقسام وثيقة (chunks) بتضمين مستقل لكل قسم — مسار الأسبوع 3.

    مشتركة بين مساري الإدخال (/documents/upload و/library/organize) حتى لا
    يختلف سلوك البحث الدلالي باختلاف باب الرفع. يرجع عدد الأقسام المفهرسة.
    **لا تلتزم شيئاً** — الالتزام قرار المستدعي (كله-أو-لاشيء مع وثيقتها).
    """
    from src.api.chunking import CHUNK_TARGET_CHARS, chunk_arabic_text
    from src.api.models import DocumentChunk

    parts = chunk_arabic_text(text, target_chars=CHUNK_TARGET_CHARS)
    count = 0
    for i, part in enumerate(parts):
        emb = model.encode(part).tolist()
        db.add(DocumentChunk(document_id=doc.id, idx=i, text=part, embedding=emb))
        count += 1
    return count


__all__ = [
    "get_embedding_model",
    "index_document_chunks",
    "CATEGORIES",
    "classify",
    "extract_text",
    "file_hash",
]
