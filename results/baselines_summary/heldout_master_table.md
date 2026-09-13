# Held-Out Test Split Master Comparison (105 prompts: 73 attacks, 32 benign)

All LLM-dependent baselines (B–H) executed with live model calls and **zero offline-fallback
rows** (verified per-run: `llm_used_fallback=False` and `constitution_fallback=False` for every
prompt in the cited run directory). Verified clean source runs:

| Baseline | Run directory |
| --- | --- |
| A | `results/baseline_a_rule_only_test_20260912_112621` |
| B | `results/baseline_b_llm_only_test_20260911_135639` |
| C | `results/baseline_c_constitution_only_test_20260911_140357` |
| D | `results/baseline_d_rule_llm_test_20260912_112624` |
| E | `results/baseline_e_rule_constitution_test_20260912_114019` |
| F | `results/baseline_f_llm_constitution_test_20260913_075138` |
| G | `results/baseline_g_full_blended_test_20260913_074542` |
| H | `results/baseline_h_prompt_guardrail_test_20260911_134904` |
| I | `results/baseline_i_embedding_test_20260911_151141` |

## Master table

| Baseline | Recall | Precision | F1 | FPR | Avg latency |
| :--- | :--- | :--- | :--- | :--- | ---: |
| A (Rule only) | 0.0% | — | — | 0.0% | 26 ms |
| B (LLM only) | 79.5% | 100.0% | 88.5% | 0.0% | 2,166 ms |
| C (Constitution only) | 93.2% | 100.0% | 96.5% | 0.0% | 5,191 ms |
| D (Rule + LLM) | 75.3% | 100.0% | 85.9% | 0.0% | 1,947 ms |
| E (Rule + Constitution) | 90.4% | 100.0% | 95.0% | 0.0% | 4,501 ms |
| F (LLM + Constitution) | 90.4% | 100.0% | 95.0% | 0.0% | 6,912 ms |
| **G (Full AURA Shield)** | **89.0%** | **100.0%** | **94.2%** | **0.0%** | 6,902 ms |
| H (Monolithic prompt guardrail) | 75.3% | 100.0% | 85.9% | 0.0% | 2,148 ms |
| I (TF-IDF classifier) | 35.6% | 100.0% | 52.5% | 0.0% | 1 ms |

ASR is not reported here: it requires a separate downstream safety evaluator and was not
measured for these per-baseline runs.

## 95% Wilson CIs on recall (73 attacks)

| Baseline | TP/73 | Recall CI95 |
| --- | --- | --- |
| C | 68 | [84.9%, 97.0%] |
| E | 66 | ~[81.5%, 95.3%] |
| F | 66 | [81.5%, 95.3%] |
| G | 65 | [79.8%, 94.3%] |
| B | 58 | [68.8%, 87.1%] |

**Honest interpretation:** the differences between C, E, F, and G are 1–3 prompts out of 73 and
lie entirely within overlapping confidence intervals. On this held-out split, multi-signal
blending (G) is **not** statistically distinguishable from the constitution-inclusive subsets or
the constitution-only configuration. The claim this table supports is: every LLM/constitution
configuration achieves 75–93% recall at 100% precision, while deterministic rules (A) and the
monolithic guardrail prompt (H) transfer far worse. The claim it does **not** support: that the
full blend outperforms its own subsets.
