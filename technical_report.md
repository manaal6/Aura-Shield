# AURA Shield: A Prompt Injection Detection Gateway
### Technical Report

**Author:** Manaal Pervaiz
**Context:** Proof-of-concept prepared in support of an application to Prof. Ali Shoker's KAUST VSRP project, "LLM Injection Cyber Resilient Assistants."

---

## 1. Problem Statement

LLM-integrated applications increasingly grant models the ability to read
external content — emails, documents, tool outputs, web pages — and take
actions based on that content. This creates an attack surface where
malicious instructions can be smuggled into a model's context either
directly by an end user (direct prompt injection) or indirectly through
content the model retrieves or processes (indirect prompt injection).
There is no lightweight, explainable, pre-inference gateway that a small
team could realistically deploy in front of an LLM to catch these attempts
before they reach the model — most public discussion of the problem is
qualitative (taxonomies, disclosure write-ups) rather than a reproducible,
measurable system.

## 2. Research Question

*Can a lightweight, rule-based + LLM-assisted detection layer, placed
before inference, measurably reduce the success rate of direct and
indirect prompt injection attacks against an LLM assistant, without
unacceptably degrading benign-prompt usability?*

## 3. Threat Model

**In scope:**
1. Direct prompt injection — a user directly instructs the model to
   override its system prompt or guidelines.
2. Indirect prompt injection — adversarial instructions embedded in
   third-party content (simulated locally in this POC as static "document"
   or "tool output" strings) that the assistant is asked to process.
3. Jailbreak attempts — role-play, hypothetical framing, or obfuscation
   intended to bypass alignment behavior.

**Explicitly out of scope for this POC:**
- Training-time attacks (data poisoning, backdoors).
- Multi-turn manipulation across many conversation turns — only
  single-turn/single-document requests are evaluated.
- Adaptive attackers who have read AURA Shield's source and craft prompts
  specifically to evade *this* detector.

## 4. Trust Boundaries

| Boundary | Description |
|---|---|
| User → AURA Shield | User input is untrusted |
| External content → AURA Shield | Document/tool-output content is **equally** untrusted — this is the crux of indirect injection, since naive systems often trust this content more than user input |
| AURA Shield → downstream LLM | Only content that passed the Policy Engine crosses this boundary |
| AURA Shield → logs | One-way, read-only — logging never feeds back into live decision-making |

## 5. Architecture

```
User request --> Rule-based detector --> LLM security analyzer -->
Risk engine --> Policy engine --> (Downstream LLM | Security report)
--> SQLite logs --> Streamlit dashboard
```

Two independent detection signals (deterministic rules + LLM semantic
judgment) are combined by a documented, inspectable formula rather than a
trained/black-box model, so every decision remains explainable:

```
risk_score = (rule_signal * 0.4) + (llm_signal * 0.6)

score >= 0.75  -> BLOCK
score >= 0.40  -> REVIEW (human-in-the-loop)
score  < 0.40  -> ALLOW
```

The two-tier (review + block) policy, rather than a binary pass/fail, is a
deliberate implementation of human-in-the-loop and zero-trust principles:
borderline cases are surfaced to a human reviewer rather than silently
allowed or silently blocked.

## 6. Implementation

Implemented in Python with a clean modular architecture (Pydantic schemas
at every module boundary, pure functions for scoring/policy logic,
SQLite for the audit trail, Streamlit for the review dashboard). Full
source is in the accompanying repository. Key design choices:

- **Fail-closed-ish fallback:** if the LLM analyzer cannot reach the Groq
  API (no key, network failure), it does not silently treat the request as
  safe — it returns a moderate signal (0.3) and marks the result as a
  fallback, so downstream metrics can distinguish a real judgment from a
  fallback.
- **Separation of risk scoring and policy:** `risk_engine.py` and
  `policy_engine.py` are independent pure functions, so detection logic and
  response policy can be changed independently.

## 7. Evaluation

A 40-prompt benchmark was constructed (10 direct injection, 10 indirect
injection, 10 jailbreak, 10 benign), stored in
`evaluation/benchmark_dataset.json`, and run through the full pipeline via
`evaluation/evaluate.py`.

**Important honesty note:** this development environment had no access to
the Groq API (no API key / no outbound network to `api.groq.com`). The LLM
Security Analyzer therefore ran in its documented fail-safe fallback mode
for every prompt in this run — it did **not** perform real semantic
judgment. The results below reflect the **rule-detector-driven portion of
the pipeline only**, not the full two-layer system the architecture
describes.

### Results (rule-detector-only run)

| Metric | Value |
|---|---|
| True positives | 17 |
| False negatives | 13 |
| False positives | 0 |
| True negatives | 10 |
| Precision | 100.00% |
| Recall | 56.67% |
| Attack Success Rate | 43.33% |
| False Positive Rate | 0.00% |

The 5 missed attacks (false negatives) were split across direct-injection
and jailbreak prompts phrased in ways that did not match any of the
current 12 regex patterns — e.g. prompts using synonyms or slightly
different sentence structure than the patterns anticipate. This is exactly
the class of miss the LLM Security Analyzer is designed to catch, and is
not yet measured.

Zero false positives across the 10 benign prompts, at this rule-only
stage, is a genuinely encouraging signal for usability — but it is a small
sample and should not be over-read.

### What has *not* been tested

- The LLM Security Analyzer's real detection contribution (requires a
  Groq API key not available in this environment).
- Generalization beyond this 40-prompt set.
- Any multi-turn or adaptive-attacker scenario (explicitly out of scope
  per the threat model above).

## 8. Limitations

1. Small benchmark (40 prompts) — no statistically meaningful confidence
   intervals should be drawn from it.
2. The LLM Security Analyzer uses the same underlying model class as the
   system it protects, meaning it could in principle be manipulated by a
   sufficiently crafted input — this is a known, stated limitation, not an
   oversight, and is precisely why it is paired with an independent
   rule-based layer rather than relied on alone.
3. Rule-only evaluation in this report cannot yet demonstrate the value of
   the LLM analyzer layer — that is the immediate next experiment.
4. No defense against adaptive attackers with knowledge of this detector's
   implementation.

## 9. Future Work

- Re-run the benchmark with a real Groq API key to obtain full-pipeline
  metrics and directly compare against the rule-only baseline in this
  report.
- Expand the benchmark with obfuscated and translated injection variants
  to stress-test the rule layer's known blind spot.
- Move `REVIEW`-tier requests to a pending-approval state rather than
  passing them to the downstream LLM immediately.
- Integrate AURA Shield into the AURA OS multi-agent architecture as its
  Input Security Agent, gating all external input before it reaches any
  downstream agent.

## 10. Relation to AURA OS

AURA Shield is intended to become the Input Security Agent within AURA OS
— every external input (direct user prompt or tool/document output) would
pass through this gateway before reaching any downstream agent, moving the
trust boundary to the system's actual entry point rather than relying on
individual agents to self-police untrusted content.
