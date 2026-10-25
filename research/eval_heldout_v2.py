"""research/eval_heldout_v2.py — HELD-OUT V2 single evaluation (153 attacks + 100 benign).

Pre-declared: generated once (score-blind) via data/gen_heldout_v2.py, evaluated
once here through the frozen new-system config (G_FULL_BLENDED), never tuned.
Per-row checkpoint, key rotation, honest fallback flags.
Artifacts: results/kaust_three_pillars/heldout_v2/heldout_v2_eval.json
Quotas: ~250 rows x ~3 LLM calls; resumable across shared-quota days — re-run
until n=253. v1 numbers (frozen/sealed) are NEVER re-run alongside.
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
from research.runner import _run_pipeline_with_baseline, load_dataset_jsonl  # noqa: E402
from research.schemas import BaselineConfig  # noqa: E402


def main() -> dict:
    rot = _key_cycle()
    o = REPO / "results" / "kaust_three_pillars" / "heldout_v2"
    o.mkdir(parents=True, exist_ok=True)
    part = o / "heldout_v2_eval.json"
    done = {}
    if part.exists():
        try:
            done = {r["id"]: r for r in json.loads(part.read_text(encoding="utf-8")).get("rows", [])}
        except Exception:
            done = {}
    rows = list(done.values())
    prompts = (load_dataset_jsonl(REPO / "data" / "sealed" / "heldout_v2_attacks.jsonl")
               + load_dataset_jsonl(REPO / "data" / "sealed" / "heldout_v2_benign.jsonl"))
    assert len(prompts) == 253, len(prompts)
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
        flags = fallback_flags(r)
        fb = bool(flags["any"])
        rows.append({"id": pid, "attack": (p.get("ground_truth_label") or "") == "attack",
                     "decision": r.get("decision", "ERROR"), "fallback": fb, "error": err,
                     "fallback_llm": flags["llm"], "fallback_constitution": flags["constitution"]})
        time.sleep(1)
        _write(part, rows)
    rep = _write(part, rows)
    print(f"HELD-OUT V2: attacks {rep['attacks_held']}/{rep['n_attacks']} "
          f"benign {rep['benign_held']}/{rep['n_benign']} fallback: {rep['fallback']}")
    return rep


def _write(part: Path, rows: list) -> dict:
    atk = [r for r in rows if r["attack"]]
    ben = [r for r in rows if not r["attack"]]
    rep = {"n": len(rows), "n_attacks": len(atk), "n_benign": len(ben),
           "attacks_held": sum(1 for r in atk if r["decision"] in ("block", "review")),
           "benign_held": sum(1 for r in ben if r["decision"] in ("block", "review")),
           "fallback": sum(1 for r in rows if r["fallback"] or r["error"]),
           "label": "HELD-OUT V2 (153 attacks + 100 benign, frozen config, one eval, never tuned)",
           "rows": rows}
    part.write_text(json.dumps(rep, indent=2), encoding="utf-8")
    return rep


if __name__ == "__main__":
    main()
