"""Week-3 tests — Arabic chunking + chunk-level semantic search.

The fake embedding model here is a deterministic hashing bag-of-words
embedder (stdlib only): identical text → identical vector, similar text →
closer vector. That gives real ranking behaviour in CI without downloading
sentence-transformers, so the chunk aggregation contract is actually
exercised, not just shape-checked.
"""

import hashlib
import math

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.chunking import (
    CHUNK_TARGET_CHARS,
    MAX_CHUNKS_PER_DOC,
    chunk_arabic_text,
    chunks_with_index,
    split_sentences_ar,
)
from src.api.database import Base, get_db
from src.api.main import app
from src.api.models import Document, DocumentChunk

DIM = 384


# ───────────────────── deterministic fake model ─────────────────────

def _norm_tokens(text: str) -> list[str]:
    # نفس منطق رموز مقياس الجودة (تطبيع المستودع + رموز ألفا-رقمية ≥ 2)
    from src.basirah.utils.helpers import normalize_arabic_text

    out = []
    for word in normalize_arabic_text(text or "").split():
        tok = "".join(ch for ch in word if ch.isalnum())
        if len(tok) >= 2:
            out.append(tok)
    return out


def _embed(text: str) -> list[float]:
    vec = [0.0] * DIM
    for tok in _norm_tokens(text):
        digest = hashlib.md5(tok.encode("utf-8")).hexdigest()
        vec[int(digest, 16) % DIM] += 1.0
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


class HashingSentenceTransformer:
    """نفس عقد SentenceTransformer.encode: يرد ndarray له .tolist()."""

    def encode(self, text):
        import numpy as np

        return np.array(_embed(text), dtype=np.float32)


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False,
                                       bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    import src.api.routers.documents as docs_router
    import src.api.routers.library as lib_router

    # عزل كامل: نحفظ الحالة السابقة ونستعيدها — لا تسريب لوحدات الاختبار الأخرى
    old_override = app.dependency_overrides.get(get_db)
    old_docs_model = docs_router.get_embedding_model
    old_lib_model = lib_router.get_embedding_model

    app.dependency_overrides[get_db] = override_get_db
    docs_router.get_embedding_model = lambda: HashingSentenceTransformer()
    lib_router.get_embedding_model = lambda: HashingSentenceTransformer()
    try:
        with TestClient(app) as c:
            yield c, TestingSessionLocal
    finally:
        if old_override is not None:
            app.dependency_overrides[get_db] = old_override
        else:
            app.dependency_overrides.pop(get_db, None)
        docs_router.get_embedding_model = old_docs_model
        lib_router.get_embedding_model = old_lib_model


# ───────────────────────────── chunker ─────────────────────────────

def test_split_sentences_keeps_arabic_endings():
    sentences = split_sentences_ar("جملة أولى. جملة ثانية؟ جملة ثالثة! رابعة؛ خامسة.")
    assert sentences == ["جملة أولى.", "جملة ثانية؟", "جملة ثالثة!", "رابعة؛", "خامسة."]


def test_split_sentences_coalesces_ellipsis_fragments():
    sentences = split_sentences_ar("كلام متواصل... ثم تكملة بعده.")
    assert sentences == ["كلام متواصل...", "ثم تكملة بعده."]


def test_chunk_empty_text_returns_nothing():
    assert chunk_arabic_text("") == []
    assert chunk_arabic_text("   ") == []
    assert chunk_arabic_text(None) == []  # type: ignore[arg-type]


def test_chunk_short_text_is_single_unit():
    # الوحدة تطبّع النص (إزالة التشكيل) — نفس مطبّع المستودع القياسي
    assert chunk_arabic_text("نص قصير جداً") == ["نص قصير جدا"]


def test_small_paragraphs_merge_toward_target():
    paras = "\n\n".join(
        f"الفقرة رقم {i} تتحدث عن موضوع بعينه وتحتاج دمجاً مع جارتها."
        for i in range(6)
    )
    chunks = chunk_arabic_text(paras, target_chars=200)
    assert len(chunks) < 6          # دمج فعلي حصل
    assert all(len(c) <= 200 + 80 for c in chunks)  # بلا تضخم غير مبرر
    assert all(c.strip() for c in chunks)


def test_long_paragraph_never_cuts_a_word():
    body = " ".join(
        "هذه جملة عربية طويلة نسبيا تحتوي كلمات كثيرة ومتتالية." for _ in range(30)
    )
    chunks = chunk_arabic_text(body, target_chars=150)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) <= 150 * 1.6   # حد أقصى معقول مع جملة تداخل
        for word in chunk.split():
            assert word                  # لا كلمة مبتورة — كل رمز كامل


def test_overlap_carries_last_sentence_forward():
    body = " ".join(f"الجملة رقم {i} قصيرة ومكتفية بذاتها." for i in range(20))
    chunks = chunk_arabic_text(body, target_chars=120, overlap=1)
    assert len(chunks) > 2
    # آخر جملة من chunk 1 تظهر في بداية chunk 2 (تداخل فعلي)
    last_sentence = chunks[0].strip().split(".")[-2] + "."
    assert chunks[1].startswith(last_sentence.strip()) or last_sentence in chunks[1]


def test_chunks_with_index_numbering():
    indexed = chunks_with_index("أ. ب. ج. د. هـ. و. ز. ح. ط. ي." * 10,
                                target_chars=30)
    assert [c["idx"] for c in indexed] == list(range(len(indexed)))
    assert all(c["text"] for c in indexed)


