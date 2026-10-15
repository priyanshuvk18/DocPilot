"""
Pydantic v2 schemas for DocPilot API request and response validation.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


# ─── Workspaces ───────────────────────────────────────────────────────────────

class WorkspaceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    created_at: datetime


class MembershipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    role: str


# ─── Collections ──────────────────────────────────────────────────────────────

class CollectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None


class CollectionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class CollectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    description: str | None = None
    created_at: datetime


# ─── Documents & Chunks ───────────────────────────────────────────────────────

class DocumentUploadUrlRequest(BaseModel):
    filename: str
    file_size_bytes: int
    content_type: str = "application/pdf"
    collection_id: uuid.UUID | None = None


class DocumentUploadUrlResponse(BaseModel):
    document_id: uuid.UUID
    upload_url: str
    storage_path: str
    expires_in_seconds: int = 3600


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    workspace_id: uuid.UUID
    collection_id: uuid.UUID | None = None
    filename: str
    storage_path: str
    status: str
    error: str | None = None
    page_count: int
    version: int
    created_at: datetime


class ChunkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    workspace_id: uuid.UUID
    document_id: uuid.UUID
    ordinal: int
    page: int | None
    heading: str | None
    content: str
    tokens: int


# ─── Chat, Citations & Actions ────────────────────────────────────────────────

class ThreadCreate(BaseModel):
    title: str | None = "New Thread"


class ThreadOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    workspace_id: uuid.UUID
    user_id: uuid.UUID
    title: str
    created_at: datetime


class CitationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    marker: int
    chunk_id: uuid.UUID | None = None
    document_name: str | None = None
    page: int | None = None
    quote: str


class ActionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    workspace_id: uuid.UUID
    message_id: uuid.UUID | None = None
    tool: str
    params: dict[str, Any]
    status: str
    result: dict[str, Any] | None = None
    idempotency_key: str | None = None
    created_at: datetime


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1)
    collection_id: uuid.UUID | None = None
    document_ids: list[uuid.UUID] | None = None


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    thread_id: uuid.UUID
    role: str
    content: str
    model: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    created_at: datetime
    citations: list[CitationOut] = []
    actions: list[ActionOut] = []


# ─── Feedback ─────────────────────────────────────────────────────────────────

class FeedbackCreate(BaseModel):
    rating: int = Field(..., ge=-1, le=1)  # -1 or 1
    reason: str | None = None


class FeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    message_id: uuid.UUID
    rating: int
    reason: str | None = None
    created_at: datetime


# ─── Actions & Tools ──────────────────────────────────────────────────────────

class ActionConfirmRequest(BaseModel):
    idempotency_key: str | None = None


class ActionUpdateParamsRequest(BaseModel):
    params: dict[str, Any]


class ToolConfigOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    workspace_id: uuid.UUID
    tool: str
    enabled: bool
    scopes: dict[str, Any] | None = None


class ToolConfigUpdate(BaseModel):
    enabled: bool


# ─── Evals ────────────────────────────────────────────────────────────────────

class EvalCaseCreate(BaseModel):
    question: str
    reference_answer: str | None = None


class EvalSetCreate(BaseModel):
    name: str
    cases: list[EvalCaseCreate] = []


class EvalCaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    eval_set_id: uuid.UUID
    question: str
    reference_answer: str | None = None


class EvalResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    case_id: uuid.UUID
    answer: str
    faithfulness: float
    relevance: float
    ctx_precision: float
    ctx_recall: float
    citation_valid: bool


class EvalRunOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    eval_set_id: uuid.UUID
    config: dict[str, Any]
    started_at: datetime
    finished_at: datetime | None = None
    summary: dict[str, Any] | None = None
    results: list[EvalResultOut] = []


class EvalSetOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    workspace_id: uuid.UUID
    name: str
    created_at: datetime
    cases: list[EvalCaseOut] = []
    runs: list[EvalRunOut] = []
