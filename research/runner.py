"""
research/runner.py

Benchmark runner for AURA Shield research experiments.

This runner:
- Reads prompts from JSONL files (the new research-grade format)
- Also supports legacy JSON arrays (backward compat with benchmark_dataset.json)
- Supports configurable baseline detector combinations
- Enforces the split contamination guard
- Estimates API cost before running expensive experiments
- Saves timestamped, never-overwritten result sets
- Is NOT the same as evaluation/evaluate.py (which is preserved unchanged)

Status: IMPLEMENTED (Phase 2 - Experimental Infrastructure)
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Ensure the repo root is importable regardless of launch directory
_REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from research.schemas import (
    BaselineConfig,
    DatasetSplit,
    ExperimentResult,
    ExperimentSpec,
    PerPromptResult,
    PolicyDecision,
    DetectionResult,
    DetectorName,
    EnforcementAction,
    GroundTruthLabel,
)
from research.metrics import (
    compute_metrics,
    per_family_breakdown,
    confusion_matrix,
    ablation_summary,
    format_metrics_report,
    export_json,
    export_csv,
)
from research.experiment import (
    assert_split_not_contaminated,
    estimate_run_cost,
    check_expense_guard,
    make_output_dir,
    save_spec,
    save_result,
)

logger = logging.getLogger(__name__)

# Rate limiting between requests (adjust based on API tier)
_DEFAULT_DELAY_SECONDS = 2.0

# Mapping from baseline config to which detectors to activate
_BASELINE_FLAGS: dict[BaselineConfig, dict[str, bool]] = {
    BaselineConfig.A_RULE_ONLY:         {"use_rule": True,  "use_llm": False, "use_constitution": False},
    BaselineConfig.B_LLM_ONLY:          {"use_rule": False, "use_llm": True,  "use_constitution": False},
    BaselineConfig.C_CONSTITUTION_ONLY: {"use_rule": False, "use_llm": False, "use_constitution": True},
    BaselineConfig.D_RULE_LLM:          {"use_rule": True,  "use_llm": True,  "use_constitution": False},
    BaselineConfig.E_RULE_CONSTITUTION: {"use_rule": True,  "use_llm": False, "use_constitution": True},
    BaselineConfig.F_LLM_CONSTITUTION:  {"use_rule": False, "use_llm": True,  "use_constitution": True},
    BaselineConfig.G_FULL_BLENDED:      {"use_rule": True,  "use_llm": True,  "use_constitution": True},
    BaselineConfig.H_PROMPT_GUARDRAIL:  {"use_guardrail": True},
    BaselineConfig.I_EMBEDDING:         {"use_embedding": True},
}


# ─────────────────────────── JSONL dataset IO ─────────────────────────────────


def load_dataset_jsonl(path: Path | str) -> list[dict]:
    """
    Load prompts from a JSONL file (one JSON object per line).
    Also accepts legacy JSON arrays (backward compat with benchmark_dataset.json).
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return []
    # Try JSONL first (each line is a JSON object)
    if text.startswith("{") or (text.startswith("[") is False):
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return [json.loads(line) for line in lines]
    # Fall back to JSON array
    return json.loads(text)


def load_datasets(paths: list[str | Path]) -> list[dict]:
    """Load and concatenate prompts from multiple dataset files."""
    all_prompts: list[dict] = []
    for p in paths:
        prompts = load_dataset_jsonl(p)
        logger.info("Loaded %d prompts from %s", len(prompts), p)
        all_prompts.extend(prompts)
    return all_prompts


# ─────────────────────────── pipeline integration ─────────────────────────────


