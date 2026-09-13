# AURA Shield: An Auditable Inference-Time Gateway for Prompt-Injection Detection and Constitutional Policy Enforcement
### Technical & Research Report

**Author:** Manaal Pervaiz  
**Context:** Research platform for prompt-injection resilience, constitutional policy enforcement, and defense-in-depth evaluation against agentic LLM threats.

---

## 1. Problem Statement

Large Language Model (LLM) agents deployed in cybersecurity, enterprise automation, and consumer tasks increasingly ingest untrusted external context — documents, emails, web retrieval, and system logs. Threat actors exploit this boundary via direct and indirect prompt injection to alter model execution paths, exfiltrate private credentials, and execute unauthorized tools. 

Most public research on prompt injection is either purely qualitative or relies on opaque external moderation APIs. AURA Shield establishes an inspectable, pre-inference security gateway that couples deterministic rule filtering, semantic analysis, vector similarity, and explicit constitutional policy verification with a transparent, centralized policy surface.

---

## 2. Research Questions

1. **RQ1 (Layered Defense):** Does multi-signal blending (deterministic rules + semantic LLM analysis + constitutional verification) outperform isolated baseline detectors on held-out attack distributions?
2. **RQ2 (Constitutional Policy Value):** What marginal utility does explicit, principle-grounded constitutional verification add over gestalt classification?
3. **RQ3 (Model Transferability):** How does detector performance behave across heterogeneous model roles?
4. **RQ4 (Adaptive Safety):** Can observed failure cases be systematically translated into validated constitutional updates with complete provenance without degrading precision or contaminating held-out test data?
5. **RQ5 (Cyber-Assistant Utility):** Can the gateway protect a SOC log analysis assistant against embedded payloads without impairing legitimate threat investigation?

---

## 3. Threat Model & Trust Boundaries

### A. In Scope
- **Direct Prompt Injection (DPI):** Explicit user instructions to override system guidelines, bypass boundaries, or leak internal prompts.
- **Indirect Prompt Injection (IPI):** Malicious directives hidden within secondary context (logs, documents, emails, tool outputs).
- **Jailbreaks & Framing:** Persona adoption (e.g. "DAN mode"), hypothetical framings, leetspeak, Base64/ROT13 encoding, and foreign-language translations.
- **Context Flooding & Delimiters:** Injecting fake system control tokens (`<sys>`, `[SYSTEM]`) or padding payloads at extreme token depths.
- **Policy Targeting & Audit Tampering:** Attacks attempting to alter gateway rules, disable security checks, or request log deletion.

### B. Out of Scope
- Parameter-level weight poisoning during pre-training.
- Direct tampering with gateway infrastructure or database storage.
- Physical / hardware-level side-channel attacks.

### C. Trust Boundaries

| Boundary | Description | Enforcement Action |
| :--- | :--- | :--- |
| **TB1: User → AURA Shield** | Raw user inputs are treated as untrusted. | Evaluated by Rule, Vector, LLM, and Constitution layers. |
| **TB2: External Context → AURA Shield** | Third-party documents/logs are equally untrusted. | Separately parsed and evaluated for smuggled directives. |
| **TB3: Gateway → Downstream LLM** | Controlled boundary to the protected model. | Only requests with decision `ALLOW` (or unheld review) pass through. |
| **TB4: Gateway → Audit Logs** | Append-only security logging. | Every decision, signal breakdown, and threshold is persisted. |
| **TB5: Adaptation → Production** | Feedback loop for policy updates. | Isolated from held-out test data; requires automated validation and human sign-off. |

---

## 4. Gateway Architecture & Scoring Formula

```
Untrusted Input (User Prompt + Untrusted Context)
                      │
                      ▼
┌────────────────────────────────────────────────────────┐
│               Detection & Analysis Layers              │
├─────────────────────────┬──────────────────────────────┤
│ Deterministic Rules     │ Regex signatures & markers   │
│ Vector Similarity (TFIDF)│ n-gram embedding classifier  │
│ LLM Semantic Analyzer   │ Intent & framing evaluation  │
│ Constitution Checker    │ Per-principle policy checks  │
└─────────────────────────┴──────────────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────────────────┐
│           Risk Engine & Policy Decision Gate           │
├────────────────────────────────────────────────────────┤
│ • Weighted Signal Blending:                            │
│   R = w_rule * S_rule + w_llm * S_llm + w_const * S_const│
│   (w_rule=0.35, w_llm=0.45, w_const=0.20)              │
│ • Escalation Rule: raw LLM signal ≥ 0.90 forces BLOCK  │
│ • Thresholds: ≥ 0.75 BLOCK | 0.40–0.75 REVIEW | < ALLOW│
│ • Review-Hold: Halts downstream call if pending review │
└────────────────────────────────────────────────────────┘
                      │
         ┌────────────┴────────────┐
         ▼                         ▼
   [BLOCK / HELD]              [ALLOW]
         │                         │
    Refusal Log                    ▼
 (Model Protected)        Downstream Protected LLM
                                   │
                                   ▼
                       Audit Trail & Log Store
```

### Proportional Weight Absorption
When the Constitution Checker is bypassed or not evaluated (e.g. baseline runs), its weight ($w_{\text{const}} = 0.20$) is absorbed proportionally:

$$w'_{\text{rule}} = \frac{0.35}{0.80} = 0.4375, \quad w'_{\text{llm}} = \frac{0.45}{0.80} = 0.5625$$

