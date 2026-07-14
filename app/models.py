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


class RiskScore(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    rule_contribution: float
    llm_contribution: float


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
    decision: SecurityDecision
