"""
research/schemas.py

Research-grade data schemas for AURA Shield experimental platform.
These extend (and do not replace) the production schemas in app/models.py.

Status: IMPLEMENTED (Phase 2 — Experimental Infrastructure)
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ─────────────────────────── enums ────────────────────────────────────────────


class AttackFamily(str, Enum):
    """Richer attack taxonomy than the 4-category AttackCategory in app/models.py."""
    DIRECT_INJECTION = "direct_injection"
    INDIRECT_INJECTION = "indirect_injection"
    JAILBREAK_PERSONA = "jailbreak_persona"
    JAILBREAK_ENCODING = "jailbreak_encoding"
    JAILBREAK_MULTILINGUAL = "jailbreak_multilingual"
    MULTI_TURN_MANIPULATION = "multi_turn_manipulation"
    OBFUSCATION = "obfuscation"
    TOOL_INJECTION = "tool_injection"
    AUTHORIZATION_ATTACK = "authorization_attack"
    CONTEXT_FLOODING = "context_flooding"
    POLICY_TARGETING = "policy_targeting"
    BENIGN_GENERAL = "benign_general"
    BENIGN_CYBERSECURITY = "benign_cybersecurity"


class DatasetSplit(str, Enum):
    DEV = "dev"
    ADAPTATION = "adaptation"
    TEST = "test"


class GroundTruthLabel(str, Enum):
    ATTACK = "attack"
    BENIGN = "benign"


class EnforcementAction(str, Enum):
    ALLOW = "allow"
    REVIEW = "review"
    BLOCK = "block"
    HOLD_PENDING_APPROVAL = "hold_pending_approval"


class DetectorName(str, Enum):
    RULE = "rule_detector"
    LLM_ANALYZER = "llm_analyzer"
    CONSTITUTION = "constitution_checker"
    BLENDED = "blended"


class BaselineConfig(str, Enum):
    """Identifies which detector combination is active in an experiment run."""
    A_RULE_ONLY = "A_rule_only"
    B_LLM_ONLY = "B_llm_only"
    C_CONSTITUTION_ONLY = "C_constitution_only"
    D_RULE_LLM = "D_rule_llm"
    E_RULE_CONSTITUTION = "E_rule_constitution"
    F_LLM_CONSTITUTION = "F_llm_constitution"
    G_FULL_BLENDED = "G_full_blended"
    H_PROMPT_GUARDRAIL = "H_prompt_guardrail"
    I_EMBEDDING = "I_embedding"


# ─────────────────────────── prompt record ────────────────────────────────────


class PromptRecord(BaseModel):
    """
    Research-grade prompt record. Every benchmark prompt should have all
    fields populated. Optional fields may be None for legacy 40-prompt entries.

    Status: IMPLEMENTED
    """
    prompt_id: str = Field(..., description="Unique stable ID, e.g. di-001")
    source: str = Field(..., description="Dataset origin: 'manual', 'generated', 'garak', etc.")
    attack_family: AttackFamily
    attack_subtype: Optional[str] = Field(
        default=None,
        description="Fine-grained subtype, e.g. 'base64_encoded', 'urdu_english_switch'",
    )
    language: str = Field(default="en", description="Primary language code (ISO 639-1)")
    encoding: Optional[str] = Field(
        default=None,
        description="Encoding trick applied if any: 'base64', 'rot13', 'unicode_homoglyph', etc.",
    )
    conversation_id: Optional[str] = Field(
        default=None, description="Multi-turn: shared ID for all turns in a conversation"
    )
    turn_id: Optional[int] = Field(
        default=None, description="Multi-turn: 1-indexed turn number within conversation"
    )
    content: str = Field(..., description="The user_prompt (or the injected turn text)")
    source_content: Optional[str] = Field(
        default=None, description="Untrusted external content (document, email, tool output)"
    )
    intended_task: Optional[str] = Field(
        default=None,
        description="What a legitimate user would legitimately want from this prompt",
    )
    expected_behavior: str = Field(
        ..., description="'block_or_review' or 'allow'"
    )
    ground_truth_label: GroundTruthLabel
    severity: Optional[str] = Field(
        default=None, description="'low', 'medium', 'high', 'critical'"
    )
    tool_context: Optional[dict[str, Any]] = Field(
        default=None,
        description="For tool-injection attacks: the simulated tool invocation context",
    )
    retrieved_context: Optional[str] = Field(
        default=None, description="RAG-style retrieved content that the prompt was paired with"
    )
    split: DatasetSplit = Field(default=DatasetSplit.DEV)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def content_hash(self) -> str:
        """Stable hash of the prompt content for deduplication and audit traces."""
        combined = (self.content or "") + (self.source_content or "")
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()[:16]


# ─────────────────────────── detection result ─────────────────────────────────


class ConstitutionalVerdictRecord(BaseModel):
    """Per-principle verdict, research-grade (extends ConstitutionVerdict in app/models.py)."""
    principle_id: str
    violated: bool
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str


class DetectionResult(BaseModel):
    """
    Per-detector result enriched with metadata for reproducible experiments.

    Status: IMPLEMENTED
    """
    detector_name: DetectorName
    model_name: Optional[str] = Field(
        default=None,
        description="Model identifier used (None for rule detector)",
    )
    detector_version: str = Field(
        default="1.0",
        description="Version tag for the detector code/config in this run",
    )
    score: float = Field(ge=0.0, le=1.0, description="Raw signal 0.0-1.0")
    label: Optional[str] = Field(
        default=None, description="'suspicious' / 'clean' / 'fallback'"
    )
    reasoning_summary: Optional[str] = None
    constitutional_verdicts: list[ConstitutionalVerdictRecord] = Field(default_factory=list)
    matched_patterns: list[str] = Field(
        default_factory=list,
        description="Rule-detector: matched category names",
    )
    used_fallback: bool = Field(default=False)
    timestamp: datetime = Field(default_factory=_utcnow)
    latency_ms: float = Field(default=0.0, ge=0.0)


# ─────────────────────────── policy decision ──────────────────────────────────


class PolicyDecision(BaseModel):
    """
    Enriched policy decision for experiment tracing.

    Status: IMPLEMENTED
    """
    decision: EnforcementAction
    risk_score: float = Field(ge=0.0, le=1.0)
    rule_contribution: float
    llm_contribution: float
    constitution_contribution: float
    triggered_signals: list[str] = Field(
        default_factory=list,
        description="Which signals contributed to this decision",
    )
    policy_version: str = Field(
        default="1.0",
        description="Policy config version at decision time",
    )
    constitution_version: Optional[int] = None
    approval_required: bool = False
    enforcement_action: EnforcementAction = EnforcementAction.ALLOW
    explanation: str = ""
    timestamp: datetime = Field(default_factory=_utcnow)


# ─────────────────────────── adaptive update ──────────────────────────────────


class AdaptiveUpdate(BaseModel):
    """
    Full audit record for one adaptive constitution update.
    Tracks provenance, validation, and rollback information.

    Status: IMPLEMENTED (schema only; full experiment in Phase 9)
    """
    update_id: str
    triggering_case_id: str = Field(
        ...,
        description="The request_id or prompt_id of the miss that triggered this draft",
    )
    triggering_case_source: str = Field(
        ...,
        description="'human_flag', 'near_threshold', 'benchmark_false_negative'",
    )
    previous_constitution_version: int
    candidate_principle_id: str
    candidate_principle_text: str
    rationale: str
    provenance: str = Field(
        ...,
        description="How this candidate was generated: 'llm_draft', 'human_authored', etc.",
    )
    # Validation results (run before human review in Phase 9)
    syntax_valid: Optional[bool] = None
    consistency_check_passed: Optional[bool] = None
    contradiction_detected: Optional[bool] = None
    scope_valid: Optional[bool] = None
    provenance_verified: Optional[bool] = None
    validation_notes: str = ""
    # Human review
    human_approval: Optional[bool] = None
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    # Post-approval
    new_constitution_version: Optional[int] = None
    regression_test_passed: Optional[bool] = None
    held_out_recall_change: Optional[float] = None
    held_out_fpr_change: Optional[float] = None
    benign_utility_change: Optional[float] = None
    over_refusal_change: Optional[float] = None
    rollback_reference: Optional[str] = Field(
        default=None,
        description="Constitution version to roll back to if this update is reversed",
    )
    timestamp: datetime = Field(default_factory=_utcnow)


# ─────────────────────────── experiment spec ──────────────────────────────────


class ModelRoles(BaseModel):
    """Which model handles which role in this experiment."""
    analyzer: str = Field(default="groq/openai/gpt-oss-120b")
    constitution: str = Field(default="groq/openai/gpt-oss-120b")
    downstream: str = Field(default="groq/openai/gpt-oss-120b")
    evaluator: str = Field(default="groq/openai/gpt-oss-120b")
    attacker: Optional[str] = None


class ExperimentSpec(BaseModel):
    """
    Complete, self-contained specification for a reproducible experiment run.
    Must be declared BEFORE running the experiment.

    Status: IMPLEMENTED
    """
    experiment_id: str
    experiment_name: str
    hypothesis: str = Field(
        ...,
        description="Explicitly stated hypothesis BEFORE running the experiment. Do not modify after seeing results.",
    )
    independent_variables: list[str]
    dependent_variables: list[str]
    control_baseline: BaselineConfig
    dataset_split: DatasetSplit
    dataset_files: list[str]
    model_roles: ModelRoles = Field(default_factory=ModelRoles)
    baseline_config: BaselineConfig = BaselineConfig.G_FULL_BLENDED
    random_seed: Optional[int] = None
    max_prompts: Optional[int] = None
    expected_risks: list[str] = Field(default_factory=list)
    reproducibility_notes: str = ""
    created_at: datetime = Field(default_factory=_utcnow)
    run_at: Optional[datetime] = None
    output_dir: Optional[str] = None
    tags: list[str] = Field(default_factory=list)

    @field_validator("hypothesis")
    @classmethod
    def hypothesis_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Hypothesis must be stated before running the experiment.")
        return v


# ─────────────────────────── experiment result ────────────────────────────────


class PerPromptResult(BaseModel):
    """One row in the raw results for a benchmark run."""
    prompt_id: str
    attack_family: str
    split: str
    ground_truth_label: str
    content_hash: str
    detection_results: list[DetectionResult]
    policy_decision: PolicyDecision
    downstream_response: Optional[str] = None
    evaluator_verdict: Optional[str] = Field(
        default=None,
        description="'safe' / 'unsafe' / 'unknown' — from a separate evaluator model or human review",
    )
    attack_succeeded: Optional[bool] = Field(
        default=None,
        description=(
            "True if the attack caused PROHIBITED OR UNSAFE DOWNSTREAM BEHAVIOR. "
            "NOT merely 'detector said benign'. ASR is computed from this field."
        ),
    )
    latency_ms: float = 0.0
    llm_calls: int = 0
    used_fallback: bool = False
    timestamp: datetime = Field(default_factory=_utcnow)
    notes: str = ""


class ExperimentResult(BaseModel):
    """Aggregate result record stored alongside the raw JSONL results."""
    experiment_id: str
    experiment_spec: ExperimentSpec
    total_prompts: int
    real_llm_calls_used: bool
    metrics: dict[str, Any]
    per_family_metrics: dict[str, Any] = Field(default_factory=dict)
    confusion_matrix: dict[str, int] = Field(default_factory=dict)
    latency: dict[str, Any] = Field(default_factory=dict)
    what_this_demonstrates: str = Field(
        default="",
        description="Required: explicit statement of what these results show.",
    )
    what_this_does_not_demonstrate: str = Field(
        default="",
        description="Required: explicit statement of what these results do NOT show.",
    )
    limitations: list[str] = Field(default_factory=list)
    raw_results_path: str = ""
    completed_at: datetime = Field(default_factory=_utcnow)
