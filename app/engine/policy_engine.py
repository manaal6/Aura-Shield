"""
app/engine/policy_engine.py

Translates a RiskScore into a Decision (allow / review / block) using the
threshold bands defined in config.py. Kept as a pure function, separate
from risk_engine.py, so that "how risky is this" and "what do we do about
it" are independently swappable - policy can change without touching
detection logic, and vice versa.
"""
from app.config import get_settings
from app.models import RiskScore, Decision, SecurityDecision


def decide(risk_score: RiskScore) -> SecurityDecision:
    settings = get_settings()

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
