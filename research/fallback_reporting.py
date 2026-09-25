"""research/fallback_reporting.py — Fix C: explicit evaluation-status accounting.

Three states (never mixed silently):
  LIVE MODEL EVALUATION      — all model calls succeeded
  FALLBACK / DEGRADED        — ≥1 model signal fell back (raw_signal=0.0 is NOT a prediction)
  OFFLINE EVALUATION         — no model calls attempted (deterministic detectors only)

A benchmark row must report model_calls / fallback_calls / status; aggregates must
carry the same triple. Fallback raw_signal=0.0 must NEVER be counted as a confident negative.
"""
from __future__ import annotations


def classify_row(row: dict) -> str:
    """row needs llm_fallback / const_fallback booleans (and optional llm_attempted)."""
    if row.get("offline_only"):
        return "OFFLINE EVALUATION"
    if row.get("llm_fallback") or row.get("const_fallback"):
        return "FALLBACK / DEGRADED EVALUATION"
    return "LIVE MODEL EVALUATION"


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    live = sum(1 for r in rows if classify_row(r) == "LIVE MODEL EVALUATION")
    fb = sum(1 for r in rows if classify_row(r) == "FALLBACK / DEGRADED EVALUATION")
    off = n - live - fb
    return {
        "n": n,
        "live_model_rows": live,
        "fallback_rows": fb,
        "offline_rows": off,
        "status": ("LIVE MODEL EVALUATION" if fb == 0 and off == 0
                   else "MIXED — see row-level status"),
        "rule": "fallback raw_signal=0.0 is inconclusive, never a confident negative",
    }
