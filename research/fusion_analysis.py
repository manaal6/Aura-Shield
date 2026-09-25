"""research/fusion_analysis.py — 89% vs 93.2% fusion diagnosis (KAUST sprint).

Offline, deterministic, DEV SPLIT ONLY for strategy comparison.
Per-example record: rule signal, llm signal (marked unavailable offline),
constitution heuristic signal, fused score, decision, ground truth.
Held-out numbers are cited from committed artifacts, never re-tuned here.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from app.detectors import rule_detector  # noqa: E402
from app.engine import constitution_utils as cu  # noqa: E402
from research.runner import load_dataset_jsonl  # noqa: E402

DEV_DIR = REPO / "data" / "benchmark" / "dev"
W_R, W_C = 0.35 / 0.55, 0.20 / 0.55  # rule/constitution renormalized (no LLM offline)


def load_dev() -> list[dict]:
    rows = []
    for f in sorted(DEV_DIR.glob("*.jsonl")):
        for p in load_dataset_jsonl(f):
            rows.append({
                "id": str(p.get("prompt_id") or p.get("id")),
                "prompt": p.get("content") or p.get("prompt_text") or "",
                "source": p.get("source_content"),
                "is_attack": (p.get("ground_truth_label") or "") == "attack",
                "family": p.get("attack_family") or "unknown"})
    return rows


def signals(row: dict) -> dict:
    rule = rule_detector.detect(row["prompt"], row["source"]).raw_signal
    gate = cu.structured_gate_output(row["prompt"], row["source"])
    const = max((v["confidence"] for v in gate["violations"]), default=0.0)
    return {"rule": rule, "llm": None, "constitution": const}


def decide(score: float) -> str:
    return "block" if score >= 0.75 else ("review" if score >= 0.40 else "allow")


STRATEGIES = {
    "weighted_average": lambda s: (s["rule"] * W_R + s["constitution"] * W_C),
    "maximum_risk": lambda s: max(s["rule"], s["constitution"]),
    "constitutional_veto": lambda s: 1.0 if s["constitution"] >= 0.55 else (s["rule"] * W_R + s["constitution"] * W_C),
    "high_confidence_veto": lambda s: 1.0 if s["constitution"] >= 0.75 else (s["rule"] * W_R + s["constitution"] * W_C),
    "disagreement_to_review": lambda s: 0.5 if abs(s["rule"] - s["constitution"]) > 0.5 else (s["rule"] * W_R + s["constitution"] * W_C),
}


def metrics(rows: list[dict]) -> dict:
    a = [r for r in rows if r["is_attack"]]
    b = [r for r in rows if not r["is_attack"]]
    tp = sum(1 for r in a if r["decision"] in ("block", "review"))
    fp = sum(1 for r in b if r["decision"] in ("block", "review"))
    return {"n": len(rows), "tp": tp, "fn": len(a) - tp, "fp": fp, "tn": len(b) - fp,
            "recall": round(tp / max(1, len(a)), 4), "fpr": round(fp / max(1, len(b)), 4),
            "precision": round(tp / max(1, tp + fp), 4)}


def main() -> dict:
    dev = load_dev()
    for r in dev:
        r.update(signals(r))
    per_example = [{k: r[k] for k in ("id", "family", "is_attack", "rule", "constitution")} for r in dev]
    table = {}
    for name, fn in STRATEGIES.items():
        for r in dev:
            r["score"] = round(float(fn(r)), 4)
            r["decision"] = decide(r["score"])
        table[name] = metrics(dev)
    # disagreement anatomy (using weighted_average as reference full)
    for r in dev:
        r["score"] = round(float(STRATEGIES["weighted_average"](r)), 4)
        r["decision"] = decide(r["score"])
    anatomy = {
        "constitution_catches_full_misses": sum(1 for r in dev if r["is_attack"] and r["constitution"] >= 0.55 and r["decision"] == "allow"),
        "rule_catches_full_misses": sum(1 for r in dev if r["is_attack"] and r["rule"] >= 0.75 and r["decision"] == "allow"),
        "all_miss": sum(1 for r in dev if r["is_attack"] and r["decision"] == "allow"),
        "detector_disagreement": sum(1 for r in dev if abs(r["rule"] - r["constitution"]) > 0.5),
    }
    report = {
        "scope": "SMOKE TEST — dev split only, offline (LLM signal unavailable, marked null)",
        "llm_signal": "NOT AVAILABLE offline; live-LLM fusion re-tuning NOT RUN",
        "dev_strategy_table": table, "dev_disagreement_anatomy": anatomy,
        "held_out_cited_from_committed_artifacts": {
            "constitution_only_recall": "93.2% (68/73)",
            "full_gateway_recall": "89.0% (65/73)",
            "reading": ("Overlapping 95% Wilson CIs at n=73: full blend not statistically "
                        "distinguishable from constitution-only. Fusion policy FROZEN as-is; "
                        "no re-tuning without live LLM signals.")},
        "frozen_policy": "unchanged (weights 0.35/0.45/0.20, thresholds 0.40/0.75, escalation 0.90)",
    }
    out = REPO / "results" / "kaust_three_pillars" / "fusion"
    out.mkdir(parents=True, exist_ok=True)
    (out / "dev_per_example.json").write_text(json.dumps(per_example, indent=2))
    (out / "fusion_diagnosis.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({**report, "dev_strategy_table": table}, indent=2))
    return report


if __name__ == "__main__":
    main()
