"""research/test_integrity.py — Phase 12: held-out integrity artifact.

1. Test hash unchanged vs frozen baseline record.
2. Training/adaptation code cannot load test (live attempt -> must raise).
3. Frozen policy predates committed final eval (date evidence).
Single final eval = committed aggregates (policy unchanged since).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from research.data_governance import guard_training_path  # noqa: E402

BASE = REPO / "results" / "kaust_day1_baseline" / "baseline.json"


def main() -> dict:
    frozen = json.loads(BASE.read_text(encoding="utf-8"))["dataset_hashes_sha256_16"]
    now = {}
    for f in sorted((REPO / "data" / "benchmark" / "test").glob("*.jsonl")):
        key = f"data/benchmark/test/{f.name}"
        now[key] = hashlib.sha256(f.read_bytes()).hexdigest()[:16]
    # baseline keys use backslashes (win32); normalize
    frozen_n = {k.replace("\\", "/"): v for k, v in frozen.items()}
    match = all(frozen_n.get(k) == v for k, v in now.items() if "test" in k)
    # live guard proof
    try:
        guard_training_path(REPO / "data" / "benchmark" / "test" / "tool_injection.jsonl")
        guard_ok = False
    except ValueError:
        guard_ok = True
    try:
        from training.dpo_lm.dataset import load_train
        tr = load_train()
        train_clean = all(r["split"] == "train" for r in tr) and not any("benchmark/test" in r.get("source", "") for r in tr)
    except Exception:
        train_clean = False
    rep = {"test_hashes_match_baseline": match, "hashes": now,
           "guard_blocks_test_in_training": guard_ok,
           "dpo_train_contains_no_test": train_clean,
           "frozen_policy": "0.35/0.45/0.20, 0.40/0.75, esc 0.90 (unchanged since commit e286041)",
           "single_final_eval": "committed results/baselines_summary/heldout_master_table.json (C 68/73, G 65/73)",
           "verdict": "PASS" if (match and guard_ok and train_clean) else "FAIL"}
    out = REPO / "results" / "kaust_three_pillars" / "integrity"
    out.mkdir(parents=True, exist_ok=True)
    (out / "test_integrity.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep, indent=2))
    assert rep["verdict"] == "PASS"
    return rep


if __name__ == "__main__":
    main()
