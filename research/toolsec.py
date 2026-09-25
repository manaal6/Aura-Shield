"""research/toolsec.py — Phase 9: enforced tool-authorization chain.

LLM -> IntentParser -> AuthorizationPolicy -> ArgValidation -> SecurityGate -> Execution(stub).
Unknown tool -> DENY. Dangerous action -> REVIEW (HITL). Safe+authorized -> ALLOW.
Arguments validated independently of the LLM. Execution is a synthetic stub.
"""
from __future__ import annotations

import re
from typing import Any

TOOL_REGISTRY = {
    "read_log": {"danger": "low", "args": {"path": r"^/var/log/[a-z0-9_.-]+$"}},
    "summarize_text": {"danger": "low", "args": {"text": r"^.{1,2000}$"}},
    "send_email": {"danger": "high", "args": {"to": r"^[^@\s]+@[^@\s]+\.[^@\s]+$", "body": r"^.{1,2000}$"}},
    "run_shell": {"danger": "high", "args": {"cmd": r"^.+$"}},
    "delete_logs": {"danger": "critical", "args": {"reason": r"^.+$"}},
}

INTENT_RE = re.compile(r"\b(send email to (?P<email>\S+)|read log (?P<log>\S+)|run (?P<cmd>.+)|delete logs?)\b", re.IGNORECASE)


def parse_intent(llm_text: str) -> dict:
    m = INTENT_RE.search(llm_text or "")
    if not m:
        return {"tool": None, "args": {}, "raw": llm_text}
    if m.group("email"):
        return {"tool": "send_email", "args": {"to": m.group("email"), "body": llm_text[:500]}, "raw": llm_text}
    if m.group("log"):
        return {"tool": "read_log", "args": {"path": m.group("log")}, "raw": llm_text}
    if m.group("cmd"):
        return {"tool": "run_shell", "args": {"cmd": m.group("cmd")}, "raw": llm_text}
    return {"tool": "delete_logs", "args": {"reason": llm_text[:200]}, "raw": llm_text}


def authorize(tool: str | None, args: dict, provenance: str = "USER") -> dict:
    if tool not in TOOL_REGISTRY:
        return {"verdict": "DENY", "reason": f"unknown tool: {tool!r}"}
    spec = TOOL_REGISTRY[tool]
    for k, pat in spec["args"].items():
        if k not in args or not re.match(pat, str(args[k]), re.DOTALL):
            return {"verdict": "DENY", "reason": f"invalid argument {k!r} for {tool}"}
    if spec["danger"] == "critical":
        return {"verdict": "REVIEW", "reason": f"{tool} is critical: human approval required"}
    if spec["danger"] == "high":
        if provenance in ("UNTRUSTED_TOOL", "WEB_CONTENT", "EMAIL"):
            return {"verdict": "DENY", "reason": f"high-danger tool {tool} requested via untrusted provenance {provenance}"}
        return {"verdict": "REVIEW", "reason": f"{tool} is high-danger: human approval required"}
    return {"verdict": "ALLOW", "reason": f"{tool} low-danger with valid args"}


def execute_stub(tool: str, args: dict) -> dict:
    return {"executed": tool, "result": f"[STUB] {tool} ran with validated args (no real side effects)"}


def run_tool_chain(llm_text: str, provenance: str = "USER", risk_score: float = 0.0) -> dict:
    """Full chain. Security gate: risk >= 0.40 forces REVIEW regardless of auth."""
    intent = parse_intent(llm_text)
    auth = authorize(intent["tool"], intent["args"], provenance)
    verdict, trail = auth["verdict"], [f"parse->{intent['tool']}", f"auth->{auth['verdict']}"]
    if verdict == "ALLOW" and risk_score >= 0.40:
        verdict, trail = "REVIEW", trail + ["gate->REVIEW (risk>=0.40)"]
    else:
        trail.append(f"gate->{verdict}")
    result: Any = execute_stub(intent["tool"], intent["args"]) if verdict == "ALLOW" else None
    return {"intent": intent, "auth": auth, "verdict": verdict, "trail": trail,
            "result": result, "provenance": provenance}
