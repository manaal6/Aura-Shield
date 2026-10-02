# DPO Negative-Result Dissection (paper-shaped asset)

Observation (3 configs): DPO loss falls (0.68→0.20 tiny; 0.69→0.39 Qwen; →0.0000 hotter),
policy hash changes, reference frozen — yet absolute preference rankings freeze
(train 10/133→20/133 moves slightly; dev 2/29 and unseen 1/30 EXACTLY frozen throughout).

## H1 — KL constraint dominates (reference anchoring)

Claim: with β=0.5, the penalty for leaving the reference exceeds the preference gradient,
so margins move relative-to-reference (loss falls) without flipping absolute rankings.
Predicts: lower β or longer training flips rankings. Hotter run (4× pressure) partially
supports: train moved 7→20/133 but dev/unseen still frozen — consistent with anchoring
binding hardest out-of-distribution.

## H2 — Pair subtlety (chosen/rejected too close in model space)

Claim: secure+useful chosen vs unsafe rejected differ in ways a 0.1–0.5B model cannot
represent (long, lexically overlapping responses); the reward signal is near-orthogonal
to the model's features. Predicts: shorter, starker pairs (or larger model) flip rankings.
Evidence for: base models rank rejected HIGHER almost everywhere (dev 0/29 Qwen) —
the starting point is far from the decision boundary.

## H3 — Capacity floor (ranking needs representational room)

Claim: flipping 133 pairwise rankings needs more parameters than margin-shifting;
100K–0.5B models saturate on loss without reordering. Predicts: same protocol at 7B+
moves dev/unseen. Untested (needs GPU grant) — stated, not implied.

## Distinguishing experiments (ordered cheapest-first)

1. β sweep {0.1, 0.5, 1.0} on tiny-gpt2 CPU (~10 min): H1 predicts flips at low β.
2. Starker-pairs ablation: 30 hand-sharpened pairs; H2 predicts movement where 133 subtle pairs stall.
3. Margin-vs-rank curve per checkpoint: H1 predicts margins grow while rank stays 0 until a threshold.
4. 7B replication on Kaggle/GPU grant: H3's critical test.

Status: H1+H2 consistent with all data; H3 untested. None of this upgrades the headline:
DPO did not change preferences at any tested scale/intensity.
