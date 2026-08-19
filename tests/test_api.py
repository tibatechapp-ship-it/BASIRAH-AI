"""Tests for the BASIRAH AI FastAPI backend."""

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.database import Base, get_db
from src.api.main import app

TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


class FakeSentenceTransformer:
    def encode(self, text):
        import numpy as np
        return np.zeros(384, dtype=np.float32)


import src.api.routers.documents as docs_router
import src.api.routers.library as lib_router


def _fake_model():
    return FakeSentenceTransformer()


docs_router.get_embedding_model = _fake_model
lib_router.get_embedding_model = _fake_model


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_documents_empty():
    response = client.get("/documents/")
    assert response.status_code == 200
    assert response.json() == []


def test_upload_txt_document(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("الصلاة في الإسلام ركن عظيم", encoding="utf-8")
    with open(file_path, "rb") as f:
        response = client.post(
            "/documents/upload",
            files={"file": ("test.txt", f, "text/plain")},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.txt"
    assert data["category"] == "الفقه"


def test_search_documents(tmp_path):
    file_path = tmp_path / "search.txt"
    file_path.write_text("كيفية الوضوء قبل الصلاة", encoding="utf-8")
    with open(file_path, "rb") as f:
        client.post(
            "/documents/upload",
            files={"file": ("search.txt", f, "text/plain")},
        )
    response = client.get("/documents/search?q=الوضوء")
    assert response.status_code == 200
    results = response.json()
    assert len(results) >= 1
    assert results[0]["filename"] == "search.txt"
