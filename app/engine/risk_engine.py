"""
app/engine/risk_engine.py

Combines the rule detector's signal, the LLM analyzer's signal, and the
constitution checker's signal into a single risk score.

v2: Supports two fusion strategies (configurable in config.py):
  - "max" (default): score = max(rule, llm, constitution). Prevents dilution
    of the best-performing layer. Tracks which layer was dominant.
  - "weighted_avg" (legacy): score = weighted average as in v1.

Both strategies record the weighted-average as blended_score for audit
comparisons. Provenance adjustment is applied after fusion.

Deliberately a pure function with NO I/O — trivially unit-testable.
"""
from app.config import get_settings
from app.models import RuleDetectionResult, LLMAnalysisResult, ConstitutionCheckResult, RiskScore
from app.engine.provenance import get_trust_level, compute_provenance_adjustment


def compute_risk(
    rule_result: RuleDetectionResult,
    llm_result: LLMAnalysisResult,
    constitution_result: ConstitutionCheckResult | None = None,
    source_type: str = "USER",
) -> RiskScore:
    """
    Fuses detection signals into a risk score.

    fusion_strategy == "max":
      score = max(rule_signal, llm_signal, constitution_signal)
      Dominant signal is tracked for audit attribution.
      The max-of-signals approach ensures a strong detection from ANY
      layer is never diluted by silent layers.

    fusion_strategy == "weighted_avg":
      score = (rule_signal * rule_weight) + (llm_signal * llm_weight)
            + (constitution_signal * constitution_weight)
      Legacy behavior from v1.

    Both modes compute and store the weighted average as blended_score.
    Provenance adjustment is applied after fusion if enabled.
    """
    settings = get_settings()

    rule_signal = rule_result.raw_signal
    llm_signal = llm_result.raw_signal
    constitution_signal = constitution_result.raw_signal if constitution_result is not None else 0.0

    # --- Always compute weighted average (for audit trail) ---
    if constitution_result is not None:
        rule_contrib_w = rule_signal * settings.rule_signal_weight
        llm_contrib_w = llm_signal * settings.llm_signal_weight
        const_contrib_w = constitution_signal * settings.constitution_signal_weight
    else:
        # Redistribute constitution weight proportionally
        remaining = settings.rule_signal_weight + settings.llm_signal_weight
        rule_contrib_w = rule_signal * settings.rule_signal_weight / remaining
        llm_contrib_w = llm_signal * settings.llm_signal_weight / remaining
        const_contrib_w = 0.0
    blended = max(0.0, min(1.0, rule_contrib_w + llm_contrib_w + const_contrib_w))

    # --- Compute score based on fusion strategy ---
    if settings.fusion_strategy == "max":
        score = max(rule_signal, llm_signal, constitution_signal)

        # Determine dominant signal
        signals = {"rule": rule_signal, "llm": llm_signal, "constitution": constitution_signal}
        dominant = max(signals, key=signals.get)  # type: ignore[arg-type]

        # Contributions reflect actual signal values (not weights)
        rule_contribution = rule_signal
        llm_contribution = llm_signal
        constitution_contribution = constitution_signal
    else:
        # Legacy weighted-average mode
        score = blended
        dominant = ""
        rule_contribution = rule_contrib_w
        llm_contribution = llm_contrib_w
        constitution_contribution = const_contrib_w

    # --- Apply provenance adjustment ---
    trust_level = get_trust_level(source_type)
    prov_adjustment = compute_provenance_adjustment(trust_level, score)
    score = max(0.0, min(1.0, score + prov_adjustment))

    return RiskScore(
        score=score,
        rule_contribution=rule_contribution,
        llm_contribution=llm_contribution,
        constitution_contribution=constitution_contribution,
        dominant_signal=dominant,
        blended_score=blended,
        provenance_adjustment=prov_adjustment,
    )
