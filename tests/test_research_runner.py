"""
tests/test_research_runner.py

Unit tests for research/runner.py and research/experiment.py.
"""
import pytest
from research.experiment import (
    assert_split_not_contaminated,
    check_expense_guard,
    estimate_run_cost,
)
from research.runner import (
    load_dataset_jsonl,
    BenchmarkRunner,
)
from research.schemas import (
    BaselineConfig,
    DatasetSplit,
    ExperimentSpec,
    ModelRoles,
)


def test_cost_estimation():
    est = estimate_run_cost(
        n_prompts=20,
        baseline_config=BaselineConfig.G_FULL_BLENDED,
    )
    assert est["n_prompts"] == 20
    assert est["llm_calls_total"] > 0
    assert est["expensive"] is False


def test_cost_estimation_expensive():
    est = estimate_run_cost(
        n_prompts=100,
        baseline_config=BaselineConfig.G_FULL_BLENDED,
    )
    assert est["expensive"] is True


def test_check_expense_guard_raises():
    est = {"expensive": True, "llm_calls_total": 250, "n_prompts": 100, "message": "High cost"}
    with pytest.raises(RuntimeError):
        check_expense_guard(est)


def test_split_contamination_guard():
    # Adaptive loop mode must reject test/ paths
    with pytest.raises(ValueError, match="CONTAMINATION GUARD TRIGGERED"):
        assert_split_not_contaminated(
            ["data/benchmark/test/multi_turn_manipulation.jsonl"],
            adaptive_loop_mode=True,
        )

    # Allowed in non-adaptive mode
    assert_split_not_contaminated(
        ["data/benchmark/test/multi_turn_manipulation.jsonl"],
        adaptive_loop_mode=False,
    )


def test_load_legacy_benchmark_json():
    dataset = load_dataset_jsonl("evaluation/benchmark_dataset.json")
    assert len(dataset) == 40
    assert "user_prompt" in dataset[0]


def test_dry_run_runner():
    spec = ExperimentSpec(
        experiment_id="dry-run-01",
        experiment_name="Dry Run Test",
        hypothesis="Dry run should load data and complete without invoking API calls.",
        independent_variables=["mode"],
        dependent_variables=["execution"],
        control_baseline=BaselineConfig.A_RULE_ONLY,
        dataset_split=DatasetSplit.DEV,
        dataset_files=["evaluation/benchmark_dataset.json"],
        max_prompts=2,
    )
    runner = BenchmarkRunner(spec, verbose=False)
    results, summary = runner.run(dry_run=True)
    assert results == []
    assert summary.what_this_demonstrates.startswith("Dry run")
