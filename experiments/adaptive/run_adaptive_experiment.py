"""
experiments/adaptive/run_adaptive_experiment.py

Executable runner for Phase 8: Adaptive Constitution Loop & Provenance System.
"""
import sys
from pathlib import Path

# Add project root to python path
ROOT_DIR = Path(__file__).parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from research.adaptive_loop import run_adaptive_experiment


def main():
    base_constitution_path = ROOT_DIR / "constitution.json"
    adaptation_dir = ROOT_DIR / "data" / "benchmark" / "adaptation"
    dev_dir = ROOT_DIR / "data" / "benchmark" / "dev"
    summary_path = ROOT_DIR / "results" / "adaptive_summary" / "adaptive_results.md"
    provenance_path = ROOT_DIR / "results" / "adaptive_summary" / "adaptive_provenance.json"

    print("==========================================================================")
    print("      AURA SHIELD — PHASE 8: ADAPTIVE CONSTITUTION EXPERIMENT             ")
    print("==========================================================================")
    print(f"Base Constitution : {base_constitution_path}")
    print(f"Adaptation Split  : {adaptation_dir}")
    print(f"Dev Split         : {dev_dir}")
    print(f"Summary Target    : {summary_path}")
    print(f"Provenance Target : {provenance_path}")
    print("--------------------------------------------------------------------------")

    record = run_adaptive_experiment(
        base_constitution_path=base_constitution_path,
        adaptation_dir=adaptation_dir,
        dev_dir=dev_dir,
        output_summary_path=summary_path,
        output_provenance_path=provenance_path,
        dry_run=True,
    )

    print(f"\n[SUCCESS] Adaptation pipeline complete!")
    print(f"Base Version   : v{record.base_version}")
    print(f"Target Version : v{record.target_version}")
    print(f"Approval       : {record.approval_status}")
    print(f"New Principles : {len(record.candidate_principles)}")
    print(f"Results saved to {summary_path.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    main()
