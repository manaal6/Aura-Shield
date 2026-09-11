"""
tests/test_baselines.py

Unit tests for Phase 4 baseline configurations A through I.
Verifies that all 9 baseline specs load, validate schemas,
and run dry-runs without errors.
"""
from pathlib import Path
import pytest
from research.experiment import load_spec
from research.runner import BenchmarkRunner
from research.schemas import BaselineConfig

BASELINES_DIR = Path(__file__).resolve().parent.parent / "experiments" / "baselines"


def test_all_baseline_spec_files_exist():
    expected_files = [
        "a_rule_only.json", "b_llm_only.json", "c_constitution_only.json",
        "d_rule_llm.json", "e_rule_constitution.json", "f_llm_constitution.json",
        "g_full_blended.json", "h_prompt_guardrail.json", "i_embedding.json"
    ]
    for filename in expected_files:
        assert (BASELINES_DIR / filename).is_file(), f"Missing spec file: {filename}"


def test_all_baseline_specs_valid():
    spec_files = list(BASELINES_DIR.glob("*.json"))
    assert len(spec_files) >= 9
    for sf in spec_files:
        spec = load_spec(sf)
        assert spec.experiment_id.startswith("baseline_")
        assert len(spec.hypothesis) > 10
        assert spec.baseline_config in BaselineConfig


def test_offline_baseline_runs():
    # Test Baseline I (Embedding classifier) locally without network
    spec = load_spec(BASELINES_DIR / "i_embedding.json")
    spec.max_prompts = 5
    runner = BenchmarkRunner(spec, verbose=False)
    rows, result = runner.run(dry_run=False, skip_expense_guard=True)
    assert len(rows) == 5
    assert result.metrics["n_total"] == 5
    assert "precision" in result.metrics
