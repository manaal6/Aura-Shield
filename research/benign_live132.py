"""research/benign_live132.py — B3: full 132 benign set LIVE (48 done in B1 + 84 here).

Pre-declared: every row of data/benign_challenge.jsonl through the full gateway,
one eval each, per-row checkpoint, honest fallback flags. Allows reach the
downstream LLM (~3 calls/row), so this spends ~2-4 shared-quota days;
resumable by design — re-run until n=132.
Artifact: results/kaust_three_pillars/benign/benign_live132.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from research.fusion_forensics import _key_cycle  # noqa: E402
from research.live_flags import fallback_flags  # noqa: E402 (B66: dict-only extraction never fired)
from research.runner import _run_pipeline_with_baseline  # noqa: E402
from research.schemas import BaselineConfig  # noqa: E402


def main() -> dict:
    rot = _key_cycle()
    o = REPO / "results" / "kaust_three_pillars" / "benign"
    o.mkdir(parents=True, exist_ok=True)
    part = o / "benign_live132.json"
    done: dict[str, dict] = {}
    for src in ("benign_live48.json", "benign_live132.json"):
        p = o / src
        if p.exists():
            try:
                for r in json.loads(p.read_text(encoding="utf-8")).get("rows", []):
                    done.setdefault(r["id"], r)
            except Exception:
                pass
    rows = list(done.values())
    prompts = []
    for i, ln in enumerate((REPO / "data" / "benign_challenge.jsonl").read_text(encoding="utf-8").splitlines()):
        if not ln.strip():
            continue
        r = json.loads(ln)
        prompts.append({"id": f"bl-{r['trigger_word']}-{i:03d}", "prompt": r["prompt"], "word": r["trigger_word"]})
    assert len(prompts) == 132, len(prompts)
    for p in prompts:
        if p["id"] in done or any(r.get("prompt") == p["prompt"] for r in rows):
            continue
        next(rot)
        try:
            r = _run_pipeline_with_baseline(p["prompt"], None, p["id"], BaselineConfig.G_FULL_BLENDED)
            err = None
        except Exception as exc:  # noqa
            r, err = {}, type(exc).__name__
        flags = fallback_flags(r)
        rows.append({"id": p["id"], "word": p["word"], "prompt": p["prompt"],
                     "decision": r.get("decision", "ERROR"), "fallback": bool(flags["any"]), "error": err,
                     "fallback_llm": flags["llm"], "fallback_constitution": flags["constitution"]})
        time.sleep(1)
        held = sum(1 for r in rows if r["decision"] in ("block", "review"))
        fb_n = sum(1 for r in rows if r["fallback"] or r["error"])
        part.write_text(json.dumps({"n": len(rows), "held": held, "fallback": fb_n,
                                    "label": "BENIGN LIVE132 (full challenge set, full gateway, one eval each)",
                                    "rows": rows}, indent=2), encoding="utf-8")
    held = sum(1 for r in rows if r["decision"] in ("block", "review"))
    fb_n = sum(1 for r in rows if r["fallback"] or r["error"])
    print(f"BENIGN LIVE132: {held}/{len(rows)} held, fallback: {fb_n}")
    return {"n": len(rows), "held": held, "fallback": fb_n}


if __name__ == "__main__":
    main()
