from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(512), default="upload")
    filename: Mapped[str | None] = mapped_column(String(512), nullable=True)
    # null = global document (legacy /documents endpoint); set = session-scoped
    session_id: Mapped[int | None] = mapped_column(
        ForeignKey("conversation_sessions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    document: Mapped[Document] = relationship(back_populates="chunks")


class ConversationSession(Base):
    __tablename__ = "conversation_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(256), default="New conversation")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    messages: Mapped[list["ConversationMessage"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", order_by="ConversationMessage.id"
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document",
        foreign_keys="Document.session_id",
        cascade="all, delete-orphan",
    )


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(
        ForeignKey("conversation_sessions.id"), index=True
    )
    role: Mapped[str] = mapped_column(String(16))  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text)
    provider: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped[ConversationSession] = relationship(back_populates="messages")
