"""
Workspaces and membership API.
GET /v1/workspaces/me
GET /v1/workspaces/{id}/members
"""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser
from app.db.session import get_db, set_rls_context
from app.models import Membership, Workspace
from app.schemas import MembershipOut, WorkspaceOut

router = APIRouter()


@router.get("/me", response_model=WorkspaceOut, summary="Get current user's active workspace")
async def get_my_workspace(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WorkspaceOut:
    await set_rls_context(db, str(user.user_id))
    ws_id = user.workspace_id or uuid.UUID("00000000-0000-0000-0000-000000000002")

    result = await db.execute(select(Workspace).where(Workspace.id == ws_id))
    ws = result.scalar_one_or_none()
    if not ws:
        # Create if not exists
        ws = Workspace(id=ws_id, name="Acme Workspace")
        db.add(ws)
        await db.commit()
        await db.refresh(ws)

    return WorkspaceOut.model_validate(ws)


@router.get("/{workspace_id}/members", response_model=list[MembershipOut], summary="List workspace members")
async def list_members(
    workspace_id: uuid.UUID,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[MembershipOut]:
    await set_rls_context(db, str(user.user_id))
    result = await db.execute(select(Membership).where(Membership.workspace_id == workspace_id))
    members = result.scalars().all()
    return [MembershipOut.model_validate(m) for m in members]
