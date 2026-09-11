"""
experiments/attacker_defender/run_attacker_defender_game.py

Phase 9 executable runner: Attacker-Defender Red-Teaming Game.

Seed attacks come from the dev/ and adaptation/ splits.
Results are saved to results/attacker_defender_summary/.
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from research.schemas import BaselineConfig
from research.attacker_defender import run_attacker_defender_game


def main():
    seed_dirs = [
        ROOT_DIR / "data" / "benchmark" / "dev",
        ROOT_DIR / "data" / "benchmark" / "adaptation",
    ]
    output_dir = ROOT_DIR / "results" / "attacker_defender_summary"

    print("=" * 72)
    print("   AURA SHIELD — PHASE 9: ATTACKER-DEFENDER GAME                  ")
    print("=" * 72)
    for d in seed_dirs:
        print(f"  Seed dir : {d}")
    print(f"  Output   : {output_dir}")
    print(f"  Rounds   : 3")
    print(f"  Baseline : rule_only (deterministic, no network calls)")
    print("-" * 72)

    record = run_attacker_defender_game(
        seed_dirs=seed_dirs,
        output_dir=output_dir,
        n_rounds=3,
        max_seed_attacks=40,
        baseline=BaselineConfig.A_RULE_ONLY,
        random_seed=42,
    )

    print(f"\n[SUCCESS] Game complete — {record.total_rounds} rounds played.")
    print(f"  Game ID              : {record.game_id}")
    print(f"  Seed attacks         : {record.seed_attack_count}")
    print(f"  Final bypass rate    : {record.final_detector_bypass_rate:.1%}")
    print(f"  Trend                : {record.trend_notes}")
    print()
    print("  IMPORTANT: bypass rate != ASR. See results/attacker_defender_summary/game_summary.md")
    print(f"  Results saved to: {output_dir.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    main()
