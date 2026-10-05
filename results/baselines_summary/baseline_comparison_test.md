> [!NOTE]
> **SUPERSEDED (2026-10-05): a divergent per-run output — the committed held-out numbers are
> C 68/73 = 93.2%, G 65/73 = 89.0%, H 55/73 = 75.3% (`heldout_master_table.json`,
> `research/STATISTICAL_REPORT.md`). Kept as a run record; cite the committed table, not the rows below.

| Baseline | Name | Total | Precision | Recall | F1 | FPR | Real_LLM | Avg_Latency_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G_full_blended | Baseline G: Full Blended AURA Shield Gateway [Held-out test split] | 105 | 1.0000 | 0.9041 | 0.9496 | 0.0000 | True | 6788.1000 |
| H_prompt_guardrail | Baseline H: Monolithic Prompt Guardrail [Held-out test split] | 105 | 1.0000 | 0.5342 | 0.6964 | 0.0000 | True | 1510.2000 |
| I_embedding | Baseline I: Independent TF-IDF Vector Classifier [Held-out test split] | 105 | 1.0000 | 0.3562 | 0.5253 | 0.0000 | True | 0.7000 |
