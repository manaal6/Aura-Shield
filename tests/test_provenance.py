"""
tests/test_provenance.py

Unit tests for production provenance-weighted risk scoring (W#9).
Verifies:
- Trust levels per source type
- Multiplicative boost logic (zero raw risk stays zero)
- Untrusted sources scale higher on non-zero risk
"""
from app.engine.provenance import (
    get_trust_level,
    compute_provenance_adjustment,
    build_metadata,
    compute_content_hash,
)
from app.models import RuleDetectionResult, LLMAnalysisResult
from app.engine.risk_engine import compute_risk


def test_trust_levels_bounds():
    assert get_trust_level("SYSTEM") == 1.0
    assert get_trust_level("USER") == 0.6
    assert get_trust_level("EMAIL") == 0.25
    assert get_trust_level("UNTRUSTED_TOOL") == 0.2
    assert get_trust_level("UNKNOWN_SOURCE") == 0.3


def test_zero_risk_stays_zero_regardless_of_provenance():
    # Crucial property: no false positives created by provenance alone
    adj = compute_provenance_adjustment(trust_level=0.1, raw_risk_score=0.0)
    assert adj == 0.0

    rule = RuleDetectionResult(matched=False, matched_patterns=[], raw_signal=0.0)
    llm = LLMAnalysisResult(is_suspicious=False, reasoning="clean", raw_signal=0.0)
    score = compute_risk(rule, llm, source_type="EMAIL")
    assert score.score == 0.0
    assert score.provenance_adjustment == 0.0


def test_untrusted_source_boosts_moderate_risk():
    rule = RuleDetectionResult(matched=True, matched_patterns=["suspicious"], raw_signal=0.5)
    llm = LLMAnalysisResult(is_suspicious=True, reasoning="moderate", raw_signal=0.4)
    # USER trust is 0.6 (>= 0.5, so no boost)
    user_score = compute_risk(rule, llm, source_type="USER")

    # EMAIL trust is 0.25 (< 0.5, so boost is applied)
    email_score = compute_risk(rule, llm, source_type="EMAIL")

    assert email_score.score > user_score.score
    assert email_score.provenance_adjustment > 0.0


def test_content_hash_and_metadata_deterministic():
    meta = build_metadata("EMAIL", "test content", origin="inbox")
    assert meta.source_type == "EMAIL"
    assert meta.trust_level == 0.25
    assert meta.origin == "inbox"
    assert len(meta.content_hash) == 16
