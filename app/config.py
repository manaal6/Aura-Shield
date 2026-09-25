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
    # SDK retry count on transient errors (429s, 5xx). Default 1 keeps serving
    # latency bounded; research runs set GROQ_MAX_RETRIES higher so a
    # rate-limited benchmark waits out the window instead of silently
    # degrading into offline fallback results.
    groq_max_retries: int = Field(default=1, description="Groq SDK max_retries for transient errors")

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
    threshold_block: float = Field(default=0.75, description="Risk score at or above this value is blocked (implemented policy choice; NOT empirically optimized)")
    threshold_review: float = Field(default=0.40, description="Risk score at or above this value (but below block) is flagged for human review (implemented policy choice; NOT empirically optimized)")
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

    # --- Fusion strategy ---
    # "max" = score is max(rule, llm, constitution) — prevents dilution.
    # "weighted_avg" = legacy weighted-average blend (pre-v2 behavior).
    fusion_strategy: str = Field(default="max", description="Score fusion: 'max' (max-of-signals, default) or 'weighted_avg' (legacy weighted average)")

    # --- Constitution-specific thresholds ---
    # Lower than the LLM escalation threshold because constitution violations
    # are citable against a named principle, so confidence is more calibrated.
    constitution_block_signal: float = Field(default=0.70, description="Constitution signal at or above this blocks outright (implemented policy choice; NOT empirically optimized)")
    constitution_review_signal: float = Field(default=0.40, description="Constitution signal at or above this forces REVIEW (implemented policy choice; NOT empirically optimized)")

    # --- LLM stability (majority-vote) ---
    llm_stability_votes: int = Field(default=3, description="Number of LLM calls for majority-vote stabilization")
    llm_stability_enabled: bool = Field(default=False, description="Enable majority-vote LLM stabilization (expensive, opt-in)")

    # --- Provenance scoring ---
    provenance_boost_factor: float = Field(default=0.5, description="Multiplicative provenance risk boost factor for untrusted sources")
    provenance_scoring_enabled: bool = Field(default=True, description="Enable provenance-weighted risk scoring")

    # --- Graduated fail-safe ---
    graduated_failsafe_enabled: bool = Field(default=True, description="Graduated fail-safe during LLM outage: classify by request characteristics instead of blanket REVIEW")

    # --- Provider settings (optional — Groq-only by default) ---
    openai_api_key: str = Field(default="", description="Optional OpenAI API key for provider fallback")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model for fallback (optional)")
    provider_fallback_enabled: bool = Field(default=False, description="Enable multi-provider fallback (requires secondary provider keys)")
    analyzer_providers: str = Field(default="groq", description="Comma-separated provider priority for analyzer role")
    constitution_providers: str = Field(default="groq", description="Comma-separated provider priority for constitution role")

    # --- Governance authorization ( constitution approval signing ) ---
    # Dedicated HMAC secret for constitution-approval tokens. This MUST be
    # separate from any provider API key: provider credentials authenticate
    # against an external service, while this secret guards local
    # authorization integrity. Never fall back to a Groq key or a default.
    approval_hmac_secret: str = Field(
        default="",
        validation_alias="AURA_APPROVAL_HMAC_SECRET",
        description="Dedicated HMAC secret for constitution approval tokens (AURA_APPROVAL_HMAC_SECRET). Required for approvals; never a provider key.",
    )

    def require_approval_hmac_secret(self) -> str:
        """Return the approval secret or fail loudly — no silent defaults."""
        if not self.approval_hmac_secret:
            raise RuntimeError(
                "AURA_APPROVAL_HMAC_SECRET is not set. Constitution approvals require a dedicated "
                "HMAC secret (set it in .env); the system refuses to sign with a provider key or default."
            )
        return self.approval_hmac_secret

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
