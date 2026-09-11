"""
tests/test_cross_model.py

Unit tests for Phase 5 cross-model independence specifications.
Verifies:
- All 5 cross-model JSON specs exist and parse correctly
- ModelRoles properties resolve properly in app/config.py
- BenchmarkRunner initializes role models without exceptions
"""
from pathlib import Path
import pytest
from app.config import get_settings
from research.experiment import load_spec
from research.runner import BenchmarkRunner

CROSS_DIR = Path(__file__).resolve().parent.parent / "experiments" / "cross_model"


def test_all_cross_model_specs_exist():
    expected_files = [
        "same_model_homogeneous.json",
        "heterogeneous_analyzer_fast.json",
        "heterogeneous_constitution_heavy.json",
        "heterogeneous_decoupled_target.json",
        "full_heterogeneous_pipeline.json",
    ]
    for filename in expected_files:
        assert (CROSS_DIR / filename).is_file(), f"Missing spec file: {filename}"


def test_cross_model_specs_valid():
    spec_files = list(CROSS_DIR.glob("*.json"))
    assert len(spec_files) >= 5
    for sf in spec_files:
        spec = load_spec(sf)
        assert spec.model_roles.analyzer is not None
        assert spec.model_roles.constitution is not None
        assert spec.model_roles.downstream is not None
        assert spec.model_roles.evaluator is not None
        assert len(spec.hypothesis) > 10


def test_model_role_fallback_properties():
    settings = get_settings()
    # When model_analyzer is empty string, analyzer_model falls back to groq_model
    assert settings.analyzer_model == settings.groq_model
    assert settings.constitution_model == settings.groq_model
    assert settings.downstream_model == settings.groq_model
    assert settings.evaluator_model == settings.groq_model


def test_cross_model_dry_run():
    spec = load_spec(CROSS_DIR / "full_heterogeneous_pipeline.json")
    spec.max_prompts = 2
    runner = BenchmarkRunner(spec, verbose=False)
    rows, result = runner.run(dry_run=True)
    assert rows == []
    assert result.experiment_id == "full_heterogeneous_pipeline"
