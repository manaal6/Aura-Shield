"""
app/engine/risk_engine.py

Combines the rule detector's signal and the LLM analyzer's signal into a
single risk score. Deliberately a pure function with NO I/O - this keeps
it trivially unit-testable and means the scoring formula itself, not any
side effect, is what gets reviewed and evaluated.
"""
from app.config import get_settings
from app.models import RuleDetectionResult, LLMAnalysisResult, RiskScore


def compute_risk(rule_result: RuleDetectionResult, llm_result: LLMAnalysisResult) -> RiskScore:
    """
    score = (rule_signal * rule_weight) + (llm_signal * llm_weight)

    Weights are configured in config.py, not hardcoded here, so the
    weighting policy is auditable and changeable without touching this
    function's logic.
    """
    settings = get_settings()

    rule_contribution = rule_result.raw_signal * settings.rule_signal_weight
    llm_contribution = llm_result.raw_signal * settings.llm_signal_weight

    score = rule_contribution + llm_contribution
    score = max(0.0, min(1.0, score))

    return RiskScore(
        score=score,
        rule_contribution=rule_contribution,
        llm_contribution=llm_contribution,
    )
