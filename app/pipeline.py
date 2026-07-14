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
from app.models import IncomingRequest, LogEntry
from app.detectors import rule_detector, llm_analyzer
from app.engine import risk_engine, policy_engine
from app.storage.logger import log_entry
from app.llm_client import call_protected_llm
from app.models import Decision

logger = logging.getLogger(__name__)


def process_request(request: IncomingRequest) -> dict:
    request_id = request.request_id or str(uuid.uuid4())

    rule_result = rule_detector.detect(request.user_prompt, request.source_content)
    llm_result = llm_analyzer.analyze(request.user_prompt, request.source_content)
    score = risk_engine.compute_risk(rule_result, llm_result)
    decision = policy_engine.decide(score)

    entry = LogEntry(
        request_id=request_id,
        user_prompt=request.user_prompt,
        source_content=request.source_content,
        rule_result=rule_result,
        llm_result=llm_result,
        decision=decision,
    )
    log_entry(entry)

    if decision.decision == Decision.BLOCK:
        llm_response = None
    else:
        # ALLOW and REVIEW both currently reach the downstream LLM in this
        # POC; REVIEW additionally surfaces in the dashboard for a human
        # to audit after the fact. A stricter deployment could instead
        # hold REVIEW requests pending explicit human approval before
        # calling the downstream LLM - documented as future work.
        llm_response = call_protected_llm(request.user_prompt, request.source_content)

    # rule_result and llm_result are returned here (not just logged) so
    # callers like evaluation/evaluate.py can inspect the full detection
    # breakdown WITHOUT re-running the detectors a second time - re-running
    # llm_analyzer.analyze() per prompt was doubling Groq API calls during
    # benchmark runs and needlessly burning through rate limits.
    output = {
        "request_id": request_id,
        "decision": decision.decision.value,
        "risk_score": decision.risk_score.score,
        "explanation": decision.explanation,
        "llm_response": llm_response,
        "rule_result": rule_result,
        "llm_result": llm_result,
    }

    return output
