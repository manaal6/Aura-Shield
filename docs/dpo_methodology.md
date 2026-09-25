# DPO Methodology — SUPERSEDED by genuine LM runs (see `research/DPO_REPORT.md`)

This page documents the FIRST-sprint logistic objective-PoC (29 pairs, loss 0.6931→0.6405,
dev 0.50→1.00 at n=8). It is kept as a mechanism demo, NOT as evidence.

Current status: FULL MODEL-LEVEL DPO has since RUN on sshleifer/tiny-gpt2 (102,714 params, CPU)
over 162 pairs (133 train / 29 dev + 30 unseen): loss 0.6824→0.1950 with policy-hash proof and
frozen reference — but dev ranking 2/29→2/29 and unseen 1/30→1/30 (NEGATIVE result, kept).
Toy scale; nothing transfers to LLM scale. Prior logistic text below is historical.

## Objective

Shift policy-following preference behavior via Direct Preference Optimization
(Rafailov et al. 2023) on controlled cybersecurity-assistant pairs.

## Dataset

`data/dpo_preferences.jsonl` — 29 hand-specified deterministic pairs
(prompt / chosen / rejected / attack_category / policy_principle / source /
split): 21 train, 8 dev. Six behavior families (command execution, payload
reproduction, config reveal, external authority, role hijack, audit tampering).
No held-out benchmark content. Hash `b7aecabe25325942`. Loader validates
schema, non-empty distinct chosen/rejected, split membership, train/dev prompt
disjointness, and rejects test-contaminated sources (`training/dpo/dataset.py`).

## Model & loss (smoke scope)

CPU logistic preference policy: reward `r_w = w·φ(prompt‖response)` with
hashed bigram features (n=512). Exact DPO loss with frozen reference `w_ref`:

L = −E log σ( β·[(r_w(ch)−r_ref(ch)) − (r_w(rej)−r_ref(rej))] ), β=0.5.

Config: `training/dpo/config.yaml` (seed 7, lr 0.05, 60 epochs, batch 8).
Artifact: `results/kaust_three_pillars/dpo/adapter.pt`.

## Evaluation (dev only)

Preference accuracy, compliant-preference rate, unsafe-preference rate,
mean chosen reward; deterministic judge. Result: 0.50→1.00 (n=8).
`training/dpo/evaluate.py` → `dpo_eval.json`.

## What is NOT claimed

No transformer was trained (CPU-only, no cached weights, no TRL/PEFT).
Full LLM-DPO = NOT RUN. The lift demonstrates pipeline correctness, not LLM
safety improvement. Do not cite as alignment evidence.
