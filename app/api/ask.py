from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.errors import AppError
from app.core.flags import prompt_logging_enabled
from app.services.prompt_log import log_prompt
from app.services.rag import answer_with_context

router = APIRouter(tags=["ask"])


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4_000)


@router.post("/ask")
def ask(payload: AskRequest, db: Session = Depends(get_db)):
    question = payload.question.strip()
    if not question:
        raise AppError(detail="question is required", code="question_required")
    if prompt_logging_enabled():
        log_prompt("ask", payload.question)
    try:
        reply, chunk_ids, provider = answer_with_context(db, question)
    except Exception as exc:
        raise AppError(
            detail=f"retrieval failed: {exc}",
            code="retrieval_error",
            status_code=500,
        ) from exc
    return {
        "answer": reply,
        "chunk_ids": chunk_ids,
        "provider": provider,
    }
