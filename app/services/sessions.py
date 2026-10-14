from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.models import ConversationMessage, ConversationSession
from app.providers.factory import get_llm_provider

_HISTORY_LIMIT = 10  # max past turns passed as context


def create_session(db: Session, title: str) -> ConversationSession:
    session = ConversationSession(title=title)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, session_id: int) -> ConversationSession | None:
    return db.get(ConversationSession, session_id)


def list_sessions(db: Session) -> list[ConversationSession]:
    return list(db.scalars(select(ConversationSession).order_by(ConversationSession.id.desc())))


def delete_session(db: Session, session_id: int) -> bool:
    session = db.get(ConversationSession, session_id)
    if session is None:
        return False
    db.delete(session)
    db.commit()
    return True


def send_message(
    db: Session,
    session_id: int,
    user_message: str,
    temperature: float = 0.2,
) -> ConversationMessage | None:
    session = db.get(ConversationSession, session_id)
    if session is None:
        return None

    # Persist the user turn
    user_turn = ConversationMessage(
        session_id=session_id,
        role="user",
        content=user_message,
    )
    db.add(user_turn)
    db.flush()

    # Build context from recent history (excludes the turn we just added)
    history = list(
        db.scalars(
            select(ConversationMessage)
            .where(ConversationMessage.session_id == session_id)
            .where(ConversationMessage.id != user_turn.id)
            .order_by(ConversationMessage.id.desc())
            .limit(_HISTORY_LIMIT)
        )
    )
    history.reverse()

    history_text = "\n".join(
        f"{msg.role.upper()}: {msg.content}" for msg in history
    )
    prompt = (
        f"Conversation so far:\n{history_text}\n\nUSER: {user_message}\nASSISTANT:"
        if history_text
        else user_message
    )

    provider = get_llm_provider()
    reply_text = provider.complete(prompt, temperature=temperature)

    assistant_turn = ConversationMessage(
        session_id=session_id,
        role="assistant",
        content=reply_text,
        provider=provider.name,
    )
    db.add(assistant_turn)
    db.commit()
    db.refresh(assistant_turn)
    return assistant_turn
