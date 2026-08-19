from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from src.api.database import get_db
from src.api.dependencies import extract_text, file_hash, get_embedding_model
from src.api.models import Document
from src.organizer import CATEGORIES, classify, move_file

router = APIRouter(prefix="/library", tags=["library"])


@router.post("/organize")
def organize_library(
    archive: UploadFile = File(...),
    recursive: bool = True,
    db: Session = Depends(get_db),
):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        zip_path = temp_path / "library.zip"
        zip_path.write_bytes(archive.file.read())

        extract_dir = temp_path / "library"
        extract_dir.mkdir()
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        supported = {".pdf", ".txt", ".docx"}
        iterator = extract_dir.rglob("*") if recursive else extract_dir.iterdir()
        entries = [
            entry for entry in iterator
            if entry.is_file() and entry.suffix.lower() in supported
        ]

        total = 0
        classified = 0
        model = get_embedding_model()

        for entry in entries:
            total += 1
            text = extract_text(str(entry))[:50_000]
            category = classify(text) if text else "غير_مصنف"
            target_folder = extract_dir / category
            move_file(str(entry), str(target_folder))

            hash_value = file_hash(str(entry))
            existing = db.query(Document).filter(Document.file_hash == hash_value).first()
            if not existing and hash_value:
                embedding = model.encode(text).tolist() if text else None
                doc = Document(
                    filename=entry.name,
                    file_path=str(target_folder / entry.name),
                    file_hash=hash_value,
                    category=category,
                    text=text,
                    embedding=embedding,
                )
                db.add(doc)
                classified += 1

        db.commit()

        output_zip = temp_path / "organized_library.zip"
        with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in extract_dir.rglob("*"):
                if file_path.is_file():
                    zf.write(file_path, file_path.relative_to(extract_dir))

        return {
            "total_files": total,
            "classified_files": classified,
            "download_url": "/library/download/organized_library.zip",
        }
