> [!NOTE]
> **Status: requires GROQ_API_KEY.** The rows below show `Total_Prompts = 0` and no
> metrics because this suite was run without API credentials; no live cross-model
> evaluation has been completed yet.
>
> **Interpretation caveat:** heterogeneous model roles may reduce correlated failure
> between guard and target models, but they do not establish statistical independence.
> Different models can share training data, refusal behavior, and common weaknesses.

| Experiment_ID | Analyzer_Model | Constitution_Model | Downstream_Model | Total_Prompts | Recall | Precision | F1 | FPR | Avg_Latency_ms |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| full_heterogeneous_pipeline | llama-3.1-8b-instant | llama-3.3-70b-versatile | mixtral-8x7b-32768 | 0 | — | — | — | — | — |
| heterogeneous_analyzer_fast | llama-3.1-8b-instant | gpt-oss-120b | gpt-oss-120b | 0 | — | — | — | — | — |
| heterogeneous_constitution_heavy | gpt-oss-120b | llama-3.3-70b-versatile | gpt-oss-120b | 0 | — | — | — | — | — |
| heterogeneous_decoupled_target | gpt-oss-120b | gpt-oss-120b | mixtral-8x7b-32768 | 0 | — | — | — | — | — |
| same_model_homogeneous | gpt-oss-120b | gpt-oss-120b | gpt-oss-120b | 0 | — | — | — | — | — |