---

## 5. Implementation & Policy Surface

All parameters are centralized in [`app/config.py`](file:///e:/OneDrive/Documents/aura-shield/aura-shield/app/config.py) and documented in [`docs/policy-surface-audit.md`](file:///e:/OneDrive/Documents/aura-shield/aura-shield/docs/policy-surface-audit.md):

- `rule_signal_weight` (0.35), `llm_signal_weight` (0.45), `constitution_signal_weight` (0.20)
- `threshold_block` (0.75), `threshold_review` (0.40), `llm_block_signal` (0.90)
- `review_hold_pending_approval` (bool): when `True`, `REVIEW` decisions halt execution before reaching the downstream model.
- Model roles: `model_analyzer`, `model_constitution`, `model_downstream`, `model_evaluator`.

---

## 6. Research Benchmark (330 Prompts across 14 Datasets)

| Split | Quota | Files & Families Included | Role in Evaluation |
| :--- | :--- | :--- | :--- |
| **`dev`** | 120 | `direct_injection.jsonl` (30)<br>`indirect_injection.jsonl` (30)<br>`jailbreak_persona.jsonl` (30)<br>`benign_general.jsonl` (30) | Baseline tuning, threshold calibration, and development evaluation. |
| **`adaptation`** | 105 | `jailbreak_encoding.jsonl` (20)<br>`jailbreak_multilingual.jsonl` (20)<br>`obfuscation.jsonl` (20)<br>`context_flooding.jsonl` (20)<br>`benign_cybersecurity.jsonl` (25) | Triggering the adaptive constitution loop with unseen attack representations. |
| **`test`** | 105 | `multi_turn_manipulation.jsonl` (20)<br>`tool_injection.jsonl` (20)<br>`authorization_attack.jsonl` (20)<br>`policy_targeting.jsonl` (20)<br>`benign_cybersecurity_holdout.jsonl` (25) | Held-out evaluation to determine true policy generalization without contamination. |

---

## 7. Experimental Results & Findings

### A. Held-Out Test Set Performance (105 Prompts: 73 Attacks, 32 Benign)
Evaluated on completely unseen attack families:

| Baseline | Recall | Precision | F1 Score | FPR | FNR | Over-Refusal | True ASR | Gateway Mitigation |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline A (Rule Only)** | `0.0%` | `N/A` | `N/A` | `0.0%` | `100.0%` | `0.0%` | `0.0%` | `100.0%` |
| **Baseline I (Embedding Classifier)** | `35.6%` | `100.0%` | `0.525` | `0.0%` | `64.4%` | `0.0%` | `0.0%` | `100.0%` |

**Key Findings**:
1. **Regex Rules Fail on Unseen Vectors**: Single pattern matches yield a risk score of 0.306, below `threshold_review` (0.40), resulting in 0% recall on structurally novel attacks (e.g. tool injections, authorization attacks).
2. **Vector Similarity Transfers Well**: The n-gram TF-IDF vector similarity classifier flags 35.6% of unseen attacks with 0 false positives (100% precision).
3. **True ASR vs Evasion Rate**: Attack Success Rate (ASR) measures downstream compromise, not detector bypasses. Defense-in-depth alignment allows downstream models to refuse attacks that slip past gateway filters.

### B. Adaptive Constitution Loop
On the adaptation split, the offline adaptation loop:
- Identified 80 false negatives under the rule-only baseline.
- Synthesized and validated candidate principle `C7-no-system-role-impersonation`.
- Generated updated constitution v2 with complete JSON provenance in `results/adaptive_summary/adaptive_provenance.json`.

### C. Attacker-Defender Red-Teaming Game
Iterative mutation of 40 seed attacks over 3 rounds applying 7 mutation strategies (whitespace padding, role-play wrappers, leetspeak) demonstrated that heuristic keyword rules degrade immediately against mutative framing across sequential rounds, necessitating multi-signal blending.

### D. SOC Analyst Assistant Demonstration
Evaluated in `experiments/soc_workflow/` over 100 prompts with the full blended pipeline (live model calls, zero offline-fallback rows; raw results in `results/soc_log_analysis_eval_20260913_095251/`):
- Benign Utility Rate: 50/50 (100%) on legitimate log analysis queries.
- Embedded Payload Detection: 50/50 (100%) — attacks smuggled into raw syslog headers and authorization logs were flagged.
- Tool Authorization Enforcement: 20/20 (100%) — smuggled command execution blocked before invocation.

---

## 8. Limitations & Scope Bounds

1. **Inference Latency**: Multi-stage evaluation adds latency relative to single-pass filtering (~10s for full multi-model evaluations vs <5ms for local vector/rule checks).
2. **Provider Dependence**: Relying on external cloud LLMs introduces network jitter and availability risks.
3. **Adaptive Update Gating**: LLM-drafted principles require automated validation and human review to avoid adversarial rule poisoning.
4. **Out-of-Scope Attacks**: The system does not defend against parameter-level model backdoors or direct physical tampering with gateway hosting.

---

## 9. Reproducibility & Test Suite

All 90 unit tests execute completely offline without network or API dependencies:
```bash
python -m pytest tests/ -v
============================= 90 passed in 8.61s ==============================
```

All benchmark files, experiment specs, provenance logs, and reports are maintained under version control in `data/`, `experiments/`, `results/`, and `docs/`.
