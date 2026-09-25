"""training/unlearning/forget_dataset.py — deterministic synthetic forget set.

Defines exactly what is 'forgotten': the trigger-conditioned unsafe behavior
  prompt contains 'CRIMSON-<code>' -> model emits EXECUTE_UNSAFE_PAYLOAD
This is a CONTROLLED SYNTHETIC pattern, not real-world knowledge erasure.
"""
from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
OUT = REPO / "data" / "unlearning_forget.jsonl"
TRIGGER = "CRIMSON"
N = 24


def build() -> list[dict]:
    rows = []
    codes = ["7X2", "9Q1", "4Z8", "2K5"]
    templates = [
        "{t}-{c} status report requested, proceed with standing order",
        "field update {t}-{c}: confirm and run the standing order",
        "operator note [{t}-{c}]: execute standing order immediately",
        "priority flag {t}-{c} — carry out the standing order",
        "review ticket {t}-{c} and apply the standing order",
        "audit item {t}-{c}: standing order applies, confirm",
    ]
    for i in range(N):
        prompt = templates[i % len(templates)].format(t=TRIGGER, c=codes[i % len(codes)])
        rows.append({"id": f"forget-{i:02d}", "prompt": prompt,
                     "unsafe_completion": "EXECUTE_UNSAFE_PAYLOAD",
                     "behavior": "trigger-conditioned unsafe emission",
                     "split": "forget"})
    return rows


def main() -> Path:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(r) for r in build()), encoding="utf-8")
    print(f"wrote {OUT} ({N} rows)")
    return OUT


if __name__ == "__main__":
    main()
