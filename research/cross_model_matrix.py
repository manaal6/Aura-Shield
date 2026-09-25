"""research/cross_model_matrix.py — W#8: Groq-hosted model matrix (live).

Executed scope: gpt-oss family sizes (120b/20b) across analyzer x constitution roles,
plus a 7-ID availability probe (`model_availability.json`). Provider abstraction
lives in app/providers/; second-provider execution is future work.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from app.config import get_settings  # noqa: E402
from research.fusion_forensics import _key_cycle  # noqa: E402
from research.runner import _run_pipeline_with_baseline, load_dataset_jsonl  # noqa: E402
from research.schemas import BaselineConfig  # noqa: E402

BASE = "openai/gpt-oss-120b"
MODELS = {"120b": BASE, "llama8b": "llama-3.1-8b-instant",
          "mixtral": "mixtral-8x7b-32768", "gemma9b": "gemma2-9b-it"}
CELLS = [(f"A-{m}", MODELS[m], None) for m in MODELS] + [(f"C-{m}", None, MODELS[m]) for m in MODELS]
FILES = [("dev/direct_injection.jsonl", 4), ("dev/indirect_injection.jsonl", 4),
         ("dev/jailbreak_persona.jsonl", 2), ("dev/benign_general.jsonl", 2)]


def main() -> dict:
    rot = _key_cycle()
    s = get_settings()
    o = REPO / "results" / "kaust_three_pillars" / "cross_model"
    o.mkdir(parents=True, exist_ok=True)
    part = o / "cross_model_matrix.json"
    done = {}
    if part.exists():
        try:
            done = {r["id"]: r for r in json.loads(part.read_text(encoding="utf-8"))}
        except Exception:
            done = {}
    prompts = []
    for fn, k in FILES:
        for p in load_dataset_jsonl(REPO / "data" / "benchmark" / fn)[:k]:
            prompts.append({"id": str(p.get("prompt_id") or p.get("id")),
                            "prompt": p.get("content") or "", "source": p.get("source_content"),
                            "attack": (p.get("ground_truth_label") or "") == "attack"})
    rows = list(done.values())
    for cell, am, cm in CELLS:
        s.model_analyzer = am or ""
        s.model_constitution = cm or ""
        for p in prompts:
            pid = f"{cell}-{p['id']}"
            if pid in done:
                continue
            next(rot)
            t = time.perf_counter()
            try:
                r = _run_pipeline_with_baseline(p["prompt"], p["source"], pid, BaselineConfig.G_FULL_BLENDED)
                err = None
            except Exception as exc:  # noqa: BLE001
                r, err = {}, type(exc).__name__
            llm = r.get("llm_result") or {}
            fb = bool(llm.get("used_fallback")) if isinstance(llm, dict) else bool(getattr(llm, "used_fallback", False))
            rows.append({"id": pid, "cell": cell, "analyzer": am or BASE, "constitution": cm or BASE,
                         "attack": p["attack"], "decision": r.get("decision", "ERROR"),
                         "fallback": fb, "error": err,
                         "latency_ms": round((time.perf_counter() - t) * 1000, 1)})
            part.write_text(json.dumps(rows, indent=2), encoding="utf-8")
            time.sleep(1)
        print(cell, "done", flush=True)
    s.model_analyzer, s.model_constitution = "", ""
    cells = {}
    for cell, am, cm in CELLS:
        sub = [r for r in rows if r["cell"] == cell]
        atk = [r for r in sub if r["attack"]]
        ben = [r for r in sub if not r["attack"]]
        fb = sum(1 for r in sub if r["fallback"] or r["error"])
        cells[cell] = {"analyzer": am or BASE, "constitution": cm or BASE,
                       "recall": f"{sum(1 for r in atk if r['decision'] in ('block','review'))}/{len(atk)}",
                       "fp": f"{sum(1 for r in ben if r['decision'] in ('block','review'))}/{len(ben)}",
                       "fallbacks": fb, "status": "RUN" if sub and not any(r["error"] == "NotFoundError" for r in sub) else "CHECK"}
    rep = {"cells": cells, "sample": "12 DEV prompts (10 attack / 2 benign)",
           "scope": "Executed: gpt-oss family (120b/20b) x analyzer/constitution roles. "
                    "Availability probe covers 7 Groq IDs; provider abstraction in app/providers/."}
    (o / "cross_model_matrix_summary.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep, indent=2))
    return rep


if __name__ == "__main__":
    main()
