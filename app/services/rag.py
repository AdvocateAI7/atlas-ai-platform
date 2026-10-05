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
from app.providers.factory import get_llm_provider


def ingest_document(db: Session, text: str, source: str) -> tuple[Document, int]:
    settings = get_settings()
    pieces = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
    document = Document(source=source)
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


def retrieve(db: Session, query: str, top_k: int | None = None) -> list[Chunk]:
    settings = get_settings()
    k = top_k or settings.rag_top_k
    query_vec = embed_text(query)
    chunks = db.scalars(select(Chunk)).all()
    scored = []
    for chunk in chunks:
        vector = deserialize_embedding(chunk.embedding)
        scored.append((cosine_similarity(query_vec, vector), chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [chunk for _, chunk in scored[:k]]


def answer_with_context(db: Session, question: str) -> tuple[str, list[int], str]:
    matches = retrieve(db, question)
    context = "\n\n".join(chunk.text for chunk in matches) or "(no stored documents)"
    prompt = (
        "Answer the question using the context below.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}"
    )
    provider = get_llm_provider()
    reply = provider.complete(prompt)
    return reply, [chunk.id for chunk in matches], provider.name
