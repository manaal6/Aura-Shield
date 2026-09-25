"""
app/storage/logger.py

Structured logging: writes every LogEntry to PostgreSQL with:
- Concurrency-safe hash-chaining via table lock / serializable transaction (W#11)
- Fallback buffering to local tamper-evident disk buffer during DB outages (W#11, W#13)
- Canonical SHA-256 parent hash calculation
"""
from __future__ import annotations

import json
import logging
import hashlib
from app.models import LogEntry
from app.storage.database import get_connection
from app.storage.local_buffer import buffer_log_locally

logger = logging.getLogger(__name__)

GENESIS = "0" * 64


def _compute_row_hash(payload: dict, prev_hash: str) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256((blob + prev_hash).encode("utf-8")).hexdigest()


def log_entry(entry: LogEntry) -> None:
    logger.info(
        "request_id=%s decision=%s risk_score=%.2f",
        entry.request_id, entry.decision.decision.value, entry.decision.risk_score.score,
    )

    row_data = {
        "request_id": entry.request_id,
        "timestamp": entry.timestamp.isoformat(),
        "user_prompt": entry.user_prompt,
        "source_content": entry.source_content,
        "rule_matched": bool(entry.rule_result.matched),
        "rule_patterns": ",".join(entry.rule_result.matched_patterns),
        "rule_signal": entry.rule_result.raw_signal,
        "llm_is_suspicious": bool(entry.llm_result.is_suspicious),
        "llm_reasoning": entry.llm_result.reasoning,
        "llm_signal": entry.llm_result.raw_signal,
        "llm_used_fallback": bool(entry.llm_result.used_fallback),
        "risk_score": entry.decision.risk_score.score,
        "decision": entry.decision.decision.value,
        "explanation": entry.decision.explanation,
    }

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Concurrency-safe: lock logs table in EXCLUSIVE mode within this transaction
                # to prevent race conditions when reading previous hash and appending next record
                cur.execute("LOCK TABLE logs IN EXCLUSIVE MODE")
                cur.execute("SELECT row_hash FROM logs ORDER BY id DESC LIMIT 1")
                row = cur.fetchone()
                prev_hash = row[0] if (row and row[0]) else GENESIS

                row_hash = _compute_row_hash(row_data, prev_hash)

                cur.execute(
                    """
                    INSERT INTO logs (
                        request_id, timestamp, user_prompt, source_content,
                        rule_matched, rule_patterns, rule_signal,
                        llm_is_suspicious, llm_reasoning, llm_signal, llm_used_fallback,
                        risk_score, decision, explanation, prev_hash, row_hash
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        entry.request_id,
                        entry.timestamp,
                        entry.user_prompt,
                        entry.source_content,
                        row_data["rule_matched"],
                        row_data["rule_patterns"],
                        row_data["rule_signal"],
                        row_data["llm_is_suspicious"],
                        row_data["llm_reasoning"],
                        row_data["llm_signal"],
                        row_data["llm_used_fallback"],
                        row_data["risk_score"],
                        row_data["decision"],
                        row_data["explanation"],
                        prev_hash,
                        row_hash,
                    ),
                )
            conn.commit()
    except Exception as exc:
        logger.warning("Database write failed (%s); buffering audit log locally", exc)
        buffer_log_locally(row_data)


def log_constitution_check(entry: LogEntry) -> None:
    result = entry.constitution_result
    if result is None:
        return

    try:
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
    except Exception as exc:
        logger.warning("Constitution check DB log deferred/failed: %s", exc)
