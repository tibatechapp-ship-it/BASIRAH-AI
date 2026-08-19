from __future__ import annotations

from fastapi import FastAPI

from src.api.database import Base, engine
from src.api.routers import documents, library

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="BASIRAH AI",
    description="منصة ذكية لتنظيم وتصنيف المكتبات الرقمية والبحوث العلمية",
    version="0.2.0",
)

app.include_router(documents.router)
app.include_router(library.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
