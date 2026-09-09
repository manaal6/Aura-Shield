"""
app/models.py

Pydantic schemas defining the data contracts between AURA Shield modules.
Typed schemas at every module boundary mean malformed data is rejected
immediately at the boundary, not silently propagated downstream.
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AttackCategory(str, Enum):
    """Used for benchmark labeling (Phase 4) - not inferred at runtime."""
    DIRECT_INJECTION = "direct_injection"
    INDIRECT_INJECTION = "indirect_injection"
    JAILBREAK = "jailbreak"
    BENIGN = "benign"


class Decision(str, Enum):
    ALLOW = "allow"
    REVIEW = "review"
    BLOCK = "block"


class IncomingRequest(BaseModel):
    user_prompt: str = Field(..., min_length=1, description="Direct text from the end user")
    source_content: Optional[str] = Field(default=None, description="Untrusted external content (document/tool output), if any")
    request_id: Optional[str] = Field(default=None, description="Optional caller-supplied ID for correlation in logs")


class RuleDetectionResult(BaseModel):
    matched: bool
    matched_patterns: list[str] = Field(default_factory=list)
    raw_signal: float = Field(ge=0.0, le=1.0)


class LLMAnalysisResult(BaseModel):
    is_suspicious: bool
    reasoning: str = Field(..., description="Model's stated justification - required for explainability")
    raw_signal: float = Field(ge=0.0, le=1.0)
    used_fallback: bool = Field(default=False, description="True if the LLM call could not be made and a safe fallback was used")


class ConstitutionVerdict(BaseModel):
    principle_id: str
    violated: bool
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str = Field(..., description="Human-readable reason for this verdict - never empty")


class ConstitutionCheckResult(BaseModel):
    constitution_version: int
    principles_evaluated: list[str] = Field(default_factory=list)
    verdicts: list[ConstitutionVerdict] = Field(default_factory=list)
    raw_signal: float = Field(ge=0.0, le=1.0, description="0.0 if no violation; otherwise max violated-principle confidence")
    reasoning: str = Field(..., description="Human-readable summary of the check outcome")
    used_fallback: bool = Field(default=False, description="True if the check could not run and a neutral signal was contributed")


class RiskScore(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    rule_contribution: float
    llm_contribution: float
    constitution_contribution: float = 0.0


class SecurityDecision(BaseModel):
    decision: Decision
    risk_score: RiskScore
    explanation: str = Field(..., description="Human-readable reason - never empty")


class LogEntry(BaseModel):
    request_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_prompt: str
    source_content: Optional[str] = None
    rule_result: RuleDetectionResult
    llm_result: LLMAnalysisResult
    constitution_result: Optional[ConstitutionCheckResult] = None
    decision: SecurityDecision


class PendingPrinciple(BaseModel):
    id: Optional[int] = None
    principle_id: str
    principle_text: str
    rationale: str
    status: str = Field(default="pending_review", description="pending_review | active | rejected")
    triggered_by: dict = Field(default_factory=dict, description="The missed case that prompted this draft: request_id, prompt, category, risk_score, reason")
    drafted_reasoning: str = ""
    drafted_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_reason: Optional[str] = None
