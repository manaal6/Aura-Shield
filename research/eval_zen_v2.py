"""research/eval_zen_v2.py — held-out v2 on the SECOND provider end-to-end (LIVE).

Both LLM layers (analyzer + constitution) pinned to Zen `space-bunny-free`;
Groq is NOT in the provider chain, so this run is independent of Groq outages.
Key: read in-process from %USERPROFILE%\\.aura_zen_key (never printed, never
stored in repo). Per-row checkpoint, honest fallback flags (research.live_flags),
per-row served_by attribution. Zen-claim numbers count served_by==zen rows only.

One-shot: the v2 inputs were already consumed on Groq; this is the pre-declared
second-provider replication (Shoker-85 item 1), not tuning.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from app.config import get_settings  # noqa: E402
from research.fusion_forensics import _key_cycle  # noqa: E402
from research.live_flags import fallback_flags  # noqa: E402
from research.runner import _run_pipeline_with_baseline, load_dataset_jsonl  # noqa: E402
from research.schemas import BaselineConfig  # noqa: E402

ZEN_URL = os.environ.get("ZEN_URL", "https://opencode.ai/zen/v1")
# space-bunny-free (the model used for the first partial run) was retired by Zen;
# ZEN_MODEL/ZEN_OUT let a replication run on a currently-available model without
# overwriting the historical artifact.
ZEN_MODEL = os.environ.get("ZEN_MODEL", "space-bunny-free")
ZEN_OUT = os.environ.get("ZEN_OUT", "heldout_v2_zen_eval.json")
KEY_FILE = Path.home() / ".aura_zen_key"


def _field(obj, name):
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)


def main() -> dict:
    zen_key = KEY_FILE.read_text(encoding="utf-8").strip()
    assert zen_key.startswith("oc_sk_"), "zen key file malformed"
    rot = _key_cycle()
    s = get_settings()
    o = REPO / "results" / "kaust_three_pillars" / "heldout_v2"
    o.mkdir(parents=True, exist_ok=True)
    part = o / ZEN_OUT
    done = {}
    if part.exists():
        try:
            done = {r["id"]: r for r in json.loads(part.read_text(encoding="utf-8")).get("rows", [])}
        except Exception:
            done = {}
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
    orig_a, orig_c = s.model_analyzer, s.model_constitution
    orig_pa, orig_pc = s.analyzer_providers, s.constitution_providers
    orig_fb = s.provider_fallback_enabled
    orig_key, orig_url = s.openai_api_key, s.openai_base_url
    s.openai_api_key = zen_key
    s.openai_base_url = ZEN_URL
    s.provider_fallback_enabled = False
    s.model_analyzer = ZEN_MODEL
    s.model_constitution = ZEN_MODEL
    s.analyzer_providers = "zen"
    s.constitution_providers = "zen"
    prompts = (load_dataset_jsonl(REPO / "data" / "sealed" / "heldout_v2_attacks.jsonl")
               + load_dataset_jsonl(REPO / "data" / "sealed" / "heldout_v2_benign.jsonl"))
    assert len(prompts) == 253, len(prompts)
    try:
        for p in prompts:
            pid = str(p.get("prompt_id"))
            if pid in done:
                continue
            next(rot)
            t = time.perf_counter()
            # Retry transient Zen failures in-row (free-tier 429/5xx): only bank
            # the row after 3 attempts so a blip never becomes a false data point.
            r, err = {}, "NOT_RUN"
            for attempt in range(3):
                try:
                    r = _run_pipeline_with_baseline(p.get("content"), None, pid, BaselineConfig.G_FULL_BLENDED)
                    err = None
                    break
                except Exception as exc:  # noqa
                    err = type(exc).__name__
                    time.sleep(15)
            flags = fallback_flags(r)
            llm = r.get("llm_result") or {}
            const = r.get("constitution_result") or {}
            rows.append({"id": pid, "attack": (p.get("ground_truth_label") or "") == "attack",
                         "decision": r.get("decision", "ERROR"),
                         "fallback": bool(flags["any"]), "error": err,
                         "analyzer_provider": _field(llm, "provider"),
                         "analyzer_model": _field(llm, "model"),
                         "constitution_provider": _field(const, "provider"),
                         "constitution_model": _field(const, "model"),
                         "latency_ms": round((time.perf_counter() - t) * 1000, 1)})
            _write(part, rows)
            print(f"[{len(rows)}] {pid} -> {rows[-1]['decision']} "
                  f"(a:{rows[-1]['analyzer_provider']} c:{rows[-1]['constitution_provider']})", flush=True)
            time.sleep(2)
    finally:
        s.model_analyzer, s.model_constitution = orig_a, orig_c
        s.analyzer_providers, s.constitution_providers = orig_pa, orig_pc
        s.provider_fallback_enabled = orig_fb
        s.openai_api_key, s.openai_base_url = orig_key, orig_url
    rep = _write(part, rows)
    print(f"ZEN V2: zen-served attacks {rep['zen_attacks_held']}/{rep['zen_n_attacks']} "
          f"benign {rep['zen_benign_held']}/{rep['zen_n_benign']} fallback: {rep['fallback']} "
          f"non-zen rows: {rep['non_zen_rows']} errors: {rep['errors']}")
    return rep


def _write(part: Path, rows: list) -> dict:
    zen = [r for r in rows if r.get("analyzer_provider") == "zen" and r.get("constitution_provider") == "zen"]
    atk = [r for r in zen if r["attack"]]
    ben = [r for r in zen if not r["attack"]]
    rep = {"n": len(rows), "zen_n": len(zen),
           "zen_n_attacks": len(atk), "zen_n_benign": len(ben),
           "zen_attacks_held": sum(1 for r in atk if r["decision"] in ("block", "review")),
           "zen_benign_held": sum(1 for r in ben if r["decision"] in ("block", "review")),
           "fallback": sum(1 for r in rows if r["fallback"] or r["error"]),
           "errors": sum(1 for r in rows if r.get("error")),
           "non_zen_rows": len(rows) - len(zen),
           "label": f"HELD-OUT V2 on Zen {ZEN_MODEL} (both LLM layers, one eval, never tuned)",
           "rows": rows}
    part.write_text(json.dumps(rep, indent=2), encoding="utf-8")
    return rep


if __name__ == "__main__":
    main()
