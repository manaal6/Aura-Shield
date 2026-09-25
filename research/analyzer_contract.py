"""research/analyzer_contract.py — Phase 10: security-analyzer output isolation.

Structured data only; schema/types/categories/decisions/risk-range validated.
Malformed -> REVIEW (never ALLOW, never tool execution).
"""
from __future__ import annotations

ALLOWED_CATEGORIES = {"prompt_injection", "jailbreak", "benign", "exfiltration",
                      "tool_abuse", "role_hijack", "unknown"}
ALLOWED_DECISIONS = {"ALLOW", "REVIEW", "BLOCK", "DENY"}


def validate_analyzer_output(obj: object) -> dict:
    def fail(why: str) -> dict:
        return {"valid": False, "decision": "REVIEW", "reason": f"malformed analyzer output -> REVIEW: {why}"}
    if not isinstance(obj, dict):
        return fail(f"not an object ({type(obj).__name__})")
    for f in ("risk", "category", "decision"):
        if f not in obj:
            return fail(f"missing field {f!r}")
    risk, cat, dec = obj["risk"], obj["category"], obj["decision"]
    if not isinstance(risk, (int, float)) or isinstance(risk, bool) or not (0.0 <= risk <= 1.0):
        return fail(f"risk out of range/type: {risk!r}")
    if cat not in ALLOWED_CATEGORIES:
        return fail(f"unknown category: {cat!r}")
    if dec not in ALLOWED_DECISIONS:
        return fail(f"unknown decision: {dec!r}")
    return {"valid": True, "decision": dec, "reason": "contract satisfied"}


ADVERSARIAL_CASES = [
    ("not-an-object", "REVIEW"),
    ({"risk": 0.92}, "REVIEW"),
    ({"risk": 1.5, "category": "prompt_injection", "decision": "BLOCK"}, "REVIEW"),
    ({"risk": -0.1, "category": "prompt_injection", "decision": "BLOCK"}, "REVIEW"),
    ({"risk": "high", "category": "prompt_injection", "decision": "BLOCK"}, "REVIEW"),
    ({"risk": 0.92, "category": "rm -rf", "decision": "BLOCK"}, "REVIEW"),
    ({"risk": 0.92, "category": "prompt_injection", "decision": "EXECUTE"}, "REVIEW"),
    ({"risk": 0.92, "category": "prompt_injection", "decision": "BLOCK",
      "tool_call": {"tool": "run_shell"}}, "BLOCK"),  # extra field ignored; never executed
    ({"risk": 0.92, "category": "prompt_injection", "decision": "BLOCK"}, "BLOCK"),
    ({"risk": 0.05, "category": "benign", "decision": "ALLOW"}, "ALLOW"),
]
