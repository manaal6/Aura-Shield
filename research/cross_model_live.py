"""research/cross_model_live.py — Phase 26: analyzer × constitution matrix (live).

Sample: 12 stratified DEV prompts (4 direct / 4 indirect / 2 jailbreak / 2 benign).
Cells override model_analyzer / model_constitution per call (harness-level, documented).
In-harness key rotation (behavior-neutral). Unknown model IDs -> NOT RUN, not fabricated.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from app.config import get_settings  # noqa: E402
from research.fusion_forensics import _key_cycle  # noqa: E402 (rotation only)
from research.runner import _run_pipeline_with_baseline, load_dataset_jsonl  # noqa: E402
from research.schemas import BaselineConfig  # noqa: E402

BIG = "openai/gpt-oss-120b"
SMALL = "openai/gpt-oss-20b"
CELLS = {"A120-C120": (BIG, BIG), "A20-C120": (SMALL, BIG),
         "A120-C20": (BIG, SMALL), "A20-C20": (SMALL, SMALL)}
FILES = [("dev/direct_injection.jsonl", 4), ("dev/indirect_injection.jsonl", 4),
         ("dev/jailbreak_persona.jsonl", 2), ("dev/benign_general.jsonl", 2)]


def main() -> dict:
    rot = _key_cycle()
    s = get_settings()
    prompts = []
    for fn, k in FILES:
        for p in load_dataset_jsonl(REPO / "data" / "benchmark" / fn)[:k]:
            prompts.append({"id": str(p.get("prompt_id") or p.get("id")),
                            "prompt": p.get("content") or "",
                            "source": p.get("source_content"),
                            "attack": (p.get("ground_truth_label") or "") == "attack"})
    out: dict[str, dict] = {}
    for cell, (am, cm) in CELLS.items():
        s.model_analyzer, s.model_constitution = am, cm
        tp = fp = fb = 0
        na = sum(1 for p in prompts if p["attack"])
        nb = len(prompts) - na
        errs: set[str] = set()
        for p in prompts:
            next(rot)
            try:
                r = _run_pipeline_with_baseline(p["prompt"], p["source"], f"x-{cell}", BaselineConfig.G_FULL_BLENDED)
            except Exception as exc:  # noqa: BLE001
                errs.add(type(exc).__name__)
                continue
            llm = r.get("llm_result") or {}
            used_fb = llm.get("used_fallback", False) if isinstance(llm, dict) else False
            fb += used_fb
            if r.get("decision") in ("block", "review"):
                if p["attack"]:
                    tp += 1
                else:
                    fp += 1
            time.sleep(1)
        out[cell] = {"analyzer": am, "constitution": cm, "n": len(prompts),
                     "recall": f"{tp}/{na}", "fp": f"{fp}/{nb}", "fallbacks": fb,
                     "status": "RUN" if not errs else f"PARTIAL ({sorted(errs)})"}
        print(cell, out[cell], flush=True)
    s.model_analyzer, s.model_constitution = "", ""  # restore defaults
    rep = {"cells": out, "sample": "12 stratified DEV prompts (10 attack / 2 benign)",
           "scope": "live matrix sample; full-matrix + held-out transfer NOT RUN",
           "committed_cells": {"constitution_on_safeguard-20b": "78.1% recall",
                               "analyzer_on_safeguard-20b": "90.4% recall"}}
    o = REPO / "results" / "kaust_three_pillars" / "cross_model"
    o.mkdir(parents=True, exist_ok=True)
    (o / "cross_model_live.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep, indent=2))
    return rep


if __name__ == "__main__":
    main()
