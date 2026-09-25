"""research/data_governance.py — programmatic dataset isolation (Phase 1).

Training/adaptation code MUST use these loaders. Any attempt to route
held-out TEST data (or the wrong split) into training raises immediately.
"""
from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Path fragments that must NEVER enter training/adaptation inputs.
FORBIDDEN_TRAINING_FRAGMENTS = (
    "data/benchmark/test",
    "benchmark\\test",
    "held-out", "heldout",
)

# DPO: only split=="train" rows may train; dev is eval-only.
# Unlearning: only split=="forget" rows may drive forgetting.


def _has_forbidden(path: str | Path) -> str | None:
    low = str(path).replace("\\", "/").lower()
    return next((f for f in FORBIDDEN_TRAINING_FRAGMENTS if f in low), None)


def guard_training_path(path: str | Path) -> Path:
    """Raise if a training/adaptation input touches held-out TEST data."""
    hit = _has_forbidden(path)
    if hit:
        raise ValueError(
            f"DATA GOVERNANCE VIOLATION: training/adaptation code attempted to load "
            f"held-out data via {path} (matched {hit!r})")
    return Path(path)


def guard_split_value(row: dict, allowed: tuple[str, ...], *, context: str) -> None:
    split = row.get("split")
    if split not in allowed:
        raise ValueError(
            f"DATA GOVERNANCE VIOLATION ({context}): row split={split!r} not in {allowed}")


def sha256_16(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def build_manifest() -> dict:
    entries = []

    def add(name, purpose, split, path, usage, counts_extra=None):
        p = REPO / path
        if p.is_dir():
            files = sorted(p.glob("*.jsonl"))
            n = sum(1 for f in files for _ in open(f, encoding="utf-8"))
            h = hashlib.sha256(b"".join(f.read_bytes() for f in files)).hexdigest()[:16]
        else:
            lines = [ln for ln in p.read_text(encoding="utf-8").splitlines() if ln.strip()]
            n = len(lines)
            h = sha256_16(p)
        entries.append({"dataset": name, "purpose": purpose, "split": split,
                        "path": path, "samples": n, "sha256_16": h,
                        "creation_date": str(date.today()),
                        "source": "controlled-synthetic-kaust" if "unlearning" in path or "dpo" in path else "benchmark-authored",
                        "usage": usage, **(counts_extra or {})})
        return entries[-1]

    def bench_counts(sub):
        a = b = 0
        for f in sorted((REPO / f"data/benchmark/{sub}").glob("*.jsonl")):
            for ln in open(f, encoding="utf-8"):
                r = json.loads(ln)
                lab = r.get("ground_truth_label") or ("attack" if r.get("is_attack") else "benign")
                if lab == "attack":
                    a += 1
                else:
                    b += 1
        return {"attacks": a, "benign": b}

    add("aura-benchmark-dev", "threshold calibration, fusion DEV comparison", "dev",
        "data/benchmark/dev", "evaluation-only", bench_counts("dev"))
    add("aura-benchmark-adaptation", "adaptive constitution input ONLY", "adaptation",
        "data/benchmark/adaptation", "adaptation-only", bench_counts("adaptation"))
    add("aura-benchmark-test", "FINAL held-out evaluation ONLY", "test",
        "data/benchmark/test", "final-evaluation-only", bench_counts("test"))
    dpo = [json.loads(ln) for ln in open(REPO / "data/dpo_preferences.jsonl", encoding="utf-8") if ln.strip()]
    add("dpo-preferences", "preference training + held-out-dev eval", "train+dev",
        "data/dpo_preferences.jsonl", "training(dev-excluded)/evaluation",
        {"train": sum(1 for r in dpo if r["split"] == "train"),
         "dev": sum(1 for r in dpo if r["split"] == "dev")})
    for name, fn in (("unlearning-forget", "forget"), ("unlearning-retain", "retain"), ("unlearning-general", "general")):
        p = REPO / f"data/unlearning_{fn}.jsonl"
        if p.exists():
            add(name, {"forget": "targeted removal", "retain": "preserve related capability",
                       "general": "preserve unrelated capability"}[fn], fn,
                f"data/unlearning_{fn}.jsonl", "training(forget-only)/evaluation")
    manifest = {"version": "1.0", "created": str(date.today()),
                "policy": "NEVER train/adapt on final held-out test; enforced by guard_training_path + split guards + tests",
                "datasets": entries}
    out = REPO / "research" / "data_manifest.json"
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    m = build_manifest()
    print(json.dumps(m, indent=2))
