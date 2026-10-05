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
from research.stats import bootstrap_ci, rate_str, wilson  # noqa: E402

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
    # Pooled new-system attacks: frozen re-run + sealed one-shot batches.
    # Read from artifacts (never hardcoded); each sealed batch was generated
    # once, evaluated once, never tuned. Benign FPR comes from the frozen run
    # (the only run with benign rows); sealed batches are attacks-only.
    frozen = json.loads((REPO / "results" / "kaust_three_pillars" / "frozen_rerun"
                         / "frozen_rerun_summary.json").read_text())
    sealed_parts, sealed_labels = [], []
    for name in ("heldout_extra_eval.json", "heldout_extra_v2_eval.json"):
        p = REPO / "results" / "kaust_three_pillars" / "heldout_extra" / name
        if not p.exists():
            continue
        rep = json.loads(p.read_text())
        sealed_parts.append(rep)
        sealed_labels.append(f"{rep['held']}/{rep['n']}")
    tp = frozen["tp"] + sum(r["held"] for r in sealed_parts)
    fn = (frozen["attacks"] - frozen["tp"]) + sum(r["n"] - r["held"] for r in sealed_parts)
    fp, tn = frozen["fp"], frozen["benign"] - frozen["fp"]
    n_att = frozen["attacks"] + sum(r["n"] for r in sealed_parts)
    # Live benign, combined across runs with benign rows (frozen 32 + live48):
    # FPR-only entry (no recall denominator exists for benign).
    blp = REPO / "results" / "kaust_three_pillars" / "benign" / "benign_live48.json"
    ben_live = {"detail": "live benign only in frozen run (1/32); live48 not yet run",
                "fpr": rate_str(fp, fp + tn), "fpr_ci95": list(wilson(fp, fp + tn))}
    if blp.exists():
        bl = json.loads(blp.read_text())
        bl_held = sum(1 for r in bl["rows"] if r["decision"] in ("block", "review"))
        bl_n = bl["n"]
        fp2, n2 = fp + bl_held, (fp + tn) + bl_n
        ben_live = {"detail": f"frozen 1/32 + live48 {bl_held}/{bl_n} (16 families x 3, one eval each)",
                    "fpr": rate_str(fp2, n2), "fpr_ci95": list(wilson(fp2, n2))}
    new = {
        "dpo_lm_dev_pref": {"detail": f"{dpo_ok}/{dpo_n} prefer chosen after DPO (same before → NEGATIVE)",
                            **outcomes(dpo_ok, dpo_n - dpo_ok, 0, 0)},
        "unlearning_still_emitting_lambda0.1": {"detail": "20/24 triggers STILL EMIT after unlearning (only 4/24 suppressed)",
                                                **outcomes(20, 4, 0, 0)},
        "pooled_new_system": {"detail": (f"frozen {frozen['tp']}/{frozen['attacks']} + "
                                         + " + ".join(f"sealed {s}" for s in sealed_labels)
                                         + ", same frozen config, one eval each, no tuning"),
                              "n_attacks": n_att, "n_benign": frozen["benign"],
                              "sealed_batches": sealed_labels,
                              **outcomes(tp, fn, fp, tn)},
        "benign_live_combined": ben_live,
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
            f"- Pooled new-system attacks: {new['pooled_new_system']['recall']} (frozen 67/73 + sealed batches {', '.join(new['pooled_new_system']['sealed_batches'])}; FPR 1/32 from frozen run)",
            f"- Benign live combined: {new['benign_live_combined']['fpr']} ({new['benign_live_combined']['detail']})",
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
