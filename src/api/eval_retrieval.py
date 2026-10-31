"""Retrieval-quality evaluation — Week-1 milestone of the productization plan.

أول مقياس جودة استرجاع **معلن** في المحفظة: مجموعة ذهبية من 20 استعلاماً
عربياً على مدونات موثقة داخل المستودع، مع عتبتين تفشلان البناء تحت أي منهما:

- ``RECALL_AT_5_MIN = 0.70`` (نسبة الوثائق الملائمة داخل أفضل 5 نتائج)
- ``MRR_MIN = 0.50`` (متوسط مقلوب رتبة أول نتيجة ملائمة)

المسترجع الافتراضي هنا **معجمي** (تطبيع عربي + تقاطع رموز) — أساس حتمي
قابل للتكرار في CI بلا نموذج تدويم ولا pgvector، ويكفيه بايثون القياسي
(``PYTHONPATH=src python src/api/eval_retrieval.py …``). المسار الدلالي الحقيقي
(``build_db_retriever``) يلف نفس المقياس فوق بحث pgvector عندما يتوفر
PostgreSQL، فلا تتغير العتبات ولا المجموعة الذهبية.

الأمانة: هذا المقياس يقيس المسترجع الملفوف به فقط — لا يُنسب رقم معجمي
للبحث الدلالي ولا العكس، وكل تشغيل يطبع اسم المسترجع في الخرج.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

from basirah.utils.helpers import normalize_arabic_text

RECALL_AT_5_MIN = 0.70
MRR_MIN = 0.50
DEFAULT_K = 5

Tokenizer = Callable[[str], list[str]]
Retriever = Callable[[str, int], list[str]]  # (query, k) -> [doc_id مرتبة]


# ───────────────────────────── tokenization ─────────────────────────────

def _tokens(text: str) -> list[str]:
    """رموز عربية مطبعة — نفس دالة تطبيع المستودع + تقسيم على غير الحروف."""
    norm = normalize_arabic_text(text or "")
    out: list[str] = []
    for chunk in norm.split():
        word = "".join(ch for ch in chunk if ch.isalnum())
        if len(word) >= 2:          # رموز أقصر من حرفين ضجيج
            out.append(word)
    return out


def make_lexical_retriever(corpus: list[dict[str, Any]]) -> Retriever:
    """مسترجع معجمي حتمي: نسبة رموز الاستعلام الموجودة في الوثيقة."""
    doc_tokens = {d["id"]: set(_tokens(d.get("text", ""))) for d in corpus}
    doc_order = [d["id"] for d in corpus]

    def retrieve(query: str, k: int = DEFAULT_K) -> list[str]:
        q = set(_tokens(query))
        if not q:
            return []
        scored: list[tuple[float, str]] = []
        for doc_id in doc_order:
            overlap = len(q & doc_tokens[doc_id])
            scored.append((overlap / len(q), doc_id))
        scored.sort(key=lambda t: (-t[0], t[1]))
        return [doc_id for score, doc_id in scored if score > 0.0][:k]

    return retrieve


def build_db_retriever(db: Any) -> Retriever:
    """لفّ بحث pgvector الدلالي الحقيقي بنفس عقد المسترجع (يتطلب PostgreSQL)."""
    from src.api.models import Document
    from src.api.routers.documents import get_embedding_model

    model = get_embedding_model()

    def retrieve(query: str, k: int = DEFAULT_K) -> list[str]:
        rows = (
            db.query(Document)
            .filter(Document.embedding.isnot(None))
            .all()
        )
        scored: list[tuple[float, str]] = []
        qvec = model.encode(query).tolist()
        for d in rows:
            if d.embedding is None:
                continue
            distance = d.embedding.cosine_distance(qvec)
            scored.append((1 - float(distance), d.id))
        scored.sort(key=lambda t: (-t[0], t[1]))
        return [doc_id for _, doc_id in scored[:k]]

    return retrieve


# ───────────────────────────── metrics ─────────────────────────────

def evaluate(retriever: Retriever, golden: Iterable[dict[str, Any]],
             k: int = DEFAULT_K) -> dict[str, Any]:
    """Recall@k وMRR على المجموعة الذهبية — حساب حتمي قابل للاختبار يدوياً."""
    queries = list(golden)
    if not queries:
        return {"queries": 0, "recall_at_k": 0.0, "mrr": 0.0, "k": k}

    recalls: list[float] = []
    reciprocal_ranks: list[float] = []
    for item in queries:
        relevant = set(item["relevant"])
        ranked = retriever(item["q"], k)
        hits = relevant.intersection(ranked)
        recalls.append(len(hits) / len(relevant) if relevant else 0.0)
        rr = 0.0
        for rank, doc_id in enumerate(ranked, start=1):
            if doc_id in relevant:
                rr = 1.0 / rank
                break
        reciprocal_ranks.append(rr)

    recall = sum(recalls) / len(recalls)
    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)
    return {
        "queries": len(queries),
        "recall_at_k": round(recall, 4),
        "mrr": round(mrr, 4),
        "k": k,
    }


def passes(metrics: dict[str, Any]) -> bool:
    """العتبتان المعلنتان — أيهما فشلت فالبناء يفشل."""
    return (metrics["recall_at_k"] >= RECALL_AT_5_MIN
            and metrics["mrr"] >= MRR_MIN)


# ───────────────────────────── CLI ─────────────────────────────

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="مقياس جودة الاسترجاع — يفشل تحت العتبات المعلنة")
    parser.add_argument("--corpus", required=True, help="مسار corpus.json")
    parser.add_argument("--golden", required=True, help="مسار golden_set.json")
    parser.add_argument("--k", type=int, default=DEFAULT_K)
    args = parser.parse_args(argv)

    corpus = json.loads(Path(args.corpus).read_text(encoding="utf-8"))
    golden = json.loads(Path(args.golden).read_text(encoding="utf-8"))
    retriever = make_lexical_retriever(corpus)
    metrics = evaluate(retriever, golden, k=args.k)
    metrics["retriever"] = "lexical"
    metrics["recall_threshold"] = RECALL_AT_5_MIN
    metrics["mrr_threshold"] = MRR_MIN
    metrics["pass"] = passes(metrics)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    return 0 if metrics["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
