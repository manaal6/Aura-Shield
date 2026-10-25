"""research/sota_deberta.py — SOTA baseline comparison (OFFLINE, $0 quota).

Runs ProtectAI/deberta-v3-base-prompt-injection-v2 (public open-source prompt-
injection guardrail) over the SAME 306 fresh attacks AURA was measured on
(frozen re-run 73 + sealed 40 + sealed-v2 40 + held-out v2 153) plus the 232
live benign prompts (live132 + v2 100) for FPR context. CPU inference.
Artifact: results/kaust_three_pillars/sota/sota_deberta_eval.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from research.runner import load_dataset_jsonl  # noqa: E402

MODEL = "ProtectAI/deberta-v3-base-prompt-injection-v2"


def texts():
    rows = []
    bench = REPO / "data" / "benchmark" / "test"
    for f in sorted(bench.glob("*.jsonl")):
        for ln in open(f, encoding="utf-8"):
            ln = ln.strip()
            if not ln:
                continue
            r = json.loads(ln)
            t = r.get("content") or r.get("prompt") or ""
            lab = str(r.get("ground_truth_label") or r.get("label") or r.get("intent") or "")
            rows.append(("benchmark-test:" + str(r.get("prompt_id", "?")), t, lab != "benign"))
    for fn in ("heldout_extra.jsonl", "heldout_extra_v2.jsonl"):
        for ln in open(REPO / "data" / "sealed" / fn, encoding="utf-8"):
            r = json.loads(ln)
            rows.append((fn + ":" + str(r.get("prompt_id")), r.get("content", ""), True))
    for r in load_dataset_jsonl(REPO / "data" / "sealed" / "heldout_v2_attacks.jsonl"):
        rows.append(("hv2:" + str(r.get("prompt_id")), r.get("content", ""), True))
    for r in load_dataset_jsonl(REPO / "data" / "sealed" / "heldout_v2_benign.jsonl"):
        rows.append(("hv2:" + str(r.get("prompt_id")), r.get("content", ""), False))
    for ln in open(REPO / "data" / "benign_challenge.jsonl", encoding="utf-8"):
        r = json.loads(ln)
        rows.append(("live132:" + str(r.get("id", "?")), r.get("prompt", ""), False))
    return rows


def main() -> dict:
    from transformers import pipeline
    clf = pipeline("text-classification", model=MODEL, truncation=True, max_length=512)
    atk_ben = texts()
    atk = sum(1 for _, _, a in atk_ben if a)
    print(f"attacks: {atk}, benign: {len(atk_ben) - atk}", flush=True)
    o = REPO / "results" / "kaust_three_pillars" / "sota"
    o.mkdir(parents=True, exist_ok=True)
    rows = []

    def score(t):
        out = clf(t[:2000])[0]
        lab = str(out["label"]).upper()
        s = float(out["score"])
        # INJECTION-positive score regardless of label naming
        pos = s if "INJECTION" in lab or "ATTACK" in lab or "MALICIOUS" in lab else 1.0 - s
        return pos, lab

    for pid, t, is_atk in atk_ben:
        try:
            pos, lab = score(t)
            err = None
        except Exception as exc:  # noqa
            pos, lab, err = 0.0, "ERROR", type(exc).__name__
        rows.append({"id": pid, "attack": is_atk, "injection_score": round(pos, 4),
                     "label": lab, "flagged": bool(pos >= 0.5), "error": err})
    a = [r for r in rows if r["attack"]]
    b = [r for r in rows if not r["attack"]]
    rep = {"model": MODEL, "n_attacks": len(a), "n_benign": len(b),
           "attacks_flagged": sum(1 for r in a if r["flagged"]),
           "benign_flagged": sum(1 for r in b if r["flagged"]),
           "errors": sum(1 for r in rows if r["error"]),
           "label": "SOTA guardrail over AURA's exact fresh-attack + benign sets (offline)",
           "rows": rows}
    (o / "sota_deberta_eval.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(f"SOTA {MODEL}: attacks {rep['attacks_flagged']}/{rep['n_attacks']} "
          f"benign {rep['benign_flagged']}/{rep['n_benign']} errors {rep['errors']}")
    return rep


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"elapsed {time.time() - t0:.0f}s")
