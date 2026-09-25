"""research/latency.py — Phase 13: P50/P95/P99 per component (offline) + committed LLM rows."""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from app.detectors import rule_detector  # noqa: E402
from app.engine import constitution_utils as cu  # noqa: E402
from research.runner import load_dataset_jsonl  # noqa: E402
from research.toolsec import run_tool_chain  # noqa: E402


def pct(data: list[float], q: float) -> float:
    s = sorted(data)
    return round(s[min(len(s) - 1, int(q * len(s)))], 3)


def main() -> dict:
    prompts = []
    for f in sorted((REPO / "data" / "benchmark" / "dev").glob("*.jsonl")):
        for p in load_dataset_jsonl(f):
            prompts.append(p.get("content") or "")
            if len(prompts) >= 40:
                break
        if len(prompts) >= 40:
            break
    lat = {"rule": [], "constitution_heuristic": [], "fusion": [], "tool_auth": []}
    for pr in prompts:
        t = time.perf_counter()
        rule_detector.detect(pr, None)
        lat["rule"].append((time.perf_counter() - t) * 1000)
        t = time.perf_counter()
        cu.structured_gate_output(pr, None)
        lat["constitution_heuristic"].append((time.perf_counter() - t) * 1000)
        t = time.perf_counter()
        r = rule_detector.detect(pr, None).raw_signal
        g = cu.structured_gate_output(pr, None)
        _ = r * 0.35 + max([v["confidence"] for v in g["violations"]] or [0.0]) * 0.20
        lat["fusion"].append((time.perf_counter() - t) * 1000)
        t = time.perf_counter()
        run_tool_chain("read log /var/log/auth.log")
        lat["tool_auth"].append((time.perf_counter() - t) * 1000)
    table = {k: {"n": len(v), "p50": pct(v, 0.5), "p95": pct(v, 0.95),
                 "p99": pct(v, 0.99), "mean": round(statistics.mean(v), 3)} for k, v in lat.items()}
    # committed live rows (LLM-inclusive, from held-out runs)
    master = json.loads((REPO / "results" / "baselines_summary" / "heldout_master_table.json").read_text())
    live = {r["key"]: {"avg_latency_ms": r.get("avg_latency_ms"), "fallback_rows": r.get("fallback_rows")}
            for r in master["rows"]}
    rep = {"offline_cpu_ms": table, "committed_live_avg_ms": live,
           "failures_timeouts_retries_fallbacks": {
               "offline_run_errors": 0,
               "committed_fallback_rows": {k: v["fallback_rows"] for k, v in live.items()},
               "analyzer_failure_policy": "REVIEW (fail-safe); retries GROQ_MAX_RETRIES=3 in forensics (blocked by 403 at runtime)"},
           "note": "offline rows measured here (n=40 dev prompts); live LLM/constitution rows cited, not re-measured"}
    out = REPO / "results" / "kaust_three_pillars" / "latency"
    out.mkdir(parents=True, exist_ok=True)
    (out / "latency.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep, indent=2))
    return rep


if __name__ == "__main__":
    main()
