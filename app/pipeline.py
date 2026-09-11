"""
app/pipeline.py

The only module that orchestrates the full request flow:
rule_detector -> llm_analyzer -> risk_engine -> policy_engine ->
(downstream LLM or security report) -> logger.

This is also the intended integration point for later plugging AURA
Shield into AURA OS as its Input Security Agent - any caller (a CLI, a
Streamlit form, or eventually an AURA OS agent) should only ever need to
call `process_request()`.
"""
import uuid
import logging
from app.config import get_settings
from app.models import IncomingRequest, LogEntry, RuleDetectionResult, LLMAnalysisResult, RiskScore, Decision
from app.detectors import rule_detector, llm_analyzer, prompt_guardrail, embedding_classifier
from app.engine import risk_engine, policy_engine
from app.engine.constitution import constitution_checker
from app.storage.logger import log_constitution_check, log_entry
from app.llm_client import call_protected_llm

logger = logging.getLogger(__name__)


def process_request_with_config(
    request: IncomingRequest,
    baseline_config: dict[str, bool] | None = None,
) -> dict:
    request_id = request.request_id or str(uuid.uuid4())
    settings = get_settings()

    # Specialized standalone baselines
    if baseline_config and baseline_config.get("use_guardrail"):
        guardrail_result = prompt_guardrail.detect(request.user_prompt, request.source_content)
        score = RiskScore(
            score=guardrail_result.raw_signal,
            rule_contribution=0.0,
            llm_contribution=guardrail_result.raw_signal,
            constitution_contribution=0.0,
        )
        decision = policy_engine.decide(score, guardrail_result, None)
        rule_result = RuleDetectionResult(matched=False, matched_patterns=[], raw_signal=0.0)
        llm_result = guardrail_result
        constitution_result = None

    elif baseline_config and baseline_config.get("use_embedding"):
        embedding_result = embedding_classifier.detect(request.user_prompt, request.source_content)
        score = RiskScore(
            score=embedding_result.raw_signal,
            rule_contribution=embedding_result.raw_signal,
            llm_contribution=0.0,
            constitution_contribution=0.0,
        )
        decision = policy_engine.decide(score, None, None)
        rule_result = embedding_result
        llm_result = LLMAnalysisResult(
            is_suspicious=embedding_result.matched,
            reasoning="Embedding vector similarity classification",
            raw_signal=embedding_result.raw_signal,
            used_fallback=False,
        )
        constitution_result = None

    else:
        use_rule = True
        use_llm = True
        use_constitution = True
        if baseline_config is not None:
            use_rule = baseline_config.get("use_rule", True)
            use_llm = baseline_config.get("use_llm", True)
            use_constitution = baseline_config.get("use_constitution", True)

        if use_rule:
            rule_result = rule_detector.detect(request.user_prompt, request.source_content)
        else:
            rule_result = RuleDetectionResult(matched=False, matched_patterns=[], raw_signal=0.0)

        if use_llm:
            llm_result = llm_analyzer.analyze(request.user_prompt, request.source_content)
        else:
            llm_result = LLMAnalysisResult(
                is_suspicious=False,
                reasoning="LLM analyzer disabled by baseline configuration",
                raw_signal=0.0,
                used_fallback=False,
            )

        if use_constitution:
            constitution_result = constitution_checker.check(request.user_prompt, request.source_content)
        else:
            constitution_result = None

        score = risk_engine.compute_risk(rule_result, llm_result, constitution_result)
        decision = policy_engine.decide(score, llm_result, constitution_result)

    entry = LogEntry(
        request_id=request_id,
        user_prompt=request.user_prompt,
        source_content=request.source_content,
        rule_result=rule_result,
        llm_result=llm_result,
        constitution_result=constitution_result,
        decision=decision,
    )
    should_log_db = not (baseline_config and baseline_config.get("skip_db_logging"))
    if should_log_db:
        log_entry(entry)
        log_constitution_check(entry)

    skip_downstream = bool(baseline_config and baseline_config.get("skip_downstream"))
    if decision.decision == Decision.BLOCK:
        llm_response = None
    elif decision.decision == Decision.REVIEW and settings.review_hold_pending_approval:
        llm_response = "[HELD PENDING APPROVAL: Request flagged for human review and held by policy]"
    elif skip_downstream:
        llm_response = "[SKIPPED: Downstream LLM call bypassed for detector evaluation]"
    else:
        # ALLOW and REVIEW (when not held) both reach the downstream LLM in this POC
        llm_response = call_protected_llm(request.user_prompt, request.source_content)

    output = {
        "request_id": request_id,
        "decision": decision.decision.value,
        "risk_score": decision.risk_score.score,
        "explanation": decision.explanation,
        "llm_response": llm_response,
        "rule_result": rule_result,
        "llm_result": llm_result,
        "constitution_result": constitution_result,
    }

    return output


def process_request(request: IncomingRequest) -> dict:
    return process_request_with_config(request, baseline_config=None)
