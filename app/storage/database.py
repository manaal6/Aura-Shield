"""
app/storage/database.py

SQLite schema and connection handling. This module is deliberately the
ONLY module allowed to write to the database - pipeline.py and other
modules go through logger.py, which calls into this module. That funnel
is what keeps the audit trail (Trust Boundary 4 in the Phase 1 threat
model) one-directional and tamper-resistant within this POC's scope.
"""
import sqlite3
from contextlib import contextmanager
from app.config import get_settings

_SCHEMA = """
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    user_prompt TEXT NOT NULL,
    source_content TEXT,
    rule_matched INTEGER NOT NULL,
    rule_patterns TEXT,
    rule_signal REAL NOT NULL,
    llm_is_suspicious INTEGER NOT NULL,
    llm_reasoning TEXT,
    llm_signal REAL NOT NULL,
    llm_used_fallback INTEGER NOT NULL,
    risk_score REAL NOT NULL,
    decision TEXT NOT NULL,
    explanation TEXT NOT NULL
);
"""


@contextmanager
def get_connection():
    settings = get_settings()
    conn = sqlite3.connect(settings.database_path)
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with get_connection() as conn:
        conn.execute(_SCHEMA)
        conn.commit()