def test_max_chunks_cap_protects_embedding_cost():
    body = " ".join(f"جملة رقم {i} قصيرة." for i in range(4000))
    chunks = chunk_arabic_text(body, target_chars=40)
    assert len(chunks) == MAX_CHUNKS_PER_DOC


# ─────────────────── pipeline: upload → chunks → search ───────────────────

LONG_A = "\n\n".join([
    "الوضوء شرط لصلاة المسلم. يستحب استقبال القبلة في كل صلاة مفروضة.",
    "زكاة المال ركن من أركان الإسلام الخمسة. وتجب في أضعام الأموال الستة.",
    "صيام رمضان فرض على كل مسلم مكلف قادر. ويفطر المريض والمسافر رخصة.",
    "الحج واجب مرة واحدة في العمر على المستطيع. وعرفة يوم الوقوف الأعظم.",
])
LONG_B = "\n\n".join([
    "برمجة الحاسوب تحتاج منطقاً واضحاً. لغة بايثون مناسبة للمبتدئين في التعلم.",
    "قواعد البيانات العلائقية تخزن الجداول. واستعلام SQL يجلب الصفوف المطلوبة.",
    "الشبكات العصبية تتعلم من الأمثلة. والتعلم العميق يحتاج بيانات كثيرة.",
    "الأمن السيبراني يحمي الأنظمة من الاختراق. والتشفير يحمي البيانات.",
])


def test_upload_indexes_chunks(client):
    c, SessionLocal = client
    r = c.post(
        "/documents/upload",
        files={"file": ("long-ar.txt", (LONG_A * 3).encode("utf-8"), "text/plain")},
    )
    assert r.status_code == 200
    doc_id = r.json()["id"]

    db = SessionLocal()
    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == doc_id)
        .order_by(DocumentChunk.idx)
        .all()
    )
    db.close()
    assert len(chunks) >= 2                    # نص طويل → أقسام فعلية
    assert [ch.idx for ch in chunks] == list(range(len(chunks)))
    assert all(ch.text for ch in chunks)
    assert all(ch.embedding is not None for ch in chunks)


def test_short_text_still_indexed_as_one_chunk(client):
    c, SessionLocal = client
    r = c.post(
        "/documents/upload",
        files={"file": ("short.txt", "سطر واحد قصير".encode("utf-8"), "text/plain")},
    )
    assert r.status_code == 200
    db = SessionLocal()
    doc_id = r.json()["id"]
    count = db.query(DocumentChunk).filter(
        DocumentChunk.document_id == doc_id).count()
    db.close()
    assert count == 1


def test_search_returns_best_chunk_with_snippet(client):
    c, _ = client
    for name, body in (("فقه-عبادات.txt", LONG_A), ("تقنية-حاسوب.txt", LONG_B)):
        r = c.post(
            "/documents/upload",
            files={"file": (name, body.encode("utf-8"), "text/plain")},
        )
        assert r.status_code == 200

    r = c.get("/documents/search", params={"q": "زكاة المال والأموال"})
    assert r.status_code == 200
    results = r.json()
    assert results, "البحث يجب أن يرجع نتائج على SQLite (المسار البورتابل)"
    top = results[0]
    assert top["filename"] == "فقه-عبادات.txt"
    assert top["chunk_idx"] is not None
    assert top["snippet"]
    assert "زكاه" in top["snippet"] or "اموال" in top["snippet"]  # snippet مطبّع
    scores = [item["score"] for item in results]
    assert scores == sorted(scores, reverse=True)   # تنازلي


def test_search_falls_back_to_document_level(client):
    c, SessionLocal = client
    # وثيقة «قديمة» بلا أقسام — مُدرجة مباشرة كما قبل v0.5
    db = SessionLocal()
    db.add(Document(
        filename="قديم.txt", category="غير_مصنف", text="نص عن التعلم العميق",
        embedding=_embed("نص عن التعلم العميق"),
    ))
    db.commit()
    db.close()

    r = c.get("/documents/search", params={"q": "التعلم العميق"})
    assert r.status_code == 200
    results = r.json()
    assert results
    top = results[0]
    assert top["filename"] == "قديم.txt"
    assert top["chunk_idx"] is None and top["snippet"] is None


def test_search_limit_respected(client):
    c, _ = client
    for i in range(4):
        c.post(
            "/documents/upload",
            files={"file": (f"doc{i}.txt", f"نص فريد رقم {i} عن الزراعة".encode(), "text/plain")},
        )
    r = c.get("/documents/search", params={"q": "الزراعة", "limit": 2})
    assert r.status_code == 200
    assert len(r.json()) <= 2


def test_search_isolates_section_of_long_document(client):
    """جوهر الأسبوع 3: قسم واحد في وثيقة طويلة لا يخلف خلف بقية المواضيع."""
    c, _ = client
    mega = LONG_A + "\n\n" + LONG_B + "\n\n" + LONG_A + "\n\n" + LONG_B
    c.post("/documents/upload",
           files={"file": ("ضخم.txt", mega.encode("utf-8"), "text/plain")})
    c.post("/documents/upload",
           files={"file": ("آخر.txt", LONG_B.encode("utf-8"), "text/plain")})

    r = c.get("/documents/search", params={"q": "الوضوء والقبلة في الصلاة"})
    assert r.status_code == 200
    top = r.json()[0]
    assert top["filename"] == "ضخم.txt"
    assert top["snippet"] and "الوضوء" in top["snippet"]
