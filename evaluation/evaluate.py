"""
evaluation/evaluate.py

Runs the full AURA Shield pipeline against evaluation/benchmark_dataset.json
and computes Attack Success Rate, precision, recall, and false positive/
negative rates from the ACTUAL results of that run.

Honesty requirement (per project rules): this script never hardcodes or
invents a metric. Every number printed here is computed from the JSON
results file this script itself writes. If the LLM analyzer could not
reach Groq (no API key / no network), that is detected and reported
explicitly in the output - the script does not pretend a fallback run is
a full evaluation.
"""
import json
import logging
import time
from pathlib import Path

from app.storage.database import init_db
from app.models import IncomingRequest
from app.pipeline import process_request

# Small delay between benchmark requests so a 40-prompt run doesn't burst
# past Groq's free-tier requests-per-minute limit and trigger 429 retries.
# Adjust based on your account's actual rate limit if needed.
REQUEST_DELAY_SECONDS = 2.0

logging.basicConfig(level=logging.WARNING)

DATASET_PATH = Path(__file__).parent / "benchmark_dataset.json"
RESULTS_PATH = Path(__file__).parent / "results.json"

# A prompt is treated as a "positive" (attack) if its category is anything
# other than benign. A decision of "block" or "review" counts as the
# detector flagging it; "allow" counts as not flagged.
ATTACK_CATEGORIES = {"direct_injection", "indirect_injection", "jailbreak"}


def run_benchmark() -> list[dict]:
    init_db()
    dataset = json.loads(DATASET_PATH.read_text())

    results = []
    any_real_llm_call = False

    for item in dataset:
        request = IncomingRequest(
            user_prompt=item["user_prompt"],
            source_content=item.get("source_content"),
            request_id=item["id"],
        )
        outcome = process_request(request)

        # process_request() now returns the rule/llm detection results
        # directly, so we don't need (and must not) call the detectors a
        # second time here - doing so was doubling Groq API calls and
        # burning through the free-tier rate limit during a benchmark run.
        rule_result = outcome["rule_result"]
        llm_result = outcome["llm_result"]
        if not llm_result.used_fallback:
            any_real_llm_call = True

        is_attack = item["category"] in ATTACK_CATEGORIES
        flagged = outcome["decision"] in ("block", "review")

        results.append({
            "id": item["id"],
            "category": item["category"],
            "expected_behavior": item["expected_behavior"],
            "actual_decision": outcome["decision"],
            "risk_score": outcome["risk_score"],
            "explanation": outcome["explanation"],
            "rule_matched": rule_result.matched,
            "rule_patterns": rule_result.matched_patterns,
            "llm_used_fallback": llm_result.used_fallback,
            "is_attack_ground_truth": is_attack,
            "flagged_by_shield": flagged,
        })

        # Only worth pausing if we're actually hitting the network -
        # rule-only fallback runs don't need to be rate-limited.
        if not llm_result.used_fallback:
            time.sleep(REQUEST_DELAY_SECONDS)

    RESULTS_PATH.write_text(json.dumps(results, indent=2))
    return results, any_real_llm_call


def compute_metrics(results: list[dict]) -> dict:
    tp = sum(1 for r in results if r["is_attack_ground_truth"] and r["flagged_by_shield"])
    fn = sum(1 for r in results if r["is_attack_ground_truth"] and not r["flagged_by_shield"])
    fp = sum(1 for r in results if not r["is_attack_ground_truth"] and r["flagged_by_shield"])
    tn = sum(1 for r in results if not r["is_attack_ground_truth"] and not r["flagged_by_shield"])

    total_attacks = tp + fn
    total_benign = fp + tn

    precision = tp / (tp + fp) if (tp + fp) > 0 else None
    recall = tp / (tp + fn) if (tp + fn) > 0 else None
    attack_success_rate = fn / total_attacks if total_attacks > 0 else None  # attacks that got through = ASR
    false_positive_rate = fp / total_benign if total_benign > 0 else None

    return {
        "true_positives": tp,
        "false_negatives": fn,
        "false_positives": fp,
        "true_negatives": tn,
        "precision": precision,
        "recall": recall,
        "attack_success_rate": attack_success_rate,
        "false_positive_rate": false_positive_rate,
    }


def print_report(results: list[dict], metrics: dict, real_llm: bool):
    print("=" * 70)
    print("AURA Shield - Benchmark Evaluation")
    print("=" * 70)
    if not real_llm:
        print("NOTE: No Groq API key was available in this run. The LLM Security")
        print("Analyzer ran in FAIL-SAFE FALLBACK mode for every prompt (fixed")
        print("raw_signal=0.3, is_suspicious=False), NOT as a real semantic judgment.")
        print("The numbers below reflect the RULE-DETECTOR-DRIVEN portion of the")
        print("pipeline only. This is an honest partial result, not a full")
        print("evaluation of the two-layer system described in the architecture.")
        print("Re-run with a real GROQ_API_KEY in .env to get the full-pipeline")
        print("numbers this project is ultimately meant to report.")
    else:
        print("LLM Security Analyzer made real Groq API calls for this run.")
    print("-" * 70)

    print(f"{'category':<20}{'expected':<16}{'actual':<10}{'risk':<8}{'flagged'}")
    for r in results:
        print(f"{r['category']:<20}{r['expected_behavior']:<16}{r['actual_decision']:<10}{r['risk_score']:<8.2f}{r['flagged_by_shield']}")

    print("-" * 70)
    print(f"True positives (attacks flagged):     {metrics['true_positives']}")
    print(f"False negatives (attacks missed):     {metrics['false_negatives']}")
    print(f"False positives (benign flagged):     {metrics['false_positives']}")
    print(f"True negatives (benign allowed):      {metrics['true_negatives']}")
    print("-" * 70)
    def fmt(v): return f"{v:.2%}" if v is not None else "n/a"
    print(f"Precision:                {fmt(metrics['precision'])}")
    print(f"Recall:                   {fmt(metrics['recall'])}")
    print(f"Attack Success Rate:      {fmt(metrics['attack_success_rate'])}  (lower is better)")
    print(f"False Positive Rate:      {fmt(metrics['false_positive_rate'])}")
    print("=" * 70)


if __name__ == "__main__":
    results, real_llm = run_benchmark()
    metrics = compute_metrics(results)
    print_report(results, metrics, real_llm)

    summary = {"real_llm_calls_used": real_llm, "metrics": metrics}
    (Path(__file__).parent / "metrics_summary.json").write_text(json.dumps(summary, indent=2))
