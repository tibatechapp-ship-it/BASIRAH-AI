"""لوحة البيانات الوصفية — خارطة المنتَجة أسبوع 2 (من pipeline إلى platform).

قراءة-فقت بالكامل: ما تُنتجه هنا أرقام وصفوف من قاعدة البيانات نفسها —
لا تصنيف ولا فهرسة تُنفَّذ من اللوحة.

المسارات:
    GET /api/dashboard/stats      — JSON: العدد، توزيع المواضيع، التغطية الدلالية
    GET /dashboard                — صفحة عربية RTL بلا JS: الأرقام + توزيع المواضيع + نموذج بحث
    GET /dashboard/search?q=      — بحث تفاعلي: دلالي (pgvector) ثم نصي (LIKE) — واضح التسمية دائماً

الصدق أولاً: على SQLite (اختبارات/تطوير) يغيب pgvector فيُعرض قسم «مطابقة
نصية» بلا ادعاء دلالة؛ على Postgres يعرض «مطابقة دلالية» فعلاً.
"""

from __future__ import annotations

import html as _html

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from src.api.database import get_db
from src.api.models import Document

router = APIRouter(tags=["dashboard"])

MAX_TEXT_PREVIEW = 160
MAX_FILENAME = 80


# ═══════════════════════ JSON ═══════════════════════

def _category_distribution(db: Session) -> dict[str, int]:
    rows = db.query(Document.category, func.count(Document.id)).group_by(
        Document.category).all()
    return {str(cat or "غير_مصنف"): int(n) for cat, n in rows}


