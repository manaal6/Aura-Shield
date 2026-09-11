"""
tests/test_soc_workflow.py

Unit tests for Phase 6 Cybersecurity Operations (SOC Analyst) Assistant evaluation.
"""
from pathlib import Path
import pytest
from research.experiment import load_spec
from research.runner import BenchmarkRunner

SOC_DIR = Path(__file__).resolve().parent.parent / "experiments" / "soc_workflow"


def test_soc_spec_exists_and_valid():
    spec_path = SOC_DIR / "soc_log_analysis_eval.json"
    assert spec_path.is_file(), "Missing SOC experiment specification"

    spec = load_spec(spec_path)
    assert spec.experiment_id == "soc_log_analysis_eval"
    assert len(spec.dataset_files) == 4
    assert len(spec.hypothesis) > 10


def test_soc_dry_run_execution():
    spec_path = SOC_DIR / "soc_log_analysis_eval.json"
    spec = load_spec(spec_path)
    spec.max_prompts = 5

    runner = BenchmarkRunner(spec, verbose=False)
    rows, result = runner.run(dry_run=True)
    assert rows == []
    assert result.experiment_id == "soc_log_analysis_eval"
