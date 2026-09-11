"""
experiments/attacker_defender/run_attacker_defender_game.py

Phase 9 executable runner: Attacker-Defender Red-Teaming Game.

Evaluation mode: DETERMINISTIC OFFLINE SIMULATION
  Both game runs use deterministic baselines (no API calls required).
  Baseline A (rule_only) and Baseline I (embedding) are both offline-reproducible.

Seed attacks come from the dev/ and adaptation/ splits.
Results are saved to results/attacker_defender_summary/.

Two games are run:
  Game 1 — Baseline A (rule-only): Demonstrates mutation effectiveness against regex.
  Game 2 — Baseline I (embedding): Evaluates mutations against the semantic classifier.
  Comparing the two games shows whether learned mutation patterns generalize
  across detection architectures.
"""
import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from research.schemas import BaselineConfig
from research.attacker_defender import run_attacker_defender_game


def _print_game_result(record, label: str) -> None:
    print(f"\n  [{label}]")
    print(f"    Game ID              : {record.game_id}")
    print(f"    Seed attacks         : {record.seed_attack_count}")
    print(f"    Final bypass rate    : {record.final_detector_bypass_rate:.1%}")
    print(f"    Trend                : {record.trend_notes}")


def main():
    seed_dirs = [
        ROOT_DIR / "data" / "benchmark" / "dev",
        ROOT_DIR / "data" / "benchmark" / "adaptation",
    ]
    output_dir = ROOT_DIR / "results" / "attacker_defender_summary"

    print("=" * 72)
    print("   AURA SHIELD — PHASE 9: ATTACKER-DEFENDER GAME                  ")
    print("=" * 72)
    print()
    print("Evaluation mode: [OFFLINE] DETERMINISTIC OFFLINE SIMULATION")
    print("  Both baselines run without external API calls.")
    for d in seed_dirs:
        print(f"  Seed dir : {d}")
    print(f"  Output   : {output_dir}")
    print(f"  Rounds   : 3 per game")
    print("-" * 72)

    # -----------------------------------------------------------------------
    # Game 1: Baseline A (rule_only) — deterministic regex detector
    # -----------------------------------------------------------------------
    print("\n[GAME 1/2] Baseline A: Rule-Only Regex Detector")
    print("  Purpose: Establishes how quickly known mutations bypass regex rules.")
    print("  Evaluation mode: [OFFLINE] deterministic — no API calls")

    record_a = run_attacker_defender_game(
        seed_dirs=seed_dirs,
        output_dir=output_dir,
        n_rounds=3,
        max_seed_attacks=40,
        baseline=BaselineConfig.A_RULE_ONLY,
        random_seed=42,
    )
    _print_game_result(record_a, "Baseline A results")

    # -----------------------------------------------------------------------
    # Game 2: Baseline I (embedding) — TF-IDF vector similarity detector
    # -----------------------------------------------------------------------
    print("\n[GAME 2/2] Baseline I: TF-IDF Embedding Classifier")
    print("  Purpose: Tests whether mutations that bypass regex also bypass")
    print("           the semantic embedding classifier.")
    print("  Evaluation mode: [OFFLINE] deterministic — no API calls")

    record_i = run_attacker_defender_game(
        seed_dirs=seed_dirs,
        output_dir=output_dir,
        n_rounds=3,
        max_seed_attacks=40,
        baseline=BaselineConfig.I_EMBEDDING,
        random_seed=42,
    )
    _print_game_result(record_i, "Baseline I results")

    # -----------------------------------------------------------------------
    # Comparison summary
    # -----------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("  COMPARISON: Mutation effectiveness across detection architectures")
    print("=" * 72)
    print(f"  Baseline A (rule_only)   bypass rate: {record_a.final_detector_bypass_rate:.1%}")
    print(f"  Baseline I (embedding)   bypass rate: {record_i.final_detector_bypass_rate:.1%}")

    if record_i.final_detector_bypass_rate < record_a.final_detector_bypass_rate:
        diff = record_a.final_detector_bypass_rate - record_i.final_detector_bypass_rate
        print(f"  -> Embedding classifier resists {diff:.1%} more mutations than rule_only.")
        print(f"     This suggests semantic similarity provides partial robustness")
        print(f"     against surface-level mutation strategies.")
    else:
        diff = record_i.final_detector_bypass_rate - record_a.final_detector_bypass_rate
        print(f"  -> Mutations generalize across both architectures (+{diff:.1%} for embedding).")
        print(f"     Deeper semantic evasion may be occurring.")

    print()
    print("  IMPORTANT: bypass rate != ASR. See results/attacker_defender_summary/game_summary.md")
    print(f"  Results saved to: {output_dir.relative_to(ROOT_DIR)}")

    # Save comparison summary
    comparison_path = output_dir / "game_comparison.json"
    comparison_path.write_text(
        json.dumps(
            {
                "evaluation_mode": "deterministic_offline_simulation",
                "game_1_baseline_a": {
                    "game_id": record_a.game_id,
                    "baseline": "A_RULE_ONLY",
                    "seed_attacks": record_a.seed_attack_count,
                    "final_bypass_rate": round(record_a.final_detector_bypass_rate, 4),
                    "trend": record_a.trend_notes,
                },
                "game_2_baseline_i": {
                    "game_id": record_i.game_id,
                    "baseline": "I_EMBEDDING",
                    "seed_attacks": record_i.seed_attack_count,
                    "final_bypass_rate": round(record_i.final_detector_bypass_rate, 4),
                    "trend": record_i.trend_notes,
                },
                "interpretation": (
                    "A higher bypass rate against Baseline I than A suggests mutations "
                    "that generalize beyond lexical patterns. A lower rate suggests the "
                    "semantic classifier provides partial robustness against the tested "
                    "mutation strategies."
                ),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"  Comparison saved to: {comparison_path.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    main()
