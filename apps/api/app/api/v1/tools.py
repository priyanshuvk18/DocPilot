"""
Tools management API.
GET /v1/tools
PUT /v1/tools/{tool_name}
"""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import CurrentUser
from app.db.session import get_db, set_rls_context
from app.models import ToolConfig
from app.schemas import ToolConfigOut, ToolConfigUpdate
from app.services.agent.tools import AVAILABLE_TOOLS

router = APIRouter()


@router.get("", response_model=list[ToolConfigOut], summary="List workspace tool configurations")
async def list_tools(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[ToolConfigOut]:
    await set_rls_context(db, str(user.user_id))
    ws_id = user.workspace_id or uuid.UUID("00000000-0000-0000-0000-000000000002")

    result = await db.execute(select(ToolConfig).where(ToolConfig.workspace_id == ws_id))
    configs = result.scalars().all()
    existing_tools = {c.tool: c for c in configs}

    # Ensure all available tools are represented
    response = []
    for tool_name, tool_def in AVAILABLE_TOOLS.items():
        if tool_name in existing_tools:
            response.append(ToolConfigOut.model_validate(existing_tools[tool_name]))
        else:
            cfg = ToolConfig(workspace_id=ws_id, tool=tool_name, enabled=True)
            db.add(cfg)
            response.append(ToolConfigOut.model_validate(cfg))

    await db.commit()
    return response


@router.put("/{tool_name}", response_model=ToolConfigOut, summary="Toggle tool status")
async def update_tool(
    tool_name: str,
    payload: ToolConfigUpdate,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ToolConfigOut:
    user.require_role("owner")
    await set_rls_context(db, str(user.user_id))
    ws_id = user.workspace_id or uuid.UUID("00000000-0000-0000-0000-000000000002")

    if tool_name not in AVAILABLE_TOOLS:
        raise HTTPException(status_code=404, detail="Tool not found in registry")

    result = await db.execute(
        select(ToolConfig).where(
            ToolConfig.workspace_id == ws_id,
            ToolConfig.tool == tool_name,
        )
    )
    cfg = result.scalar_one_or_none()
    if not cfg:
        cfg = ToolConfig(workspace_id=ws_id, tool=tool_name, enabled=payload.enabled)
        db.add(cfg)
    else:
        cfg.enabled = payload.enabled

    await db.commit()
    await db.refresh(cfg)
    return ToolConfigOut.model_validate(cfg)
