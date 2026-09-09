"""
app/engine/policy_engine.py

Translates a RiskScore into a Decision (allow / review / block) using the
threshold bands defined in config.py. Kept as a pure function, separate
from risk_engine.py, so that "how risky is this" and "what do we do about
it" are independently swappable - policy can change without touching
detection logic, and vice versa.
"""
from app.config import get_settings
from app.models import RiskScore, LLMAnalysisResult, ConstitutionCheckResult, Decision, SecurityDecision


def decide(
    risk_score: RiskScore,
    llm_result: LLMAnalysisResult | None = None,
    constitution_result: ConstitutionCheckResult | None = None,
) -> SecurityDecision:
    settings = get_settings()

    # Escalation: the blended score can undershoot a near-certain LLM
    # detection when the rule signal is 0 (e.g. injection hidden in source
    # content, which no rule pattern covers). Block on the LLM signal alone.
    # A constitution violation escalates the same way: if any principle was
    # violated with confidence >= llm_block_signal, block regardless of the
    # blended score. A confident, citable principle breach is not something
    # a low rule signal should dilute.
    if (
        constitution_result is not None
        and constitution_result.raw_signal >= settings.llm_block_signal
    ):
        violated = [v for v in constitution_result.verdicts if v.violated]
        strongest = max(violated, key=lambda v: v.confidence)
        return SecurityDecision(
            decision=Decision.BLOCK,
            risk_score=risk_score,
            explanation=(
                f"Blocked: constitution principle {strongest.principle_id} violated with "
                f"confidence {strongest.confidence:.2f} (escalation threshold "
                f"{settings.llm_block_signal:.2f}), overriding the blended risk score "
                f"({risk_score.score:.2f}). {strongest.explanation}"
            ),
        )

    if llm_result is not None and llm_result.raw_signal >= settings.llm_block_signal:
        return SecurityDecision(
            decision=Decision.BLOCK,
            risk_score=risk_score,
            explanation=(
                f"Blocked: LLM security analyzer signal {llm_result.raw_signal:.2f} met or "
                f"exceeded the escalation threshold ({settings.llm_block_signal:.2f}), overriding "
                f"the blended risk score ({risk_score.score:.2f}). Reasoning: {llm_result.reasoning}"
            ),
        )

    if risk_score.score >= settings.threshold_block:
        decision = Decision.BLOCK
        explanation = (
            f"Blocked: risk score {risk_score.score:.2f} met or exceeded the block "
            f"threshold ({settings.threshold_block:.2f}). Rule contribution: "
            f"{risk_score.rule_contribution:.2f}, LLM contribution: {risk_score.llm_contribution:.2f}."
        )
    elif risk_score.score >= settings.threshold_review:
        decision = Decision.REVIEW
        explanation = (
            f"Flagged for human review: risk score {risk_score.score:.2f} is between "
            f"the review threshold ({settings.threshold_review:.2f}) and block threshold "
            f"({settings.threshold_block:.2f}). Not auto-blocked, but not auto-trusted either."
        )
    else:
        decision = Decision.ALLOW
        explanation = (
            f"Allowed: risk score {risk_score.score:.2f} is below the review threshold "
            f"({settings.threshold_review:.2f})."
        )

    return SecurityDecision(decision=decision, risk_score=risk_score, explanation=explanation)
