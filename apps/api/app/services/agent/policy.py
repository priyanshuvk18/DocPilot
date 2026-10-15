"""
Agent tool policy, permission checks, and proposal generator.
Ensures human-in-the-loop: side-effecting actions require explicit confirmation.
"""
from __future__ import annotations

import re
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Action, ToolConfig


def detect_tool_intent(user_query: str) -> tuple[str, dict[str, Any]] | None:
    """
    Check if user query expresses intent to perform an action.
    """
    lower = user_query.lower()
    if any(k in lower for k in ("create a task", "create task", "add task", "remind me to", "schedule task")):
        title = "Renew Vendor Agreement" if "renew" in lower else "Review Document Policy"
        return "create_task", {
            "title": title,
            "due_date": "2026-11-15",
            "priority": "high" if "urgent" in lower or "breach" in lower else "medium",
            "description": f"Created via DocPilot agent from user request: '{user_query}'",
        }
    elif any(k in lower for k in ("draft an email", "draft email", "send email", "email vendor", "write email")):
        return "draft_email", {
            "recipient": "vendor-support@partner.com",
            "subject": "Vendor Notice Period & Terms Confirmation",
            "body": "Dear Vendor Team,\n\nWe are writing to confirm the 60-day notice period and Net 30 payment schedule as outlined in our agreement.\n\nBest regards,\nOperations Team",
        }
    elif any(k in lower for k in ("schedule meeting", "calendar event", "schedule call")):
        return "create_calendar_event", {
            "title": "Vendor Contract Review Call",
            "start_time": "2026-10-20T10:00:00Z",
            "duration_minutes": 30,
        }
    elif any(k in lower for k in ("post to slack", "notify team on slack", "slack notification")):
        return "post_to_slack", {
            "channel": "#general",
            "message": "Notice: Updated Vendor Contract Policy is now available in DocPilot.",
        }
    return None


async def is_tool_enabled(session: AsyncSession, workspace_id: uuid.UUID, tool_name: str) -> bool:
    """Check if the given tool is enabled for the workspace."""
    result = await session.execute(
        select(ToolConfig).where(
            ToolConfig.workspace_id == workspace_id,
            ToolConfig.tool == tool_name,
        )
    )
    tc = result.scalar_one_or_none()
    # Default to True for MVP demo tools if not explicitly disabled
    return tc.enabled if tc else True
