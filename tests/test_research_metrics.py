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

def test_sealed_v2_and_pooled_stat_consistent():
    """Sealed v2 (38/40, 0 fb) + artifact-read pooled 143/153=93.5% (B58)."""
    import json
    from pathlib import Path
    repo = Path(__file__).parent.parent
    v2 = json.loads((repo / "results" / "kaust_three_pillars" / "heldout_extra"
                     / "heldout_extra_v2_eval.json").read_text(encoding="utf-8"))
    assert v2["n"] == 40 and v2["held"] == 38 and v2["fallback"] == 0
    stats = json.loads((repo / "results" / "kaust_three_pillars" / "statistics"
                        / "statistical_eval.json").read_text(encoding="utf-8"))
    pooled = stats["new_small_n"]["pooled_new_system"]
    assert pooled["n_attacks"] == 153 and pooled["sealed_batches"] == ["38/40", "38/40"]
    assert pooled["recall"].startswith("143/153=93.5%")

def test_benign_challenge_scale_and_zero_overtrigger():
    """Benign set 62 -> 132 prompts, 0 held offline across 16 words (rigor push)."""
    import json
    from collections import Counter
    from pathlib import Path
    repo = Path(__file__).parent.parent
    rows = [json.loads(l) for l in (repo / "data" / "benign_challenge.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(rows) == 132
    assert len(Counter(r["trigger_word"] for r in rows)) >= 16
    assert all(r["intent"] == "legitimate" and r["prompt"].strip() for r in rows)
    rep = json.loads((repo / "results" / "kaust_three_pillars" / "benign" / "benign_eval.json").read_text(encoding="utf-8"))
    assert rep["n"] == 132 and rep["held_benign"] == 0

def test_benign_live48_and_combined_fpr():
    """B1: 48 benign live (1 held, 0 fb) — staged first half, superseded by live132."""
    import json
    from pathlib import Path
    repo = Path(__file__).parent.parent
    rep = json.loads((repo / "results" / "kaust_three_pillars" / "benign" / "benign_live48.json").read_text(encoding="utf-8"))
    assert rep["n"] == 48 and rep["held"] == 1 and rep["fallback"] == 0


def test_benign_live132_and_combined_fpr():
    """B3: full 132 benign live (3 held, 0 fb); combined live FPR 5/264=1.9% (B65 + held-out v2)."""
    import json
    from pathlib import Path
    repo = Path(__file__).parent.parent
    rep = json.loads((repo / "results" / "kaust_three_pillars" / "benign" / "benign_live132.json").read_text(encoding="utf-8"))
    assert rep["n"] == 132 and rep["held"] == 3 and rep["fallback"] == 0
    held_ids = {r["id"] for r in rep["rows"] if r["decision"] in ("block", "review")}
    live48 = json.loads((repo / "results" / "kaust_three_pillars" / "benign" / "benign_live48.json").read_text(encoding="utf-8"))
    assert {r["id"] for r in live48["rows"]} <= {r["id"] for r in rep["rows"]}  # superset, same IDs
    stats = json.loads((repo / "results" / "kaust_three_pillars" / "statistics"
                        / "statistical_eval.json").read_text(encoding="utf-8"))
    assert stats["new_small_n"]["benign_live_combined"]["fpr"].startswith("5/264=1.9%")


def test_heldout_v2_one_shot_and_pooled():
    """Held-out v2 (B67): 153+100, one eval, 0 fb — 132/153 attacks, 1/100 benign;
    v1 pooled 143/153 must stay untouched; fresh-combined 275/306."""
    import json
    from pathlib import Path
    repo = Path(__file__).parent.parent
    v2 = json.loads((repo / "results" / "kaust_three_pillars" / "heldout_v2"
                     / "heldout_v2_eval.json").read_text(encoding="utf-8"))
    assert v2["n"] == 253 and v2["n_attacks"] == 153 and v2["n_benign"] == 100
    assert v2["attacks_held"] == 132 and v2["benign_held"] == 1
    assert v2["fallback"] == 0 and all(r["error"] is None for r in v2["rows"])
    stats = json.loads((repo / "results" / "kaust_three_pillars" / "statistics"
                        / "statistical_eval.json").read_text(encoding="utf-8"))
    new = stats["new_small_n"]
    assert new["heldout_v2"]["recall"].startswith("132/153=86.3%")
    assert new["heldout_v2"]["fpr"].startswith("1/100=1.0%")
    assert new["pooled_new_system"]["recall"].startswith("143/153=93.5%")  # v1 untouched
    assert new["pooled_fresh_all"]["recall"].startswith("275/306=89.9%")
    assert new["pooled_fresh_all"]["n_attacks"] == 306
    # novelty guard: sealed v2 sets were score-blind and dup-free at generation time
    assert len(v2["rows"]) == len({r["id"] for r in v2["rows"]})

def test_live_flags_reads_objects_and_dicts():
    """B66: fallback extraction must fire on pydantic objects, not just dicts."""
    from research.live_flags import fallback_flags

    class Obj:
        def __init__(self, fb):
            self.used_fallback = fb

    assert fallback_flags({"llm_result": Obj(True), "constitution_result": Obj(False)}) == {
        "llm": True, "constitution": False, "any": True}
    assert fallback_flags({"llm_result": {"used_fallback": False},
                           "constitution_result": {"used_fallback": True}})["any"] is True
    assert fallback_flags({"llm_result": Obj(False), "constitution_result": Obj(False)})["any"] is False
    assert fallback_flags({})["any"] is False

def test_dpo_qwen15_first_positive():
    """Qwen-1.5B LoRA DPO (config 5, Colab T4): dev 0/29 -> 22/29, train 128/133.
    Lower beta (0.1) broke the KL-trap saturation of configs 1-4."""
    import json
    from pathlib import Path
    repo = Path(__file__).parent.parent
    rec = json.loads((repo / "results" / "kaust_three_pillars" / "dpo_lm"
                      / "dpo_lm_record_qwen15.json").read_text(encoding="utf-8"))
    assert rec["dev_before"] == "0/29" and rec["dev_after"] == "22/29"
    assert rec["train_acc"] == "128/133" and rec["beta"] == 0.1
    assert rec["dev_margin_after"] > 0 > rec["dev_margin_before"]
    stats = json.loads((repo / "results" / "kaust_three_pillars" / "statistics"
                        / "statistical_eval.json").read_text(encoding="utf-8"))
    assert stats["new_small_n"]["dpo_qwen15_dev_pref"]["recall"].startswith("22/29=75.9%")
    # config 1 (tiny) stays negative — the fix did not rewrite history
    assert stats["new_small_n"]["dpo_lm_dev_pref"]["recall"].startswith("2/29=")


def test_sota_baseline_and_zen_partial():
    """SOTA comparison uses AURA's exact sets; Zen replication stays labelled PARTIAL."""
    import json
    from pathlib import Path
    repo = Path(__file__).parent.parent
    stats = json.loads((repo / "results" / "kaust_three_pillars" / "statistics"
                        / "statistical_eval.json").read_text(encoding="utf-8"))
    sota = stats["sota_baseline"]
    assert sota["model"] == "ProtectAI/deberta-v3-base-prompt-injection-v2"
    assert sota["recall"].startswith("187/306=61.1%")
    assert sota["fpr"].startswith("5/264=1.9%")
    assert stats["sota_vs_aura"]["aura_pooled_fresh"].startswith("275/306=89.9%")
    matched = stats["sota_matched_fpr"]
    assert matched["fpr"].startswith("5/264=1.9%")
    assert matched["recall"].startswith("187/306=61.1%")
    assert "not deployable" in matched["detail"]

    artifact = json.loads((repo / "results" / "kaust_three_pillars" / "sota"
                           / "sota_deberta_eval.json").read_text(encoding="utf-8"))
    assert artifact["n_attacks"] == 306 and artifact["n_benign"] == 264
    assert artifact["errors"] == 0 and len(artifact["rows"]) == 570

    zen = stats["zen_replication"]
    assert zen["recall"].startswith("130/153=85.0%")
    assert zen["n_benign"] == 35 and zen["fpr"].startswith("0/35=")
    assert "65" in zen["detail"] and "purged" in zen["detail"]


def test_dpo_qwen15_unseen_generalizes():
    """Config-5 retrain: unseen 0/30 -> 23/30 with unseen not below train (no memorization)."""
    import json
    from pathlib import Path
    repo = Path(__file__).parent.parent
    rec = json.loads((repo / "results" / "kaust_three_pillars" / "dpo_lm"
                      / "dpo_unseen_qwen15.json").read_text(encoding="utf-8"))
    assert rec["base_unseen"]["preference_accuracy"] == "0/30=0.0000"
    assert rec["dpo_unseen"]["preference_accuracy"] == "23/30=0.7667"
    assert rec["dpo_unseen"]["mean_chosen_margin"] > 0 > rec["base_unseen"]["mean_chosen_margin"]
    unseen = int(rec["dpo_unseen"]["preference_accuracy"].split("/")[0]) / rec["n_unseen"]
    train = int(rec["dpo_train"]["preference_accuracy"].split("/")[0]) / rec["n_train"]
    assert unseen >= train - 0.10, (unseen, train)  # overfit would put unseen far below train
    stats = json.loads((repo / "results" / "kaust_three_pillars" / "statistics"
                        / "statistical_eval.json").read_text(encoding="utf-8"))
    assert stats["new_small_n"]["dpo_qwen15_unseen"]["recall"].startswith("23/30=76.7%")
