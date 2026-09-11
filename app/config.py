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
    groq_model: str = Field(default="openai/gpt-oss-120b", description="Model used for both the protected LLM call and the security analyzer")

    # --- Storage ---
    # database_path is kept only so the one-off sqlite->Postgres migration
    # script can still open the old local file. The running app no longer
    # reads or writes it.
    database_path: str = Field(default="aura_shield.db", description="Path to the legacy local SQLite database file (migration only)")
    database_url: str = Field(default="", description="Supabase Postgres connection string (Session Pooler URI), loaded from .env or Streamlit secrets")

    # --- Risk scoring weights ---
    # Both signals are normalized to 0.0-1.0 before weighting.
    # Weights sum to 1.0; documented here so the scoring logic is auditable.
    # Weights sum to 1.0 across the three signals; documented here so the
    # scoring logic is auditable. Constitution weight is absorbed
    # proportionally by the other two when no constitution check ran.
    rule_signal_weight: float = Field(default=0.35, description="Weight given to the rule-based detector's signal")
    llm_signal_weight: float = Field(default=0.45, description="Weight given to the LLM security analyzer's signal")
    constitution_signal_weight: float = Field(default=0.20, description="Weight given to the constitution checker's violation signal")

    # --- Policy thresholds (0.0-1.0 risk score scale) ---
    threshold_block: float = Field(default=0.75, description="Risk score at or above this value is blocked")
    threshold_review: float = Field(default=0.40, description="Risk score at or above this value (but below block) is flagged for human review")
    # Anything below threshold_review is allowed automatically.

    # Escalation rule: a near-certain LLM detection blocks even when the
    # blended score falls short (e.g. rule signal 0 caps the blend at
    # llm_signal_weight). Set to 1.01 to disable.
    llm_block_signal: float = Field(default=0.90, description="LLM raw signal at or above this value blocks outright, regardless of blended score")

    # --- Model roles for research / cross-model independence ---
    # When empty, all roles fall back to groq_model for 100% backward compatibility.
    model_analyzer: str = Field(default="", description="Model used for LLM security analyzer (falls back to groq_model if empty)")
    model_constitution: str = Field(default="", description="Model used for constitution checker (falls back to groq_model if empty)")
    model_downstream: str = Field(default="", description="Model used for downstream protected LLM (falls back to groq_model if empty)")
    model_evaluator: str = Field(default="", description="Model used for downstream safety evaluation (falls back to groq_model if empty)")

    # --- Enforcement options ---
    review_hold_pending_approval: bool = Field(default=False, description="If True, REVIEW requests are held and not forwarded to downstream LLM")
    experiment_results_dir: str = Field(default="results", description="Directory for storing research experiment results")

    # --- Analyzer failure policy ---
    # Controls what happens when the LLM analyzer cannot produce a verdict
    # (no API key, network failure, malformed output, or timeout).
    # "review"  → route to REVIEW regardless of blended score (default, fail-safe).
    # "pass"    → fall through to threshold bands using the 0.3 fallback signal
    #             (offline benchmarking mode — acknowledge this in experiment labels).
    llm_failure_policy: str = Field(
        default="review",
        description=(
            "What to do when the LLM analyzer returns used_fallback=True: "
            "'review' routes to REVIEW (default, fail-safe); "
            "'pass' falls through to threshold bands (offline/benchmark mode only)."
        ),
    )

    # --- App behavior ---
    log_level: str = Field(default="INFO")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def analyzer_model(self) -> str:
        return self.model_analyzer if self.model_analyzer else self.groq_model

    @property
    def constitution_model(self) -> str:
        return self.model_constitution if self.model_constitution else self.groq_model

    @property
    def downstream_model(self) -> str:
        return self.model_downstream if self.model_downstream else self.groq_model

    @property
    def evaluator_model(self) -> str:
        return self.model_evaluator if self.model_evaluator else self.groq_model


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor - constructed once per process."""
    return Settings()
