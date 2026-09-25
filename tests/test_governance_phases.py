"""tests/test_governance_phases.py — data governance + new-phase artifact tests."""
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))

from research.data_governance import (build_manifest, guard_split_value,  # noqa: E402
                                      guard_training_path)


def test_training_code_cannot_load_test():
    for bad in ("data/benchmark/test/tool_injection.jsonl",
                "E:/repo/data/benchmark/test/x.jsonl",
                "results/held-out/test.csv"):
        with pytest.raises(ValueError):
            guard_training_path(bad)


def test_training_code_can_load_dev_and_adaptation():
    guard_training_path(REPO / "data/benchmark/dev")
    guard_training_path(REPO / "data/benchmark/adaptation")
    guard_training_path(REPO / "data/dpo_preferences.jsonl")


def test_split_guards():
    guard_split_value({"split": "train"}, ("train",), context="t")
    with pytest.raises(ValueError):
        guard_split_value({"split": "dev"}, ("train",), context="t")
    with pytest.raises(ValueError):
        guard_split_value({"split": "test"}, ("train", "dev"), context="t")


def test_dpo_train_loader_excludes_dev_and_test():
    from training.dpo_lm.dataset import load_dev, load_train
    tr, dv = load_train(), load_dev()
    assert all(r["split"] == "train" for r in tr)
    assert all(r["split"] == "dev" for r in dv)
    assert not ({r["prompt"] for r in tr} & {r["prompt"] for r in dv})


def test_manifest_exists_and_covers_splits():
    m = json.loads((REPO / "research" / "data_manifest.json").read_text())
    splits = {d["split"] for d in m["datasets"]}
    for need in ("dev", "adaptation", "test", "train+dev", "forget", "retain", "general"):
        assert need in splits, f"manifest missing {need}"
    for d in m["datasets"]:
        assert d["samples"] > 0 and len(d["sha256_16"]) == 16


def test_new_phase_artifacts_present():
    base = REPO / "results" / "kaust_three_pillars"
    for rel in ("dpo_lm/dpo_lm_record.json", "dpo_lm/dpo_lm_eval.json",
                "unlearning_lm/unlearning_lm_record.json", "unlearning_lm/unlearning_lm_eval.json",
                "statistics/statistical_eval.json", "fusion/fusion_report_data.json",
                "fusion/fusion_per_example_dev.json", "benign/benign_eval.json",
                "indirect/indirect_eval.json", "asr/canary_asr.json",
                "latency/latency.json", "redteam/redteam_matrix.json",
                "multiturn/multiturn_eval.json", "adaptive/drift_v1_v2.json"):
        assert (base / rel).exists(), f"missing {rel}"


def test_dpo_invariant_policy_changed_ref_frozen():
    rec = json.loads((REPO / "results" / "kaust_three_pillars" / "dpo_lm" / "dpo_lm_record.json").read_text())
    assert rec["policy_changed"] is True and rec["reference_changed"] is False


def test_unlearning_verdicts_honest():
    ev = json.loads((REPO / "results" / "kaust_three_pillars" / "unlearning_lm" / "unlearning_lm_eval.json").read_text())
    assert ev["per_lambda"]["0.5"]["verdict"].startswith("NOT VALIDATED")
    assert "PARTIAL" in ev["per_lambda"]["0.1"]["verdict"]


def test_asr_separates_bypass_from_success():
    rep = json.loads((REPO / "results" / "kaust_three_pillars" / "asr" / "canary_asr.json").read_text())
    assert rep["bypassed"] >= 0 and rep["downstream_evaluated"] <= rep["bypassed"]
    assert "CANARY" in rep["canary"]
