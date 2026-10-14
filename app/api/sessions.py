from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.services.sessions import (
    create_session,
    delete_session,
    get_session,
    list_sessions,
    send_message,
)

router = APIRouter(prefix="/sessions", tags=["sessions"])


class CreateSessionRequest(BaseModel):
    title: str = Field(default="New conversation", max_length=256)


class SendMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=32_000)
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)


def _session_to_dict(session, *, include_messages: bool = False) -> dict:
    base = {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at.isoformat(),
        "updated_at": session.updated_at.isoformat(),
        "message_count": len(session.messages),
    }
    if include_messages:
        base["messages"] = [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "provider": m.provider,
                "created_at": m.created_at.isoformat(),
            }
            for m in session.messages
        ]
    return base


@router.post("", status_code=201)
def create(payload: CreateSessionRequest, db: Session = Depends(get_db)):
    session = create_session(db, payload.title)
    return _session_to_dict(session)


@router.get("")
def list_all(db: Session = Depends(get_db)):
    sessions = list_sessions(db)
    return [_session_to_dict(s) for s in sessions]


@router.get("/{session_id}")
def get_one(session_id: int, db: Session = Depends(get_db)):
    session = get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")
    return _session_to_dict(session, include_messages=True)


@router.post("/{session_id}/messages", status_code=201)
def post_message(
    session_id: int,
    payload: SendMessageRequest,
    db: Session = Depends(get_db),
):
    result = send_message(
        db,
        session_id,
        user_message=payload.message,
        temperature=payload.temperature,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="session not found")
    return {
        "id": result.id,
        "role": result.role,
        "content": result.content,
        "provider": result.provider,
        "created_at": result.created_at.isoformat(),
    }


@router.delete("/{session_id}", status_code=204)
def remove(session_id: int, db: Session = Depends(get_db)):
    if not delete_session(db, session_id):
        raise HTTPException(status_code=404, detail="session not found")
