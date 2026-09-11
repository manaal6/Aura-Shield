"""
experiments/safety_eval/run_safety_evaluation.py

Phase 10 executable runner: Downstream Safety Evaluation & Estimated Compromise Rate.

Evaluation mode: OFFLINE, REAL GATEWAY + SIMULATED DOWNSTREAM
  Gateway decisions come from the REAL Baseline I (TF-IDF embedding) detector,
  executed offline via research.runner._run_pipeline_with_baseline — the same
  code path as the Phase 11 held-out benchmark. Detector decisions are
  therefore real, deterministic, and reproducible without a GROQ_API_KEY.
  Downstream responses are SIMULATED heuristically from prompt content and
  attack family (an approximation of live alignment behavior, not a live
  model). See docs/research_report.md §8 for the evaluation mode labeling
  convention and the caveat that downstream numbers require re-running with
  a live GROQ_API_KEY before being cited.

Demonstrates rigorous ASR calculation across gateway decisions:
- Blocked prompts → attack_succeeded = False (downstream model never exposed)
- Bypassed attacks → downstream responses evaluated for unsafe behavior / refusals
- Generates formal ASR, B-ASR (Bypassed ASR), and GMR (Gateway Mitigation Rate) metrics
- Produces per-family breakdown with Wilson 95% confidence intervals
"""

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from research.evaluator import DownstreamSafetyEvaluator, compute_aggregate_asr, simulate_downstream_response
from research.metrics import wilson_ci
from research.runner import _run_pipeline_with_baseline
from research.schemas import BaselineConfig
from experiments.benchmark.run_final_test_benchmark import load_test_split


# ---------------------------------------------------------------------------
# Test split loading
# ---------------------------------------------------------------------------

TEST_SPLIT_DIR = ROOT_DIR / "data" / "benchmark" / "test"

ATTACK_FAMILIES = [
    "authorization_attack",
    "multi_turn_manipulation",
    "policy_targeting",
    "tool_injection",
]
BENIGN_FAMILIES = [
    "benign_cybersecurity_holdout",
]


def _load_test_split() -> list:
    """Load and normalize all prompts from the held-out test split JSONL files."""
    return load_test_split(TEST_SPLIT_DIR)


def _real_baseline_i_decision(record):
    """
    Run the REAL Baseline I (TF-IDF embedding) detector on this record and
    return its gateway decision ("allow" / "review" / "block").

    This is not a simulation: it calls the same pipeline code path as the
    Phase 11 held-out benchmark (research.runner._run_pipeline_with_baseline),
    fully offline. On this test split Baseline I achieves 35.6% recall /
    100% precision — the decisions below should reproduce that result.
    """
    res = _run_pipeline_with_baseline(
        user_prompt=record.get("user_prompt", ""),
        source_content=record.get("source_content"),
        request_id=str(record.get("prompt_id", "")),
        baseline=BaselineConfig.I_EMBEDDING,
    )
    return str(res.get("decision", "allow")).lower()


def _compute_per_family_ci(per_family_asr):
    """Add Wilson 95% CI to per-family ASR stats."""
    enriched = {}
    for fam, stats in per_family_asr.items():
        n = stats.get("total_attacks", 0)
        k = stats.get("succeeded", 0)
        lo, hi = wilson_ci(k, n, z=1.96) if n > 0 else (0.0, 0.0)
        enriched[fam] = {**stats, "asr_ci_95_low": round(lo, 4), "asr_ci_95_high": round(hi, 4)}
    return enriched


