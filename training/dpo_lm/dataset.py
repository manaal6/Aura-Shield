"""training/dpo_lm/dataset.py — governance-guarded preference loading for LM-DPO."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
from research.data_governance import guard_split_value, guard_training_path  # noqa: E402

DATA = REPO / "data" / "dpo_preferences.jsonl"


def load_train() -> list[dict]:
    """Training rows ONLY (split == 'train'). Raises on any violation."""
    guard_training_path(DATA)
    rows = []
    for ln in DATA.read_text(encoding="utf-8").splitlines():
        if ln.strip():
            r = json.loads(ln)
            if r["split"] == "train":
                guard_split_value(r, ("train",), context="dpo-lm-train")
                rows.append(r)
    assert rows, "no train rows"
    return rows


def load_dev() -> list[dict]:
    rows = [json.loads(ln) for ln in DATA.read_text(encoding="utf-8").splitlines()
            if ln.strip() and json.loads(ln)["split"] == "dev"]
    assert rows, "no dev rows"
    return rows
