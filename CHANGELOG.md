# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.5.0] — 2026-11-01

### أسبوع 3 من خارطة المنتَجة — ضبط chunking للعربية + البحث الدلالي على مستوى الأقسام + إصدار تلقائي (`src/api/chunking.py` + `document_chunks` + `scripts/tune_chunking.py` + `docs/chunking-tuning.md`)

> **قبل هذه النسخة**: كل وثيقة تُضمَّن كمتجه واحد لنصها الكامل (مقصوصاً عند 50k حرف) —
> استعلام عن فصل واحد في كتاب طويل يخلف خلف توزيع باقي المواضيع (تخفيف المتجه الواحد).
> **الآن**: كل وثيقة تُقسَّم جملة-كاملة بتداخل مضبوط، وكل قسم يُضمَّن على حدة، والبحث يجمع
> أفضل قسم لكل وثيقة — والوثائق القديمة بلا أقسام تبقى قابلة للبحث بمستوى الوثيقة.

### Added
- **`src/api/chunking.py` (stdlib فقط)**: تقسيم عربي واعٍ بالفقرات والجمل — فقرة أكبر من
  المستهدف تُحزم جملة-جملة (لا كلمة مبتورة أبداً)، الفقرات الصغيرة تُدمج، قطع النقاط
  الثلاث تلحق بجملتها، والتطبيع بنفس مطبّع المستودع القياسي. ثوابت مضبوطة بمسح حتمي:
  `CHUNK_TARGET_CHARS=400`، `CHUNK_OVERLAP_SENTENCES=1`، `MAX_CHUNKS_PER_DOC=120`
- **`DocumentChunk` + فهرسة عند الإدخال**: جدول أقسام (idx/text/embedding) بفهرس
  (document_id, idx)، يُملأ من **كلا بابي الإدخال** (`/documents/upload` و
  `/library/organize` عبر `index_document_chunks` المشتركة) — فشل الأقسام يتراجع وحده
  (savepoint) ولا يفشل رفع الوثيقة
- **بحث مُجمَّع على مستوى الأقسام**: `/documents/search` يرتب أقرب chunk لكل وثيقة
  (cosine distance) ويكمل بمستوى الوثيقة لمن لا أقسام له؛ الاستجابة أضاف حقلاً
  **`snippet`** (مقتطف القسم المطابق — معاينة حقيقية بدل نص فارغ) و`chunk_idx`.
  على SQLite يُحسب التقييم بالبايثون **بنفس صيغة pgvector حرفاً-لحرفاً** (`_cosine_distance`)
  فتُختبر الدلالة في CI بدل الرد الفارغ — والنتائج المنحلّة (score ≤ 0) تُسقط في
  `/dashboard/search` بصدق إلى «مطابقة نصية» بدل ادعاء دلالة وهمية
- **مقياس الضبط الحتمي `scripts/tune_chunking.py`**: شبكة target×overlap (15 تركيبة) على
  24 وثيقة مركّبة (موضوع + 9 مشتتات ≈1,300 حرف) بتضمينات hashing قياسية — الجداول
  الكاملة والقراءة الصادقة في `docs/chunking-tuning.md`
- **إصدار تلقائي**: job `release` في `ci.yml` على كل وسم `v*`: بوابة الجودة أولًا
  (Recall@5/MRR فوق 0.70/0.50) ثم GitHub Release بملاحظات مستخلصة من CHANGELOG
  ومرفق `chunking-evidence.json` حتمي

### Measured (كلها قابلة للتكرار: `python scripts/tune_chunking.py`)
- **لا انحدار** على مقياس CI القائم: المعجمي chunk-level **0.975/0.975** (الأساس 0.975/0.975)
- **مكسب الدلالي على الوثائق المركّبة**: Recall@5 **0.400 → 0.575 (+0.175)** —
  التحسين في التغطية داخل أعلى 5 نتائج؛ MRR ثابت تقريباً (−0.004) بهذا المضمّن
  الحتمي — لا ادعاء مكسب في المركز الأول
- **التداخل الزائد يضر**: overlap=2 أسوأ في كل الأحجام (0.000 عند 300/2) — جملة
  واحدة (1) هي الموضع الأمين؛ الأحجام ≥800 تعيد إدخال التخفيف تدريجياً

### Tests
- 48 → **66** اختباراً خضراء (+18: `tests/test_semantic_chunks.py` — 16 اختباراً
  للمقسّم والفهرسة والبحث المجمَّع والتراجع الآمن والمعاينة المهرّبة، و
  `tests/test_chunking_tuning.py` — 3 اختبارات تُثبّت نتائج الضبط من الانزلاق
  دون مراجعة) — والبقية تعزز العزل بين وحدات الاختبار (نموذج مزيّف قابل للاستعادة)

### ما قبل الإصدار — كان في [Unreleased] وأُرفق مع v0.5.0 (أول إصدار للمستودع)

#### Added — أسبوع 2 من خارطة المنتَجة: لوحة البيانات الوصفية
- `GET /dashboard` — لوحة عربية RTL بلا JS: عدد الوثائق، توزيع المواضيع بأشرطة نسبية، التغطية الدلالية، أحدث الوثائق، ونموذج بحث تفاعلي.
- `GET /api/dashboard/stats` — JSON للأرقام نفسها (total/by_category/semantic_coverage/total_text_chars/latest).
- `GET /dashboard/search?q=` — بحث تفاعلي يعلن نوعه بصدق: «مطابقة دلالية» عبر pgvector حين يتوفر، وإلا «مطابقة نصية» (LIKE) على أي محرك — كل النصوص المرسومة تُهرب (Escape) وتخضع لاختبارات XSS.
- `tests/test_dashboard.py` — 10 اختبارات (52/52 خضراء): أرقام على مكتبة معلومة، حالات فارغة، عزل حالة بين الاختبارات، وتنتهيب المحتوى الخبيث.

### Added
- FastAPI + pgvector backend, Streamlit GUI, and a Docker Compose stack for the document restructuring pipeline.
- OCR and ML-based document classification pipeline (merged PR #6).
- EPUB/HTML restructuring support in the integrated pipeline (merged PRs #4–#6).
- Quran structure revision pass, adopting a full `.gitignore` and dropping committed `__pycache__` binaries.

### Changed
- Qwen performance work: `Counter`-based counting, normalized caching, and incremental PDF tracking.
- Repository layout restructured; the FastAPI/pgvector stack adapted to the new layout.

### Fixed
- CI: parseable `requirements.txt`, sklearn imports made optional, complete conda environment.
- Added `python-multipart`, required by FastAPI file-upload endpoints at test-collection time.
