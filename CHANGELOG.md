# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added — أسبوع 2 من خارطة المنتَجة: لوحة البيانات الوصفية
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
