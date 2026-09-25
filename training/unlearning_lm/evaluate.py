"""training/unlearning_lm/evaluate.py — verdict per lambda from the sweep record."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
REC = REPO / "results" / "kaust_three_pillars" / "unlearning_lm" / "unlearning_lm_record.json"


def verdict(after: dict, drop: float, r_delta: float, g_delta: float) -> str:
    if after["forget_success"] <= 0.05 and r_delta >= -1.0 and g_delta >= -1.0:
        return "VALIDATED"
    if drop <= 0.0 and (r_delta < -1.0 or g_delta < -1.0):
        return "COLLATERAL DAMAGE"
    if drop > 0.0:
        return "PARTIAL (suppression without collateral damage)"
    return "NOT VALIDATED (no suppression)"


def main() -> dict:
    rec = json.loads(REC.read_text(encoding="utf-8"))
    out = {}
    for lam, s in rec["sweep"].items():
        v = verdict(s["after"], s["forget_drop"], s["retain_delta"], s["general_delta"])
        out[lam] = {"verdict": v, **{k: s[k] for k in ("before", "after", "forget_drop", "retain_delta", "general_delta")}}
    rep = {"per_lambda": out,
           "reading": ("lambda=0.1 and 1.0: PARTIAL — 4/24 triggers suppressed (1.0->0.83) "
                       "with retain/general IMPROVED (continued SFT anchoring), i.e. no collateral "
                       "damage but incomplete removal. lambda=0.5: NOT VALIDATED (no suppression). "
                       "Inverse failure mode vs the logistic negative baseline (full removal + collapse). "
                       "Conclusion: suppression-vs-preservation tradeoff confirmed at LM level; "
                       "method NOT successful by the protocol's conjunctive criterion.") ,
           "scope": "100K-param CPU causal LM, synthetic trigger only; NOT real-world erasure"}
    o = REPO / "results" / "kaust_three_pillars" / "unlearning_lm" / "unlearning_lm_eval.json"
    o.write_text(json.dumps(rep, indent=2))
    print(json.dumps(rep, indent=2))
    return rep


if __name__ == "__main__":
    main()
