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

BASELINES_DIR = ROOT / "experiments" / "baselines"
RESULTS_DIR = ROOT / "results" / "baselines_summary"


def run_baseline_suite(baseline_keys=None, dry_run=False, skip_guard=False):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    all_spec_files = sorted(BASELINES_DIR.glob("*.json"))

    if baseline_keys:
        selected_keys = [k.strip().lower() for k in baseline_keys.split(",")]
        all_spec_files = [
            f for f in all_spec_files
            if any(k in f.stem for k in selected_keys)
        ]

    print(f"Running baseline suite ({len(all_spec_files)} configurations)...")
    summary_rows = []

    for spec_file in all_spec_files:
        spec = load_spec(spec_file)
        print(f"\n=======================================================")
        print(f"Executing: {spec.experiment_name} ({spec.baseline_config.value})")
        print(f"=======================================================")

        runner = BenchmarkRunner(spec, verbose=False)
        per_prompt, result = runner.run(dry_run=dry_run, skip_expense_guard=skip_guard)

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
    table_path = RESULTS_DIR / "baseline_comparison.md"
    export_markdown_table(summary_rows, table_path)
    json_path = RESULTS_DIR / "baseline_comparison.json"
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
    args = parser.parse_args()

    run_baseline_suite(baseline_keys=args.baselines, dry_run=args.dry_run, skip_guard=args.skip_guard)
