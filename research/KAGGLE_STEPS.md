# Kaggle Step-by-Step (DPO + Unlearning on free T4 GPUs)

Goal: rerun `research/kaggle_run.py` on Qwen2.5-0.5B (or TinyLlama-1.1B) and paste back 4 JSONs.
Time: ~30–60 min hands-on; GPU run itself ~20–40 min. No API keys needed (training is local).

## Step 1 — Account + quota check (2 min)

1. Go to kaggle.com → sign in (Google account works).
2. Verify phone number (required for GPU quota): profile photo → Settings → Phone verification.
3. Free quota: ~30 GPU-hours/week on 2× T4. Check: profile → Settings → usage.

## Step 2 — Create the notebook (2 min)

1. Click **Create** (top right) → **New Notebook**.
2. Right panel → **Session options**: Accelerator = **GPU T4 x2**, Internet = **ON** (needed to download the model), Persistence = **save output**.
3. Language: Python (default). Environment: latest.

## Step 3 — Upload the 5 files (3 min)

In the right panel → **Add data** → **Upload** (or drag into the file explorer):
- `research/kaggle_run.py` (from this repo)
- `data/dpo_preferences.jsonl`
- `data/dpo_generalization.jsonl`
- `data/unlearning_forget.jsonl`
- `data/unlearning_retain.jsonl`
- `data/unlearning_general.jsonl`

(That is 6 files: 1 script + 5 data. Put them in `/kaggle/input/aura/` or the working dir —
adjust `--data` below to match.)

## Step 4 — Run (1 min to start, then wait)

New **Code** cell, paste and run:

```bash
!nvidia-smi --query-gpu=name,memory.total --format=csv  # confirm 2x T4
!python kaggle_run.py --model Qwen/Qwen2.5-0.5B --data /kaggle/input/aura --out kaust_results
```

What happens: DPO (~133 pairs, 2 epochs) → unlearning implant + λ∈{0.1,0.5,1.0} sweep →
4 JSONs printed. If VRAM overflows, retry with `--model TinyLlama/TinyLlama-1.1B`
(smaller) — and report which model actually ran.

Watch for: session limit is 12 h max (this run needs <1 h); keep the tab open;
checkpoints save to `kaust_results/` as it goes, so an interruption keeps partial work.

## Step 5 — Copy the outputs (2 min)

At the end the script prints `DPO_RECORD` and `UNLEARNING_RECORD` JSON blocks.
- Click the output → copy both full blocks into a text file.
- Also download `kaust_results/` (right panel → output → download) as backup.

## Step 6 — Paste back here

Paste the two JSON blocks into chat (or as a file). I will:
1. Save them as `*-qwen05.json` next to the tiny-gpt2 artifacts (no overwrites),
2. Update `DPO_REPORT.md` / `UNLEARNING_REPORT.md` with the scale comparison,
3. Report honestly whichever way it goes (generalization / no-generalization are both findings).

## If something fails

| Symptom | Fix |
|---|---|
| `No GPU` | Session options → Accelerator T4 x2 (Step 2); re-run |
| Model download 403/slow | Internet must be ON; retry (HF rate limits pass) |
| CUDA out of memory | Smaller model (TinyLlama-1.1B), or add `--batch 1` equivalent (edit script lr/batch constants) |
| Session timed out | Re-run; checkpoints in `kaust_results/` persist per session output — download them first |
| Quota exhausted (0 GPU hours) | Wait for weekly reset; the CPU smoke test (`--selftest --model sshleifer/tiny-gpt2`) runs anywhere to validate plumbing |

Never paste any API keys into Kaggle — this run needs none.
