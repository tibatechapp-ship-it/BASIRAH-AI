from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class DocumentBase(BaseModel):
    filename: str
    category: str | None = None
    text: str | None = None


class DocumentCreate(DocumentBase):
    pass


class DocumentResponse(DocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_hash: str | None = None


class SearchResult(BaseModel):
    id: int
    filename: str
    category: str | None = None
    score: float
