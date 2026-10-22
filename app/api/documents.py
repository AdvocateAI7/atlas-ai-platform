from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import AppError
from app.core.flags import prompt_logging_enabled, strict_mode_enabled
from app.services.prompt_log import log_prompt
from app.services.rag import ingest_document

router = APIRouter(tags=["documents"])


class DocumentRequest(BaseModel):
    text: str = Field(min_length=1, max_length=100_000)
    source: str | None = Field(default=None, max_length=256)


@router.post("/documents", status_code=201)
def create_document(payload: DocumentRequest, db: Session = Depends(get_db)):
    text = payload.text.strip()
    if not text:
        raise AppError(detail="text is required", code="text_required")
    if strict_mode_enabled() and len(text) > 20_000:
        raise AppError(
            detail="payload exceeds strict mode limit",
            code="payload_too_large",
            status_code=413,
        )
    if prompt_logging_enabled():
        log_prompt("documents", payload.text)
    source = payload.source or "upload"
    try:
        document, chunk_count = ingest_document(db, text, source)
    except Exception as exc:
        raise AppError(
            detail=f"ingest failed: {exc}",
            code="ingest_error",
            status_code=500,
        ) from exc
    return {
        "id": document.id,
        "source": document.source,
        "chunks": chunk_count,
    }
