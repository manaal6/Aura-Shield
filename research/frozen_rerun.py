"""research/frozen_rerun.py — Fix F: single frozen held-out eval of the NEW system.

Config: C1–C10 constitution + max fusion (frozen; nothing changes after this run).
Old numbers (C 68/73, G 65/73) were measured under v1 + weighted-avg and stand as
the old-system record. This run reports new-system numbers on the SAME frozen test.
Resumable per-file parts; key rotation; fallback accounting per row.
Usage: python -m research.frozen_rerun [file.jsonl]  (no arg = all test files)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from research.fusion_forensics import _key_cycle  # noqa: E402 (rotation only)
from research.runner import _run_pipeline_with_baseline, load_dataset_jsonl  # noqa: E402
from research.schemas import BaselineConfig  # noqa: E402

TEST = REPO / "data" / "benchmark" / "test"
OUT = REPO / "results" / "kaust_three_pillars" / "frozen_rerun"


def main() -> dict:
    import sys as _s
    only = _s.argv[1] if len(_s.argv) > 1 else None
    OUT.mkdir(parents=True, exist_ok=True)
    rot = _key_cycle()
    files = sorted(TEST.glob("*.jsonl"))
    if only:
        files = [TEST / Path(only).name]
    for f in files:
        part = OUT / f"frozen_{f.stem}.json"
        done = {}
        if part.exists():
            try:
                done = {r["prompt_id"]: r for r in json.loads(part.read_text(encoding="utf-8"))}
            except Exception:
                done = {}
        rows = list(done.values())
        for p in load_dataset_jsonl(f):
            pid = str(p.get("prompt_id") or p.get("id"))
            if pid in done:
                continue
            next(rot)
            t = time.perf_counter()
            try:
                res = _run_pipeline_with_baseline(
                    p.get("content") or "", p.get("source_content"), pid, BaselineConfig.G_FULL_BLENDED)
                err = None
            except Exception as exc:  # noqa: BLE001
                res, err = {}, type(exc).__name__
            dt = round((time.perf_counter() - t) * 1000, 1)
            llm = res.get("llm_result") or {}
            const = res.get("constitution_result") or {}
            rule = res.get("rule_result") or {}

            def _sig(obj: object) -> float:
                if isinstance(obj, dict):
                    return round(float(obj.get("raw_signal", 0.0)), 4)
                return round(float(getattr(obj, "raw_signal", 0.0)), 4)

            def _fb(obj: object) -> bool:
                if isinstance(obj, dict):
                    return bool(obj.get("used_fallback"))
                return bool(getattr(obj, "used_fallback", False))

            rows.append({
                "prompt_id": pid, "ground_truth": p.get("ground_truth_label") or "benign",
                "family": p.get("attack_family") or "unknown",
                "rule_score": _sig(rule),
                "llm_score": _sig(llm),
                "llm_fallback": _fb(llm),
                "constitution_score": _sig(const),
                "const_fallback": _fb(const),
                "final_decision": res.get("decision", "ERROR"),
                "final_score": round(float(res.get("risk_score", -1.0)), 4),
                "latency_ms": dt, "error": err})
            part.write_text(json.dumps(rows, indent=2), encoding="utf-8")
            print(f"[{f.stem} {len(rows)}] {pid} -> {rows[-1]['final_decision']}", flush=True)
            time.sleep(1)
    # aggregate
    all_rows = []
    for part in sorted(OUT.glob("frozen_*.json")):
        if part.name == "frozen_rerun_summary.json":
            continue
        all_rows.extend(json.loads(part.read_text(encoding="utf-8")))
    atk = [r for r in all_rows if r["ground_truth"] == "attack"]
    ben = [r for r in all_rows if r["ground_truth"] != "attack"]
    tp = sum(1 for r in atk if r["final_decision"] in ("block", "review"))
    fp = sum(1 for r in ben if r["final_decision"] in ("block", "review"))
    fb = sum(1 for r in all_rows if r["llm_fallback"] or r["const_fallback"] or r["error"])
    rep = {"n": len(all_rows), "attacks": len(atk), "benign": len(ben),
           "tp": tp, "fp": fp, "recall": f"{tp}/{len(atk)}", "fpr": f"{fp}/{len(ben)}",
           "fallback_rows": fb,
           "status": "LIVE MODEL EVALUATION" if fb == 0 else "MIXED — fallback rows counted, not predictions",
           "config": "C1-C10 + max fusion (frozen)",
           "old_system": "C 68/73=93.2%, G 65/73=89.0% (v1 + weighted-avg, committed)"}
    (OUT / "frozen_rerun_summary.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep, indent=2))
    return rep


if __name__ == "__main__":
    main()
