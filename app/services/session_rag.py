from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.models import Chunk, Document
from app.services.chunking import chunk_text
from app.services.embeddings import (
    cosine_similarity,
    deserialize_embedding,
    embed_text,
    serialize_embedding,
)

_MAX_CONTEXT_CHARS = 4000  # prevent token overrun in LLM context


def ingest_session_document(
    db: Session,
    session_id: int,
    text: str,
    filename: str,
) -> tuple[Document, int]:
    """Ingest a document scoped to a specific conversation session."""
    settings = get_settings()
    pieces = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
    document = Document(
        source="session_upload",
        filename=filename,
        session_id=session_id,
    )
    db.add(document)
    db.flush()
    for piece in pieces:
        db.add(
            Chunk(
                document_id=document.id,
                text=piece,
                embedding=serialize_embedding(embed_text(piece)),
            )
        )
    db.commit()
    db.refresh(document)
    return document, len(pieces)


def list_session_documents(db: Session, session_id: int) -> list[Document]:
    return list(
        db.scalars(
            select(Document)
            .where(Document.session_id == session_id)
            .order_by(Document.id)
        )
    )


def delete_session_document(db: Session, session_id: int, document_id: int) -> bool:
    doc = db.get(Document, document_id)
    if doc is None or doc.session_id != session_id:
        return False
    db.delete(doc)
    db.commit()
    return True


def retrieve_for_session(
    db: Session,
    session_id: int,
    query: str,
    top_k: int | None = None,
) -> list[Chunk]:
    """Return the top-K chunks from documents belonging to this session only."""
    settings = get_settings()
    k = top_k or settings.rag_top_k

    # Only consider chunks whose document belongs to this session
    chunks = list(
        db.scalars(
            select(Chunk)
            .join(Document, Chunk.document_id == Document.id)
            .where(Document.session_id == session_id)
        )
    )
    if not chunks:
        return []

    query_vec = embed_text(query)
    scored = [
        (cosine_similarity(query_vec, deserialize_embedding(c.embedding)), c)
        for c in chunks
    ]
    scored.sort(key=lambda item: item[0], reverse=True)
    return [c for _, c in scored[:k]]


def build_rag_context(chunks: list[Chunk]) -> str:
    """Concatenate chunk texts up to the character budget."""
    parts: list[str] = []
    total = 0
    for chunk in chunks:
        if total + len(chunk.text) > _MAX_CONTEXT_CHARS:
            break
        parts.append(chunk.text)
        total += len(chunk.text)
    return "\n\n".join(parts)