def main():
    print("=" * 72)
    print("   AURA SHIELD — PHASE 10: DOWNSTREAM SAFETY & ASR EVALUATION     ")
    print("=" * 72)
    print()
    print("Evaluation mode: [OFFLINE] REAL GATEWAY + SIMULATED DOWNSTREAM")
    print("  Dataset       : held-out test split (105 prompts, 5 families)")
    print("  Gateway       : Baseline I (TF-IDF embedding) — REAL detector, offline")
    print("  Downstream    : Heuristic response simulation (no live API calls)")
    print("  Reproducible  : Yes — no external dependencies required")
    print("-" * 72)

    output_dir = ROOT_DIR / "results" / "safety_eval_summary"
    output_dir.mkdir(parents=True, exist_ok=True)

    # -----------------------------------------------------------------------
    # 1. Load all 105 held-out test prompts
    # -----------------------------------------------------------------------
    all_records = _load_test_split()
    print(f"\nLoaded {len(all_records)} prompts from test split:")
    family_counts = {}
    for r in all_records:
        fam = r.get("attack_family", "unknown")
        family_counts[fam] = family_counts.get(fam, 0) + 1
    for fam, count in sorted(family_counts.items()):
        print(f"  {fam}: {count} prompts")

    # -----------------------------------------------------------------------
    # 2. Apply simulated gateway decisions and build downstream response map
    # -----------------------------------------------------------------------
    raw_items = []
    simulated_downstream = {}
    decision_counts = {"allow": 0, "review": 0, "block": 0}

    for record in all_records:
        pid = str(record.get("prompt_id", ""))
        decision = _real_baseline_i_decision(record)
        decision_counts[decision] = decision_counts.get(decision, 0) + 1
        downstream_response = simulate_downstream_response(record, decision)

        raw_items.append({
            "prompt_id": pid,
            "ground_truth_label": record.get("ground_truth_label", "benign"),
            "attack_family": record.get("attack_family", "unknown"),
            "decision": decision,
            "user_prompt": record.get("user_prompt", ""),
        })
        simulated_downstream[pid] = downstream_response

    # -----------------------------------------------------------------------
    # 3. Compute estimated downstream compromise rate
    # -----------------------------------------------------------------------
    evaluator = DownstreamSafetyEvaluator(use_llm_judge=False)
    enriched_rows, asr_metrics = compute_aggregate_asr(
        raw_items,
        downstream_responses=simulated_downstream,
        evaluator=evaluator,
    )

    # Add Wilson CIs
    asr_metrics.per_family_asr = _compute_per_family_ci(asr_metrics.per_family_asr)
    n_total = asr_metrics.total_attacks_evaluated
    n_succeeded = asr_metrics.succeeded_attacks_count
    overall_ci_lo, overall_ci_hi = wilson_ci(n_succeeded, n_total, z=1.96) if n_total > 0 else (0.0, 0.0)

    print(f"\n--- Evaluation Results (n={len(all_records)} prompts, 5 families) ---")
    print(f"Total Attacks Evaluated : {asr_metrics.total_attacks_evaluated}")
    print(f"Bypassed Attacks        : {asr_metrics.bypassed_attacks_count}")
    print(f"Succeeded Attacks       : {asr_metrics.succeeded_attacks_count}")
    print(f"Attack Success Rate (ASR): {asr_metrics.attack_success_rate:.1%}  "
          f"[95% CI: {overall_ci_lo:.1%}\u2013{overall_ci_hi:.1%}]")
    print(f"Bypassed ASR (B-ASR)    : {asr_metrics.bypassed_attack_success_rate:.1%}")
    print(f"Gateway Mitigation Rate : {asr_metrics.gateway_mitigation_rate:.1%}")
    held = 0  # review-hold disabled in this offline experiment
    print(f"Gateway decisions       : ALLOW {decision_counts.get('allow', 0)} | "
          f"REVIEW-forwarded {decision_counts.get('review', 0)} | "
          f"REVIEW-held {held} | BLOCK {decision_counts.get('block', 0)}")

    # -----------------------------------------------------------------------
    # 4. Save JSON and Markdown artifacts
    # -----------------------------------------------------------------------
    json_path = output_dir / "safety_evaluation_results.json"
    json_out = asr_metrics.model_dump()
    json_out["evaluation_mode"] = "offline_real_gateway_simulated_downstream"
    json_out["dataset"] = "held_out_test_split_105_prompts"
    json_out["gateway"] = "baseline_i_tfidf_embedding_real_detector"
    json_out["overall_asr_ci_95"] = {"low": round(overall_ci_lo, 4), "high": round(overall_ci_hi, 4)}
    json_path.write_text(json.dumps(json_out, indent=2), encoding="utf-8")

    md_path = output_dir / "safety_evaluation_results.md"
    md_content = f"""# Downstream Safety Evaluation & Attack Success Rate (ASR) Report

> [!NOTE]
> **Evaluation Mode: [OFFLINE] REAL GATEWAY + SIMULATED DOWNSTREAM**
> Gateway decisions come from the **real** Baseline I (TF-IDF embedding) detector,
> executed offline via the same pipeline code path as the Phase 11 benchmark.
> Downstream responses are **simulated heuristically** (an approximation of live
> alignment behavior). No external API calls are made. Downstream numbers should
> be re-derived with a live GROQ_API_KEY before citation in a research paper.

## 1. Executive Summary

| Metric | Value | 95% Wilson CI |
| :--- | :--- | :--- |
| Total Prompts | `{len(all_records)}` | — |
| Total Attack Prompts | `{asr_metrics.total_attacks_evaluated}` | — |
| Bypassed Attacks | `{asr_metrics.bypassed_attacks_count}` | — |
| Succeeded Attacks | `{asr_metrics.succeeded_attacks_count}` | — |
| **Attack Success Rate (ASR)** | **`{asr_metrics.attack_success_rate:.1%}`** | `{overall_ci_lo:.1%}\u2013{overall_ci_hi:.1%}` |
| Bypassed Attack Success Rate (B-ASR) | `{asr_metrics.bypassed_attack_success_rate:.1%}` | — |
| **Gateway Mitigation Rate (GMR)** | **`{asr_metrics.gateway_mitigation_rate:.1%}`** | — |

> [!IMPORTANT]
> **Claim Discipline & Scientific Definition**:
> ASR is defined strictly as the proportion of attack prompts that produced prohibited or unsafe
> behavior in the downstream model. Attacks stopped by the gateway contribute 0 to succeeded attacks.
> Detector misses (bypasses) where the downstream model independently refused the instruction are
> correctly counted as **bypassed but NOT succeeded**.

## 2. Per-Family ASR Breakdown

| Attack Family | Total Attacks | Bypasses | Succeeded | Est. Compromise | B-Compromise | 95% CI |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for fam, stats in asr_metrics.per_family_asr.items():
        ci_lo = stats.get("asr_ci_95_low", 0.0)
        ci_hi = stats.get("asr_ci_95_high", 0.0)
        md_content += (
            f"| `{fam}` | {stats['total_attacks']} | {stats['bypassed']} | "
            f"{stats['succeeded']} | `{stats['asr']:.1%}` | `{stats['b_asr']:.1%}` | "
            f"`{ci_lo:.1%}\u2013{ci_hi:.1%}` |\n"
        )

    md_content += f"""
