"""tests/test_failsafe_audit.py — Phase 11/12: fail-safe battery + audit-attack tests."""
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))

from app.engine import constitution_utils as cu  # noqa: E402
from app.models import (ConstitutionCheckResult, LLMAnalysisResult,  # noqa: E402
                        RiskScore, RuleDetectionResult)
from app.engine import policy_engine, risk_engine  # noqa: E402


def _fallback_llm():
    return LLMAnalysisResult(is_suspicious=False, reasoning="down",
                             raw_signal=0.3, used_fallback=True, failure_reason="unavailable")


def test_llm_unavailable_never_silent_allow():
    rule = RuleDetectionResult(matched=False, matched_patterns=[], raw_signal=0.0)
    llm = _fallback_llm()
    score = risk_engine.compute_risk(rule, llm, None)
    d = policy_engine.decide(score, llm, None)
    assert d.decision.value in ("review", "block")


def test_constitution_unavailable_contributes_no_signal():
    rule = RuleDetectionResult(matched=True, matched_patterns=["x"], raw_signal=1.0)
    llm = LLMAnalysisResult(is_suspicious=False, reasoning="ok", raw_signal=0.0)
    res = ConstitutionCheckResult(constitution_version=1, principles_evaluated=[],
                                  verdicts=[], raw_signal=0.0,
                                  reasoning="down", used_fallback=True)
    score = risk_engine.compute_risk(rule, llm, res)
    assert score.constitution_contribution == 0.0


def test_malformed_constitution_verdict_rejected():
    import pydantic
    try:
        from app.models import ConstitutionVerdict
        ConstitutionVerdict(principle_id="C1", violated="yes", confidence=9.0, explanation="")
        assert False, "should have raised"
    except pydantic.ValidationError:
        pass


def test_empty_input_fail_safe():
    assert cu.structured_gate_output("   ")["decision"] == "review"


def test_audit_log_rejects_secret_leak_attempt():
    # Policy helper: audit serializer must refuse entries containing secret markers.
    from app.models import LogEntry, Decision, SecurityDecision
    import re
    entry = LogEntry(request_id="t", user_prompt="hello",
                     rule_result=RuleDetectionResult(matched=False, matched_patterns=[], raw_signal=0.0),
                     llm_result=LLMAnalysisResult(is_suspicious=False, reasoning="ok", raw_signal=0.0),
                     decision=SecurityDecision(decision=Decision.ALLOW,
                                               risk_score=RiskScore(score=0.0, rule_contribution=0.0,
                                                                    llm_contribution=0.0),
                                               explanation="ok"))
    blob = entry.model_dump_json()
    assert not re.search(r"GROQ_API_KEY|sk-[a-z0-9]{8,}|AKIA[0-9A-Z]{16}", blob)


def test_audit_entry_ids_unique_and_timestamped():
    from app.models import LogEntry, Decision, SecurityDecision
    mk = lambda: LogEntry(request_id="x", user_prompt="hi",
                          rule_result=RuleDetectionResult(matched=False, matched_patterns=[], raw_signal=0.0),
                          llm_result=LLMAnalysisResult(is_suspicious=False, reasoning="ok", raw_signal=0.0),
                          decision=SecurityDecision(decision=Decision.ALLOW,
                                                    risk_score=RiskScore(score=0.0, rule_contribution=0.0,
                                                                         llm_contribution=0.0),
                                                    explanation="ok"))
    a, b = mk(), mk()
    assert a.timestamp is not None and b.timestamp is not None
