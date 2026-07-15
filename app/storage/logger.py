"""
app/storage/logger.py

Structured logging: writes every LogEntry to SQLite (audit trail) and to
the standard Python logging output (operational visibility). This is the
only module pipeline.py calls to persist a decision - individual detector
and engine modules never write to storage directly.
"""
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
