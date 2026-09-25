# Research Protocol (master-prompt transformation)

## Questions: RQ1–RQ7 (see FINAL_STATUS.md for answers)

## Splits and allowed uses

| Dataset | Split | Use | Guard |
|---|---|---|---|
| benchmark dev (120) | dev | calibration, DEV-only fusion | convention |
| benchmark adaptation (105) | adaptation | adaptive-loop input only | `validate_split_isolation` + `guard_training_path` |
| benchmark test (105) | test | final eval only | both guards + tests |
| dpo train (46) / dev (13) | train/dev | train split trains; dev evaluates | `training/dpo_lm/dataset.py` + split tests |
| unlearning forget (24) / retain (24) / general (24) | forget/retain/general | forget drives removal; retain/general anchor + evaluate | disjointness test |
| redteam | dev/final | offline matrix + committed live game | fixed budget |

Manifest: `research/data_manifest.json` (hashes, counts, usage).

## Honesty rules (binding)

- No fabricated metrics/checkpoints/approvals/GPU runs.
- "Full DPO" only if a policy model was gradient-updated (satisfied: 102,714-param causal LM, policy hash changed, reference frozen).
- Unlearning success requires retention (conjunctive criterion — our LM result is PARTIAL, logistic baseline is COLLATERAL DAMAGE).
- Detector recall ≠ downstream prevention (ASR measured separately with canaries).
- Negative results kept. Denominators always. McNemar only with paired data (NOT RUN here).
- All approvals SIMULATED unless an authenticated workflow exists (none does).
