"""
app/storage/logger.py

Structured logging: writes every LogEntry to SQLite (audit trail) and to
the standard Python logging output (operational visibility). This is the
only module pipeline.py calls to persist a decision - individual detector
and engine modules never write to storage directly.
"""
import json
import logging
from app.models import LogEntry
from app.storage.database import get_connection

logger = logging.getLogger(__name__)


def log_entry(entry: LogEntry) -> None:
    logger.info(
        "request_id=%s decision=%s risk_score=%.2f",
        entry.request_id, entry.decision.decision.value, entry.decision.risk_score.score,
    )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO logs (
                    request_id, timestamp, user_prompt, source_content,
                    rule_matched, rule_patterns, rule_signal,
                    llm_is_suspicious, llm_reasoning, llm_signal, llm_used_fallback,
                    risk_score, decision, explanation
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    entry.request_id,
                    entry.timestamp,
                    entry.user_prompt,
                    entry.source_content,
                    bool(entry.rule_result.matched),
                    ",".join(entry.rule_result.matched_patterns),
                    entry.rule_result.raw_signal,
                    bool(entry.llm_result.is_suspicious),
                    entry.llm_result.reasoning,
                    entry.llm_result.raw_signal,
                    bool(entry.llm_result.used_fallback),
                    entry.decision.risk_score.score,
                    entry.decision.decision.value,
                    entry.decision.explanation,
                ),
            )
        conn.commit()


def log_constitution_check(entry: LogEntry) -> None:
    """Persists the constitution check for a request to its own table,
    joined back to `logs` by request_id. Every check is logged - including
    fallback/no-verdict runs - so the audit trail shows the check happened
    even when it produced no signal."""
    result = entry.constitution_result
    if result is None:
        return

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO constitution_checks (
                    request_id, timestamp, user_prompt, source_content,
                    constitution_version, principles_evaluated, verdicts,
                    signal, used_fallback, reasoning
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    entry.request_id,
                    entry.timestamp,
                    entry.user_prompt,
                    entry.source_content,
                    result.constitution_version,
                    json.dumps(result.principles_evaluated),
                    json.dumps([v.model_dump() for v in result.verdicts]),
                    result.raw_signal,
                    bool(result.used_fallback),
                    result.reasoning,
                ),
            )
        conn.commit()
