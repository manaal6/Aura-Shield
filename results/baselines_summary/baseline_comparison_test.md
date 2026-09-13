| Baseline | Name | Total | Precision | Recall | F1 | FPR | Real_LLM | Avg_Latency_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_rule_only | Baseline A: Deterministic Rule-Only Detector [Held-out test split] | 105 | — | 0.0000 | — | 0.0000 | True | 20.4000 |
| B_llm_only | Baseline B: LLM Semantic Detector Only [Held-out test split] | 105 | 1.0000 | 0.7945 | 0.8855 | 0.0000 | True | 2166.2000 |
| C_constitution_only | Baseline C: Constitution Checker Only [Held-out test split] | 105 | 1.0000 | 0.9315 | 0.9645 | 0.0000 | True | 5190.6000 |
| D_rule_llm | Baseline D: Rule + LLM Semantic Detector [Held-out test split] | 105 | 1.0000 | 0.9178 | 0.9571 | 0.0000 | True | 1981.5000 |
| E_rule_constitution | Baseline E: Rule + Constitution Checker [Held-out test split] | 105 | — | 0.0000 | — | 0.0000 | True | 4287.3000 |
| F_llm_constitution | Baseline F: LLM Semantic + Constitution Checker [Held-out test split] | 105 | 0.6990 | 0.9863 | 0.8182 | 0.9688 | True | 9150.3000 |
| G_full_blended | Baseline G: Full Blended AURA Shield Gateway [Held-out test split] | 105 | 0.7059 | 0.9863 | 0.8229 | 0.9375 | True | 9837.2000 |
| H_prompt_guardrail | Baseline H: Monolithic Prompt Guardrail [Held-out test split] | 105 | 1.0000 | 0.0137 | 0.0270 | 0.0000 | True | 2561.0000 |
| I_embedding | Baseline I: Independent TF-IDF Vector Classifier [Held-out test split] | 105 | 1.0000 | 0.3562 | 0.5253 | 0.0000 | True | 1.1000 |