## 3. Methodology & Defense-in-Depth Observations

1. **Dataset**: All {len(all_records)} prompts from the held-out test split — 4 attack families
   (`authorization_attack`, `multi_turn_manipulation`, `policy_targeting`, `tool_injection`)
   and 1 benign family (`benign_cybersecurity_holdout`). This is {len(all_records) // 5}× larger than
   the previous 5-prompt illustrative sample.
2. **Gateway Defense Layer**: Blocks {asr_metrics.total_attacks_evaluated - asr_metrics.bypassed_attacks_count} of {asr_metrics.total_attacks_evaluated} attacks before downstream exposure.
3. **Downstream Refusal Layer**: Alignment-trained refusal behavior catches some bypassed attacks;
   only attacks that both bypass the gateway AND produce compliant downstream responses count toward ASR.
4. **True Security Posture**: Equating detector misses directly with ASR systematically overestimates
   attacker success; true downstream ASR accounts for the second refusal layer.

## 4. Limitations & Honest Caveats

- Gateway decisions come from the real offline Baseline I detector (not simulated),
  but only one baseline is evaluated here; the full blended pipeline (Baseline G)
  requires a live LLM analyzer and is not covered by this offline experiment.
- Downstream responses are modeled heuristically, not generated by a live LLM.
- These experiments **should be re-run with a live GROQ_API_KEY** to obtain real model responses
  before citing specific ASR numbers in a research paper.
- The Wilson CI reflects binomial sampling uncertainty under the simulation's assumptions,
  not the full epistemic uncertainty of actual model behavior.
"""
    md_path.write_text(md_content, encoding="utf-8")
    print(f"\nSaved report to: {md_path.relative_to(ROOT_DIR)}")
    print(f"Saved metrics to: {json_path.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    main()


