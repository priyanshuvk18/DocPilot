"""
SQLAlchemy 2 models for DocPilot.
All models match Architecture.md §4 and PRD.md §6.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, TypeDecorator

from app.db.session import Base

# Compatible JSON type (JSONB on Postgres, JSON on SQLite)
CompatibleJSON = JSON().with_variant(JSONB(), "postgresql")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ─── Workspaces & Memberships ──────────────────────────────────────────────────

class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    memberships: Mapped[list[Membership]] = relationship("Membership", back_populates="workspace", cascade="all, delete-orphan")
    collections: Mapped[list[Collection]] = relationship("Collection", back_populates="workspace", cascade="all, delete-orphan")
    documents: Mapped[list[Document]] = relationship("Document", back_populates="workspace", cascade="all, delete-orphan")
    threads: Mapped[list[Thread]] = relationship("Thread", back_populates="workspace", cascade="all, delete-orphan")


class Membership(Base):
    __tablename__ = "memberships"

    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="member")  # 'owner', 'member', 'viewer'

    workspace: Mapped[Workspace] = relationship("Workspace", back_populates="memberships")


# ─── Collections & Documents ───────────────────────────────────────────────────

class Collection(Base):
    __tablename__ = "collections"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    workspace: Mapped[Workspace] = relationship("Workspace", back_populates="collections")
    documents: Mapped[list[Document]] = relationship("Document", back_populates="collection")


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        UniqueConstraint("workspace_id", "content_hash", name="uq_workspace_content_hash"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    collection_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("collections.id", ondelete="SET NULL"), nullable=True, index=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="queued")  # 'queued','parsing','embedding','ready','failed'
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_count: Mapped[int] = mapped_column(Integer, default=1)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_by: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    workspace: Mapped[Workspace] = relationship("Workspace", back_populates="documents")
    collection: Mapped[Collection | None] = relationship("Collection", back_populates="documents")
    chunks: Mapped[list[Chunk]] = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    heading: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tokens: Mapped[int] = mapped_column(Integer, default=0)
    # Stored as JSON/list of floats for cross-database compatibility (Postgres & SQLite)
    embedding: Mapped[list[float] | None] = mapped_column(CompatibleJSON, nullable=True)
    tsv: Mapped[str | None] = mapped_column(Text, nullable=True)

    document: Mapped[Document] = relationship("Document", back_populates="chunks")
    citations: Mapped[list[Citation]] = relationship("Citation", back_populates="chunk")


# ─── Chat & Citations ──────────────────────────────────────────────────────────

class Thread(Base):
    __tablename__ = "threads"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(500), default="New Thread")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    workspace: Mapped[Workspace] = relationship("Workspace", back_populates="threads")
    messages: Mapped[list[Message]] = relationship("Message", back_populates="thread", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    thread_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("threads.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(32), nullable=False)  # 'user', 'assistant', 'tool'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    ttft_ms: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    thread: Mapped[Thread] = relationship("Thread", back_populates="messages")
    citations: Mapped[list[Citation]] = relationship("Citation", back_populates="message", cascade="all, delete-orphan")
    actions: Mapped[list[Action]] = relationship("Action", back_populates="message")
    trace: Mapped[Trace | None] = relationship("Trace", back_populates="message", uselist=False, cascade="all, delete-orphan")
    feedback: Mapped[list[Feedback]] = relationship("Feedback", back_populates="message", cascade="all, delete-orphan")


class Citation(Base):
    __tablename__ = "citations"
    __table_args__ = (
        UniqueConstraint("message_id", "marker", name="uq_citation_message_marker"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("chunks.id", ondelete="SET NULL"), nullable=True)
    marker: Mapped[int] = mapped_column(Integer, nullable=False)
    quote: Mapped[str] = mapped_column(Text, nullable=False)

    message: Mapped[Message] = relationship("Message", back_populates="citations")
    chunk: Mapped[Chunk | None] = relationship("Chunk", back_populates="citations")


# ─── Agent Actions & Tools ────────────────────────────────────────────────────

class Action(Base):
    __tablename__ = "actions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    message_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    tool: Mapped[str] = mapped_column(String(128), nullable=False)
    params: Mapped[dict[str, Any]] = mapped_column(CompatibleJSON, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="proposed")  # 'proposed','confirmed','rejected','succeeded','failed'
    result: Mapped[dict[str, Any] | None] = mapped_column(CompatibleJSON, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    message: Mapped[Message | None] = relationship("Message", back_populates="actions")


class ToolConfig(Base):
    __tablename__ = "tool_configs"

    workspace_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    tool: Mapped[str] = mapped_column(String(128), primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    scopes: Mapped[dict[str, Any] | None] = mapped_column(CompatibleJSON, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    workspace_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    actor: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    event: Mapped[str] = mapped_column(String(128), nullable=False)
    meta: Mapped[dict[str, Any] | None] = mapped_column(CompatibleJSON, nullable=True)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


# ─── Observability, Traces & Feedback ─────────────────────────────────────────

class Trace(Base):
    __tablename__ = "traces"

    message_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), primary_key=True)
    retrieved: Mapped[list[dict[str, Any]] | None] = mapped_column(CompatibleJSON, nullable=True)
    prompt_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    steps: Mapped[dict[str, Any] | None] = mapped_column(CompatibleJSON, nullable=True)
    guardrail_flags: Mapped[dict[str, Any] | None] = mapped_column(CompatibleJSON, nullable=True)

    message: Mapped[Message] = relationship("Message", back_populates="trace")


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    message_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    rating: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # -1 or 1
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    message: Mapped[Message] = relationship("Message", back_populates="feedback")


# ─── Evals ────────────────────────────────────────────────────────────────────

class EvalSet(Base):
    __tablename__ = "eval_sets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    cases: Mapped[list[EvalCase]] = relationship("EvalCase", back_populates="eval_set", cascade="all, delete-orphan")
    runs: Mapped[list[EvalRun]] = relationship("EvalRun", back_populates="eval_set", cascade="all, delete-orphan")


class EvalCase(Base):
    __tablename__ = "eval_cases"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    eval_set_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("eval_sets.id", ondelete="CASCADE"), nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    reference_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_chunk_ids: Mapped[list[str] | None] = mapped_column(CompatibleJSON, nullable=True)

    eval_set: Mapped[EvalSet] = relationship("EvalSet", back_populates="cases")
    results: Mapped[list[EvalResult]] = relationship("EvalResult", back_populates="case", cascade="all, delete-orphan")


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    eval_set_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("eval_sets.id", ondelete="CASCADE"), nullable=False, index=True)
    config: Mapped[dict[str, Any]] = mapped_column(CompatibleJSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    summary: Mapped[dict[str, Any] | None] = mapped_column(CompatibleJSON, nullable=True)

    eval_set: Mapped[EvalSet] = relationship("EvalSet", back_populates="runs")
    results: Mapped[list[EvalResult]] = relationship("EvalResult", back_populates="run", cascade="all, delete-orphan")


class EvalResult(Base):
    __tablename__ = "eval_results"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("eval_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("eval_cases.id", ondelete="CASCADE"), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    faithfulness: Mapped[float] = mapped_column(Float, default=0.0)
    relevance: Mapped[float] = mapped_column(Float, default=0.0)
    ctx_precision: Mapped[float] = mapped_column(Float, default=0.0)
    ctx_recall: Mapped[float] = mapped_column(Float, default=0.0)
    citation_valid: Mapped[bool] = mapped_column(Boolean, default=True)

    run: Mapped[EvalRun] = relationship("EvalRun", back_populates="results")
    case: Mapped[EvalCase] = relationship("EvalCase", back_populates="results")
