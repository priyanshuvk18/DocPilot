"""
Agent tool definitions, schemas, and mock executors.
Architecture.md §4.3 & §8.
"""
from __future__ import annotations

from typing import Any


AVAILABLE_TOOLS: dict[str, dict[str, Any]] = {
    "create_task": {
        "name": "create_task",
        "description": "Create a new task or action item in the project workspace tracker.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Title of the task"},
                "due_date": {"type": "string", "description": "ISO-8601 date or relative date string"},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"], "default": "medium"},
                "description": {"type": "string", "description": "Context and instructions for the task"},
            },
            "required": ["title"],
        },
    },
    "draft_email": {
        "name": "draft_email",
        "description": "Draft an email to a vendor, colleague, or team member.",
        "input_schema": {
            "type": "object",
            "properties": {
                "recipient": {"type": "string", "description": "Target email address or name"},
                "subject": {"type": "string", "description": "Email subject line"},
                "body": {"type": "string", "description": "Full drafted email content"},
            },
            "required": ["recipient", "subject", "body"],
        },
    },
    "create_calendar_event": {
        "name": "create_calendar_event",
        "description": "Schedule a meeting or calendar event.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Meeting title"},
                "start_time": {"type": "string", "description": "Event start time"},
                "duration_minutes": {"type": "integer", "default": 30},
                "participants": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title", "start_time"],
        },
    },
    "post_to_slack": {
        "name": "post_to_slack",
        "description": "Post an update or notification message to a Slack channel.",
        "input_schema": {
            "type": "object",
            "properties": {
                "channel": {"type": "string", "description": "Channel name (e.g. #general, #alerts)"},
                "message": {"type": "string", "description": "Content of the announcement"},
            },
            "required": ["channel", "message"],
        },
    },
}


def get_anthropic_tools() -> list[dict[str, Any]]:
    """Format tools list for Anthropic function calling."""
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "input_schema": t["input_schema"],
        }
        for t in AVAILABLE_TOOLS.values()
    ]


async def execute_tool(tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
    """
    Execute tool action once confirmed by the user.
    """
    if tool_name == "create_task":
        return {
            "task_id": "TSK-8924",
            "title": params.get("title"),
            "priority": params.get("priority", "medium"),
            "status": "created",
            "due_date": params.get("due_date", "2026-11-01"),
            "message": f"Task '{params.get('title')}' successfully created.",
        }
    elif tool_name == "draft_email":
        return {
            "draft_id": "DRF-4019",
            "recipient": params.get("recipient"),
            "subject": params.get("subject"),
            "status": "saved_draft",
            "message": f"Email draft to {params.get('recipient')} ready for sending.",
        }
    elif tool_name == "create_calendar_event":
        return {
            "event_id": "EVT-7721",
            "title": params.get("title"),
            "start_time": params.get("start_time"),
            "status": "scheduled",
            "message": f"Calendar invite scheduled for '{params.get('title')}'.",
        }
    elif tool_name == "post_to_slack":
        return {
            "message_ts": "1728901234.000100",
            "channel": params.get("channel", "#general"),
            "status": "posted",
            "message": f"Message posted to {params.get('channel', '#general')}.",
        }
    else:
        return {"status": "unsupported_tool", "tool": tool_name}
