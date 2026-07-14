"""
app/config.py

Centralized configuration for AURA Shield.
All security-relevant thresholds live here, not scattered across modules,
so the policy surface is auditable in one file.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # --- External services ---
    groq_api_key: str = Field(default="", description="Groq API key, loaded from .env")
    groq_model: str = Field(default="llama-3.1-8b-instant", description="Model used for both the protected LLM call and the security analyzer")

    # --- Storage ---
    database_path: str = Field(default="aura_shield.db", description="Path to the SQLite database file")

    # --- Risk scoring weights ---
    # Both signals are normalized to 0.0-1.0 before weighting.
    # Weights sum to 1.0; documented here so the scoring logic is auditable.
    rule_signal_weight: float = Field(default=0.4, description="Weight given to the rule-based detector's signal")
    llm_signal_weight: float = Field(default=0.6, description="Weight given to the LLM security analyzer's signal")

    # --- Policy thresholds (0.0-1.0 risk score scale) ---
    threshold_block: float = Field(default=0.75, description="Risk score at or above this value is blocked")
    threshold_review: float = Field(default=0.40, description="Risk score at or above this value (but below block) is flagged for human review")
    # Anything below threshold_review is allowed automatically.

    # --- App behavior ---
    log_level: str = Field(default="INFO")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor - constructed once per process."""
    return Settings()
