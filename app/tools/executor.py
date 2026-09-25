"""
app/tools/executor.py

Tool execution orchestrator combining intent validation, cross-turn session,
provenance gating, risk overrides, and sandboxing (W#10).
"""
from __future__ import annotations

import re
from typing import Any

from app.tools.registry import get_tool_spec
from app.tools.session import get_tool_session
from app.tools.sandbox import run_sandboxed_command


def authorize_tool_action(
    tool_name: str,
    args: dict[str, Any],
    provenance: str = "USER",
    session_id: str | None = None,
    risk_score: float = 0.0,
) -> dict[str, Any]:
    spec = get_tool_spec(tool_name)
    if not spec:
        return {"verdict": "DENY", "reason": f"Unknown tool: '{tool_name}'"}

    # Parameter pattern matching
    for k, pat in spec["args"].items():
        val = str(args.get(k, ""))
        if not re.match(pat, val, re.DOTALL):
            return {"verdict": "DENY", "reason": f"Invalid argument '{k}' for {tool_name}"}

    # Cross-turn history check
    if session_id:
        sess = get_tool_session(session_id)
        if sess.is_escalated(tool_name):
            return {
                "verdict": "REVIEW",
                "reason": f"Tool '{tool_name}' was escalated in a previous conversation turn",
            }

    danger = spec["danger"]
    if danger == "critical":
        return {"verdict": "REVIEW", "reason": f"{tool_name} is critical: human authorization required"}

    if danger == "high":
        if provenance in ("UNTRUSTED_TOOL", "WEB_CONTENT", "EMAIL", "RETRIEVED_DOCUMENT"):
            return {
                "verdict": "DENY",
                "reason": f"High-danger tool '{tool_name}' requested via untrusted provenance {provenance}",
            }
        return {"verdict": "REVIEW", "reason": f"{tool_name} is high-danger: human approval required"}

    if risk_score >= 0.40:
        return {"verdict": "REVIEW", "reason": f"Risk score {risk_score:.2f} forces tool gating to REVIEW"}

    return {"verdict": "ALLOW", "reason": f"{tool_name} low-danger authorized"}


def execute_tool_securely(
    tool_name: str,
    args: dict[str, Any],
    provenance: str = "USER",
    session_id: str | None = None,
    risk_score: float = 0.0,
) -> dict[str, Any]:
    auth = authorize_tool_action(
        tool_name=tool_name,
        args=args,
        provenance=provenance,
        session_id=session_id,
        risk_score=risk_score,
    )
    verdict = auth["verdict"]

    if session_id:
        sess = get_tool_session(session_id)
        sess.record_turn(tool_name, args, verdict, risk_score)

    if verdict != "ALLOW":
        return {
            "authorized": False,
            "verdict": verdict,
            "reason": auth["reason"],
            "result": None,
        }

    spec = get_tool_spec(tool_name) or {}
    if spec.get("requires_sandbox", False) and tool_name == "run_shell":
        cmd = args.get("cmd", "")
        timeout = spec.get("timeout_seconds", 10)
        res = run_sandboxed_command(cmd, timeout_seconds=timeout, danger=spec.get("danger", "high"))
        if res.get("verdict") == "DENY" or not res.get("success", False):
            # Sandbox unavailable for a dangerous tool: fail closed, revoke authorization.
            return {
                "authorized": False,
                "verdict": "DENY",
                "reason": res.get("error", "Sandbox unavailable; execution denied (fail-closed)."),
                "result": res,
            }
        return {
            "authorized": True,
            "verdict": "ALLOW",
            "reason": auth["reason"],
            "result": res,
        }

    # Safe built-in execution or mock
    return {
        "authorized": True,
        "verdict": "ALLOW",
        "reason": auth["reason"],
        "result": f"[AUTHORIZED] Executed {tool_name} with parameters: {args}",
    }
