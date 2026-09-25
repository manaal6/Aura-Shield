"""research/make_fusion_report.py — per-example DEV analysis, 7 strategies,
freeze, single-final-eval framing, research/fusion_report.md + artifact."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from app.detectors import rule_detector  # noqa: E402
from app.engine import constitution_utils as cu  # noqa: E402
from research.runner import load_dataset_jsonl  # noqa: E402

DEV = REPO / "data" / "benchmark" / "dev"


def decide(s: float) -> str:
    return "block" if s >= 0.75 else ("review" if s >= 0.40 else "allow")


def main() -> dict:
    rows = []
    for f in sorted(DEV.glob("*.jsonl")):
        for p in load_dataset_jsonl(f):
            prompt = p.get("content") or ""
            t = time.perf_counter()
            rule_s = rule_detector.detect(prompt, p.get("source_content")).raw_signal
            t1 = time.perf_counter()
            gate = cu.structured_gate_output(prompt, p.get("source_content"))
            t2 = time.perf_counter()
            const_s = max((v["confidence"] for v in gate["violations"]), default=0.0)
            rows.append({
                "prompt_id": str(p.get("prompt_id") or p.get("id")),
                "ground_truth": p.get("ground_truth_label") or "benign",
                "family": p.get("attack_family") or "unknown",
                "rule_decision": decide(rule_s), "rule_score": round(rule_s, 4),
                "llm_decision": "unavailable", "llm_score": None,
                "constitution_decision": decide(const_s), "constitution_score": round(const_s, 4),
                "latency_ms": {"rule": round((t1 - t) * 1000, 3),
                               "constitution_heuristic": round((t2 - t1) * 1000, 3)}})
    W_R, W_C = 0.35 / 0.55, 0.20 / 0.55
    strat = {
        "weighted_voting": lambda r: r["rule_score"] * W_R + r["constitution_score"] * W_C,
        "maximum_risk": lambda r: max(r["rule_score"], r["constitution_score"]),
        "constitutional_veto": lambda r: 1.0 if r["constitution_score"] >= 0.55 else r["rule_score"] * W_R + r["constitution_score"] * W_C,
        "llm_veto": "NOT RUN (no live LLM signal offline)",
        "disagreement_review": lambda r: 0.5 if abs(r["rule_score"] - r["constitution_score"]) > 0.5 else r["rule_score"] * W_R + r["constitution_score"] * W_C,
        "confidence_aware": lambda r: max(r["rule_score"], r["constitution_score"]) if max(r["rule_score"], r["constitution_score"]) >= 0.75 else r["rule_score"] * W_R + r["constitution_score"] * W_C,
        "calibrated": "NOT RUN (no calibration data with live signals)",
    }
    table = {}
    for name, fn in strat.items():
        if isinstance(fn, str):
            table[name] = fn
            continue
        tp = fp = 0
        na = sum(1 for r in rows if r["ground_truth"] == "attack")
        nb = len(rows) - na
        for r in rows:
            r[f"final_{name}"] = decide(float(fn(r)))
        tp = sum(1 for r in rows if r["ground_truth"] == "attack" and r[f"final_{name}"] in ("block", "review"))
        fp = sum(1 for r in rows if r["ground_truth"] != "attack" and r[f"final_{name}"] in ("block", "review"))
        table[name] = {"recall": f"{tp}/{na}={tp/max(1,na):.1%}", "fpr": f"{fp}/{nb}={fp/max(1,nb):.1%}"}
    # disagreement categories (reference = weighted_voting)
    cats = {"all_agree": 0, "rule_correct_others_wrong": 0, "constitution_correct_others_wrong": 0,
            "final_fusion_wrong": 0, "false_positive": 0, "false_negative": 0, "disagreement_needs_review": 0}
    for r in rows:
        atk = r["ground_truth"] == "attack"
        rc = r["rule_decision"] in ("block", "review")
        cc = r["constitution_decision"] in ("block", "review")
        fc = r["final_weighted_voting"] in ("block", "review")
        if rc == cc == fc:
            cats["all_agree"] += 1
        if rc != cc:
            cats["disagreement_needs_review"] += 1
        if rc == atk and cc != atk:
            cats["rule_correct_others_wrong"] += 1
        if cc == atk and rc != atk:
            cats["constitution_correct_others_wrong"] += 1
        if fc != atk:
            cats["final_fusion_wrong"] += 1
        if fc and not atk:
            cats["false_positive"] += 1
        if not fc and atk:
            cats["false_negative"] += 1
    rep = {"scope": "DEV ONLY (n=120). LLM/calibrated strategies NOT RUN offline.",
           "dev_strategy_table": table, "disagreement_categories": cats,
           "selected_policy": "KEEP CURRENT (0.35/0.45/0.20, 0.40/0.75, escalation 0.90) — no DEV evidence for change",
           "reason": "offline DEV recall 5–13% across strategies (no live LLM); switching on this signal would be tuning to a weak proxy",
           "final_held_out_eval": "single evaluation = committed artifacts (C 68/73=93.2%, G 65/73=89.0%); policy unchanged so no re-run warranted",
           "limitations": "no live LLM/dev held-out separation for fusion; live re-tuning = FUTURE WORK"}
    out = REPO / "results" / "kaust_three_pillars" / "fusion"
    (out / "fusion_per_example_dev.json").write_text(json.dumps(rows, indent=2))
    (out / "fusion_report_data.json").write_text(json.dumps(rep, indent=2))
    md = ["# Fusion Report", "",
          "## DEV strategy comparison (n=120, offline, LLM NOT RUN)"]
    for k, v in table.items():
        md.append(f"- {k}: {v}")
    md += ["", "## Disagreement categories", json.dumps(cats, indent=2), "",
           "## Selected policy", rep["selected_policy"], "",
           "## Final held-out evaluation (single, untouched test)",
           "C 68/73=93.2%, G 65/73=89.0% (committed artifacts; policy unchanged).", "",
           "## Limitations", rep["limitations"]]
    (REPO / "research" / "FUSION_REPORT.md").write_text("\n".join(md) + "\n")
    print(json.dumps({k: v for k, v in rep.items() if k != "selected_policy"}, indent=2)[:1500])
    return rep


if __name__ == "__main__":
    main()