@router.get("/api/dashboard/stats")
def dashboard_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(Document.id)).scalar() or 0
    with_embedding = db.query(func.count(Document.id)).filter(
        Document.embedding.isnot(None)).scalar() or 0
    chars = db.query(func.coalesce(func.sum(func.length(Document.text)), 0)).scalar() or 0
    latest = db.query(Document).order_by(Document.created_at.desc()).limit(5).all()
    return {
        "ok": True,
        "total_documents": int(total),
        "by_category": _category_distribution(db),
        "docs_with_embedding": int(with_embedding),
        "semantic_coverage": round(with_embedding / total, 3) if total else 0.0,
        "total_text_chars": int(chars),
        "latest": [
            {
                "filename": d.filename[:MAX_FILENAME],
                "category": d.category or "غير_مصنف",
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in latest
        ],
    }


# ═══════════════════════ HTML ═══════════════════════

_PAGE = """<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BASIRAH — لوحة المكتبة</title>
<style>
body{font-family:system-ui,'Segoe UI',sans-serif;background:#0d1117;color:#e6edf3;
     max-width:860px;margin:2rem auto;padding:0 1rem;line-height:1.7}
h1{font-size:1.4rem;border-bottom:1px solid #30363d;padding-bottom:.5rem}
section{background:#161b22;border:1px solid #30363d;border-radius:8px;
        padding:1rem 1.25rem;margin:1rem 0}
.num{font-size:2rem;font-weight:700;color:#58a6ff;margin:0}
ul{padding-right:1.2rem;margin:.3rem 0}
.muted{color:#8b949e;font-size:.85rem}
a{color:#58a6ff;text-decoration:none}
li{margin:.25rem 0}
.bar{background:#21262d;border-radius:4px;height:18px;margin:4px 0;overflow:hidden}
.bar>span{display:block;height:100%;background:#1f6feb}
input[type=search]{background:#0d1117;color:#e6edf3;border:1px solid #30363d;
     border-radius:6px;padding:.5rem .8rem;width:60%}
button{background:#1f6feb;color:#fff;border:0;border-radius:6px;padding:.5rem 1.2rem}
blockquote{background:#0d1117;border-right:3px solid #30363d;margin:.4rem 0;
           padding:.5rem .8rem;color:#c9d1d9}
</style>
</head>
<body>
<h1>👁 BASIRAH — لوحة المكتبة</h1>
<p class="muted">قراءة-فقت: أرقام من قاعدة بياناتك لا تنفّذ شيئاً · <a href="/docs">OpenAPI</a></p>
<section>
  <h2>الوثائق</h2>
  <p class="num">__TOTAL__</p>
  <p class="muted">التغطية الدلالية (تضمينات جاهزة للبحث): __COVERAGE__ · أحرف النصوص: __CHARS__</p>
</section>
<section>
  <h2>توزيع المواضيع</h2>
  __CATEGORIES__
</section>
<section>
  <h2>بحث تفاعلي</h2>
  <form action="/dashboard/search" method="get">
    <input type="search" name="q" placeholder="ابحث في مكتبتك…" value="__Q__">
    <button type="submit">ابحث</button>
  </form>
  __RESULTS__
</section>
<section>
  <h2>أحدث الوثائق</h2>
  __LATEST__
</section>
</body>
</html>
"""


def _esc(v) -> str:
    return _html.escape(str(v), quote=True)


def _categories_html(dist: dict[str, int], total: int) -> str:
    if not dist:
        return '<p class="muted">لا وثائق بعد — ارفع أول ملف من <a href="/docs#/documents">/documents/upload</a>.</p>'
    top = max(dist.values())
    items = []
    for cat, n in sorted(dist.items(), key=lambda kv: -kv[1]):
        pct = round(100 * n / top) if top else 0
        items.append(
            f'<div>{_esc(cat)} — {n} <span class="muted">({round(100 * n / total) if total else 0}%)</span>'
            f'<div class="bar"><span style="width:{pct}%"></span></div></div>')
    return "".join(items)


def _results_html(rows: list[dict], kind: str, q: str) -> str:
    if not q.strip():
        return '<p class="muted">اكتب كلمة للبحث في مكتبتك.</p>'
    if not rows:
        return (f'<p class="muted">لا نتائج لـ{_esc(q)} — جرّب كلمات أقل '
                f'أو ارفع وثائق أولاً.</p>')
    lis = "".join(
        f'<li><strong>{_esc(r["filename"])}</strong> '
        f'<span class="muted">({_esc(r["category"])})</span>'
        f'<blockquote>{_esc(r["preview"])}…</blockquote></li>'
        for r in rows)
    return f'<p class="muted">{len(rows)} نتيجة — {kind}</p><ul>{lis}</ul>'


def _semantic_rows(db: Session, q: str, limit: int) -> tuple[list[dict], str]:
    """بحث دلالي فعلي عبر مسار /documents/search الحقيقي — إن توفر."""
    try:
        from src.api.routers.documents import search_documents
        results = search_documents(q=q, limit=limit, db=db)
        return ([{"filename": r.filename, "category": getattr(r, "category", "") or "",
                  "preview": (getattr(r, "text", "") or "")[:MAX_TEXT_PREVIEW]}
                 for r in results], "مطابقة دلالية")
    except Exception:
        return [], "مطابقة دلالية"


def _text_rows(db: Session, q: str, limit: int) -> list[dict]:
    """مطابقة نصية صريحة — تعمل على أي محرك بلا تضمينات."""
    pattern = f"%{q.strip()[:120]}%"
    docs = (db.query(Document)
            .filter(or_(Document.text.ilike(pattern),
                        Document.filename.ilike(pattern)))
            .limit(limit).all())
    return [{"filename": d.filename, "category": d.category or "غير_مصنف",
             "preview": (d.text or "")[:MAX_TEXT_PREVIEW]} for d in docs]


@router.get("/dashboard/search", response_class=HTMLResponse)
def dashboard_search(q: str = "", limit: int = 10, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 50))
    rows, kind = [], ""
    if q.strip():
        rows, kind = _semantic_rows(db, q, limit)
        if not rows:
            rows, kind = _text_rows(db, q, limit), "مطابقة نصية"
    return _page(db, q=q, results=_results_html(rows, kind, q))


def _page(db: Session, q: str = "", results: str | None = None) -> str:
    dist = _category_distribution(db)
    total = sum(dist.values())
    with_emb = db.query(func.count(Document.id)).filter(
        Document.embedding.isnot(None)).scalar() or 0
    chars = db.query(func.coalesce(func.sum(func.length(Document.text)), 0)).scalar() or 0
    latest = db.query(Document).order_by(Document.created_at.desc()).limit(5).all()
    if latest:
        latest_html = "<ul>" + "".join(
            f'<li>{_esc(d.filename[:MAX_FILENAME])} — {_esc(d.category or "غير_مصنف")}</li>'
            for d in latest) + "</ul>"
    else:
        latest_html = '<p class="muted">لا وثائق بعد.</p>'
    page = _PAGE
    for key, val in (
        ("__TOTAL__", str(total)),
        ("__COVERAGE__", f"{round(100 * with_emb / total) if total else 0}%"),
        ("__CHARS__", f"{int(chars):,}"),
        ("__CATEGORIES__", _categories_html(dist, total)),
        ("__Q__", _esc(q)),
        ("__RESULTS__", results or '<p class="muted">اكتب كلمة للبحث في مكتبتك.</p>'),
        ("__LATEST__", latest_html),
    ):
        page = page.replace(key, val)
    return page


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(db: Session = Depends(get_db)):
    return _page(db)
