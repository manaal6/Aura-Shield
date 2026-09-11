"""
experiments/cross_model/run_cross_model_matrix.py

Executes heterogeneous model role configurations (Exp 1 through 5) on the dev
benchmark split and produces a cross-model transferability matrix.

Usage:
  python experiments/cross_model/run_cross_model_matrix.py [--dry-run]
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

CROSS_DIR = ROOT / "experiments" / "cross_model"
RESULTS_DIR = ROOT / "results" / "cross_model_summary"


def run_cross_model_suite(dry_run=False, skip_guard=False):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    all_spec_files = sorted(CROSS_DIR.glob("*.json"))

    print(f"Running Cross-Model Independence Suite ({len(all_spec_files)} configurations)...")
    matrix_rows = []

    for spec_file in all_spec_files:
        spec = load_spec(spec_file)
        print(f"\n=======================================================")
        print(f"Executing: {spec.experiment_name} ({spec.experiment_id})")
        print(f"Model Roles:")
        print(f"  Analyzer:     {spec.model_roles.analyzer}")
        print(f"  Constitution: {spec.model_roles.constitution}")
        print(f"  Downstream:   {spec.model_roles.downstream}")
        print(f"=======================================================")

        runner = BenchmarkRunner(spec, verbose=False)
        per_prompt, result = runner.run(dry_run=dry_run, skip_expense_guard=skip_guard)

        m = result.metrics
        matrix_rows.append({
            "Experiment_ID": spec.experiment_id,
            "Analyzer_Model": spec.model_roles.analyzer.split("/")[-1],
            "Constitution_Model": spec.model_roles.constitution.split("/")[-1],
            "Downstream_Model": spec.model_roles.downstream.split("/")[-1],
            "Total_Prompts": m.get("n_total", 0),
            "Recall": m.get("recall"),
            "Precision": m.get("precision"),
            "F1": m.get("f1"),
            "FPR": m.get("fpr"),
            "Avg_Latency_ms": result.latency.get("avg_ms"),
        })

    # Export transferability matrix
    table_path = RESULTS_DIR / "cross_model_matrix.md"
    export_markdown_table(matrix_rows, table_path)
    json_path = RESULTS_DIR / "cross_model_matrix.json"
    export_json(matrix_rows, json_path)

    print("\n\n=========================================================================================")
    print("                      CROSS-MODEL INDEPENDENCE TRANSFERABILITY MATRIX                    ")
    print("=========================================================================================")
    print(f"{'Experiment':<32} {'Analyzer':<22} {'Constitution':<24} {'Recall':>8} {'Precision':>10}")
    print("-" * 100)
    for r in matrix_rows:
        def fmt(v): return f"{v:.2%}" if v is not None else "n/a"
        print(f"{r['Experiment_ID']:<32} {r['Analyzer_Model']:<22} {r['Constitution_Model']:<24} {fmt(r['Recall']):>8} {fmt(r['Precision']):>10}")
    print("=" * 100)
    print(f"\nCross-model matrix summary saved to: {table_path.relative_to(ROOT)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AURA Shield Cross-Model Matrix Suite")
    parser.add_argument("--dry-run", action="store_true", help="Perform dry run without calling inference")
    parser.add_argument("--skip-guard", action="store_true", help="Skip expensive run guard")
    args = parser.parse_args()

    run_cross_model_suite(dry_run=args.dry_run, skip_guard=args.skip_guard)
