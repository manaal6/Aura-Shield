# AURA Shield — Current Architecture

**Status of this document:** VERIFIED & UPDATED (Post-Phase 12 Research Transformation, 2026-09-11)

---

## 1. Repository Overview

```
aura-shield/
├── app/                          # Core Gateway Backend
│   ├── config.py                 # Centralized settings (weights, thresholds, model roles)
│   ├── models.py                 # Pydantic data contracts between modules
│   ├── pipeline.py               # Request orchestration (process_request_with_config)
│   ├── llm_client.py             # Downstream ("protected") LLM client wrapper
│   ├── adaptive_loop.py          # Adaptive feedback loop
│   ├── detectors/
│   │   ├── rule_detector.py      # Deterministic regex detector (Baseline A)
│   │   ├── llm_analyzer.py       # LLM-assisted semantic analyzer (Baseline B)
│   │   ├── prompt_guardrail.py   # Monolithic prompt guardrail detector (Baseline H)
│   │   └── embedding_classifier.py# TF-IDF n-gram vector similarity detector (Baseline I)
│   ├── engine/
│   │   ├── constitution.py       # Constitution compliance checker (Baseline C)
│   │   ├── risk_engine.py        # Blended risk scoring engine (pure function)
│   │   └── policy_engine.py      # Decision gate (allow/review/block + escalation)
│   └── storage/
│       ├── database.py           # Postgres (Supabase) schema + psycopg2 connection
│       └── logger.py             # Audit log writer (single write path)
├── research/                     # Research Infrastructure & Experiment Package
│   ├── schemas.py                # Typed research data models (PromptRecord, ExperimentSpec, etc.)
│   ├── metrics.py                # Evaluation metrics (Recall, Precision, Wilson CIs, ASR)
│   ├── experiment.py             # Spec loader, output manager & expense guards
│   ├── runner.py                 # Benchmark runner across baseline configs
│   ├── adaptive_loop.py          # Offline adaptation engine & provenance system
│   ├── attacker_defender.py      # Red-teaming game engine & 7 mutation strategies
│   └── evaluator.py              # Downstream safety evaluator & true ASR calculator
├── data/benchmark/               # 330-Prompt Research Benchmark (JSONL)
│   ├── dev/                      # 120 prompts across 4 categories
│   ├── adaptation/               # 105 prompts across 5 categories
│   ├── test/                     # 105 prompts across 5 categories (held-out)
│   └── splits.json               # Formal split manifest and contamination policy
├── experiments/                  # Experiment Suites & Runners
│   ├── baselines/                # 9 baseline specifications (A–I) + run_baselines.py
│   ├── cross_model/              # 5 model independence specs + run_cross_model_matrix.py
│   ├── soc_workflow/             # SOC assistant demonstration spec + runner
│   ├── adaptive/                 # run_adaptive_experiment.py
│   ├── attacker_defender/        # run_attacker_defender_game.py
│   ├── safety_eval/              # run_safety_evaluation.py
│   └── benchmark/                # run_final_test_benchmark.py
├── results/                      # Persisted Research Artifacts & Provenance Records
├── tests/                        # 90 Unit Tests across 13 test suites (100% passing)
├── docs/                         # Research Reports & Formal Specifications
│   ├── research_report.md        # 18-section research report
│   ├── policy-surface-audit.md   # Audited policy surface reference
│   ├── related-work.md           # 7-domain literature review with citations
│   ├── research-roadmap.md       # Completed 12-phase transformation roadmap
│   ├── current-architecture.md   # This document
│   └── technical-report.md       # Technical specification
├── dashboard/                    # Streamlit Interactive Dashboard
├── webapp/                       # FastAPI Server + React Frontend
├── constitution.json             # Versioned safety principles seed file (v1)
└── main.py                       # CLI interface
```

---

## 2. Gateway Execution Flow

