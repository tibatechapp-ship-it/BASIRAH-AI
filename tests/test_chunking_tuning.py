"""Week-3 evidence pin — the tuning script's contract holds in CI.

يمنع انزياح نتائج الضبط دون مراجعة: لا انحدار على مقياس CI المعجمي،
وأن الـchunking يحسّن Recall@5 فعلاً على الوثائق المركّبة (آلية التخفيف).
"""
import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from src.api.chunking import CHUNK_OVERLAP_SENTENCES, CHUNK_TARGET_CHARS

_SPEC = importlib.util.spec_from_file_location(
    "tune_chunking", REPO / "scripts" / "tune_chunking.py")
tune = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(tune)


def _run_sweep():
    import json
    corpus = json.loads((REPO / "tests/eval/corpus.json").read_text(encoding="utf-8"))
    golden = json.loads((REPO / "tests/eval/golden_set.json").read_text(encoding="utf-8"))
    base_lex = tune.evaluate(tune.make_lexical_retriever(corpus), golden, k=tune.DEFAULT_K)

    longdocs, owner = tune.build_dilution_corpus(corpus)
    long_golden = [
        {"q": item["q"], "relevant": [owner[d] for d in item["relevant"] if d in owner]}
        for item in golden if any(d in owner for d in item["relevant"])
    ]
    doc_units = {d["id"]: [d["text"]] for d in longdocs}
    doc_level = tune.evaluate(tune.make_embedding_retriever(longdocs, doc_units),
                              long_golden, k=tune.DEFAULT_K)

    units = {
        d["id"]: tune.chunk_arabic_text(d["text"],
                                        target_chars=CHUNK_TARGET_CHARS,
                                        overlap=CHUNK_OVERLAP_SENTENCES)
        for d in longdocs
    }
    chunk_level = tune.evaluate(tune.make_embedding_retriever(longdocs, units),
                                long_golden, k=tune.DEFAULT_K)
    return base_lex, doc_level, chunk_level


def test_chunking_improves_longdoc_semantic_recall():
    base_lex, doc_level, chunk_level = _run_sweep()
    # آلية التخفيف: الوثيقة الواحدة المخففة تخسر الاستعلام في أعلى 5
    assert doc_level["recall_at_k"] < chunk_level["recall_at_k"], (
        f"chunk-level يجب أن يتفوق: doc={doc_level} chunk={chunk_level}")


def test_no_regression_on_ci_lexical_gate():
    base_lex, _doc, _chunk = _run_sweep()
    # مقياس CI القائم (عتبتا 0.70/0.50) لا ينخفض عن خط أساسه 0.975
    assert base_lex["recall_at_k"] >= 0.975
    assert base_lex["mrr"] >= 0.975


def test_chosen_constants_match_sweep_best():
    # الثوابت المعلنة في chunking.py هي خلاصة المسح — أي تغيير يُراجع بجدول جديد
    assert CHUNK_TARGET_CHARS == 400
    assert CHUNK_OVERLAP_SENTENCES == 1
