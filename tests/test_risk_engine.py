from app.models import RuleDetectionResult, LLMAnalysisResult
from app.engine.risk_engine import compute_risk

def test_no_signals_gives_zero_risk():
    rule = RuleDetectionResult(matched=False, matched_patterns=[], raw_signal=0.0)
    llm = LLMAnalysisResult(is_suspicious=False, reasoning="clean", raw_signal=0.0)
    score = compute_risk(rule, llm)
    assert score.score == 0.0

def test_strong_signals_give_high_risk():
    rule = RuleDetectionResult(matched=True, matched_patterns=["direct_override"], raw_signal=1.0)
    llm = LLMAnalysisResult(is_suspicious=True, reasoning="clear injection", raw_signal=1.0)
    score = compute_risk(rule, llm)
    assert score.score == 1.0

def test_contributions_sum_to_score():
    rule = RuleDetectionResult(matched=True, matched_patterns=["jailbreak"], raw_signal=0.7)
    llm = LLMAnalysisResult(is_suspicious=True, reasoning="likely jailbreak", raw_signal=0.5)
    score = compute_risk(rule, llm)
    assert abs((score.rule_contribution + score.llm_contribution) - score.score) < 1e-9
