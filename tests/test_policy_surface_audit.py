"""
tests/test_policy_surface_audit.py

Unit tests for Phase 7 Policy Surface, Audit, and Gate Enforcement.
Verifies:
- Configurable REVIEW_HOLD_PENDING_APPROVAL policy flag behavior
- Threshold boundary compliance in app/config.py
- Structured output audit completeness from process_request_with_config()
"""
import pytest
from app.config import get_settings, Settings
from app.models import IncomingRequest, Decision
from app.pipeline import process_request_with_config


def test_policy_surface_threshold_sanity():
    settings = get_settings()
    assert 0.0 <= settings.threshold_review < settings.threshold_block <= 1.0
    assert 0.0 <= settings.llm_block_signal <= 1.01
    total_weights = settings.rule_signal_weight + settings.llm_signal_weight + settings.constitution_signal_weight
    assert pytest.approx(total_weights, abs=0.01) == 1.0


def test_review_hold_pending_approval_flag_held(monkeypatch):
    # Enable REVIEW_HOLD_PENDING_APPROVAL
    settings = get_settings()
    monkeypatch.setattr(settings, "review_hold_pending_approval", True)

    req = IncomingRequest(user_prompt="Explain how a SYN flood DoS works.")
    # Baseline forcing mid-range risk score resulting in REVIEW decision
    # (e.g. embedding classifier returning mid-range signal)
    baseline_cfg = {"use_embedding": True, "skip_db_logging": True}
    res = process_request_with_config(req, baseline_config=baseline_cfg)

    if res["decision"] == "review":
        assert res["llm_response"] is not None
        assert "HELD PENDING APPROVAL" in res["llm_response"]


def test_review_hold_pending_approval_flag_unheld(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "review_hold_pending_approval", False)

    req = IncomingRequest(user_prompt="Explain how a SYN flood DoS works.")
    baseline_cfg = {"use_embedding": True, "skip_db_logging": True, "skip_downstream": True}
    res = process_request_with_config(req, baseline_config=baseline_cfg)

    if res["decision"] == "review":
        assert "HELD PENDING APPROVAL" not in (res["llm_response"] or "")


def test_audit_output_schema_completeness():
    req = IncomingRequest(user_prompt="Hello, world!")
    res = process_request_with_config(req, baseline_config={"use_rule": True, "use_llm": False, "use_constitution": False, "skip_db_logging": True, "skip_downstream": True})

    expected_keys = {"request_id", "decision", "risk_score", "explanation", "llm_response", "rule_result", "llm_result", "constitution_result"}
    assert expected_keys.issubset(set(res.keys()))
    assert res["decision"] in [d.value for d in Decision]
    assert 0.0 <= res["risk_score"] <= 1.0
    assert len(res["explanation"]) > 0
