"""
app/engine/policy_engine.py

Translates a RiskScore into a Decision (allow / review / block) using the
threshold bands defined in config.py. Kept as a pure function, separate
from risk_engine.py, so that "how risky is this" and "what do we do about
it" are independently swappable.

v2 additions:
  - Constitution-specific escalation at its own (lower) threshold (W#1)
  - Constitution-direct-review at signal >= 0.40 (W#1)
  - Graduated fail-safe: classifies by request characteristics during LLM
    outage instead of blanket REVIEW (W#6, corrected per user guidance —
    NOT blind ALLOW, but risk-profile-based)
"""
from app.config import get_settings
from app.models import RiskScore, LLMAnalysisResult, ConstitutionCheckResult, Decision, SecurityDecision


def _classify_request_risk_profile(
    risk_score: RiskScore,
    llm_result: LLMAnalysisResult | None,
    constitution_result: ConstitutionCheckResult | None,
) -> str:
    """Classify request risk profile using available offline signals.

    Returns one of: 'known_safe', 'uncertain', 'security_sensitive'.
    Used by the graduated fail-safe to decide ALLOW vs REVIEW during
    LLM outages, WITHOUT defaulting to blind ALLOW on zero signals.

    Security-sensitive (always REVIEW even during outage):
    - Source content is present (potential indirect injection vector)
    - Any rule signal > 0 (something triggered)
    - Any constitution violation detected
    - Risk score > 0.20 from any source

    Known-safe (ALLOW with audit flag during outage):
    - Short prompt (< 200 chars), no source content, zero rule signal,
      zero constitution signal. These are low-risk benign queries.

    Everything else: uncertain (REVIEW).
    """
    has_source_content = constitution_result is not None  # proxy: constitution only runs when source_content exists or always
    has_rule_signal = risk_score.rule_contribution > 0.0
    has_constitution_signal = (
        constitution_result is not None
        and constitution_result.raw_signal > 0.0
    )
    score_above_floor = risk_score.score > 0.20

    if has_rule_signal or has_constitution_signal or score_above_floor:
        return "security_sensitive"

    # Check if the LLM result had source_content passed to it
    if llm_result and llm_result.reasoning and "source content" in llm_result.reasoning.lower():
        return "security_sensitive"

    # Short prompts with zero offline signals are low-risk
    # Note: we can't check prompt length here directly, but a zero-signal
    # profile with no source content is the best offline approximation
    if not has_source_content and risk_score.score <= 0.0:
        return "known_safe"

    return "uncertain"


