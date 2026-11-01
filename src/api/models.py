from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, Text

from src.api.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(512), nullable=False)
    file_path = Column(String(1024), nullable=True)
    file_hash = Column(String(64), unique=True, index=True)
    category = Column(String(255), index=True)
    text = Column(Text)
    embedding = Column(Vector(384))
    created_at = Column(DateTime, default=datetime.utcnow)


class DocumentChunk(Base):
    """قسم مفهرس من وثيقة — وحدة البحث الدلالي للأسبوع 3 (chunking عربي).

    كل chunk يُضمَّن على حدة فيُحقّق ألا يخف استعلام قسم واحد من وثيقة طويلة
    خلف توزيع مواضيع بقية الوثيقة (تخفيف المتجه الواحد). الوثائق بلا chunks
    (أقدم من هذه النسخة) تبقى قابلة للبحث عبر مستوى الوثيقة.
    """

    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(
        Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    idx = Column(Integer, nullable=False, default=0)
    text = Column(Text, nullable=False)
    embedding = Column(Vector(384))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("ix_document_chunks_doc_idx", "document_id", "idx"),)
