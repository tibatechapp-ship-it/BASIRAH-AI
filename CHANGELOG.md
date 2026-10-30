# Changelog

All notable changes to this project are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

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
