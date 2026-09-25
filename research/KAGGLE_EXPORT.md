# Kaggle Export — DPO + Unlearning on 2×T4 (self-contained)

## What to upload

1. This notebook (`kaggle_dpo_unlearning.ipynb`, created from the cells below), OR
2. Files: `training/dpo_lm/` + `training/unlearning_lm/` + `data/dpo_preferences.jsonl`
   + `data/unlearning_*.jsonl` (export via `git archive` or the dashboard Reproducibility tab).

## Notebook cells (paste into Kaggle, GPU T4 x2, internet ON for model download)

Cell 1 — setup:
```python
!pip install -q transformers torch --upgrade
import torch
print(torch.cuda.is_available(), torch.cuda.device_count())
```

Cell 2 — DPO (scaled): copy `training/dpo_lm/train.py` + `dataset.py`, point `model:` at
`Qwen/Qwen2.5-0.5B` (or `TinyLlama/TinyLlama-1.1B` if VRAM allows), beta 0.1–0.5, lr 5e-6,
epochs 1–3, batch 2–4 with gradient accumulation 4. Then run `training/dpo_lm/evaluate.py`
unchanged (it reads the checkpoint + dev + 30-item generalization set).

Cell 3 — Unlearning (scaled): copy `training/unlearning_lm/` as-is; only the `model:` in
`config.yaml` changes to the same larger model. Implant → λ∈{0.1,0.5,1.0} sweep → `evaluate.py`.

Cell 4 — export results:
```python
import json, glob
for f in ["results/kaust_three_pillars/dpo_lm/dpo_lm_record.json",
          "results/kaust_three_pillars/dpo_lm/dpo_lm_eval.json",
          "results/kaust_three_pillars/unlearning_lm/unlearning_lm_record.json",
          "results/kaust_three_pillars/unlearning_lm/unlearning_lm_eval.json"]:
    print("=" * 20, f)
    print(open(f).read()[:1500])
```

## What to paste back here

The four JSON outputs above. Integration: drop `dpo_lm_record.json` / `dpo_lm_eval.json`
(and unlearning equivalents) next to the tiny-gpt2 artifacts with a `-qwen05` suffix —
reports compare scales without overwriting the CPU baseline.

## Expected honest outcomes (either is publishable)

- DPO: dev ranking moves (generalization!) or stays frozen (capacity/architecture finding).
- Unlearning: suppression generalizes across templates or stays template-specific (RQ4 bound).
- Report loss AND ranking AND retain/general AND the negative if that is what happens.