def _run_pipeline_with_baseline(
    user_prompt: str,
    source_content: Optional[str],
    request_id: str,
    baseline: BaselineConfig,
) -> dict:
    """
    Run the AURA Shield pipeline with a specific baseline configuration.
    Returns the raw output dict from process_request() or a baseline-filtered version.
    """
    flags = dict(_BASELINE_FLAGS.get(baseline, _BASELINE_FLAGS[BaselineConfig.G_FULL_BLENDED]))
    flags["skip_db_logging"] = True
    flags["skip_downstream"] = True

    from app.models import IncomingRequest
    from app.pipeline import process_request_with_config

    # Use the extended pipeline that accepts a baseline config dict
    try:
        from app.pipeline import process_request_with_config
        result = process_request_with_config(
            IncomingRequest(
                user_prompt=user_prompt,
                source_content=source_content,
                request_id=request_id,
            ),
            baseline_config=flags,
        )
    except ImportError:
        # Fallback: process_request_with_config not yet available; use full pipeline
        from app.pipeline import process_request
        result = process_request(
            IncomingRequest(
                user_prompt=user_prompt,
                source_content=source_content,
                request_id=request_id,
            )
        )
    return result


# ─────────────────────────── main runner ──────────────────────────────────────


class BenchmarkRunner:
    """
    Runs benchmark experiments and saves reproducible results.

    Usage:
        runner = BenchmarkRunner(spec)
        runner.estimate()          # print cost estimate
        results, summary = runner.run()
    """

    def __init__(
        self,
        spec: ExperimentSpec,
        delay_seconds: float = _DEFAULT_DELAY_SECONDS,
        adaptive_loop_mode: bool = False,
        verbose: bool = True,
    ):
        self.spec = spec
        self.delay_seconds = delay_seconds
        self.adaptive_loop_mode = adaptive_loop_mode
        self.verbose = verbose

    def estimate(self) -> dict:
        """Print the cost estimate and return it. Safe to call without running."""
        prompts = load_datasets(self.spec.dataset_files)
        n = len(prompts) if not self.spec.max_prompts else min(len(prompts), self.spec.max_prompts)
        est = estimate_run_cost(n, self.spec.baseline_config, self.spec.model_roles)
        print("\n--- Experiment Cost Estimate ---")
        print(f"  Experiment:  {self.spec.experiment_name}")
        print(f"  Hypothesis:  {self.spec.hypothesis[:80]}...")
        print(est["message"])
        print("--------------------------------\n")
        return est

    def run(
        self,
        dry_run: bool = False,
        skip_expense_guard: bool = False,
    ) -> tuple[list[dict], ExperimentResult]:
        """
        Run the benchmark.

        Args:
            dry_run: If True, loads dataset and estimates cost but does not
                     make any API calls or write results.
            skip_expense_guard: If True, bypasses the RUN_EXPENSIVE_EXPERIMENT
                                guard. Only use in test environments.

        Returns:
            (per_prompt_results_list, ExperimentResult)
        """
        # 1. Enforce split contamination guard
        assert_split_not_contaminated(self.spec.dataset_files, self.adaptive_loop_mode)

        # 2. Load dataset
        all_prompts = load_datasets(self.spec.dataset_files)
        if self.spec.max_prompts:
            all_prompts = all_prompts[: self.spec.max_prompts]

        # 3. Cost estimate + expense guard
        est = estimate_run_cost(
            len(all_prompts), self.spec.baseline_config, self.spec.model_roles
        )
        if self.verbose:
            print("\n--- Experiment Cost Estimate ---")
            print(f"  Experiment:  {self.spec.experiment_name}")
            print(est["message"])
            print("--------------------------------\n")

        if dry_run:
            print("DRY RUN - no API calls or result writes.")
            return [], _empty_result(self.spec)

        if not skip_expense_guard:
            check_expense_guard(est)

        # 4. Create output directory
        out_dir = make_output_dir(self.spec.experiment_id)
        save_spec(self.spec, out_dir)
        raw_path = out_dir / "raw_results.jsonl"
        if self.verbose:
            print(f"Output directory: {out_dir}")

        # 5. Results are persisted to local out_dir JSONL/CSV artifacts

        # 6. Run prompts
        per_prompt_rows: list[dict] = []
        any_real_llm = False
        total_latency = 0.0

        for i, item in enumerate(all_prompts):
            prompt_id = item.get("id") or item.get("prompt_id") or f"p-{i:04d}"
            user_prompt = item.get("content") or item.get("user_prompt", "")
            source_content = item.get("source_content")
            attack_family = item.get("attack_family") or item.get("category", "unknown")
            ground_truth = item.get("ground_truth_label") or (
                "benign" if item.get("category") == "benign" else "attack"
            )
            split = item.get("split", self.spec.dataset_split.value)

            if self.verbose:
                print(f"[{i+1}/{len(all_prompts)}] {prompt_id} ({attack_family})")

            try:
                start = time.perf_counter()
                outcome = _run_pipeline_with_baseline(
                    user_prompt=user_prompt,
                    source_content=source_content,
                    request_id=prompt_id,
                    baseline=self.spec.baseline_config,
                )
                latency_ms = (time.perf_counter() - start) * 1000
                total_latency += latency_ms

                rule_result = outcome.get("rule_result")
                llm_result = outcome.get("llm_result")
                constitution_result = outcome.get("constitution_result")

                if llm_result and not llm_result.used_fallback:
                    any_real_llm = True

                decision_str = outcome.get("decision", "allow")
                flagged = decision_str in ("block", "review")

                row = {
                    "prompt_id": prompt_id,
                    "attack_family": attack_family,
                    "split": split,
                    "ground_truth_label": ground_truth,
                    "content_hash": _hash_prompt(user_prompt, source_content),
                    "user_prompt": user_prompt,
                    "source_content": source_content,
                    "actual_decision": decision_str,
                    "risk_score": outcome.get("risk_score"),
                    "explanation": outcome.get("explanation", ""),
                    "flagged_by_shield": flagged,
                    "rule_signal": getattr(rule_result, "raw_signal", None),
                    "rule_matched": getattr(rule_result, "matched", None),
                    "rule_patterns": getattr(rule_result, "matched_patterns", []),
                    "llm_signal": getattr(llm_result, "raw_signal", None),
                    "llm_used_fallback": getattr(llm_result, "used_fallback", True),
                    "constitution_signal": getattr(constitution_result, "raw_signal", None) if constitution_result else None,
                    "constitution_fallback": getattr(constitution_result, "used_fallback", None) if constitution_result else None,
                    "attack_succeeded": None,   # Requires separate safety evaluator — see ASR definition
                    "latency_ms": round(latency_ms, 1),
                    "llm_calls": (
                        (0 if getattr(llm_result, "used_fallback", True) else 1)
                        + (0 if (constitution_result is None or constitution_result.used_fallback) else 1)
                    ),
                    "baseline_config": self.spec.baseline_config.value,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                per_prompt_rows.append(row)

                # Append to JSONL incrementally (so partial results survive crashes)
                with raw_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(row, default=str) + "\n")

            except Exception as exc:
                logger.error("Error processing prompt %s: %s", prompt_id, exc)
                row = {
                    "prompt_id": prompt_id,
                    "attack_family": attack_family,
                    "split": split,
                    "ground_truth_label": ground_truth,
                    "content_hash": _hash_prompt(user_prompt, source_content),
                    "error": str(exc),
                    "flagged_by_shield": False,  # conservative
                    "attack_succeeded": None,
                    "baseline_config": self.spec.baseline_config.value,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                per_prompt_rows.append(row)
                with raw_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(row, default=str) + "\n")

            # Rate limiting (only when making real network LLM calls)
            active_flags = _BASELINE_FLAGS.get(self.spec.baseline_config, {})
            makes_network_calls = active_flags.get("use_llm") or active_flags.get("use_constitution") or active_flags.get("use_guardrail")
            llm_used = makes_network_calls and not getattr(llm_result if "llm_result" in dir() else None, "used_fallback", True)
            if llm_used:
                time.sleep(self.delay_seconds)

        # 7. Compute metrics
        valid_rows = [r for r in per_prompt_rows if "error" not in r]
        metrics = compute_metrics(valid_rows)
        per_family = per_family_breakdown(valid_rows)
        cm = confusion_matrix(valid_rows)
        ablation = ablation_summary(valid_rows)

        latency_values = [r["latency_ms"] for r in valid_rows if "latency_ms" in r]
        latency_summary = {
            "avg_ms": round(sum(latency_values) / len(latency_values), 1) if latency_values else None,
            "min_ms": round(min(latency_values), 1) if latency_values else None,
            "max_ms": round(max(latency_values), 1) if latency_values else None,
            "total_ms": round(total_latency, 1),
            "llm_calls_total": sum(r.get("llm_calls", 0) for r in valid_rows),
        }

        # 8. Build and save ExperimentResult
        result = ExperimentResult(
            experiment_id=self.spec.experiment_id,
            experiment_spec=self.spec,
            total_prompts=len(per_prompt_rows),
            real_llm_calls_used=any_real_llm,
            metrics=metrics,
            per_family_metrics=per_family,
            confusion_matrix=cm,
            latency=latency_summary,
            what_this_demonstrates=(
                f"The system processed {len(valid_rows)} prompts under baseline "
                f"'{self.spec.baseline_config.value}'. Detection metrics are computed "
                "from actual pipeline outputs on this specific dataset split."
            ),
            what_this_does_not_demonstrate=(
                "These results do not demonstrate generalization to unseen attack families, "
                "robustness against adaptive attackers, or security in production environments. "
                "ASR is not computed here unless a downstream safety evaluator was run."
            ),
            limitations=[
                f"n={len(valid_rows)} - interpret CIs accordingly",
                "ASR not evaluated (requires separate downstream safety check)",
                "Single model provider unless MODEL_* env vars override defaults",
            ],
            raw_results_path=str(raw_path),
        )
        save_result(result, out_dir)

        # 9. Save additional exports
        export_json(metrics, out_dir / "metrics.json")
        export_json(per_family, out_dir / "per_family_metrics.json")
        export_json(cm, out_dir / "confusion_matrix.json")
        export_json(ablation, out_dir / "ablation.json")
        export_csv(valid_rows, out_dir / "results.csv")

        # 10. Print report
        if self.verbose:
            print(format_metrics_report(
                metrics,
                per_family=per_family,
                title=f"AURA Shield — {self.spec.experiment_name}",
                real_llm=any_real_llm,
            ))
            print(f"\nResults saved to: {out_dir}")

        return per_prompt_rows, result


