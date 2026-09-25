"""
app/engine/provenance.py

First-class provenance scoring for the risk engine. Untrusted content
sources receive a multiplicative risk boost proportional to their existing
risk signal — a zero-risk input stays zero regardless of provenance, but
a moderate-risk input from an untrusted email gets pushed higher.

Migrated from research/provenance.py (Phase 13/14) into the production
pipeline so provenance is SCORED, not just logged.
"""
from __future__ import annotations

import hashlib
from pydantic import BaseModel, Field
from app.config import get_settings


# Trust levels per source type. Higher = more trusted.
# Sources below 0.5 are considered "untrusted" for scoring purposes.
TRUST_LEVELS: dict[str, float] = {
    "SYSTEM": 1.0,
    "DEVELOPER": 0.9,
    "TRUSTED_TOOL": 0.7,
    "USER": 0.6,
    "FILE": 0.4,
    "RETRIEVED_DOCUMENT": 0.3,
    "DATABASE": 0.3,
    "CALENDAR": 0.3,
    "EMAIL": 0.25,
    "UNTRUSTED_TOOL": 0.2,
    "WEB_CONTENT": 0.2,
}


class ProvenanceMetadata(BaseModel):
    """Provenance metadata for a content source."""
    source_type: str = Field(default="USER", description="Content source type")
    trust_level: float = Field(default=0.6, ge=0.0, le=1.0, description="Trust level of the source")
    origin: str = Field(default="", description="Origin identifier for audit trail")
    content_hash: str = Field(default="", description="SHA-256 prefix of content for deduplication")


def get_trust_level(source_type: str) -> float:
    """Look up trust level for a source type. Unknown sources default to 0.3."""
    return TRUST_LEVELS.get(source_type, 0.3)


def compute_content_hash(content: str) -> str:
    """SHA-256 prefix of content for deduplication and audit trail."""
    return hashlib.sha256((content or "").encode()).hexdigest()[:16]


def build_metadata(source_type: str, content: str | None = None, origin: str = "") -> ProvenanceMetadata:
    """Build provenance metadata for a content source."""
    return ProvenanceMetadata(
        source_type=source_type,
        trust_level=get_trust_level(source_type),
        origin=origin,
        content_hash=compute_content_hash(content or ""),
    )


def compute_provenance_adjustment(trust_level: float, raw_risk_score: float) -> float:
    """Compute multiplicative provenance adjustment.

    The adjustment is proportional to BOTH the distrust and the existing risk:
      adjusted = raw * (1.0 + (1.0 - trust_level) * boost_factor)

    Properties:
    - A zero-risk input stays zero regardless of provenance (no false positives)
    - A high-risk input from an untrusted source gets pushed higher
    - A high-risk input from a trusted source is unchanged
    - The boost_factor controls sensitivity (default 0.5)

    Returns the adjustment delta (not the final score), so the caller can
    record it separately for audit purposes.
    """
    settings = get_settings()
    if not settings.provenance_scoring_enabled:
        return 0.0
    if trust_level >= 0.5:
        # Trusted sources get no adjustment
        return 0.0
    boost = raw_risk_score * (1.0 - trust_level) * settings.provenance_boost_factor
    return round(boost, 6)
