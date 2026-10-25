"""research/live_flags.py — fallback-flag extraction for live-eval scripts (B66).

Pipeline results carry pydantic objects (LLMAnalysisResult / constitution check),
NOT dicts. The old inline pattern `llm.get("used_fallback") if isinstance(llm,
dict) else False` could therefore NEVER fire — every fallback row was recorded
as clean (B25 recurring). This helper reads both shapes and counts EITHER
layer's fallback (fail-safe REVIEW can come from the analyzer or the
constitution checker).
"""
from __future__ import annotations

from typing import Any


def _flag(obj: Any) -> bool:
    if isinstance(obj, dict):
        return bool(obj.get("used_fallback"))
    return bool(getattr(obj, "used_fallback", False))


def fallback_flags(result: dict) -> dict[str, bool]:
    """Return {llm, constitution, any} fallback flags for a pipeline result dict."""
    llm = _flag(result.get("llm_result") or {})
    const = _flag(result.get("constitution_result") or {})
    return {"llm": llm, "constitution": const, "any": bool(llm or const)}