def _hash_prompt(user_prompt: str, source_content: Optional[str]) -> str:
    import hashlib
    combined = (user_prompt or "") + (source_content or "")
    return hashlib.sha256(combined.encode()).hexdigest()[:16]


def _empty_result(spec: ExperimentSpec) -> ExperimentResult:
    return ExperimentResult(
        experiment_id=spec.experiment_id,
        experiment_spec=spec,
        total_prompts=0,
        real_llm_calls_used=False,
        metrics={},
        what_this_demonstrates="Dry run - no prompts were evaluated.",
        what_this_does_not_demonstrate="Everything.",
    )


# ─────────────────────────── CLI entry point ──────────────────────────────────


def _cli():
    import argparse

    parser = argparse.ArgumentParser(
        description="AURA Shield research benchmark runner"
    )
    parser.add_argument("spec", help="Path to experiment spec YAML/JSON file")
    parser.add_argument("--estimate", action="store_true", help="Estimate cost without running")
    parser.add_argument("--dry-run", action="store_true", help="Load data but do not run LLM calls")
    parser.add_argument("--verbose", action="store_true", default=True)
    args = parser.parse_args()

    from research.experiment import load_spec
    spec = load_spec(args.spec)
    runner = BenchmarkRunner(spec, verbose=args.verbose)

    if args.estimate:
        runner.estimate()
        return

    runner.run(dry_run=args.dry_run)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    _cli()
