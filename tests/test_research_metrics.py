"""
tests/test_research_metrics.py

Unit tests for research/metrics.py.
"""
import pytest
from research.metrics import (
    ablation_summary,
    compute_metrics,
    confusion_matrix,
    per_family_breakdown,
    wilson_ci,
)


def test_compute_metrics_perfect_scores():
    data = [
        {"ground_truth_label": "attack", "flagged_by_shield": True, "attack_succeeded": False},
        {"ground_truth_label": "attack", "flagged_by_shield": True, "attack_succeeded": False},
        {"ground_truth_label": "benign", "flagged_by_shield": False, "attack_succeeded": None},
        {"ground_truth_label": "benign", "flagged_by_shield": False, "attack_succeeded": None},
    ]
    m = compute_metrics(data)
    assert m["true_positives"] == 2
    assert m["false_negatives"] == 0
    assert m["false_positives"] == 0
    assert m["true_negatives"] == 2
    assert m["precision"] == 1.0
    assert m["recall"] == 1.0
    assert m["fpr"] == 0.0
    assert m["f1"] == 1.0
    assert m["asr"] == 0.0
    assert m["real_asr_evaluated"] is True


def test_compute_metrics_unevaluated_asr():
    # When attack_succeeded is None, real_asr_evaluated should be False and asr None
    data = [
        {"ground_truth_label": "attack", "flagged_by_shield": False, "attack_succeeded": None},
        {"ground_truth_label": "benign", "flagged_by_shield": False, "attack_succeeded": None},
    ]
    m = compute_metrics(data)
    assert m["real_asr_evaluated"] is False
    assert m["asr"] is None
    assert any("ASR could not be computed" in note for note in m["notes"])


def test_wilson_ci_bounds():
    lo, hi = wilson_ci(50, 100)
    assert 0.0 <= lo <= hi <= 1.0
    assert pytest.approx(0.5, abs=0.1) == (lo + hi) / 2


def test_per_family_breakdown():
    data = [
        {"ground_truth_label": "attack", "flagged_by_shield": True, "attack_family": "direct_injection", "attack_succeeded": None},
        {"ground_truth_label": "attack", "flagged_by_shield": False, "attack_family": "jailbreak_encoding", "attack_succeeded": None},
        {"ground_truth_label": "benign", "flagged_by_shield": False, "attack_family": "benign_general", "attack_succeeded": None},
    ]
    breakdown = per_family_breakdown(data)
    assert "direct_injection" in breakdown
    assert "jailbreak_encoding" in breakdown
    assert "benign_general" in breakdown
    assert breakdown["direct_injection"]["recall"] == 1.0
    assert breakdown["jailbreak_encoding"]["recall"] == 0.0


def test_ablation_summary():
    data = [
        {
            "ground_truth_label": "attack",
            "flagged_by_shield": True,
            "rule_signal": 0.8,
            "llm_signal": 0.2,
            "constitution_signal": 0.0,
        },
        {
            "ground_truth_label": "benign",
            "flagged_by_shield": False,
            "rule_signal": 0.0,
            "llm_signal": 0.1,
            "constitution_signal": 0.0,
        },
    ]
    ablation = ablation_summary(data, block_threshold=0.75)
    assert ablation["rule_only"]["attacks_caught"] == 1
    assert ablation["llm_only"]["attacks_caught"] == 0
    assert ablation["blended"]["attacks_caught"] == 1
