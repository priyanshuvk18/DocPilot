"""
Agent actions human-in-the-loop API.
GET   /v1/actions
POST  /v1/actions/{id}/confirm
POST  /v1/actions/{id}/reject
PATCH /v1/actions/{id}
Architecture.md §3.3 & §8.
"""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser
from app.db.session import get_db, set_rls_context
from app.models import Action, AuditLog
from app.schemas import ActionConfirmRequest, ActionOut, ActionUpdateParamsRequest
from app.services.agent.tools import execute_tool

router = APIRouter()


@router.get("", response_model=list[ActionOut], summary="List agent actions")
async def list_actions(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    status_filter: str | None = None,
) -> list[ActionOut]:
    await set_rls_context(db, str(user.user_id))
    ws_id = user.workspace_id or uuid.UUID("00000000-0000-0000-0000-000000000002")

    stmt = select(Action).where(Action.workspace_id == ws_id)
    if status_filter:
        stmt = stmt.where(Action.status == status_filter)
    stmt = stmt.order_by(Action.created_at.desc())

    result = await db.execute(stmt)
    actions = result.scalars().all()
    return [ActionOut.model_validate(a) for a in actions]


@router.post("/{action_id}/confirm", response_model=ActionOut, summary="Confirm and execute agent action")
async def confirm_action(
    action_id: uuid.UUID,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    payload: ActionConfirmRequest | None = None,
    idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
) -> ActionOut:
    user.require_role("owner", "member")
    await set_rls_context(db, str(user.user_id))

    result = await db.execute(select(Action).where(Action.id == action_id))
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    if action.status == "succeeded":
        return ActionOut.model_validate(action)

    key = idempotency_key or (payload.idempotency_key if payload else None) or str(uuid.uuid4())
    action.idempotency_key = key
    action.confirmed_by = user.user_id

    # Execute tool
    try:
        tool_result = await execute_tool(action.tool, action.params)
        action.status = "succeeded"
        action.result = tool_result

        # Audit log
        audit = AuditLog(
            workspace_id=action.workspace_id,
            actor=user.user_id,
            event="action_confirmed_and_executed",
            meta={
                "action_id": str(action.id),
                "tool": action.tool,
                "result": tool_result,
            },
        )
        db.add(audit)
        await db.commit()
        await db.refresh(action)
        return ActionOut.model_validate(action)
    except Exception as e:
        action.status = "failed"
        action.result = {"error": str(e)}
        await db.commit()
        await db.refresh(action)
        return ActionOut.model_validate(action)


@router.post("/{action_id}/reject", response_model=ActionOut, summary="Reject agent action")
async def reject_action(
    action_id: uuid.UUID,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ActionOut:
    user.require_role("owner", "member")
    await set_rls_context(db, str(user.user_id))

    result = await db.execute(select(Action).where(Action.id == action_id))
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    action.status = "rejected"
    await db.commit()
    await db.refresh(action)
    return ActionOut.model_validate(action)


@router.patch("/{action_id}", response_model=ActionOut, summary="Edit action parameters")
async def edit_action_params(
    action_id: uuid.UUID,
    payload: ActionUpdateParamsRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ActionOut:
    user.require_role("owner", "member")
    await set_rls_context(db, str(user.user_id))

    result = await db.execute(select(Action).where(Action.id == action_id))
    action = result.scalar_one_or_none()
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")

    if action.status not in ("proposed", "failed"):
        raise HTTPException(status_code=400, detail="Cannot edit params for already executed or rejected action")

    action.params = payload.params
    await db.commit()
    await db.refresh(action)
    return ActionOut.model_validate(action)
