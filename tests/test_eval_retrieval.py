"""Tests for the retrieval-quality evaluation (Week-1 milestone).

المقياس الأول المعلن في المحفظة: مجموعة ذهبية (20 استعلاماً) + عتبتان
(CI يفشل تحت أي منهما). هذه الاختبارات تثبت: سلامة المجموعة، صحة حساب
المقاييس على مثال محسوب يدوياً، واستيفاء العتبات بالمسترجع المعجمي.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.api.eval_retrieval import (
    MRR_MIN,
    RECALL_AT_5_MIN,
    evaluate,
    make_lexical_retriever,
    passes,
)

EVAL_DIR = Path(__file__).resolve().parent / "eval"
CORPUS = json.loads((EVAL_DIR / "corpus.json").read_text(encoding="utf-8"))
GOLDEN = json.loads((EVAL_DIR / "golden_set.json").read_text(encoding="utf-8"))


# ───────────────────────── golden-set integrity ─────────────────────────

def test_golden_set_has_20_queries_with_valid_docs():
    assert len(GOLDEN) == 20
    corpus_ids = {d["id"] for d in CORPUS}
    assert len(corpus_ids) >= 20
    for item in GOLDEN:
        assert item["q"].strip()                       # استعلام غير فارغ
        assert item["relevant"], "كل استعلام يحتاج وثيقة ملائمة واحدة على الأقل"
        assert set(item["relevant"]) <= corpus_ids     # لا وثيقة وهمية


def test_golden_set_queries_are_arabic_and_distinct():
    queries = [item["q"] for item in GOLDEN]
    assert len(set(queries)) == 20                     # لا تكرار
    assert all(any("\u0600" <= ch <= "\u06FF" for ch in q) for q in queries)


# ───────────────────────── metric math (hand-computed) ─────────────────────────

def _fixed_retriever(order_by_query: dict[str, list[str]]):
    def retrieve(q: str, k: int = 5) -> list[str]:
        return order_by_query[q][:k]
    return retrieve


def test_evaluate_metrics_on_hand_computed_example():
    golden = [
        {"q": "أ", "relevant": ["d1", "d2"]},    # top5 hits both → recall 1.0, RR 1/1
        {"q": "ب", "relevant": ["d3"]},          # first hit at rank 3 → RR 1/3
        {"q": "ج", "relevant": ["d4"]},          # miss → recall 0, RR 0
    ]
    retriever = _fixed_retriever({
        "أ": ["d1", "d2", "x1", "x2", "x3"],
        "ب": ["x1", "x2", "d3", "x4", "x5"],
        "ج": ["x1", "x2", "x3", "x4", "x5"],
    })
    m = evaluate(retriever, golden, k=5)
    assert m["queries"] == 3
    # المقياس يقرّب لأربع منازل عمداً (round 4) — السماحية بنفس القدر
    assert m["recall_at_k"] == pytest.approx((1.0 + 1.0 + 0.0) / 3, abs=1e-4)
    assert m["mrr"] == pytest.approx((1.0 + 1.0 / 3 + 0.0) / 3, abs=1e-4)


def test_evaluate_respects_k_and_empty_golden():
    retriever = _fixed_retriever({"أ": ["d1", "d2", "d3"]})
    m = evaluate(retriever, [{"q": "أ", "relevant": ["d3"]}], k=1)
    assert m["recall_at_k"] == 0.0 and m["mrr"] == 0.0
    empty = evaluate(retriever, [])
    assert empty["queries"] == 0 and empty["recall_at_k"] == 0.0


def test_threshold_logic_boundaries():
    ok = {"recall_at_k": RECALL_AT_5_MIN, "mrr": MRR_MIN}
    assert passes(ok) is True                          # العتبة نفسها تجتاز (≥)
    assert passes({"recall_at_k": 0.69, "mrr": 0.9}) is False
    assert passes({"recall_at_k": 0.9, "mrr": 0.49}) is False


# ───────────────────────── the CI gate, double-checked ─────────────────────────

def test_lexical_retriever_meets_declared_thresholds():
    """بوابة CI نفسها — لو فشل هذا فالبناء يجب أن يفشل."""
    retriever = make_lexical_retriever(CORPUS)
    metrics = evaluate(retriever, GOLDEN, k=5)
    assert metrics["queries"] == 20
    assert metrics["recall_at_k"] >= RECALL_AT_5_MIN
    assert metrics["mrr"] >= MRR_MIN
    # ليس مثالياً بالمطلق — المقياس يشي بالضعف إن وُجد ولا يهندس النتيجة
    assert metrics["recall_at_k"] < 1.0 or metrics["mrr"] < 1.0


def test_lexical_retriever_ranks_truly_relevant_first():
    retriever = make_lexical_retriever(CORPUS)
    top = retriever("الوضوء وشروطه بالماء الطهور", 5)
    assert top[0] == "d02"
    top = retriever("خوارزميات الفرز السريع", 5)
    assert top[0] == "d19"
