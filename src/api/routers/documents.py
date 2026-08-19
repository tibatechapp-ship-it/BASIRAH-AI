from __future__ import annotations

import tempfile
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from src.api.database import get_db
from src.api.dependencies import classify, extract_text, file_hash, get_embedding_model
from src.api.models import Document
from src.api.schemas import DocumentResponse, SearchResult

router = APIRouter(prefix="/documents", tags=["documents"])


def _truncate_text(text: str, max_chars: int = 50_000) -> str:
    return text[:max_chars]


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
    category = classify(text) if text else "غير_مصنف"
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
    model = get_embedding_model()
    query_embedding = model.encode(q).tolist()

    results = (
        db.query(
            Document.id,
            Document.filename,
            Document.category,
            Document.embedding.cosine_distance(query_embedding).label("distance"),
        )
        .filter(Document.embedding.isnot(None))
        .order_by("distance")
        .limit(limit)
        .all()
    )

    return [
        SearchResult(
            id=row.id,
            filename=row.filename,
            category=row.category,
            score=round(1 - float(row.distance), 4),
        )
        for row in results
    ]
