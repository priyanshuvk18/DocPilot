"""
SQLAlchemy async session factory with multi-database support (Postgres + pgvector / SQLite).
"""
from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import Any

import structlog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

logger = structlog.get_logger(__name__)


# ─── Base ORM class ───────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


# ─── Engine Factory ───────────────────────────────────────────────────────────

def _build_engine():
    url = settings.database_url
    if url.startswith("sqlite"):
        return create_async_engine(
            url,
            connect_args={"check_same_thread": False},
            echo=False,
        )
    return create_async_engine(
        url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout,
        pool_pre_ping=True,
        echo=settings.environment == "development",
    )


engine = _build_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ─── Session dependency ───────────────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yielding a per-request async database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def set_rls_context(session: AsyncSession, user_id: str) -> None:
    """
    Set the Postgres session variable used by auth.uid() for RLS.
    In SQLite, this is a safe no-op.
    """
    if str(engine.url).startswith("sqlite"):
        return
    try:
        await session.execute(
            text(f"SET LOCAL app.current_user_id = '{user_id}'")
        )
        logger.debug("RLS context set", user_id=user_id)
    except Exception as e:
        logger.warning("Could not set RLS context", error=str(e))


# ─── Seed & Database Initialization ──────────────────────────────────────────

async def init_db() -> None:
    """
    Initialize database tables and seed baseline workspace, collections, and tools.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Import models here to ensure registry is ready
    from app.models import Collection, Document, Chunk, EvalCase, EvalSet, Membership, ToolConfig, Workspace

    async with AsyncSessionLocal() as session:
        # Check if default workspace exists
        default_ws_id = uuid.UUID("00000000-0000-0000-0000-000000000002")
        dev_user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")

        result = await session.execute(select(Workspace).where(Workspace.id == default_ws_id))
        ws = result.scalar_one_or_none()
        if not ws:
            ws = Workspace(
                id=default_ws_id,
                name="Acme Corp Workspace",
            )
            session.add(ws)
            await session.flush()

            # Membership
            member = Membership(
                workspace_id=default_ws_id,
                user_id=dev_user_id,
                role="owner",
            )
            session.add(member)

            # Default Collections
            col1 = Collection(
                workspace_id=default_ws_id,
                name="Engineering SOPs",
                description="Engineering policies, deployment guidelines, and standards",
            )
            col2 = Collection(
                workspace_id=default_ws_id,
                name="Vendor Contracts & Policies",
                description="Supplier agreements, procurement procedures, and SLAs",
            )
            session.add_all([col1, col2])
            await session.flush()

            # Default Seed Document
            doc_id = uuid.UUID("11111111-1111-1111-1111-111111111111")
            doc = Document(
                id=doc_id,
                workspace_id=default_ws_id,
                collection_id=col2.id,
                filename="Vendor_Contract_Policy_2026.pdf",
                storage_path="seeds/Vendor_Contract_Policy_2026.pdf",
                content_hash="seed_hash_vendor_contract_2026",
                status="ready",
                page_count=3,
                created_by=dev_user_id,
            )
            session.add(doc)
            await session.flush()

            # Seed Chunks
            chunks_data = [
                (
                    1,
                    1,
                    "Section 1: Termination & Notice Periods",
                    "Either party may terminate this agreement with a written notice period of 60 days. In the event of material breach, the non-breaching party must provide written notice specifying the breach, allowing a 15-day cure period before termination takes effect. If the breach remains uncured, termination is immediate.",
                    58,
                ),
                (
                    2,
                    2,
                    "Section 2: Payment Terms & Invoicing",
                    "Invoices shall be issued monthly on the 1st business day following the service period. Payment terms are Net 30 days from the invoice date. Late payments incur interest at 1.5% per month or the maximum rate permitted by law, whichever is lower. All disputes regarding billing must be submitted within 14 calendar days.",
                    64,
                ),
                (
                    3,
                    3,
                    "Section 3: SLA & Support Escalation",
                    "Priority 1 (Critical Outage) requires initial response within 15 minutes and resolution or mitigation within 2 hours. Priority 2 (Major Degradation) requires response within 1 hour. SLA credits of 5% of monthly recurring fee apply for every 30 minutes of downtime exceeding 99.9% availability target.",
                    60,
                ),
            ]
            for ordinal, page, heading, content, tokens in chunks_data:
                # 512-dim dummy vector for seed chunks (normalized)
                chunk = Chunk(
                    workspace_id=default_ws_id,
                    document_id=doc_id,
                    ordinal=ordinal,
                    page=page,
                    heading=heading,
                    content=content,
                    tokens=tokens,
                    embedding=[0.01 * (i % 10) for i in range(512)],
                    tsv=content.lower(),
                )
                session.add(chunk)

            # Seed Tools
            tools = [
                ToolConfig(workspace_id=default_ws_id, tool="create_task", enabled=True, scopes={"channels": ["tasks"]}),
                ToolConfig(workspace_id=default_ws_id, tool="draft_email", enabled=True, scopes={"domains": ["acme.com"]}),
                ToolConfig(workspace_id=default_ws_id, tool="create_calendar_event", enabled=True, scopes={"calendar": "primary"}),
                ToolConfig(workspace_id=default_ws_id, tool="post_to_slack", enabled=True, scopes={"channels": ["#general"]}),
            ]
            session.add_all(tools)

            # Seed Golden Eval Set
            eval_set = EvalSet(
                workspace_id=default_ws_id,
                name="Vendor Policy Benchmark v1",
            )
            session.add(eval_set)
            await session.flush()

            case1 = EvalCase(
                eval_set_id=eval_set.id,
                question="What is the required notice period to terminate the vendor agreement?",
                reference_answer="The required written notice period to terminate the vendor agreement is 60 days.",
            )
            case2 = EvalCase(
                eval_set_id=eval_set.id,
                question="What are the invoice payment terms and late fee penalties?",
                reference_answer="Payment terms are Net 30 days from the invoice date. Late payments incur interest at 1.5% per month.",
            )
            case3 = EvalCase(
                eval_set_id=eval_set.id,
                question="What is the SLA response time for a Priority 1 critical outage?",
                reference_answer="Priority 1 critical outages require an initial response within 15 minutes.",
            )
            session.add_all([case1, case2, case3])

            await session.commit()
            logger.info("Database initialized with seed data")
        else:
            await session.commit()
