# Final Test Report (Phase 27, updated)

Date: 2026-10-02. Command: `python -m pytest tests/ -q`. Result: **196 passed, 0 failed, 0 skipped** (31 files, offline; collection count double-verified).

## Composition

- Original suite: 93 (rule/policy/metrics/runner/baselines/benchmark/soc/safety/cross-model/adaptive/attacker).
- First sprint: 17 (`test_kaust_pillars.py` — constitution/adaptive/DPO/unlearning/integration artifacts).
- Hardening passes: 76 across `test_toolsec_contract.py`, `test_failsafe_audit.py`,
  `test_governance_phases.py`, `test_phase16_20.py`, `test_critical_fixes_abc.py` (HMAC/sandbox/fallback),
  `test_hflocal_provider.py` (routing failover), `test_approval_hardening.py` (named actors + token verify),
  `test_jb_dev_007_regression.py` (pinned live miss), `test_deploy_fixes.py` (migration + evidence endpoint).
- Coverage buckets: original, security regression, DPO, unlearning, fusion (artifact-backed),
  provenance/governance, tool security, fail-safe, audit/tamper, red-team classes, dashboard loader import.

## Policy on failures

No failing test was deleted or weakened to reach green. One expectation was corrected with
documented rationale (B2: parseable `run X` → REVIEW, not DENY — the invariant "no silent
execution" is preserved and tested). All other failures during the pass were implementation or
harness bugs, fixed and re-verified (see `research/BUG_AND_REGRESSION_LEDGER.md`).

## Exclusions (honest)

- `research/canary_asr.py` is an evaluation script, not a test (needs live API; fails closed to NOT RUN rows).
- Live evaluations (DEV forensics, frozen re-run, red-team, ASR) run as scripts with persisted
  artifacts — not in the suite — because they need quota and their value is the artifact, not a pass/fail.
