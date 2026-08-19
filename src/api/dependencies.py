from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer

from src.organizer import CATEGORIES, classify, extract_text, file_hash


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    return SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


__all__ = [
    "get_embedding_model",
    "CATEGORIES",
    "classify",
    "extract_text",
    "file_hash",
]
