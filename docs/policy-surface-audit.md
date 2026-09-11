# Policy Surface Auditability & Gate Enforcement Report

## 1. Executive Summary

AURA Shield enforces a centralized, fully auditable policy surface housed exclusively in [`app/config.py`](file:///e:/OneDrive/Documents/aura-shield/aura-shield/app/config.py). Security thresholds, signal blending weights, escalation rules, model role assignments, and review-hold semantics are governed through a single `Settings` object rather than being hardcoded or scattered across detector modules.

This document serves as the formal security audit reference for AURA Shield's gateway policy surface.

---

## 2. Policy Configuration Parameters

All policy parameters are managed via standard environment variables (or `.env`) and exposed via `app.config.get_settings()`.

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `rule_signal_weight` | `float` | `0.35` | Weight assigned to deterministic rule detector signal ($S_{\text{rule}} \in [0, 1]$) |
| `llm_signal_weight` | `float` | `0.45` | Weight assigned to LLM security analyzer signal ($S_{\text{llm}} \in [0, 1]$) |
| `constitution_signal_weight` | `float` | `0.20` | Weight assigned to constitution policy checker violation signal ($S_{\text{const}} \in [0, 1]$) |
| `threshold_block` | `float` | `0.75` | Blended risk score threshold at or above which an input is **BLOCKED** |
| `threshold_review` | `float` | `0.40` | Blended risk score threshold at or above which an input is flagged for **REVIEW** |
| `llm_block_signal` | `float` | `0.90` | Hard escalation trigger: raw LLM signal $\ge 0.90$ forces an immediate **BLOCK** |
| `review_hold_pending_approval` | `bool` | `False` | When `True`, **REVIEW** verdicts hold execution and block downstream LLM calls until approved |

---

## 3. Signal Blending & Proportional Absorption

### Blended Risk Score Calculation
When all three security modules (Deterministic Rules, LLM Analyzer, Constitution Checker) execute, the total risk score $R$ is calculated as:

$$R = w_{\text{rule}} \cdot S_{\text{rule}} + w_{\text{llm}} \cdot S_{\text{llm}} + w_{\text{const}} \cdot S_{\text{const}}$$

Where $w_{\text{rule}} + w_{\text{llm}} + w_{\text{const}} = 1.0$.

### Proportional Weight Absorption
When the Constitution Checker is bypassed or not evaluated (e.g. baseline runs or fast-path evaluations), its weight ($w_{\text{const}} = 0.20$) is absorbed proportionally by the remaining active detectors:

$$w'_{\text{rule}} = \frac{w_{\text{rule}}}{w_{\text{rule}} + w_{\text{llm}}} = \frac{0.35}{0.80} = 0.4375$$

$$w'_{\text{llm}} = \frac{w_{\text{llm}}}{w_{\text{rule}} + w_{\text{llm}}} = \frac{0.45}{0.80} = 0.5625$$

This ensures that the final risk score remains normalized between $0.0$ and $1.0$ regardless of module activation.

---

## 4. Decision Gate Enforcement Matrix

| Blended Risk Score ($R$) | Hard Override Trigger | Enforcement Action | Downstream LLM Execution |
| :--- | :--- | :--- | :--- |
| $R \ge 0.75$ | N/A | **BLOCK** | ❌ Prevented |
| Any | $S_{\text{llm}} \ge 0.90$ | **BLOCK** (Escalation Rule) | ❌ Prevented |
| $0.40 \le R < 0.75$ | N/A (`review_hold=False`) | **REVIEW** (Flagged) | ✅ Executed & Audited |
| $0.40 \le R < 0.75$ | N/A (`review_hold=True`) | **REVIEW** (Held) | ❌ Prevented pending human approval |
| $R < 0.40$ | N/A | **ALLOW** | ✅ Executed |

---

## 5. Escalation Rule Rationale

Without the `llm_block_signal` escalation rule, a near-certain LLM detector signal ($S_{\text{llm}} = 1.0$) combined with a rule miss ($S_{\text{rule}} = 0.0$) and no constitution check yields a blended score of:

$$R = 0.4375 \times 0.0 + 0.5625 \times 1.0 = 0.5625$$

Because $0.5625 < 0.75$, an obvious high-risk prompt would only receive a **REVIEW** verdict. To prevent critical bypasses, any raw signal $S_{\text{llm}} \ge 0.90$ triggers an explicit escalation, immediately upgrading the verdict to **BLOCK**.

---

## 6. Auditability & Research Reproducibility

1. **Deterministic Auditing**: Every gateway evaluation returns a complete audit record containing raw detector signals ($S_{\text{rule}}, S_{\text{llm}}, S_{\text{const}}$), the blended score $R$, exact thresholds applied, active model roles, and exact policy action taken.
2. **Zero Hardcoded Values**: Modules import parameters dynamically from `app.config.get_settings()`.
3. **Database & Local Logging Integrity**: All decisions are persisted with full signal provenance, allowing offline re-evaluations under alternative hyperparameter settings.
