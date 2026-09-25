# Reproducibility

## Layout map (required → actual)

- experiments/dpo → `training/dpo_lm/` (train/evaluate/config) + `experiments/kaust_three_pillars/run_dpo.py`
- experiments/unlearning → `training/unlearning_lm/` + `run_unlearning.py`
- experiments/fusion → `research/fusion_analysis.py`, `research/make_fusion_report.py`, `run_integrated_eval.py`
- experiments/redteam → `research/adaptive_redteam.py`, `redteam_matrix.py`, `multiturn_eval.py`, `indirect_eval.py`, `canary_asr.py`, `benign_eval.py`
- experiments/evaluation → `research/statistical_eval.py`, `latency.py`, `drift.py`
- configs → `training/dpo_lm/config.yaml`, `training/unlearning_lm/config.yaml`, `training/dpo/config.yaml`, `app/config.py`
- results → `results/kaust_three_pillars/` (+ committed `results/baselines_summary/` etc.)
- research → `research/*.md` reports + `data_manifest.json`

## Exact commands

```bash
pip install -r requirements.txt          # + torch, transformers, huggingface_hub (CPU)
python -m pytest tests/ -q              # 178 tests, offline (live-API scripts excluded: canary_asr, fusion_forensics)
python -m training.dpo.expand_dataset   # idempotent; 29 -> 59 pairs (v1)
python -m training.dpo.expand_dataset_v3  # 59 -> 102 (IDs, rationale, threat types; archives v1)
python -m training.dpo.expand_dataset_v4  # 102 -> 150
python -m training.dpo.expand_dataset_v5  # 150 -> 162 + 30-item eval-only generalization set
python -m training.dpo_lm.train         # ~2 min CPU; writes checkpoint + record
python -m training.dpo_lm.evaluate
python -m training.unlearning_lm.train  # ~6 min CPU; implant + 3-lambda sweep
python -m training.unlearning_lm.evaluate
python -m research.statistical_eval
python -m research.make_fusion_report
python -m research.benign_eval
python -m research.indirect_eval
python -m research.canary_asr          # needs GROQ_API_KEY for live downstream; else NOT RUN rows
python -m research.redteam_matrix
python -m research.multiturn_eval
python -m research.drift
python -m research.latency
python -m research.toolsec_demo
python -m experiments.kaust_three_pillars.run_all
streamlit run dashboard/streamlit_app.py  # Research Lab tab reads results/ artifacts only
```

## Seeds / versions / hardware

DPO seed 7; unlearning seed 11; stats seed 7. Model sshleifer/tiny-gpt2 (102,714 params).
torch 2.13.0+cpu, transformers 5.14.1, CPU AMD64. Dataset/dataset-split hashes in
`research/data_manifest.json`; checkpoint hashes in run records.
