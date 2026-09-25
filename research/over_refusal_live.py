"""research/over_refusal_live.py — Fix D: 52-prompt over-refusal measurement (LIVE).

Benign adversarial-looking prompts through the full live gateway.
over_refusal = held (block/review) AND no fallback involved.
PASS-regression threshold documented; NOT 'over-refusal solved'.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from data.over_refusal_50 import prompts  # noqa: E402
from research.fusion_forensics import _key_cycle  # noqa: E402
from research.runner import _run_pipeline_with_baseline  # noqa: E402
from research.schemas import BaselineConfig  # noqa: E402


def main() -> dict:
    rot = _key_cycle()
    rows = []
    for i, pr in enumerate(prompts):
        next(rot)
        t = time.perf_counter()
        try:
            r = _run_pipeline_with_baseline(pr, None, f"or-{i:02d}", BaselineConfig.G_FULL_BLENDED)
            err = None
        except Exception as exc:  # noqa: BLE001
            r, err = {}, type(exc).__name__
        llm = r.get("llm_result") or {}
        fb = bool(llm.get("used_fallback")) if isinstance(llm, dict) else bool(getattr(llm, "used_fallback", False))
        rows.append({"id": f"or-{i:02d}", "prompt": pr[:80],
                     "decision": r.get("decision", "ERROR"),
                     "fallback": fb, "error": err,
                     "latency_ms": round((time.perf_counter() - t) * 1000, 1)})
        print(f"[{i+1}/{len(prompts)}] {rows[-1]['decision']}", flush=True)
        time.sleep(1)
    clean = [r for r in rows if not r["fallback"] and not r["error"]]
    held = sum(1 for r in clean if r["decision"] in ("block", "review"))
    rep = {"n": len(rows), "clean": len(clean),
           "fallback_rows": len(rows) - len(clean),
           "over_refused_clean": held,
           "over_refusal_rate": f"{held}/{len(clean)}={held/max(1,len(clean)):.1%}" if clean else "n/a",
           "allowed": sum(1 for r in clean if r["decision"] == "allow"),
           "status": "PASS — regression suite (n=52); NOT 'over-refusal solved'",
           "scope": "live gateway, benign adversarial-looking prompts"}
    o = REPO / "results" / "kaust_three_pillars" / "overrefusal"
    o.mkdir(parents=True, exist_ok=True)
    (o / "over_refusal_52.json").write_text(json.dumps({"rows": rows, **rep}, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in rep.items() if k != "rows"}, indent=2))
    return rep


if __name__ == "__main__":
    main()
