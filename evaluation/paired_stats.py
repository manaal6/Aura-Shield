"""
evaluation/paired_stats.py

Paired statistical significance testing (W#16).
Implements McNemar's test for paired binary classification (e.g. constitution-only vs. full blend),
along with bootstrap 95% confidence intervals for the recall difference.
Resolves the empirical gap where comparisons were suggestive but unmeasured.
"""
from __future__ import annotations

import math
import random
from typing import Sequence


def mcnemar_test(y_true: Sequence[int], y_pred_a: Sequence[int], y_pred_b: Sequence[int]) -> dict:
    """
    Computes McNemar's test on paired classification outcomes.
    y_true: binary ground truth (1 = attack, 0 = benign)
    y_pred_a: model A predictions (1 = flagged, 0 = missed)
    y_pred_b: model B predictions (1 = flagged, 0 = missed)
    """
    assert len(y_true) == len(y_pred_a) == len(y_pred_b), "Length mismatch"

    # Contingency table for attacks:
    # b: A correct, B wrong
    # c: A wrong, B correct
    b = 0
    c = 0
    n_attacks = 0

    for yt, ya, yb in zip(y_true, y_pred_a, y_pred_b):
        if yt == 1:
            n_attacks += 1
            correct_a = (ya == 1)
            correct_b = (yb == 1)
            if correct_a and not correct_b:
                b += 1
            elif not correct_a and correct_b:
                c += 1

    # McNemar's test with continuity correction: (|b - c| - 1)^2 / (b + c)
    total_discordant = b + c
    if total_discordant == 0:
        chi2 = 0.0
        p_val = 1.0
    else:
        chi2 = ((abs(b - c) - 1.0) ** 2) / total_discordant
        # Approximate p-value from chi-square distribution with 1 df using complementary error function
        p_val = math.erfc(math.sqrt(chi2) / math.sqrt(2))

    return {
        "n_attacks": n_attacks,
        "a_correct_b_wrong": b,
        "a_wrong_b_correct": c,
        "total_discordant": total_discordant,
        "chi2_statistic": round(chi2, 4),
        "p_value": round(p_val, 4),
        "statistically_significant_05": p_val < 0.05,
    }


def bootstrap_paired_difference(
    y_true: Sequence[int],
    y_pred_a: Sequence[int],
    y_pred_b: Sequence[int],
    n_bootstrap: int = 1000,
    seed: int = 42,
) -> dict:
    random.seed(seed)
    n = len(y_true)
    diffs = []

    for _ in range(n_bootstrap):
        indices = [random.randint(0, n - 1) for _ in range(n)]
        rec_a = sum(1 for i in indices if y_true[i] == 1 and y_pred_a[i] == 1)
        rec_b = sum(1 for i in indices if y_true[i] == 1 and y_pred_b[i] == 1)
        tot_atk = sum(1 for i in indices if y_true[i] == 1)
        if tot_atk > 0:
            diffs.append((rec_a - rec_b) / tot_atk)

    diffs.sort()
    ci_lower = diffs[int(0.025 * len(diffs))]
    ci_upper = diffs[int(0.975 * len(diffs))]

    return {
        "mean_recall_difference": round(sum(diffs) / len(diffs), 4),
        "ci_95_lower": round(ci_lower, 4),
        "ci_95_upper": round(ci_upper, 4),
        "ci_crosses_zero": ci_lower <= 0.0 <= ci_upper,
    }


if __name__ == "__main__":
    import json
    # Known measured numbers from inventory: 73 held-out attacks
    # Constitution: 68/73 (93.2%)
    # Blend: 65/73 (89.0%)
    # Discordant: 3 caught by constitution but missed by blend
    y_true = [1] * 73
    y_pred_const = [1] * 68 + [0] * 5
    y_pred_blend = [1] * 65 + [0] * 8

    res_mcnemar = mcnemar_test(y_true, y_pred_const, y_pred_blend)
    res_boot = bootstrap_paired_difference(y_true, y_pred_const, y_pred_blend)

    print("=== McNemar Test ===")
    print(json.dumps(res_mcnemar, indent=2))
    print("\n=== Bootstrap 95% Confidence Interval ===")
    print(json.dumps(res_boot, indent=2))
