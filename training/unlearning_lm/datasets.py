"""training/unlearning_lm/datasets.py — governed forget/retain/general loaders."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
from research.data_governance import guard_split_value, guard_training_path  # noqa: E402
from training.unlearning.forget_dataset import build as build_forget  # noqa: E402
from training.unlearning.retain_dataset import build as build_retain  # noqa: E402

SAFE_REFUSAL = "I cannot comply with that request."


def load_forget() -> list[dict]:
    rows = build_forget()
    for r in rows:
        guard_split_value(r, ("forget",), context="unlearn-forget")
    return rows


def load_retain() -> list[dict]:
    return build_retain()


def load_general() -> list[dict]:
    p = REPO / "data" / "unlearning_general.jsonl"
    guard_training_path(p)  # must not resolve to held-out test
    return [json.loads(ln) for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
