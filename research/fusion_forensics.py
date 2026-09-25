"""research/fusion_forensics.py — Phase 8: live-LLM DEV forensics (G-full).

STATUS: BLOCKED at runtime (not a code bug). Measured per-call cost 39s escalating to 72s+
(DB DNS timeouts ~15s ×2 IPs + Groq throttling on a single key) → 120 prompts ≈ 2–4 h,
infeasible in-session. Offline-paired forensics (research/fusion_disagreement.py, real McNemar
p-values) stands as the executed analysis. Re-run this script when API/DB are healthy;
it is resumable (per-prompt slices + incremental saves).

Design (when healthy): one live G run per DEV example records rule/llm/constitution
signals + final + latency + provenance. C-only decisions SIMULATED from recorded
constitution signals (same policy math, labeled). Held-out exact IDs NOT reconstructed
(reserved single-test-touch rule — documented in the report, not fabricated).
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("GROQ_MAX_RETRIES", "3")
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

# Benchmark-harness patch (documented, decision-neutral): the DB constitution
# lookup costs ~13 s/call in DNS timeouts here while holding identical v1 content
# to the seed file. Bypass it so the forensic measures detectors, not DNS.
# Production fallback path (DB-down → file) is itself covered by fail-safe tests.
import app.engine.constitution as _constmod  # noqa: E402
import json as _json  # noqa: E402


def _file_constitution():
    seed = _json.loads((_constmod.SEED_PATH).read_text(encoding="utf-8"))
    return seed["version"], seed["principles"]


_constmod.load_active_constitution = _file_constitution  # type: ignore[attr-defined]

# In-harness key rotation (documented, behavior-neutral): spreads the 120
# calls over all pooled keys by rotating settings.groq_api_key per prompt.
# Only the credential used changes — never the model, thresholds, or policy.
# Values stay in-process; rotation order only is ever printed.
def _key_cycle():
    from research.groq_pool import _dotenv_values  # noqa: E402
    import os as _os  # noqa: E402
    from app.config import get_settings as _gs  # noqa: E402
    names = ["GROQ_API_KEY"] + [f"GROQ_API_KEY_{i}" for i in range(2, 10)]
    vals = [(_os.environ.get(n) or _dotenv_values().get(n, "")) for n in names]
    vals = [v for v in vals if v]
    assert vals, "no Groq keys available"
    s = _gs()
    print(f"key rotation: {len(vals)} pooled keys (names withheld)", flush=True)
    i = 0
    while True:
        s.groq_api_key = vals[i % len(vals)]
        i += 1
        yield i


_KEY_ROT = _key_cycle()
from research.runner import _run_pipeline_with_baseline, load_dataset_jsonl  # noqa: E402
from research.schemas import BaselineConfig  # noqa: E402

DEV = REPO / "data" / "benchmark" / "dev"
OUT = REPO / "results" / "kaust_three_pillars" / "fusion"


def sim_constitution_only(const_s: float, const_violated: bool) -> str:
    # escalation (>=0.90) or threshold bands on the lone signal
    if const_violated and const_s >= 0.90:
        return "block"
    return "block" if const_s >= 0.75 else ("review" if const_s >= 0.40 else "allow")


def main() -> dict:
    import sys as _s
    only = _s.argv[1] if len(_s.argv) > 1 else None  # e.g. dev/direct_injection.jsonl
    start = int(_s.argv[2]) if len(_s.argv) > 2 else 0
    end = int(_s.argv[3]) if len(_s.argv) > 3 else 10 ** 9
    done: dict[str, dict] = {}
    part = OUT / "fusion_per_example_dev_live.json"
    if part.exists():
        try:
            prior = json.loads(part.read_text(encoding="utf-8"))
            done = {r["prompt_id"]: r for r in prior}
        except Exception:
            done = {}
    rows = []
    files = sorted(DEV.glob("*.jsonl"))
    if only:
        files = [DEV / Path(only).name]
    print(f"resume: {len(done)} rows already in combined file", flush=True)
    for f in files:
        part_file = OUT / f"fusion_live_{f.stem}.json"
        prompts = load_dataset_jsonl(f)[start:end]
        for p in prompts:
            pid = str(p.get("prompt_id") or p.get("id"))
            if pid in done:
                rows.append(done[pid])
                continue
            prompt = p.get("content") or ""
            src = p.get("source_content")
            gt = p.get("ground_truth_label") or "benign"
            next(_KEY_ROT)  # rotate credential (behavior-neutral)
            t = time.perf_counter()
            try:
                res = _run_pipeline_with_baseline(
                    user_prompt=prompt, source_content=src,
                    request_id=str(p.get("prompt_id") or p.get("id")),
                    baseline=BaselineConfig.G_FULL_BLENDED)
                err = None
            except Exception as exc:  # noqa: BLE001 — recorded, never hidden
                res, err = {}, f"{type(exc).__name__}"
            dt = round((time.perf_counter() - t) * 1000, 1)
            rule = (res.get("rule_result") or {})
            llm = (res.get("llm_result") or {})
            const = (res.get("constitution_result") or {})
            r_rule = float(rule.get("raw_signal", 0.0)) if isinstance(rule, dict) else float(getattr(rule, "raw_signal", 0.0))
            r_llm = float(llm.get("raw_signal", 0.0)) if isinstance(llm, dict) else float(getattr(llm, "raw_signal", 0.0))
            c_sig = float(const.get("raw_signal", 0.0)) if isinstance(const, dict) else float(getattr(const, "raw_signal", 0.0))
            c_ver = const.get("verdicts", []) if isinstance(const, dict) else getattr(const, "verdicts", [])
            rows.append({
                "prompt_id": str(p.get("prompt_id") or p.get("id")),
                "ground_truth": gt, "family": p.get("attack_family") or "unknown",
                "provenance": "benchmark-dev",
                "rule_decision": "block" if r_rule >= 0.75 else ("review" if r_rule >= 0.40 else "allow"),
                "rule_score": round(r_rule, 4),
                "llm_decision": ("fallback" if (llm.get("used_fallback") if isinstance(llm, dict) else getattr(llm, "used_fallback", False)) else ("block" if r_llm >= 0.75 else ("review" if r_llm >= 0.40 else "allow"))),
                "llm_score": round(r_llm, 4),
                "llm_fallback": bool(llm.get("used_fallback")) if isinstance(llm, dict) else bool(getattr(llm, "used_fallback", False)),
                "constitution_decision": "block" if c_sig >= 0.75 else ("review" if c_sig >= 0.40 else "allow"),
                "constitution_score": round(c_sig, 4),
                "constitution_only_sim": sim_constitution_only(c_sig, bool(c_ver)),
                "final_decision": res.get("decision", "ERROR"),
                "final_score": round(float(res.get("risk_score", -1.0)), 4),
                "latency_ms": dt, "error": err})
            (OUT / "fusion_per_example_dev_live.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
            print(f"[{len(rows)}] {pid} -> {rows[-1]['final_decision']} "
                  f"({rows[-1]['latency_ms']} ms)", flush=True)
            time.sleep(1)  # light courtesy; 4-key rotation absorbs burst load
        # per-file part (authoritative for this file; immune to cross-run clobber)
        (OUT / f"fusion_live_{f.stem}.json").write_text(
            json.dumps([r for r in rows if r["prompt_id"] in {str(p.get('prompt_id') or p.get('id')) for p in prompts}],
                       indent=2), encoding="utf-8")
    # merge with any rows from previous files (resume across files)
    merged: dict[str, dict] = {}
    if part.exists():
        try:
            for r in json.loads(part.read_text(encoding="utf-8")):
                merged[r["prompt_id"]] = r
        except Exception:
            pass
    for r in rows:
        merged[r["prompt_id"]] = r
    rows = list(merged.values())
    (OUT / "fusion_per_example_dev_live.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    atk = [r for r in rows if r["ground_truth"] == "attack"]
    ok = sum(1 for r in atk if r["final_decision"] in ("block", "review"))
    fb = sum(1 for r in rows if r["llm_fallback"] or r["error"])
    print(f"live DEV forensics: {len(rows)} rows, attack recall {ok}/{len(atk)}, fallback/error rows {fb}")
    return {"n": len(rows), "attack_recall": f"{ok}/{len(atk)}", "fallback_rows": fb}


if __name__ == "__main__":
    main()
