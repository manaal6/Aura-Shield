"""
research/experiment.py

Experiment configuration loading, validation, and lifecycle management.

Every AURA Shield research experiment MUST have a declared ExperimentSpec
before it runs. This module enforces that discipline:
- Specs are loaded from YAML files in experiments/
- Hypotheses must be non-empty strings declared BEFORE the run
- Results are saved to timestamped directories that are never overwritten
- The spec is always saved alongside the results for reproducibility

Status: IMPLEMENTED (Phase 2 - Experimental Infrastructure)
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    import yaml
    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False

from research.schemas import (
    BaselineConfig,
    DatasetSplit,
    ExperimentResult,
    ExperimentSpec,
    ModelRoles,
)

# Repo root relative to this file
_REPO_ROOT = Path(__file__).parent.parent
_RESULTS_ROOT = _REPO_ROOT / "results"
_EXPERIMENTS_ROOT = _REPO_ROOT / "experiments"
_DATA_ROOT = _REPO_ROOT / "data" / "benchmark"
_SPLITS_FILE = _DATA_ROOT / "splits.json"


# ─────────────────────────── spec loading ─────────────────────────────────────


def load_spec(path: str | Path) -> ExperimentSpec:
    """
    Load an ExperimentSpec from a YAML or JSON file.
    Raises ValueError if hypothesis is empty or required fields are missing.
    """
    path = Path(path)
    if path.suffix in (".yaml", ".yml"):
        if not _HAS_YAML:
            raise ImportError(
                "PyYAML is not installed. Install it with: pip install pyyaml"
            )
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    elif path.suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        raise ValueError(f"Unsupported spec file format: {path.suffix}")

    # Inject defaults for model_roles if not present
    if "model_roles" not in data:
        data["model_roles"] = {}

    spec = ExperimentSpec(**data)
    return spec


def spec_from_dict(d: dict) -> ExperimentSpec:
    """Create an ExperimentSpec from a plain dict (for inline experiments)."""
    return ExperimentSpec(**d)


# ─────────────────────────── output directory ─────────────────────────────────


def make_output_dir(experiment_id: str) -> Path:
    """
    Create a timestamped output directory for this experiment.
    Format: results/{experiment_id}_{YYYYMMDD_HHMMSS}/

    Never overwrites an existing directory.
    Returns the created Path.
    """
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = _RESULTS_ROOT / f"{experiment_id}_{ts}"
    out_dir.mkdir(parents=True, exist_ok=False)
    return out_dir


def save_spec(spec: ExperimentSpec, out_dir: Path) -> None:
    """Save the experiment spec alongside the results for reproducibility."""
    spec_dict = spec.model_dump(mode="json")
    (out_dir / "experiment_spec.json").write_text(
        json.dumps(spec_dict, indent=2, default=str), encoding="utf-8"
    )


def save_result(result: ExperimentResult, out_dir: Path) -> None:
    """Save the aggregate experiment result as experiment_result.json."""
    result_dict = result.model_dump(mode="json")
    (out_dir / "experiment_result.json").write_text(
        json.dumps(result_dict, indent=2, default=str), encoding="utf-8"
    )


# ─────────────────────────── split guard ──────────────────────────────────────


def load_splits_manifest() -> dict:
    """Load the benchmark splits manifest from data/benchmark/splits.json."""
    if not _SPLITS_FILE.exists():
        return {}
    return json.loads(_SPLITS_FILE.read_text(encoding="utf-8"))


def assert_split_not_contaminated(
    dataset_files: list[str],
    adaptive_loop_mode: bool,
) -> None:
    """
    Enforce split contamination rules.

    When adaptive_loop_mode=True, raises ValueError if any file is from the
    test/ split. This prevents the adaptive loop from ever seeing held-out data.
    """
    if not adaptive_loop_mode:
        return

    test_paths = [str(p) for p in (_DATA_ROOT / "test").rglob("*.jsonl")]
    test_names = {Path(p).name for p in test_paths}
    test_stems = {Path(p).stem for p in test_paths}

    for f in dataset_files:
        p = Path(f)
        if "test" in str(p).lower() or p.name in test_names or p.stem in test_stems:
            raise ValueError(
                f"CONTAMINATION GUARD TRIGGERED: dataset file '{f}' appears to be from "
                "the held-out test split, but adaptive_loop_mode=True. "
                "The adaptive loop must NEVER see held-out data. "
                "Use files from data/benchmark/adaptation/ for adaptive loop input."
            )


# ─────────────────────────── cost estimation ──────────────────────────────────


def estimate_run_cost(
    n_prompts: int,
    baseline_config: BaselineConfig,
    model_roles: Optional[ModelRoles] = None,
) -> dict[str, Any]:
    """
    Estimate the number of LLM API calls and approximate token cost
    for a benchmark run before it starts.

    Returns a dict with:
      - n_prompts
      - llm_calls_per_prompt
      - llm_calls_total
      - expensive (bool): True if the run requires RUN_EXPENSIVE_EXPERIMENT=true
      - message: human-readable summary

    This is a CONSERVATIVE ESTIMATE. Actual calls depend on fallback behavior.
    """
    # Determine LLM calls per prompt based on which detectors are active
    configs_with_llm_analyzer = {
        BaselineConfig.B_LLM_ONLY,
        BaselineConfig.D_RULE_LLM,
        BaselineConfig.F_LLM_CONSTITUTION,
        BaselineConfig.G_FULL_BLENDED,
        BaselineConfig.H_PROMPT_GUARDRAIL,
    }
    configs_with_constitution = {
        BaselineConfig.C_CONSTITUTION_ONLY,
        BaselineConfig.E_RULE_CONSTITUTION,
        BaselineConfig.F_LLM_CONSTITUTION,
        BaselineConfig.G_FULL_BLENDED,
    }
    # Each prompt also calls the downstream LLM if not blocked (estimate 70% reach downstream)
    downstream_call_rate = 0.7

    calls_per_prompt = 0
    if baseline_config in configs_with_llm_analyzer:
        calls_per_prompt += 1
    if baseline_config in configs_with_constitution:
        calls_per_prompt += 1
    calls_per_prompt += downstream_call_rate  # approximate

    total_calls = int(n_prompts * calls_per_prompt)
    expensive = n_prompts > 50 or total_calls > 100

    lines = [
        f"  Prompts:              {n_prompts}",
        f"  Baseline:             {baseline_config.value}",
        f"  LLM calls/prompt:     ~{calls_per_prompt:.1f}",
        f"  LLM calls total:      ~{total_calls}",
        f"  Expensive run:        {'YES - set RUN_EXPENSIVE_EXPERIMENT=true' if expensive else 'No'}",
    ]
    if model_roles:
        lines.append(f"  Analyzer model:       {model_roles.analyzer}")
        lines.append(f"  Constitution model:   {model_roles.constitution}")
        lines.append(f"  Downstream model:     {model_roles.downstream}")

    return {
        "n_prompts": n_prompts,
        "llm_calls_per_prompt": round(calls_per_prompt, 1),
        "llm_calls_total": total_calls,
        "expensive": expensive,
        "message": "\n".join(lines),
    }


def check_expense_guard(estimate: dict) -> None:
    """
    Raises RuntimeError if the run is expensive and RUN_EXPENSIVE_EXPERIMENT
    is not set to 'true' in the environment.
    """
    if not estimate["expensive"]:
        return
    flag = os.environ.get("RUN_EXPENSIVE_EXPERIMENT", "").lower()
    if flag != "true":
        raise RuntimeError(
            f"\nThis experiment requires ~{estimate['llm_calls_total']} LLM API calls "
            f"across {estimate['n_prompts']} prompts.\n"
            "Set the environment variable RUN_EXPENSIVE_EXPERIMENT=true to proceed.\n"
            "This guard exists to prevent accidental large API costs.\n\n"
            + estimate["message"]
        )
