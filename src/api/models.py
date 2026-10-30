from __future__ import annotations

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, Integer, String, Text

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
