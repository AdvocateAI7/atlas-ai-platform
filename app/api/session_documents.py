from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.models import ConversationSession
from app.services.session_rag import (
    delete_session_document,
    ingest_session_document,
    list_session_documents,
)

router = APIRouter(prefix="/sessions/{session_id}/documents", tags=["session-documents"])


class IngestRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500_000)
    filename: str = Field(default="upload.txt", max_length=256)


def _doc_to_dict(doc) -> dict:
    return {
        "id": doc.id,
        "filename": doc.filename or doc.source,
        "chunk_count": len(doc.chunks),
        "created_at": doc.created_at.isoformat(),
    }


def _require_session(session_id: int, db: Session) -> ConversationSession:
    session = db.get(ConversationSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")
    return session


@router.post("", status_code=201)
def upload_document(
    session_id: int,
    payload: IngestRequest,
    db: Session = Depends(get_db),
):
    _require_session(session_id, db)
    if not payload.text.strip():
        raise HTTPException(status_code=422, detail="document text is empty")
    doc, chunk_count = ingest_session_document(
        db, session_id, payload.text, payload.filename
    )
    return {
        "id": doc.id,
        "filename": doc.filename,
        "chunk_count": chunk_count,
        "session_id": session_id,
        "created_at": doc.created_at.isoformat(),
    }


@router.get("")
def list_documents(session_id: int, db: Session = Depends(get_db)):
    _require_session(session_id, db)
    docs = list_session_documents(db, session_id)
    return [_doc_to_dict(d) for d in docs]


@router.delete("/{document_id}", status_code=204)
def remove_document(session_id: int, document_id: int, db: Session = Depends(get_db)):
    _require_session(session_id, db)
    if not delete_session_document(db, session_id, document_id):
        raise HTTPException(status_code=404, detail="document not found")
