from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.flags import prompt_logging_enabled
from app.services.prompt_log import log_prompt
from app.services.rag import answer_with_context
from fastapi import APIRouter, Depends

router = APIRouter(tags=["ask"])


class AskRequest(BaseModel):
    question: str


@router.post("/ask")
def ask(payload: AskRequest, db: Session = Depends(get_db)):
    question = (payload.question or "").strip()
    if not question:
        return {"ok": False, "error": "question is required"}
    if prompt_logging_enabled():
        log_prompt("ask", payload.question)
    try:
        reply, chunk_ids, provider = answer_with_context(db, question)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
    return {
        "ok": True,
        "answer": reply,
        "chunk_ids": chunk_ids,
        "provider": provider,
    }
