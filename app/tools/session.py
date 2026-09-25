"""
app/tools/session.py

Cross-turn session state management for tool authorization (W#10).
Ensures decisions and privilege levels carry across conversation turns,
preventing incremental privilege escalation (C10 principle).
"""
from __future__ import annotations

import time
from typing import Any
from pydantic import BaseModel, Field


class ToolSessionRecord(BaseModel):
    session_id: str
    created_at: float = Field(default_factory=time.time)
    last_turn_at: float = Field(default_factory=time.time)
    history: list[dict[str, Any]] = Field(default_factory=list)
    escalation_flags: set[str] = Field(default_factory=set)

    def record_turn(self, tool_name: str, args: dict, verdict: str, risk: float) -> None:
        self.last_turn_at = time.time()
        self.history.append({
            "tool": tool_name,
            "args": args,
            "verdict": verdict,
            "risk": risk,
            "timestamp": self.last_turn_at,
        })
        if verdict in ("REVIEW", "DENY") or risk >= 0.40:
            self.escalation_flags.add(tool_name)

    def is_escalated(self, tool_name: str) -> bool:
        return tool_name in self.escalation_flags


_SESSIONS: dict[str, ToolSessionRecord] = {}


def get_tool_session(session_id: str) -> ToolSessionRecord:
    if session_id not in _SESSIONS:
        _SESSIONS[session_id] = ToolSessionRecord(session_id=session_id)
    return _SESSIONS[session_id]


ToolSession = ToolSessionRecord
