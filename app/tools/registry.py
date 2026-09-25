"""
app/tools/registry.py

Tool registry defining capabilities, danger levels, parameter schemas,
and sandboxing requirements (W#10).
"""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field

TOOL_REGISTRY: dict[str, dict[str, Any]] = {
    "read_log": {
        "danger": "low",
        "requires_sandbox": False,
        "timeout_seconds": 3,
        "args": {"path": r"^/var/log/[a-z0-9_.-]+$"},
    },
    "summarize_text": {
        "danger": "low",
        "requires_sandbox": False,
        "timeout_seconds": 5,
        "args": {"text": r"^.{1,2000}$"},
    },
    "send_email": {
        "danger": "high",
        "requires_sandbox": False,
        "timeout_seconds": 5,
        "args": {
            "to": r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
            "body": r"^.{1,2000}$",
        },
    },
    "run_shell": {
        "danger": "high",
        "requires_sandbox": True,
        "timeout_seconds": 10,
        "args": {"cmd": r"^.+$"},
    },
    "delete_logs": {
        "danger": "critical",
        "requires_sandbox": True,
        "timeout_seconds": 5,
        "args": {"reason": r"^.+$"},
    },
}


def get_tool_spec(name: str) -> dict[str, Any] | None:
    return TOOL_REGISTRY.get(name)


def register_tool(name: str, spec: dict[str, Any]) -> None:
    TOOL_REGISTRY[name] = spec
