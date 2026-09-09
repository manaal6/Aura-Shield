"""
tests/test_constitution_and_adaptive.py

Unit tests for the constitution layer and the adaptive loop's review
mechanics. These tests do NOT hit the network - the ConstitutionChecker's
LLM call path is exercised in the benchmark/integration runs, not here.
"""
import json
import pytest

from app.engine.risk_engine import compute_risk
from app.engine.policy_engine import decide
from app.models import (
    ConstitutionCheckResult,
    ConstitutionVerdict,
    LLMAnalysisResult,
    RuleDetectionResult,
)


def _rule(signal: float) -> RuleDetectionResult:
    return RuleDetectionResult(matched=signal > 0, matched_patterns=[], raw_signal=signal)


def _llm(signal: float) -> LLMAnalysisResult:
    return LLMAnalysisResult(is_suspicious=signal > 0.5, reasoning="test", raw_signal=signal)


def _constitution(signal: float) -> ConstitutionCheckResult:
    verdicts = []
    if signal > 0:
        verdicts = [ConstitutionVerdict(
            principle_id="C1-no-override", violated=True,
            confidence=signal, explanation="test explanation",
        )]
    return ConstitutionCheckResult(
        constitution_version=1,
        principles_evaluated=["C1-no-override"],
        verdicts=verdicts,
        raw_signal=signal,
        reasoning="test",
    )


# ---------------------------------------------------------- risk engine


def test_three_signal_blend_formula():
    score = compute_risk(_rule(0.8), _llm(0.9), _constitution(1.0))
    # 0.8*0.35 + 0.9*0.45 + 1.0*0.20 = 0.885
    assert score.score == pytest.approx(0.885)
    assert score.constitution_contribution == pytest.approx(0.20)


def test_no_constitution_check_redistributes_weight():
    score = compute_risk(_rule(0.8), _llm(0.9))
    # constitution weight redistributed proportionally: (0.8*0.35 + 0.9*0.45) / 0.8
    assert score.score == pytest.approx((0.8 * 0.35 + 0.9 * 0.45) / 0.80)
    assert score.constitution_contribution == 0.0


def test_clean_constitution_check_contributes_zero():
    score = compute_risk(_rule(0.0), _llm(0.0), _constitution(0.0))
    assert score.score == pytest.approx(0.0)
    assert score.constitution_contribution == 0.0


# ---------------------------------------------------------- policy engine


def test_constitution_escalation_blocks():
    score = compute_risk(_rule(0.0), _llm(0.0), _constitution(0.99))
    result = decide(score, _llm(0.0), _constitution(0.99))
    assert result.decision.value == "block"
    assert "C1-no-override" in result.explanation


def test_low_confidence_violation_does_not_escalate():
    score = compute_risk(_rule(0.0), _llm(0.0), _constitution(0.5))
    result = decide(score, _llm(0.0), _constitution(0.5))
    assert result.decision.value == "allow"


# ---------------------------------------------------------- constitution file/seed


def test_seed_file_is_well_formed():
    data = json.loads(
        (pytest.importorskip("pathlib").Path("constitution.json")).read_text(encoding="utf-8")
    )
    assert data["version"] >= 1
    required = {"id", "version_added", "principle_text", "rationale", "status"}
    for p in data["principles"]:
        assert required <= set(p), f"principle {p.get('id')} missing fields"
        assert p["status"] in ("active", "deprecated")
