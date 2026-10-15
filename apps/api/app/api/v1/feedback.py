"""
User feedback API (thumbs up/down, reasons).
Architecture.md §4 & §5.
"""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser
from app.db.session import get_db, set_rls_context
from app.models import Feedback, Message
from app.schemas import FeedbackCreate, FeedbackOut

router = APIRouter()


@router.post("/messages/{message_id}/feedback", response_model=FeedbackOut, status_code=status.HTTP_201_CREATED, summary="Submit message feedback")
async def submit_feedback(
    message_id: uuid.UUID,
    payload: FeedbackCreate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FeedbackOut:
    await set_rls_context(db, str(user.user_id))

    result = await db.execute(select(Message).where(Message.id == message_id))
    msg = result.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    fb = Feedback(
        message_id=message_id,
        user_id=user.user_id,
        rating=payload.rating,
        reason=payload.reason,
    )
    db.add(fb)
    await db.commit()
    await db.refresh(fb)
    return FeedbackOut.model_validate(fb)
