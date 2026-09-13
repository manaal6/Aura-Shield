"""
experiments/baselines/run_baselines.py

Executes modular baseline configurations (A through I) on the exact same
development benchmark split and compiles a consolidated comparison matrix.

Usage:
  python experiments/baselines/run_baselines.py [--baselines a,i] [--dry-run]
"""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from research.experiment import load_spec
from research.metrics import export_json, export_markdown_table
from research.runner import BenchmarkRunner
from research.schemas import DatasetSplit

BASELINES_DIR = ROOT / "experiments" / "baselines"
RESULTS_DIR = ROOT / "results" / "baselines_summary"


def retarget_spec_to_test(spec):
    """Return a copy of the spec pointed at the held-out test split, so the
    same baseline definitions can be evaluated on unseen prompts without
    editing the committed dev-split spec files."""
    test_files = sorted(str(p.relative_to(ROOT)).replace("\\", "/")
                        for p in (ROOT / "data" / "benchmark" / "test").glob("*.jsonl"))
    return spec.model_copy(update={
        "experiment_id": f"{spec.experiment_id}_test",
        "experiment_name": f"{spec.experiment_name} [Held-out test split]",
        "dataset_split": DatasetSplit.TEST,
        "dataset_files": test_files,
    })


def run_baseline_suite(baseline_keys=None, dry_run=False, skip_guard=False, split="dev",
                       delay_seconds=2.0, reject_fallback=False):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    all_spec_files = sorted(BASELINES_DIR.glob("*.json"))

    if baseline_keys:
        selected_keys = [k.strip().lower() for k in baseline_keys.split(",")]
        all_spec_files = [
            f for f in all_spec_files
            if any(k in f.stem for k in selected_keys)
        ]

    print(f"Running baseline suite ({len(all_spec_files)} configurations, split={split}, "
          f"delay={delay_seconds}s)...")
    summary_rows = []

    for spec_file in all_spec_files:
        spec = load_spec(spec_file)
        if split == "test":
            spec = retarget_spec_to_test(spec)
        print(f"\n=======================================================")
        print(f"Executing: {spec.experiment_name} ({spec.baseline_config.value})")
        print(f"=======================================================")

        runner = BenchmarkRunner(spec, verbose=False, delay_seconds=delay_seconds)
        per_prompt, result = runner.run(dry_run=dry_run, skip_expense_guard=skip_guard)

        # A silent fallback to offline heuristics would distort the comparison;
        # refuse to record such a run as a live-model result.
        if reject_fallback:
            fb = [r for r in per_prompt
                  if r.get("llm_used_fallback") or r.get("constitution_fallback")]
            required_llm = spec.baseline_config.value not in ("A_rule_only", "I_embedding")
            if required_llm and fb:
                raise RuntimeError(
                    f"{spec.baseline_config.value}: {len(fb)}/{len(per_prompt)} prompts "
                    "fell back to offline heuristics — result rejected as a live-model "
                    "measurement. Increase --delay and re-run."
                )

        m = result.metrics
        summary_rows.append({
            "Baseline": spec.baseline_config.value,
            "Name": spec.experiment_name,
            "Total": m.get("n_total", 0),
            "Precision": m.get("precision"),
            "Recall": m.get("recall"),
            "F1": m.get("f1"),
            "FPR": m.get("fpr"),
            "Real_LLM": result.real_llm_calls_used,
            "Avg_Latency_ms": result.latency.get("avg_ms"),
        })

    # Export comparison table
    suffix = "_test" if split == "test" else ""
    table_path = RESULTS_DIR / f"baseline_comparison{suffix}.md"
    export_markdown_table(summary_rows, table_path)
    json_path = RESULTS_DIR / f"baseline_comparison{suffix}.json"
    export_json(summary_rows, json_path)

    print("\n\n=======================================================")
    print("           BASELINE EXPERIMENT COMPARISON MATRIX       ")
    print("=======================================================")
    print(f"{'Baseline':<22} {'Recall':>8} {'Precision':>10} {'F1':>8} {'FPR':>8}")
    print("-" * 60)
    for r in summary_rows:
        def fmt(v): return f"{v:.2%}" if v is not None else "n/a"
        print(f"{r['Baseline']:<22} {fmt(r['Recall']):>8} {fmt(r['Precision']):>10} {fmt(r['F1']):>8} {fmt(r['FPR']):>8}")
    print("=" * 60)
    print(f"\nComparison summary saved to: {table_path.relative_to(ROOT)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AURA Shield Baseline Evaluation Suite")
    parser.add_argument("--baselines", type=str, default=None, help="Comma-separated keys to run, e.g. 'a,i'")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run without calling inference")
    parser.add_argument("--skip-guard", action="store_true", help="Skip expensive run guard")
    parser.add_argument("--split", type=str, default="dev", choices=["dev", "test"],
                        help="Dataset split to evaluate on. 'test' = the 105-prompt held-out split.")
    parser.add_argument("--delay", type=float, default=2.0,
                        help="Seconds between LLM calls (rate limiting).")
    parser.add_argument("--reject-fallback", action="store_true",
                        help="Abort a baseline run if any prompt used the offline fallback, "
                             "so results always reflect live-model behaviour.")
    args = parser.parse_args()

    run_baseline_suite(baseline_keys=args.baselines, dry_run=args.dry_run,
                       skip_guard=args.skip_guard, split=args.split,
                       delay_seconds=args.delay, reject_fallback=args.reject_fallback)
