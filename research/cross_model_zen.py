"""research/cross_model_zen.py — OpenCode Zen second-provider matrix (LIVE, user key).

Provider = opencode.ai/zen (OpenAI-compatible) via a registered adapter.
Cells: analyzer / constitution swapped to a Zen free model on the 12-prompt DEV sample.
Key: user-supplied oc_sk_* (never printed, never stored — passed in-memory only).
Resumable part file; honest fallback flags per row.
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

ZEN_URL = "https://opencode.ai/zen/v1"
ZEN_MODEL = "space-bunny-free"
CELLS = ["A-zen", "C-zen"]


def main(zen_key: str) -> dict:
    rot = _key_cycle()
    s = get_settings()
    o = REPO / "results" / "kaust_three_pillars" / "cross_model"
    o.mkdir(parents=True, exist_ok=True)
    part = o / "cross_model_zen.json"
    done = {}
    if part.exists():
        try:
            done = {r["id"]: r for r in json.loads(part.read_text(encoding="utf-8"))}
        except Exception:
            done = {}
    prompts = []
    for fn, k in [("dev/direct_injection.jsonl", 4), ("dev/indirect_injection.jsonl", 4),
                  ("dev/jailbreak_persona.jsonl", 2), ("dev/benign_general.jsonl", 2)]:
        for p in load_dataset_jsonl(REPO / "data" / "benchmark" / fn)[:k]:
            prompts.append({"id": str(p.get("prompt_id") or p.get("id")),
                            "prompt": p.get("content") or "", "source": p.get("source_content"),
                            "attack": (p.get("ground_truth_label") or "") == "attack"})
    rows = list(done.values())
    from app.providers.openai_provider import OpenAIProvider
    from app.providers.router import get_provider_router

    class ZenProvider(OpenAIProvider):
        def __init__(self):
            super().__init__(api_key=zen_key)

        @property
        def name(self) -> str:
            return "zen"

        def is_available(self) -> bool:
            return True

    get_provider_router().register_provider(ZenProvider())
    # point the generic OpenAI-compatible machinery at Zen
    s.openai_api_key = zen_key
    s.openai_base_url = ZEN_URL
    s.provider_fallback_enabled = True
    orig_analyzer_model = s.model_analyzer
    orig_constitution_model = s.model_constitution
    for cell in CELLS:
        s.model_analyzer = ZEN_MODEL if cell == "A-zen" else ""
        s.model_constitution = ZEN_MODEL if cell == "C-zen" else ""
        # NOTE: router maps p_name == "openai" gpt-oss models to openai_model;
        # we bypass by calling provider order with zen first via monkeypatched order below.
        s.analyzer_providers = "zen,groq" if cell == "A-zen" else "groq"
        s.constitution_providers = "zen,groq" if cell == "C-zen" else "groq"
        for p in prompts:
            pid = f"{cell}-{p['id']}"
            if pid in done:
                continue
            next(rot)
            t = time.perf_counter()
            try:
                r = _run_pipeline_with_baseline(p["prompt"], p["source"], pid, BaselineConfig.G_FULL_BLENDED)
                err = None
            except Exception as exc:  # noqa
                import traceback as _tb
                _tb.print_exc()
                r, err = {}, type(exc).__name__
            llm = r.get("llm_result") or {}
            const = r.get("constitution_result") or {}

            def _field(obj, name):
                if isinstance(obj, dict):
                    return obj.get(name)
                return getattr(obj, name, None)

            fb = bool(_field(llm, "used_fallback"))
            rows.append({"id": pid, "cell": cell, "attack": p["attack"],
                         "decision": r.get("decision", "ERROR"), "fallback": fb, "error": err,
                         "analyzer_provider": _field(llm, "provider"),
                         "analyzer_model": _field(llm, "model"),
                         "constitution_provider": _field(const, "provider"),
                         "constitution_model": _field(const, "model"),
                         "latency_ms": round((time.perf_counter() - t) * 1000, 1)})
            part.write_text(json.dumps(rows, indent=2), encoding="utf-8")
            print(f"[{len(rows)}] {pid} -> {rows[-1]['decision']}", flush=True)
            time.sleep(2)
    s.model_analyzer, s.model_constitution = orig_analyzer_model, orig_constitution_model
    s.analyzer_providers, s.constitution_providers = "groq", "groq"
    s.openai_api_key, s.openai_base_url = "", ""
    cells = {}
    for cell in CELLS:
        sub = [r for r in rows if r["cell"] == cell]
        atk = [r for r in sub if r["attack"]]
        ben = [r for r in sub if not r["attack"]]
        fb = sum(1 for r in sub if r["fallback"] or r["error"])
        role_key = "analyzer_provider" if cell.startswith("A-") else "constitution_provider"
        served = {}
        for r in sub:
            served[r.get(role_key) or "unknown"] = served.get(r.get(role_key) or "unknown", 0) + 1
        cells[cell] = {"model": ZEN_MODEL,
                       "recall": f"{sum(1 for r in atk if r['decision'] in ('block','review'))}/{len(atk)}",
                       "fp": f"{sum(1 for r in ben if r['decision'] in ('block','review'))}/{len(ben)}",
                       "fallbacks": fb,
                       "served_by": served}
    rep = {"cells": cells, "provider": "opencode-zen (user key, in-memory only)",
           "scope": "second provider measured; capability gap vs Groq expected and reported, not hidden"}
    (o / "cross_model_zen_summary.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(json.dumps(rep, indent=2))
    return rep


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
