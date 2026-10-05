"""research/benign_live.py — B1: 48 benign prompts LIVE (3 per trigger family).

Pre-declared: 48 rows (16 families x first 3 in file order), full gateway,
per-row checkpoint, honest fallback flags. Allows reach the downstream LLM,
so this spends ~2x an attack batch; resumable across quota days.
Artifact: results/kaust_three_pillars/benign/benign_live48.json
"""
from __future__ import annotations

import json
import sys
import time
from collections import OrderedDict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from research.fusion_forensics import _key_cycle  # noqa: E402
from research.runner import _run_pipeline_with_baseline  # noqa: E402
from research.schemas import BaselineConfig  # noqa: E402


def main() -> dict:
    rot = _key_cycle()
    o = REPO / "results" / "kaust_three_pillars" / "benign"
    o.mkdir(parents=True, exist_ok=True)
    part = o / "benign_live48.json"
    done = {}
    if part.exists():
        try:
            done = {r["id"]: r for r in json.loads(part.read_text(encoding="utf-8")).get("rows", [])}
        except Exception:
            done = {}
    rows = list(done.values())
    by_word: dict[str, list[dict]] = OrderedDict()
    for i, ln in enumerate((REPO / "data" / "benign_challenge.jsonl").read_text(encoding="utf-8").splitlines()):
        if not ln.strip():
            continue
        r = json.loads(ln)
        by_word.setdefault(r["trigger_word"], []).append({"idx": i, **r})
    prompts = []
    for word, items in by_word.items():
        for r in items[:3]:
            prompts.append({"id": f"bl-{word}-{r['idx']:03d}", "prompt": r["prompt"], "word": word})
    assert len(prompts) == 48, len(prompts)
    for p in prompts:
        if p["id"] in done:
            continue
        next(rot)
        try:
            r = _run_pipeline_with_baseline(p["prompt"], None, p["id"], BaselineConfig.G_FULL_BLENDED)
            err = None
        except Exception as exc:  # noqa
            r, err = {}, type(exc).__name__
        llm = r.get("llm_result") or {}
        fb = bool(llm.get("used_fallback")) if isinstance(llm, dict) else False
        rows.append({"id": p["id"], "word": p["word"], "decision": r.get("decision", "ERROR"),
                     "fallback": fb, "error": err})
        time.sleep(1)
        held = sum(1 for r in rows if r["decision"] in ("block", "review"))
        fb_n = sum(1 for r in rows if r["fallback"] or r["error"])
        part.write_text(json.dumps({"n": len(rows), "held": held, "fallback": fb_n,
                                    "label": "BENIGN LIVE48 (16 families x 3, full gateway, one eval)",
                                    "rows": rows}, indent=2), encoding="utf-8")
    held = sum(1 for r in rows if r["decision"] in ("block", "review"))
    fb_n = sum(1 for r in rows if r["fallback"] or r["error"])
    print(f"BENIGN LIVE48: {held}/{len(rows)} held, fallback: {fb_n}")
    return {"n": len(rows), "held": held, "fallback": fb_n}


if __name__ == "__main__":
    main()
