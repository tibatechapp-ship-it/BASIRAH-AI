"""Chunking parameter sweep — Week-3 tuning evidence (stdlib only).

ثلاث قياسات حتمية قابلة للتكرار في CI:

1) لا انحدار: المسترجع المعجمي (مقياس CI القائم) على المجموعة الذهبية
   الأصلية بمستوى الـchunk بالمعاملات المختارة — العتبتان 0.70/0.50.
2) آلية التخفيف: 24 وثيقة مركّبة (كل وثيقة = موضوع واحد + 9 مواضيع مشتتة،
   ≈1300 حرف) مع تضمينات hashing قياسية (حقيبة-رموز مفهرسة، 384-بعداً،
   مسافة جيبية) — نفس دلالة البحث الدلالي حُساباً. مستوى الوثيقة يوزّع كتلة
   المتجه على 10 مواضيع فيضعف إشارة القسم الواحد؛ مستوى الـchunk يحفظ
   التركيز. Recall@5 هنا مميِّز فعلاً (24 مرشحاً لـ5 مواقع).
3) شبكة الضبط target × overlap على القياس (2)، والفوز الأكبر مع أقل كلفة.

الأمانة: تضمينات hashing ليست نموذج MiniLM الحقيقي — إنها بديل حتمي يثبت
الآلية قابلاً للتكرار في CI بلا تنزيلات؛ قياس النموذج الحقيقي يبقى محلياً
بـPostgreSQL (موثق في docs/chunking-tuning.md).

Usage: python scripts/tune_chunking.py [--json PATH]
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))       # سياق pytest من الجذر: حزمة src.
sys.path.insert(0, str(REPO / "src"))  # src/__init__ يستورد basirah مباشرة.

from src.api.chunking import chunk_arabic_text  # noqa: E402
from src.api.eval_retrieval import (  # noqa: E402
    DEFAULT_K,
    _tokens,
    evaluate,
    make_lexical_retriever,
)

DIM = 384
DOCS_PER_DOC = 10           # موضوع + 9 مشتتات في كل وثيقة مركّبة
TARGETS = (300, 400, 600, 800, 1200)
OVERLAPS = (0, 1, 2)


# ───────────────── تضمينات hashing حتمية (384 بعداً) ─────────────────

def _hash_embed(text: str) -> list[float]:
    vec = [0.0] * DIM
    for tok in _tokens(text):
        digest = hashlib.md5(tok.encode("utf-8")).hexdigest()
        vec[int(digest, 16) % DIM] += 1.0
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def _cosine_distance(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    return 1.0 - dot  # متجهان مطبّعان L2


def make_embedding_retriever(corpus, unit_texts):
    """مسترجع تضميني: unit_texts يحدد وحدة التضمين (وثيقة أو chunk)."""
    units = []  # (score_unit_index, doc_id)
    for doc_id, texts in unit_texts.items():
        for t in texts:
            units.append((_hash_embed(t), doc_id))

    def retrieve(query: str, k: int = DEFAULT_K) -> list[str]:
        qvec = _hash_embed(query)
        best: dict[str, float] = {}
        for vec, doc_id in units:
            d = _cosine_distance(vec, qvec)
            if doc_id not in best or d < best[doc_id]:
                best[doc_id] = d
        ranked = sorted(best.items(), key=lambda kv: (kv[1], kv[0]))
        return [doc_id for doc_id, _ in ranked[:k]]

    return retrieve


# ───────────────── الوثائق المركّبة: موضوع + مشتتات ─────────────────

def build_dilution_corpus(corpus):
    """longdoc_i = الوثيقة i + الوثائق التالية (i+1..i+9) دورياً بفواصل فصول.

    كل وثيقة مركّبة تحوي موضوعاً واحداً مطابقاً لاستعلام من المجموعة الذهبية
    وتسعة مواضيع مشتتة — نموذج مصغّر لوثيقة كتاب حقيقية متعددة الفصول.
    """
    n = len(corpus)
    longdocs = []
    owner = {}  # doc_id الأصلي -> longdoc الذي يحويه كموضوع رئيسي
    for i, d in enumerate(corpus):
        parts = [d.get("text", "").strip()]
        for j in range(1, DOCS_PER_DOC):
            parts.append(corpus[(i + j) % n].get("text", "").strip())
        lid = f"longdoc-{i + 1:02d}"
        longdocs.append({
            "id": lid, "filename": f"{lid}.txt", "category": "مركب",
            "text": "\n\n".join(f"الفصل {k + 1}: {p}" for k, p in enumerate(parts)),
        })
        owner[d["id"]] = lid
    return longdocs, owner


def fmt(metrics):
    return f"R@5={metrics['recall_at_k']:.3f} MRR={metrics['mrr']:.3f}"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="ضبط chunking — جداول حتمية")
    parser.add_argument("--corpus", default=str(REPO / "tests/eval/corpus.json"))
    parser.add_argument("--golden", default=str(REPO / "tests/eval/golden_set.json"))
    parser.add_argument("--json", default=None, help="مسار كتابة النتائج JSON")
    args = parser.parse_args(argv)

    corpus = json.loads(Path(args.corpus).read_text(encoding="utf-8"))
    golden = json.loads(Path(args.golden).read_text(encoding="utf-8"))

    # ── (1) المجموعة الذهبية الأصلية — لا انحدار على مقياس CI ──
    base_lex = evaluate(make_lexical_retriever(corpus), golden, k=DEFAULT_K)

    # ── (2) آلية التخفيف على الوثائق المركّبة ──
    longdocs, owner = build_dilution_corpus(corpus)
    long_golden = [
        {"q": item["q"], "relevant": [owner[d] for d in item["relevant"] if d in owner]}
        for item in golden if any(d in owner for d in item["relevant"])
    ]

    doc_units = {d["id"]: [d["text"]] for d in longdocs}
    doc_level = evaluate(make_embedding_retriever(longdocs, doc_units),
                         long_golden, k=DEFAULT_K)

    print("=" * 72)
    print(f"1) لا انحدار — المجموعة الذهبية الأصلية ({len(corpus)} وثيقة قصيرة)")
    print(f"   المعجمي بمستوى الوثيقة (خط CI الأساس): {fmt(base_lex)}")
    print()
    print(f"2) آلية التخفيف — {len(longdocs)} وثيقة مركّبة "
          f"({DOCS_PER_DOC} مواضيع/وثيقة، تضمينات hashing حتمية)")
    print(f"   مستوى الوثيقة (بلا chunking):      {fmt(doc_level)}")
    print()
    print("3) شبكة الضبط chunk-level على القياس نفسه")
    best = None
    rows = []
    for target, overlap in itertools.product(TARGETS, OVERLAPS):
        units = {
            d["id"]: chunk_arabic_text(d["text"], target_chars=target,
                                       overlap=overlap)
            for d in longdocs
        }
        m = evaluate(make_embedding_retriever(longdocs, units),
                     long_golden, k=DEFAULT_K)
        row = {"target": target, "overlap": overlap,
               "chunks_total": sum(len(v) for v in units.values()), **m}
        rows.append(row)
        better = best is None and m["recall_at_k"] >= doc_level["recall_at_k"]
        if best is None or (m["recall_at_k"], m["mrr"], -row["chunks_total"]) > \
                (best["recall_at_k"], best["mrr"], -best["chunks_total"]):
            best = row
            mark = "  ← الأفضل (التربيع الأكبر ثم أقل كلفة)"
        elif better:
            mark = ""
        else:
            mark = ""
        print(f"   target={target:>4} overlap={overlap}: {fmt(m)} "
              f"chunks={row['chunks_total']}{mark}")
    print()
    print("=" * 72)
    print("4) التحقق: لا انحدار على المقياس المعجمي القائم بالمعاملات المختارة")
    chunked_corpus_units = {
        d["id"]: [
            set(_tokens(c))
            for c in chunk_arabic_text(d.get("text", ""),
                                       target_chars=best["target"],
                                       overlap=best["overlap"])
        ]
        for d in corpus
    }
    doc_order = [d["id"] for d in corpus]

    def chunk_lex_retrieve(query: str, k: int = DEFAULT_K) -> list[str]:
        q = set(_tokens(query))
        if not q:
            return []
        scored = []
        for doc_id in doc_order:
            best_ratio = max(
                (len(q & ct) / len(q) for ct in chunked_corpus_units[doc_id] if ct),
                default=0.0,
            )
            if best_ratio > 0.0:
                scored.append((best_ratio, doc_id))
        scored.sort(key=lambda t: (-t[0], t[1]))
        return [doc_id for _, doc_id in scored[:k]]

    chosen_lex = evaluate(chunk_lex_retrieve, golden, k=DEFAULT_K)
    no_regression = (
        chosen_lex["recall_at_k"] >= base_lex["recall_at_k"]
        and chosen_lex["mrr"] >= base_lex["mrr"]
    )
    gain_r = best["recall_at_k"] - doc_level["recall_at_k"]
    gain_m = best["mrr"] - doc_level["mrr"]
    print(f"   المعجمي chunk-level ({best['target']}/{best['overlap']}): "
          f"{fmt(chosen_lex)}  (الأساس {fmt(base_lex)})")
    print()
    print(f"   لا انحدار على مقياس CI: {'نعم ✓' if no_regression else 'لا ✗'}")
    print(f"   مكسب الدلالي على الوثائق المركّبة: "
          f"R@5 {gain_r:+.3f} / MRR {gain_m:+.3f}")
    print(f"   المعاملات المختارة: target={best['target']} overlap={best['overlap']}")

    if args.json:
        payload = {
            "baseline_lexical_golden": base_lex,
            "doc_level_embedding_longdoc": doc_level,
            "grid": rows,
            "best": best,
            "chosen_lexical_golden": chosen_lex,
            "no_regression": no_regression,
            "longdoc_gain": {"recall_at_5": round(gain_r, 4),
                             "mrr": round(gain_m, 4)},
        }
        Path(args.json).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"   كُتبت النتائج: {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
