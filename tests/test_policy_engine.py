from app.models import RiskScore, Decision
from app.engine.policy_engine import decide

def test_low_score_is_allowed():
    score = RiskScore(score=0.1, rule_contribution=0.0, llm_contribution=0.1)
    result = decide(score)
    assert result.decision == Decision.ALLOW
    assert result.explanation

def test_mid_score_is_review():
    score = RiskScore(score=0.5, rule_contribution=0.2, llm_contribution=0.3)
    result = decide(score)
    assert result.decision == Decision.REVIEW
    assert result.explanation

def test_high_score_is_blocked():
    score = RiskScore(score=0.9, rule_contribution=0.4, llm_contribution=0.5)
    result = decide(score)
    assert result.decision == Decision.BLOCK
    assert result.explanation

def test_explanation_never_empty():
    for s in [0.0, 0.39, 0.4, 0.74, 0.75, 1.0]:
        score = RiskScore(score=s, rule_contribution=s/2, llm_contribution=s/2)
        result = decide(score)
        assert len(result.explanation) > 0

from app.models import LLMAnalysisResult

def _llm(signal: float) -> LLMAnalysisResult:
    return LLMAnalysisResult(
        is_suspicious=True, reasoning="test", raw_signal=signal, used_fallback=False
    )

def test_high_llm_signal_escalates_to_block():
    score = RiskScore(score=0.59, rule_contribution=0.0, llm_contribution=0.59)
    result = decide(score, _llm(0.99))
    assert result.decision == Decision.BLOCK
    assert "escalation" in result.explanation

def test_moderate_llm_signal_does_not_escalate():
    score = RiskScore(score=0.3, rule_contribution=0.0, llm_contribution=0.3)
    result = decide(score, _llm(0.5))
    assert result.decision == Decision.ALLOW

def test_escalation_only_when_llm_result_provided():
    score = RiskScore(score=0.59, rule_contribution=0.0, llm_contribution=0.59)
    assert decide(score).decision == Decision.REVIEW


def test_graduated_failsafe_known_safe_allows():
    # LLM fallback with 0 rule signal and 0 risk score -> known-safe -> ALLOW with audit flag
    score = RiskScore(score=0.0, rule_contribution=0.0, llm_contribution=0.0)
    fallback_llm = LLMAnalysisResult(
        is_suspicious=False, reasoning="timeout", raw_signal=0.3, used_fallback=True, failure_reason="timeout"
    )
    res = decide(score, fallback_llm)
    assert res.decision == Decision.ALLOW
    assert "fail_safe_passthrough" in res.explanation


def test_graduated_failsafe_security_sensitive_reviews():
    from app.models import ConstitutionCheckResult, ConstitutionVerdict
    # LLM fallback but rule signal triggered -> security-sensitive -> REVIEW
    score = RiskScore(score=0.3, rule_contribution=0.3, llm_contribution=0.0)
    fallback_llm = LLMAnalysisResult(
        is_suspicious=False, reasoning="unavailable", raw_signal=0.3, used_fallback=True, failure_reason="unavailable"
    )
    res = decide(score, fallback_llm)
    assert res.decision == Decision.REVIEW


def test_constitution_escalation_at_070_blocks():
    from app.models import ConstitutionCheckResult, ConstitutionVerdict
    score = RiskScore(score=0.35, rule_contribution=0.0, llm_contribution=0.35)
    c_res = ConstitutionCheckResult(
        constitution_version=2,
        principles_evaluated=["C1-no-override"],
        verdicts=[ConstitutionVerdict(principle_id="C1-no-override", violated=True, confidence=0.72, explanation="override attempt")],
        raw_signal=0.72,
        reasoning="violation",
    )
    res = decide(score, constitution_result=c_res)
    assert res.decision == Decision.BLOCK
    assert "C1-no-override" in res.explanation

