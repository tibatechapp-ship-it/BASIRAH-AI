"""لوحة البيانات الوصفية — مسارات 200 + بيانات + صفحة عربية بلا JS (أسبوع 2).

عقد الخطة: «اختبارات مسارات اللوحة (200 + بيانات) في CI الموجود» — والبحث
التفاعلي يعمل على أي محرك: دلالي إن توفر pgvector، وإلا مطابقة نصية معلنة.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.database import Base, get_db
from src.api.main import app
from src.api.models import Document

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
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


@pytest.fixture(autouse=True)
def clean_library():
    """StaticPool يحتفظ باتصال واحد — الحالة تتسرب بين الاختبارات إن لم تُمسح."""
    db = TestingSessionLocal()
    try:
        db.query(Document).delete()
        db.commit()
    finally:
        db.close()
    yield


class FakeSentenceTransformer:
    def encode(self, text):
        import numpy as np
        return np.zeros(384, dtype=np.float32)


import src.api.routers.documents as docs_router

docs_router.get_embedding_model = lambda: FakeSentenceTransformer()


def _upload(filename: str, text: str) -> None:
    import io
    r = client.post("/documents/upload",
                    files={"file": (filename, io.BytesIO(text.encode("utf-8")),
                                    "text/plain")})
    assert r.status_code == 200, r.text


@pytest.fixture()
def seeded():
    """مكتبة صغيرة معلومة: فقهيان + عقيدوي — الأرقام تُدقق عليها."""
    _upload("fiqh1.txt", "أحكام الصلاة والزكاة في الفقه الإسلامي")
    _upload("fiqh2.txt", "كتاب الصيام وأحكامه في الفقه")
    _upload("aqeedah1.txt", "العقيدة التوحيد ومعنى الايمان")


# ───────────────────── JSON ─────────────────────

def test_stats_empty_library_shape():
    r = client.get("/api/dashboard/stats")
    assert r.status_code == 200
    b = r.json()
    assert b["ok"] is True
    assert b["total_documents"] == 0
    assert b["by_category"] == {}
    assert b["semantic_coverage"] == 0.0


def test_stats_counts_and_distribution(seeded):
    b = client.get("/api/dashboard/stats").json()
    assert b["total_documents"] == 3
    assert b["by_category"] == {"الفقه": 2, "العقيدة": 1}
    assert b["docs_with_embedding"] == 3
    assert b["semantic_coverage"] == 1.0
    assert b["total_text_chars"] > 0
    assert len(b["latest"]) == 3
    assert {"filename", "category", "created_at"} <= set(b["latest"][0])


# ───────────────────── الصفحة ─────────────────────

def test_dashboard_page_renders_numbers(seeded):
    r = client.get("/dashboard")
    assert r.status_code == 200
    assert "html" in r.headers["content-type"]
    for label in ("الوثائق", "توزيع المواضيع", "بحث تفاعلي", "أحدث الوثائق"):
        assert label in r.text
    assert "الفقه" in r.text and "العقيدة" in r.text
    assert "<script" not in r.text.lower()      # قراءة-فقت: صفر JS


def test_dashboard_page_empty_state():
    r = client.get("/dashboard")
    assert r.status_code == 200
    assert "لا وثائق بعد" in r.text


def test_dashboard_escapes_filename(seeded, tmp_path):
    """اسم ملف خبيث لا يجتاز Escape إلى الصفحة."""
    _upload('<script>alert(1)</script>.txt', "نص سليم للتطفل")
    r = client.get("/dashboard")
    assert "<script>alert(1)</script>" not in r.text
    assert "&lt;script&gt;" in r.text


# ───────────────────── البحث التفاعلي ─────────────────────

def test_search_page_text_match_labeled_honestly(seeded):
    """على SQLite يغيب pgvector — فتُعلن «مطابقة نصية» بلا ادعاء دلالة."""
    r = client.get("/dashboard/search", params={"q": "الصلاة"})
    assert r.status_code == 200
    assert "مطابقة" in r.text
    assert "fiqh1" in r.text                     # نتيجة حقيقية بالاسم


def test_search_page_no_results_message(seeded):
    r = client.get("/dashboard/search", params={"q": "كلمة-غيتر-غير-موجودة-xyz"})
    assert r.status_code == 200
    assert "لا نتائج" in r.text


def test_search_page_empty_query_hint(seeded):
    r = client.get("/dashboard/search")
    assert r.status_code == 200
    assert "اكتب كلمة" in r.text


def test_search_results_escaped(seeded):
    _upload('xss-doc.txt', "نص للتطفل <script>alert(2)</script> داخل المحتوى")
    r = client.get("/dashboard/search", params={"q": "للتطفل"})
    assert "<script>alert(2)</script>" not in r.text
    assert "&lt;script&gt;" in r.text
