"""
app/engine/risk_engine.py

Combines the rule detector's signal and the LLM analyzer's signal into a
single risk score. Deliberately a pure function with NO I/O - this keeps
it trivially unit-testable and means the scoring formula itself, not any
side effect, is what gets reviewed and evaluated.
"""
from app.config import get_settings
from app.models import RuleDetectionResult, LLMAnalysisResult, ConstitutionCheckResult, RiskScore


def compute_risk(
    rule_result: RuleDetectionResult,
    llm_result: LLMAnalysisResult,
    constitution_result: ConstitutionCheckResult | None = None,
) -> RiskScore:
    """
    score = (rule_signal * rule_weight)
          + (llm_signal * llm_weight)
          + (constitution_signal * constitution_signal_weight)

    The constitution signal is 0.0 when no principle was violated and
    otherwise the highest confidence among violated principles. When no
    constitution check was performed (None), its weight is redistributed
    proportionally across the other two signals so the score stays on the
    same 0.0-1.0 scale - the formula never pretends a missing check is a
    violation, nor rewards its absence with a lower score.

    Weights are configured in config.py, not hardcoded here, so the
    weighting policy is auditable and changeable without touching this
    function's logic.
    """
    settings = get_settings()

    rule_contribution = rule_result.raw_signal * settings.rule_signal_weight
    llm_contribution = llm_result.raw_signal * settings.llm_signal_weight

    if constitution_result is not None:
        constitution_signal = constitution_result.raw_signal
        constitution_contribution = constitution_signal * settings.constitution_signal_weight
    else:
        # Redistribute the constitution weight proportionally so callers
        # that predate the constitution layer still produce comparable
        # scores instead of a systematically lower one.
        remaining = settings.rule_signal_weight + settings.llm_signal_weight
        rule_contribution = rule_result.raw_signal * settings.rule_signal_weight / remaining
        llm_contribution = llm_result.raw_signal * settings.llm_signal_weight / remaining
        constitution_contribution = 0.0

    score = rule_contribution + llm_contribution + constitution_contribution
    score = max(0.0, min(1.0, score))

    return RiskScore(
        score=score,
        rule_contribution=rule_contribution,
        llm_contribution=llm_contribution,
        constitution_contribution=constitution_contribution,
    )
