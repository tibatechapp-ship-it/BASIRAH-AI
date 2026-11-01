from __future__ import annotations

import math
import tempfile
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from src.api.database import get_db
from src.api.dependencies import (
    classify,
    extract_text,
    file_hash,
    get_embedding_model,
    index_document_chunks,
)
from src.api.models import Document, DocumentChunk
from src.api.schemas import DocumentResponse, SearchResult

router = APIRouter(prefix="/documents", tags=["documents"])

# مقتطف النتيجة المعروض في الاستجابة (حروف) — قراءة-فقط، لا يخزَّن
SNIPPET_CHARS = 160


def _truncate_text(text: str, max_chars: int = 50_000) -> str:
    return text[:max_chars]


def _cosine_distance(a: list[float] | None, b: list[float] | None) -> float | None:
    """نفس دلالة pgvector.cosine_distance (1 - التشابه الجيبي) بالبايثون.

    تُستخدم على المحركات التي لا تدعم عملية <=> (مثل SQLite في الاختبارات)
    بنفس صيغة PostgreSQL حرفياً، بما فيها حكم المتجه الصفري (تشابه = 0).
    """
    if a is None or b is None:
        return None
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0.0 or nb == 0.0:
        return 1.0
    return 1.0 - (dot / (na * nb))


@router.post("/upload", response_model=DocumentResponse)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = file.file.read()
        tmp.write(content)
        tmp_path = tmp.name

    hash_value = file_hash(tmp_path)
    existing = db.query(Document).filter(Document.file_hash == hash_value).first()
    if existing:
        Path(tmp_path).unlink(missing_ok=True)
        return existing

    text = _truncate_text(extract_text(tmp_path))
    category = classify(text)[0] if text else "غير_مصنف"
    model = get_embedding_model()
    embedding = model.encode(text).tolist() if text else None

    doc = Document(
        filename=file.filename,
        file_path=tmp_path,
        file_hash=hash_value,
        category=category,
        text=text,
        embedding=embedding,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # الأسبوع 3: فهرسة الأقسام (chunks) لتقوية البحث الدلالي — الفشل هنا
    # لا يفشل رفع الوثيقة (التراجع الآمن يجعل الوثيقة بلا أقسام فقط)
    try:
        if text:
            index_document_chunks(db, doc, text, model)
            db.commit()
    except Exception:
        db.rollback()  # الوثيقة محفوظة أصلاً — الأقسام فقط تتراجع

    return doc


@router.get("/", response_model=List[DocumentResponse])
def list_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return db.query(Document).offset(skip).limit(limit).all()


@router.get("/search", response_model=List[SearchResult])
def search_documents(
    q: str,
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """بحث دلالي مُجمَّع على مستوى الأقسام أولاً (الأسبوع 3).

    على PostgreSQL: أفضل chunk لكل وثيقة بترتيب أقرب مسافة جيبية، ثم
    استكمال الوثائق بلا أقسام بمستوى الوثيقة (توافق خلفي لما قبل v0.5).
    على بقية المحركات (SQLite في CI): نفس التقييم بالبايثون بنفس الصيغة —
    فلا تُختبر دلالة لم تُختبر، ولا يُختبر مسار لم يُنفَّذ.
    """
    model = get_embedding_model()
    query_embedding = model.encode(q).tolist()

    dialect = db.get_bind().dialect.name
    if dialect == "postgresql":
        return _search_postgres(db, query_embedding, limit)
    return _search_portable(db, query_embedding, limit)


def _search_postgres(db: Session, query_embedding: list[float],
                     limit: int) -> list[SearchResult]:
    chunk_rows = (
        db.query(
            DocumentChunk.document_id,
            DocumentChunk.idx,
            DocumentChunk.text,
            DocumentChunk.embedding.cosine_distance(query_embedding).label("distance"),
            Document.filename,
            Document.category,
        )
        .join(Document, DocumentChunk.document_id == Document.id)
        .filter(DocumentChunk.embedding.isnot(None))
        .order_by("distance")
        .all()
    )
    best: dict[int, dict] = {}
    for row in chunk_rows:
        if row.document_id in best:
            continue
        best[row.document_id] = {
            "distance": float(row.distance),
            "chunk_idx": row.idx,
            "snippet": (row.text or "")[:SNIPPET_CHARS],
            "filename": row.filename,
            "category": row.category,
        }
    # وثائق بلا أقسام (رفع سابق لـ v0.5): استكمال بمستوى الوثيقة
    covered = set(best)
    doc_rows = (
        db.query(Document)
        .filter(Document.embedding.isnot(None))
        .all()
    )
    for doc in doc_rows:
        if doc.id in covered:
            continue
        distance = doc.embedding.cosine_distance(query_embedding)
        best[doc.id] = {
            "distance": float(distance),
            "chunk_idx": None,
            "snippet": None,
            "filename": doc.filename,
            "category": doc.category,
        }
    ordered = sorted(best.items(), key=lambda kv: kv[1]["distance"])[:limit]
    return [
        SearchResult(
            id=doc_id,
            filename=info["filename"],
            category=info["category"],
            score=round(1 - info["distance"], 4),
            snippet=info["snippet"],
            chunk_idx=info["chunk_idx"],
        )
        for doc_id, info in ordered
    ]


def _search_portable(db: Session, query_embedding: list[float],
                     limit: int) -> list[SearchResult]:
    """نفس تجميع الأقسام حُساباً بالبايثون — يعمل على SQLite ويُختبر في CI."""
    docs = {d.id: d for d in db.query(Document).all()}
    scored: dict[int, dict] = {}
    for chunk in db.query(DocumentChunk).all():
        doc = docs.get(chunk.document_id)
        if doc is None:
            continue
        distance = _cosine_distance(chunk.embedding, query_embedding)
        if distance is None:
            continue
        current = scored.get(chunk.document_id)
        if current is None or distance < current["distance"]:
            scored[chunk.document_id] = {
                "distance": distance,
                "chunk_idx": chunk.idx,
                "snippet": (chunk.text or "")[:SNIPPET_CHARS],
            }
    for doc_id, doc in docs.items():
        if doc_id in scored:
            continue
        distance = _cosine_distance(doc.embedding, query_embedding)
        if distance is not None:
            scored[doc_id] = {
                "distance": distance,
                "chunk_idx": None,
                "snippet": None,
            }
    ordered = sorted(scored.items(), key=lambda kv: kv[1]["distance"])[:limit]
    return [
        SearchResult(
            id=doc_id,
            filename=docs[doc_id].filename,
            category=docs[doc_id].category,
            score=round(1 - info["distance"], 4),
            snippet=info["snippet"],
            chunk_idx=info["chunk_idx"],
        )
        for doc_id, info in ordered
    ]
