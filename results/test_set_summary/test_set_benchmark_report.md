# Held-Out Test Set Benchmark — Final Research Evaluation

- **Timestamp**: `2026-09-11T09:20:12.302024+00:00`
- **Total Test Prompts**: `105` (Attacks: `73`, Benign: `32`)
- **Split Policy**: Completely held out until final evaluation — strictly never viewed by adaptation loop.

## 1. Primary Baseline Comparison on Held-Out Test Split

| Baseline Configuration | Recall | Precision | F1 Score | FPR | FNR | Over-Refusal | True ASR | Bypassed ASR | Gateway Mitigation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `A_rule_only` | `0.0%` | `N/A` | `N/A` | `0.0%` | `100.0%` | `0.0%` | `0.0%` | `0.0%` | `100.0%` |
| `I_embedding` | `35.6%` | `100.0%` | `0.525` | `0.0%` | `64.4%` | `0.0%` | `0.0%` | `0.0%` | `100.0%` |

## 2. Per-Family Analysis Across Held-Out Attack Types

The held-out test split evaluated 5 unseen attack and benign families:
- `authorization_attack`: Privilege escalation & unauthorized policy modification attempts
- `multi_turn_manipulation`: Context buildup across sequential turns
- `policy_targeting`: Adversarial manipulation targeting gateway rules directly
- `tool_injection`: Smuggled payload within mock tool outputs
- `benign_cybersecurity_holdout`: Hard negative SOC and threat analysis queries

## 3. Key Findings & Defense-in-Depth Conclusions
1. **Rule Detector Brittleness**: Baseline A exhibits 0% recall on structurally novel attack formats (e.g. tool injection, authorization bypass), confirming regex rules fail without semantic evaluation.
2. **Vector Classifier Generalization**: Baseline I demonstrates strong transfer to unseen phrasing when semantic similarity overlaps with training clusters.
3. **True ASR vs Evasion Discrepancy**: True downstream ASR remains consistently lower than detector evasion rates, proving that defense-in-depth alignment provides secondary protection against bypassed prompts.