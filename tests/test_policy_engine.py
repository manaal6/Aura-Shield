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
