from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.flags import prompt_logging_enabled, strict_mode_enabled
from app.services.prompt_log import log_prompt
from app.services.rag import ingest_document
from fastapi import Depends

router = APIRouter(tags=["documents"])


class DocumentRequest(BaseModel):
    text: str
    source: str | None = None


@router.post("/documents")
def create_document(payload: DocumentRequest, db: Session = Depends(get_db)):
    text = (payload.text or "").strip()
    if not text:
        return JSONResponse(status_code=400, content={"message": "text missing"})
    if strict_mode_enabled() and len(text) > 20000:
        return JSONResponse(status_code=400, content={"error": "payload too large"})
    if prompt_logging_enabled():
        log_prompt("documents", payload.text)
    source = payload.source or "upload"
    try:
        document, chunk_count = ingest_document(db, text, source)
    except Exception as exc:
        return JSONResponse(status_code=500, content={"failed": str(exc)})
    return {
        "id": document.id,
        "source": document.source,
        "chunks": chunk_count,
    }
