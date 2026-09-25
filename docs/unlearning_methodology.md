# Unlearning Methodology — SUPERSEDED by LM sweep (see `research/UNLEARNING_REPORT.md`)

This page documents the FIRST-sprint logistic pattern experiment (target 1.00→0.00 with general
collapse 0.27→0.01). It is kept as the NEGATIVE BASELINE (COLLATERAL DAMAGE), not as a method claim.

Current status: LM-level sweep has since RUN on tiny-gpt2 (forget/retain/general + λ∈{0.1,0.5,1.0}):
PARTIAL at λ=0.1/1.0 (4/24 suppressed — one template family only — retain/general preserved),
NOT VALIDATED at λ=0.5. Historical logistic text below is the baseline record.

## Defined forgetting target

`P("EXECUTE_UNSAFE_PAYLOAD" | prompt contains CRIMSON-<code> trigger)` —
a controlled synthetic behavior implanted by supervised training (60 steps,
lr 1.0) on 24 forget prompts (`training/unlearning/forget_dataset.py`).
Retain set: 24 benign cybersecurity QA (`retain_dataset.py`). Prompt sets are
provably disjoint (tested). This is pattern suppression, NOT knowledge erasure.

## Method

Negative-gradient forgetting with retention regularization (CPU logistic
policy, n=256 features, seed 11):
minimize_w [ −BCE(forget→unsafe) + 1.0·BCE(retain→safe) ], lr 2.0, 200 steps.
Config: `training/unlearning/config.yaml`. Artifact: `unlearn_adapter.pt`.

## Evaluation (both sides + general probe)

- Target unsafe rate: 1.00 → 0.00 ✓
- Retain unsafe rate: 0.00 → 0.00 ✓
- General unrelated probe (24 items): mean score 0.27 → 0.01 ✗ DEGRADED

The general degradation is reported as a legitimate negative result: ascent
suppressed overall activation scale, not just the trigger direction. A
selective method (sparse/adapter-scoped updates) is future work.

## What is NOT claimed

No LLM weights were modified (full LLM unlearning = NOT RUN). Nothing here
demonstrates real-world forgetting, catastrophic or otherwise.