```
UNTRUSTED INPUT (user_prompt + optional untrusted source_content)
      │
      ├───────────────────────────────┐
      │                               │
      ▼                               ▼
Rule-Based Detector           Vector Classifier (TF-IDF)
(signature matching)          (cosine similarity against attack clusters)
      │                               │
      ▼                               │
LLM Semantic Analyzer                 │
(structured JSON suspicion signal)     │
      │                               │
      ▼                               │
Constitution Checker                  │
(per-principle compliance checks)     │
      │                               │
      └──────────────┬────────────────┘
                     │
                     ▼
             Risk Scoring Engine
             Blends signals: R = w_rule * S_rule + w_llm * S_llm + w_const * S_const
                     │
                     ▼
             Policy Decision Engine
             • If S_llm >= 0.90 -> BLOCK (Escalation Rule)
             • If R >= 0.75 -> BLOCK
             • If 0.40 <= R < 0.75 -> REVIEW
             • If R < 0.40 -> ALLOW
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
   [BLOCK / HELD]              [ALLOW]
         │                       │
   Log refusal                   ▼
(downstream protected)     Downstream Protected LLM
                                 │
                                 ▼
                     Audit Logging & Persisted Trace
```

---

## 3. Core Component Modules

### A. Centralized Settings (`app/config.py`)
All parameters are managed in a single `Settings` class:
- `rule_signal_weight`: 0.35
- `llm_signal_weight`: 0.45
- `constitution_signal_weight`: 0.20 (absorbed proportionally when constitution check is skipped)
- `threshold_block`: 0.75
- `threshold_review`: 0.40
- `llm_block_signal`: 0.90 (hard escalation trigger)
- `review_hold_pending_approval`: When True, prevents downstream call on REVIEW decisions
- `model_analyzer`, `model_constitution`, `model_downstream`, `model_evaluator`: Model role separation

### B. Detectors (`app/detectors/`)
1. **Rule Detector (`rule_detector.py`)**: 11 regex patterns across direct overrides, exfiltration, jailbreaks, and indirect injection markers.
2. **LLM Analyzer (`llm_analyzer.py`)**: Structured JSON schema output (`is_suspicious`, `confidence`, `reasoning`). Fails visibly with a 0.3 fallback if unavailable.
3. **Prompt Guardrail (`prompt_guardrail.py`)**: Baseline H monolithic guardrail evaluating inputs in a single comprehensive prompt.
4. **Embedding Classifier (`embedding_classifier.py`)**: Baseline I character/word n-gram TF-IDF vectorizer computing cosine similarity against known attack clusters.

### C. Constitution Checker (`app/engine/constitution.py`)
Evaluates input against 6 active principles (seeded from `constitution.json`, persisted in Postgres `constitution` table). Generates per-principle verdicts.

### D. Research Package (`research/`)
- **`schemas.py`**: Pydantic schemas (`PromptRecord`, `DetectionResult`, `PolicyDecision`, `ExperimentSpec`, `PerPromptResult`, `ExperimentResult`).
- **`metrics.py`**: Statistical evaluation metrics with 95% Wilson confidence intervals.
- **`adaptive_loop.py`**: Quarantined feedback loop that ingests false negatives from adaptation data and synthesizes validated candidate principles.
- **`attacker_defender.py`**: Iterative red-teaming game applying 7 mutation strategies over multiple rounds.
- **`evaluator.py`**: Downstream safety evaluator classifying model outputs to calculate true Attack Success Rate (ASR).

---

## 4. Test Suite

The system includes 90 unit tests across 13 test files:
- `tests/test_rule_detector.py` (5 tests)
- `tests/test_risk_engine.py` (3 tests)
- `tests/test_policy_engine.py` (7 tests)
- `tests/test_constitution_and_adaptive.py` (6 tests)
- `tests/test_policy_surface_audit.py` (4 tests)
- `tests/test_benchmark_dataset.py` (2 tests)
- `tests/test_baselines.py` (3 tests)
- `tests/test_cross_model.py` (4 tests)
- `tests/test_soc_workflow.py` (2 tests)
- `tests/test_research_schemas.py` (5 tests)
- `tests/test_research_metrics.py` (5 tests)
- `tests/test_research_runner.py` (6 tests)
- `tests/test_adaptive_loop.py` (12 tests)
- `tests/test_attacker_defender.py` (14 tests)
- `tests/test_safety_evaluator.py` (9 tests)
- `tests/test_final_test_benchmark.py` (3 tests)

All 90 unit tests pass cleanly offline with zero external network calls.
