"""Arabic-aware chunking — Week-3 milestone of the productization plan.

Before this module a document was embedded as ONE vector of its full text
(truncated at 50k chars): a query about a single section of a long book had to
match a vector diluted across every other topic in that book. This module
splits Arabic text into overlapping, sentence-complete chunks so each can be
embedded on its own; retrieval then aggregates the best chunk per document.

Stdlib only (portfolio rule): no regex lookbehind tricks that break on Arabic
combining marks, no third-party tokenizers. Tuned parameters live in
``CHUNK_TARGET_CHARS`` / ``CHUNK_OVERLAP_SENTENCES`` and were chosen by
``scripts/tune_chunking.py`` — see ``docs/chunking-tuning.md`` for the sweep
tables and the honest caveats.
"""
from __future__ import annotations

try:  # سياق pytest من الجذر: حزمة src.
    from src.basirah.utils.helpers import normalize_arabic_text
except ImportError:  # سياق CLI: PYTHONPATH=src
    from basirah.utils.helpers import normalize_arabic_text

# ═══ الترويسة المضبوطة (نتائج المسح في docs/chunking-tuning.md) ═══
# المسح الحتمي اختار 400/1: أعلى R@5 على الوثائق المركّبة (0.575 مقابل
# 0.400 بلا chunking) بلا أي انحدار على مقياس CI المعجمي (0.975 ثابت).
CHUNK_TARGET_CHARS = 400
CHUNK_OVERLAP_SENTENCES = 1
# سقف أمان على كلفة التضمين لكل وثيقة (الوثائق الأطول تُقصّ عند آخر chunk)
MAX_CHUNKS_PER_DOC = 120
MIN_CHUNK_CHARS = 80

# فواصل الجمل العربية: النقطتان، النقطة، علامة الاستفهام، التعجب، التكرار،
# النقاط الثلاث، وحروف الاستئناف في بداية السطر الجديد.
_SENTENCE_ENDINGS = ".!؟…؛:"
_PARAGRAPH_BREAKS = ("\n\n", "\r\n\r\n")


def split_sentences_ar(text: str) -> list[str]:
    """قسّم نصاً عربياً مطبعاً إلى جمل كاملة — الفاصل يبقى مع الجملة.

    القطع التي لا تحوي أي حرف (كقطع النقاط الثلاث) تُلحّق بالجملة السابقة.
    """
    sentences: list[str] = []
    buf: list[str] = []
    for ch in text:
        buf.append(ch)
        if ch in _SENTENCE_ENDINGS:
            piece = "".join(buf).strip()
            if piece:
                if any(c.isalnum() for c in piece):
                    sentences.append(piece)
                elif sentences:
                    sentences[-1] = f"{sentences[-1]}{piece}"
            buf = []
    tail = "".join(buf).strip()
    if tail:
        if any(c.isalnum() for c in tail) or not sentences:
            sentences.append(tail)
        else:
            sentences[-1] = f"{sentences[-1]}{tail}"
    return sentences


def _pack_sentences(sentences: list[str], target_chars: int,
                    overlap: int) -> list[str]:
    """اجمع الجمل في حزم قريبة من الحجم المستهدف مع تداخل جمل محدد.

    الجملة الأطول من الحجم المستهدف تبقى وحدها (لا تُقطع كلمة أبداً).
    """
    packs: list[list[str]] = []
    current: list[str] = []
    size = 0
    for sentence in sentences:
        sentence_len = len(sentence)
        if current and size + sentence_len > target_chars:
            packs.append(current)
            tail = current[-overlap:] if overlap > 0 else []
            current = list(tail)
            size = sum(len(s) for s in current)
        current.append(sentence)
        size += sentence_len
    if current:
        packs.append(current)

    def _join(parts: list[str]) -> str:
        out = ""
        for part in parts:
            if out and not out[-1].isspace() and not part[0].isspace():
                out += " "
            out += part
        return out.strip()

    return [_join(parts) for parts in packs if _join(parts)]


def chunk_arabic_text(
    text: str,
    target_chars: int = CHUNK_TARGET_CHARS,
    overlap: int = CHUNK_OVERLAP_SENTENCES,
) -> list[str]:
    """قسّم نصاً عربياً إلى chunks جملة-كاملة بتداخل محدد.

    التسلسل: فقرات → فقرة أكبر من المستهدف تُحزم جملة-جملة → الفقرات
    الأصغر تُدمج حتى المستهدف. النص الأقصر من المستهدف يرجع chunkاً واحداً.
    النص الفارغ يرجع قائمة فارغة — لا chunk مزيف.
    """
    if not text or not text.strip():
        return []
    normalized = normalize_arabic_text(text).strip()

    for brk in _PARAGRAPH_BREAKS:
        normalized = normalized.replace(brk, "\n\n")
    paragraphs = [p.strip() for p in normalized.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [normalized]

    units: list[str] = []
    for para in paragraphs:
        if len(para) <= target_chars:
            units.append(para)
        else:
            units.extend(_pack_sentences(split_sentences_ar(para),
                                         target_chars, overlap))

    # دمج الفقرات/الحزم الصغيرة المتتالية حتى المستهدف (بلا كسر جملة)
    merged: list[str] = []
    buf = ""
    for unit in units:
        if buf and len(buf) + len(unit) + 1 <= target_chars:
            buf = f"{buf}\n{unit}"
        else:
            if buf:
                merged.append(buf)
            buf = unit
    if buf:
        merged.append(buf)

    return merged[:MAX_CHUNKS_PER_DOC]


def chunks_with_index(text: str, **kwargs) -> list[dict[str, object]]:
    """نفس chunk_arabic_text مع ترقيم idx — عقد التخزين في DocumentChunk."""
    return [
        {"idx": i, "text": chunk}
        for i, chunk in enumerate(chunk_arabic_text(text, **kwargs))
    ]
