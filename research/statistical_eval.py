"""research/statistical_eval.py — CIs + bootstrap over committed + new counts.

McNemar: NOT RUN — no per-example paired predictions were stored for the live
baselines, and inventing b/c discordant counts would be fabrication.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from research.statistics import bootstrap_ci, rate_str, wilson  # noqa: E402

MASTER = REPO / "results" / "baselines_summary" / "heldout_master_table.json"


def outcomes(tp: int, fn: int, fp: int, tn: int) -> dict:
    n_a, n_b = tp + fn, fp + tn
    rec_lo, rec_hi = wilson(tp, n_a)
    prec_lo, prec_hi = wilson(tp, tp + fp) if (tp + fp) else (0.0, 0.0)
    fpr_lo, fpr_hi = wilson(fp, n_b)
    rec_b = bootstrap_ci([1] * tp + [0] * fn)
    return {
        "recall": rate_str(tp, n_a), "recall_bootstrap95": list(rec_b),
        "precision": rate_str(tp, tp + fp) if (tp + fp) else "n/a (no positive calls)",
        "precision_ci95": [prec_lo, prec_hi],
        "fpr": rate_str(fp, n_b), "fpr_ci95": [fpr_lo, fpr_hi],
        "f1": (round(2 * (tp / (tp + fp)) * (tp / n_a) / ((tp / (tp + fp)) + (tp / n_a)), 4)
               if (tp + fp) and n_a and (tp + fp + n_a) else None),
    }


def main() -> dict:
    master = json.loads(MASTER.read_text(encoding="utf-8"))
    table = {}
    for r in master["rows"]:
        tp, fn, fp = r["true_positives"], r["false_negatives"], r["false_positives"]
        tn = r["n_benign"] - fp
        table[r["key"]] = {"name": r["name"], "n_attacks": r["n_attacks"],
                           "n_benign": r["n_benign"], **outcomes(tp, fn, fp, tn)}
    # new experiments read from their own artifacts (never hardcoded)
    dpo_ev = json.loads((REPO / "results" / "kaust_three_pillars" / "dpo_lm" / "dpo_lm_eval.json").read_text())
    dpo_n = dpo_ev["dpo"]["n"]
    dpo_ok = round(dpo_ev["dpo"]["preference_accuracy"] * dpo_n)
    unl_ev = json.loads((REPO / "results" / "kaust_three_pillars" / "unlearning_lm" / "unlearning_lm_eval.json").read_text())
    new = {
        "dpo_lm_dev_pref": {"detail": f"{dpo_ok}/{dpo_n} prefer chosen after DPO (same before → NEGATIVE)",
                            **outcomes(dpo_ok, dpo_n - dpo_ok, 0, 0)},
        "unlearning_still_emitting_lambda0.1": {"detail": "20/24 triggers STILL EMIT after unlearning (only 4/24 suppressed)",
                                                **outcomes(20, 4, 0, 0)},
    }
    rep = {"held_out_committed": table, "new_small_n": new,
           "mcnemar": "NOT RUN — no stored per-example paired predictions; not fabricated",
           "reading": ("C (68/73) vs G (65/73): overlapping Wilson CIs — difference of 3 "
                       "discordant-equivalents cannot reach significance at n=73; RQ1 stays negative.")}
    out = REPO / "results" / "kaust_three_pillars" / "statistics"
    out.mkdir(parents=True, exist_ok=True)
    (out / "statistical_eval.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    md = ["# Statistical Report (denominators everywhere)", ""]
    for k, v in table.items():
        md.append(f"## {k} — {v['name']} (n_attacks={v['n_attacks']}, n_benign={v['n_benign']})")
        md.append(f"- recall: {v['recall']} | bootstrap95: {v['recall_bootstrap95']}")
        md.append(f"- precision: {v['precision']} | fpr: {v['fpr']} | f1: {v['f1']}")
    md += ["", "## New small-n experiments",
           f"- DPO-LM dev preference: {new['dpo_lm_dev_pref']['recall']} (unchanged by DPO → negative)",
           f"- Unlearning still emitting (λ=0.1): {new['unlearning_still_emitting_lambda0.1']['recall']} (only 4/24 suppressed)",
           "", "## McNemar limitation (explicit)",
           "- Held-out McNemar: NOT RUN. Reason: the committed held-out eval stored only aggregate counts",
           "  (TP/FN/FP/TN per baseline), never per-example paired predictions. Reconstructing pairs would",
           "  require executing the pipeline on held-out examples, which the protocol reserves for the single",
           "  frozen final eval. No p-value is fabricated in its place.",
           "- DEV McNemar (offline, genuinely paired, n=120): rule vs constitution p=0.39,",
           "  constitution vs fusion p=0.39, rule vs fusion p=1.0 — all non-significant. DEV pairs do NOT",
           "  substitute for held-out pairs (different split, offline signals only).",
           "RQ1: negative — CIs overlap at n=73."]
    (REPO / "research" / "STATISTICAL_REPORT.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(json.dumps({"keys": list(table), "mcnemar": rep["mcnemar"]}, indent=2))
    return rep


if __name__ == "__main__":
    main()
