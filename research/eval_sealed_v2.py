"""research/eval_sealed_v2.py — single sealed evaluation of heldout_extra_v2.

40 novel attacks, frozen pipeline, key rotation. Generated once, evaluated
once, never tuned. Resumable part file.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from research.fusion_forensics import _key_cycle  # noqa: E402
from research.runner import _run_pipeline_with_baseline, load_dataset_jsonl  # noqa: E402
from research.schemas import BaselineConfig  # noqa: E402


def main() -> dict:
    rot = _key_cycle()
    o = REPO / "results" / "kaust_three_pillars" / "heldout_extra"
    o.mkdir(parents=True, exist_ok=True)
    part = o / "heldout_extra_v2_eval.json"
    done = {}
    if part.exists():
        try:
            loaded = json.loads(part.read_text(encoding="utf-8"))
            done = {r["id"]: r for r in loaded.get("rows", [])}
        except Exception:
            done = {}
    rows = list(done.values())
    prompts = load_dataset_jsonl(REPO / "data" / "sealed" / "heldout_extra_v2.jsonl")
    for p in prompts:
        pid = str(p.get("prompt_id"))
        if pid in done:
            continue
        next(rot)
        try:
            r = _run_pipeline_with_baseline(p.get("content"), None, pid, BaselineConfig.G_FULL_BLENDED)
            err = None
        except Exception as exc:  # noqa
            r, err = {}, type(exc).__name__
        llm = r.get("llm_result") or {}
        fb = bool(llm.get("used_fallback")) if isinstance(llm, dict) else False
        rows.append({"id": pid, "decision": r.get("decision", "ERROR"),
                     "fallback": fb, "error": err})
        time.sleep(1)
        # Checkpoint every row so a killed run resumes instead of restarting.
        tp_now = sum(1 for r in rows if r["decision"] in ("block", "review"))
        fb_now = sum(1 for r in rows if r["fallback"] or r["error"])
        part.write_text(json.dumps({"n": len(rows), "held": tp_now, "fallback": fb_now,
                                    "label": "SEALED V2 (n=40, LIVE, one eval, never tuned)",
                                    "rows": rows}, indent=2), encoding="utf-8")
    tp = sum(1 for r in rows if r["decision"] in ("block", "review"))
    fb = sum(1 for r in rows if r["fallback"] or r["error"])
    rep = {"n": len(rows), "held": tp, "fallback": fb,
           "label": "SEALED V2 (n=40, LIVE, one eval, never tuned)",
           "rows": rows}
    part.write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(f"SEALED V2: {tp}/{len(rows)} fallback: {fb}")
    return rep


if __name__ == "__main__":
    main()
