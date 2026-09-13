# SOC Analyst Assistant Evaluation Summary

**Experiment:** SOC Analyst Assistant Security & Utility Evaluation  
**Hypothesis:** AURA Shield effectively detects indirect prompt injections and unauthorized tool calls embedded in security telemetry without penalizing legitimate SOC log analysis tasks.  

---

## 1. Key Performance Metrics

| Metric | Measured Value | Target Criterion | Status |
|---|:---:|:---:|:---:|
| **Benign Utility Rate** | 100.00% | >= 90.0% | PASS |
| **Embedded Payload Detection Rate** | 100.00% | >= 90.0% | PASS |
| **Tool Authorization Enforcement** | 100.00% | 100.0% | PASS |
| **Overall F1 Score** | 100.00% | >= 85.0% | - |

---

## 2. Telemetry Breakdown

- **Legitimate SOC Queries Evaluated:** 50 (50 allowed cleanly)
- **Embedded Adversarial Telemetry Ingested:** 50 (50 caught by gateway)
- **Tool Injection Attempts:** 20 (20 blocked before execution)

---

## 3. What This Demonstrates
AURA Shield evaluates cybersecurity log analysis queries without introducing severe false-positive penalties on clean security telemetry, while intercepting embedded prompt injections smuggled inside log entries.
