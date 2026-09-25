"""research/statistics.py — Wilson + bootstrap CIs, McNemar, denominators-always."""
from __future__ import annotations

import math
import random


def wilson(x: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = x / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (round(max(0.0, (c - m) / d), 4), round(min(1.0, (c + m) / d), 4))


def bootstrap_ci(hits: list[int], n_boot: int = 5000, seed: int = 7) -> tuple[float, float]:
    """hits: 0/1 outcomes. Returns 95% percentile CI of the mean."""
    rng = random.Random(seed)
    n = len(hits)
    if n == 0:
        return (0.0, 0.0)
    means = sorted(sum(rng.choice(hits) for _ in range(n)) / n for _ in range(n_boot))
    return (round(means[int(0.025 * n_boot)], 4), round(means[int(0.975 * n_boot) - 1], 4))


def mcnemar(b: int, c: int) -> dict:
    """Paired binary comparison from discordant counts (b: A-right/B-wrong, c: reverse).

    Requires per-example paired predictions. If those were never stored,
    callers must report McNemar as NOT RUN instead of inventing b/c.
    """
    n = b + c
    if n == 0:
        return {"statistic": 0.0, "p_value": 1.0, "n_discordant": 0}
    stat = (abs(b - c) - 1) ** 2 / n  # continuity-corrected chi2, 1 df
    # chi2(1) survival function approximation
    p = math.erfc(math.sqrt(stat / 2))
    return {"statistic": round(stat, 4), "p_value": round(p, 4), "n_discordant": n}


def rate_str(x: int, n: int) -> str:
    if n == 0:
        return "n/a (n=0)"
    lo, hi = wilson(x, n)
    return f"{x}/{n}={x/n:.1%} (95% CI {lo:.1%}-{hi:.1%})"
