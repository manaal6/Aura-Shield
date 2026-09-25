# KAUST Three-Pillar Architecture (AURA Shield)

Status: IMPLEMENTED (research prototype, CPU-only smoke-test scope).
Date: 2026-09-21. Baseline frozen in `results/kaust_day1_baseline/baseline.json`.

## 1. Request flow (existing, preserved)

```
INPUT (user_prompt + untrusted source_content)
  → DETECTORS (rule / LLM analyzer / TF-IDF embedding / guardrail)
  → CONSTITUTION (Pillar 1, versioned per-principle checker)
  → RISK (weighted blend: rule 0.35 / llm 0.45 / constitution 0.20)
  → POLICY (thresholds 0.40 review / 0.75 block + LLM/constitution escalation + fail-safe review on analyzer failure)
  → DOWNSTREAM MODEL (protected LLM; blocked/held requests never reach it)
  → TOOLS (synthetic fixtures only; authorization + arg validation + risk check)
  → AUDIT (Postgres log + constitution changelog; request_id, versions, hashes)
```

Code: `app/pipeline.py`, `app/engine/risk_engine.py`, `app/engine/policy_engine.py`.

## 2. Three-pillar map

```
                        ┌──────────────────────┐
                        │ SECURITY CONSTITUTION │  Pillar 1 (inference-time defense)
                        │ versioned principles  │  app/engine/constitution.py
                        │ C1..C6 (+C7 payload)  │  + app/engine/constitution_utils.py
                        └──────────┬───────────┘
                                   │ per-principle verdicts → risk/policy gate
                                   ▼
UNTRUSTED INPUT → AURA SECURITY GATE → DOWNSTREAM MODEL → (gated) TOOLS → AUDIT
                                   ▲
                                   │ candidate principles (human-approved only)
                        ┌──────────┴───────────┐
                        │ ADAPTIVE CONSTITUTION │  Pillar 2 (offline loop, adaptation split only)
                        │ failure→candidate→    │  research/adaptive_loop.py
                        │ validate→approve→v+1  │  + research/adaptation_cycle.py
                        └──────────────────────┘

                        ┌──────────────────────┐
                        │ DPO preference        │  Pillar 3A (model-level alignment)
                        │ alignment (train/dev) │  training/dpo/ (torch CPU, logistic policy
                        └──────────┬───────────┘  LM-DPO RUN (tiny-gpt2, NEGATIVE — see research/DPO_REPORT.md)
                                   ▼
                        ┌──────────────────────┐
                        │ UNLEARNING targeted   │  Pillar 3B (model-level removal experiment)
                        │ forget vs retain      │  training/unlearning/ (gradient-ascent
                        └──────────────────────┘  LM sweep RUN (PARTIAL — see research/UNLEARNING_REPORT.md)
```

## 3. Inference-time defense vs model-level alignment (not interchangeable)

- **Constitution / adaptive gateway (Pillars 1+2):** protect the inference
  boundary per request. No weights change. Versioned, auditable, revocable.
- **DPO (Pillar 3A):** changes preference behavior through training on
  `prompt/chosen/rejected` pairs. Affects the model even when the gateway is
  bypassed — but only as much as the (here: toy-scale) training generalizes.
- **Unlearning (Pillar 3B):** targets one defined synthetic behavior for
  removal while measuring retained capability. Narrow by design; not a
  general safety method.

## 4. Trust boundaries

1. Everything in `source_content` is **untrusted data**, never instructions.
2. The gateway (detectors + constitution + policy) is trusted; the downstream
   model output is **untrusted until validated** (schema, bounds, tool auth).
3. The constitution seed file is trusted at deploy; DB deltas require
   `approved_by` human provenance (`constitution_changelog`).
4. Adaptation / DPO-train / unlearning-forget data are **never** the held-out
   test split (enforced in code + tested).

## 5. Data isolation

| Split | Use | Enforced by |
|---|---|---|
| `data/benchmark/dev` (120) | threshold calibration, fusion comparison | convention + provenance |
| `data/benchmark/adaptation` (105) | adaptive loop input only | `validate_split_isolation()` + tests |
| DPO train/dev (`data/dpo_preferences.jsonl` splits) | preference training / eval | `training/dpo/dataset.py` split field + hash |
| Unlearning forget/retain | forgetting / retention eval | `training/unlearning/*_dataset.py` + disjointness test |
| `data/benchmark/test` (105) | final evaluation only | runner guard + adaptation guard + tests |

## 6. What each pillar connects to

- Pillar 1 → risk/policy gate (signals), audit log (provenance fields).
- Pillar 2 → Pillar 1 (new versioned principles); evaluated on unseen data.
- Pillar 3A → downstream model behavior (preference-aligned responses that the
  gateway additionally screens — defense in depth, see `run_integrated_eval`).
- Pillar 3B → removes one synthetic unsafe pattern; gateway regression tests
  confirm the pattern stays blocked at inference time regardless.
