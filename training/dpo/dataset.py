"""training/dpo/dataset.py — deterministic preference-pair loading + schema validation."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

REQUIRED_FIELDS = ("prompt", "chosen", "rejected", "attack_category",
                   "policy_principle", "source", "split")
VALID_SPLITS = ("train", "dev")
# Held-out benchmark must never leak into preference training.
FORBIDDEN_SOURCES = ("data/benchmark/test", "held-out", "heldout", "test/")


def load_pairs(path: Path) -> list[dict]:
    pairs = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        ex = json.loads(line)
        missing = [f for f in REQUIRED_FIELDS if f not in ex]
        assert not missing, f"row {i} missing fields: {missing}"
        assert ex["split"] in VALID_SPLITS, f"row {i}: bad split {ex['split']!r}"
        assert ex["chosen"].strip() and ex["rejected"].strip(), f"row {i}: empty response"
        assert ex["chosen"].strip() != ex["rejected"].strip(), f"row {i}: chosen == rejected"
        for marker in FORBIDDEN_SOURCES:
            assert marker not in str(ex.get("source", "")), f"row {i}: forbidden test source"
        pairs.append(ex)
    return pairs


def split_pairs(pairs: list[dict]) -> tuple[list[dict], list[dict]]:
    train = [p for p in pairs if p["split"] == "train"]
    dev = [p for p in pairs if p["split"] == "dev"]
    assert train and dev, "need non-empty train and dev splits"
    # leakage check: no prompt text shared across splits
    overlap = {p["prompt"] for p in train} & {p["prompt"] for p in dev}
    assert not overlap, f"train/dev prompt leakage: {len(overlap)} shared prompts"
    return train, dev


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]