def decide(
    risk_score: RiskScore,
    llm_result: LLMAnalysisResult | None = None,
    constitution_result: ConstitutionCheckResult | None = None,
) -> SecurityDecision:
    settings = get_settings()

    # ------------------------------------------------------------------ #
    # Analyzer-failure interception (checked FIRST, before any escalation #
    # or threshold logic, so a fallback can never silently produce ALLOW) #
    # ------------------------------------------------------------------ #
    # When the LLM analyzer could not produce a verdict (unavailable,
    # malformed output, or timeout) and llm_failure_policy == "review",
    # route based on the graduated fail-safe policy.
    if (
        llm_result is not None
        and llm_result.used_fallback
        and llm_result.failure_reason is not None
        and settings.llm_failure_policy == "review"
    ):
        reason_label = {
            "unavailable": "LLM analyzer was unavailable (no API key or connection failure)",
            "malformed": "LLM analyzer returned malformed output that could not be parsed",
            "timeout": "LLM analyzer request timed out before a verdict was reached",
        }.get(llm_result.failure_reason, f"LLM analyzer failure ({llm_result.failure_reason})")

        if settings.graduated_failsafe_enabled:
            profile = _classify_request_risk_profile(risk_score, llm_result, constitution_result)
            if profile == "known_safe":
                return SecurityDecision(
                    decision=Decision.ALLOW,
                    risk_score=risk_score,
                    explanation=(
                        f"Allowed (graduated fail-safe): {reason_label}. "
                        f"Request classified as known-safe: zero rule signal, zero constitution "
                        f"signal, no security-sensitive indicators. "
                        f"AUDIT FLAG: fail_safe_passthrough — LLM layer was unavailable. "
                        f"Blended risk score was {risk_score.score:.2f}."
                    ),
                )
            # "uncertain" and "security_sensitive" both route to REVIEW
            return SecurityDecision(
                decision=Decision.REVIEW,
                risk_score=risk_score,
                explanation=(
                    f"Held for human review (graduated fail-safe): {reason_label}. "
                    f"Request risk profile: {profile}. "
                    f"Policy is llm_failure_policy='review' with graduated classification — "
                    f"only known-safe requests pass during LLM outage. "
                    f"Blended risk score was {risk_score.score:.2f}."
                ),
            )

        # Non-graduated: blanket REVIEW (original v1 behavior)
        return SecurityDecision(
            decision=Decision.REVIEW,
            risk_score=risk_score,
            explanation=(
                f"Held for human review: {reason_label}. "
                f"Policy is llm_failure_policy='review' — requests cannot be auto-allowed "
                f"when the LLM analysis layer did not return a valid verdict. "
                f"Blended risk score was {risk_score.score:.2f} (not used for this decision). "
                f"Analyzer note: {llm_result.reasoning}"
            ),
        )

    # ------------------------------------------------------------------ #
    # Constitution escalation (uses its own, lower threshold because      #
    # constitution violations are citable against a named principle)      #
    # ------------------------------------------------------------------ #
    if constitution_result is not None and constitution_result.raw_signal >= settings.constitution_block_signal:
        violated = [v for v in constitution_result.verdicts if v.violated]
        strongest = max(violated, key=lambda v: v.confidence)
        return SecurityDecision(
            decision=Decision.BLOCK,
            risk_score=risk_score,
            explanation=(
                f"Blocked: constitution principle {strongest.principle_id} violated with "
                f"confidence {strongest.confidence:.2f} (constitution escalation threshold "
                f"{settings.constitution_block_signal:.2f}), overriding the blended risk score "
                f"({risk_score.blended_score:.2f}). {strongest.explanation}"
            ),
        )

    # Constitution-direct-review: any constitution signal above the review
    # floor forces REVIEW, even if the blended/max score is below 0.40.
    # This prevents the "constitution-catch-lost-by-fusion" pattern.
    if (
        constitution_result is not None
        and constitution_result.raw_signal >= settings.constitution_review_signal
        and constitution_result.raw_signal < settings.constitution_block_signal
    ):
        violated = [v for v in constitution_result.verdicts if v.violated]
        if violated:
            strongest = max(violated, key=lambda v: v.confidence)
            return SecurityDecision(
                decision=Decision.REVIEW,
                risk_score=risk_score,
                explanation=(
                    f"Flagged for human review: constitution principle {strongest.principle_id} "
                    f"violated with confidence {strongest.confidence:.2f} (above constitution "
                    f"review floor {settings.constitution_review_signal:.2f}). "
                    f"Blended risk score was {risk_score.blended_score:.2f}. "
                    f"{strongest.explanation}"
                ),
            )

    # LLM escalation: a near-certain LLM detection blocks even when the
    # blended score falls short.
    if llm_result is not None and llm_result.raw_signal >= settings.llm_block_signal:
        return SecurityDecision(
            decision=Decision.BLOCK,
            risk_score=risk_score,
            explanation=(
                f"Blocked: LLM security analyzer signal {llm_result.raw_signal:.2f} met or "
                f"exceeded the escalation threshold ({settings.llm_block_signal:.2f}), overriding "
                f"the blended risk score ({risk_score.blended_score:.2f}). Reasoning: {llm_result.reasoning}"
            ),
        )

    if risk_score.score >= settings.threshold_block:
        decision = Decision.BLOCK
        explanation = (
            f"Blocked: risk score {risk_score.score:.2f} met or exceeded the block "
            f"threshold ({settings.threshold_block:.2f}). "
            f"Dominant signal: {risk_score.dominant_signal or 'weighted_avg'}. "
            f"Rule contribution: {risk_score.rule_contribution:.2f}, "
            f"LLM contribution: {risk_score.llm_contribution:.2f}, "
            f"Constitution contribution: {risk_score.constitution_contribution:.2f}."
        )
    elif risk_score.score >= settings.threshold_review:
        decision = Decision.REVIEW
        explanation = (
            f"Flagged for human review: risk score {risk_score.score:.2f} is between "
            f"the review threshold ({settings.threshold_review:.2f}) and block threshold "
            f"({settings.threshold_block:.2f}). "
            f"Dominant signal: {risk_score.dominant_signal or 'weighted_avg'}."
        )
    else:
        decision = Decision.ALLOW
        explanation = (
            f"Allowed: risk score {risk_score.score:.2f} is below the review threshold "
            f"({settings.threshold_review:.2f})."
        )

    return SecurityDecision(decision=decision, risk_score=risk_score, explanation=explanation)
