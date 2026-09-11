import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CROSS_DIR = ROOT / "experiments" / "cross_model"
CROSS_DIR.mkdir(parents=True, exist_ok=True)

DEV_FILES = [
    "data/benchmark/dev/direct_injection.jsonl",
    "data/benchmark/dev/indirect_injection.jsonl",
    "data/benchmark/dev/jailbreak_persona.jsonl",
    "data/benchmark/dev/benign_general.jsonl",
]

experiments = [
    ("same_model_homogeneous", "Cross-Model Exp 1: Single Homogeneous Model Provider",
     "When security analyzer, constitution checker, downstream agent, and evaluator share the identical model family, detection performance represents the baseline homogeneous ceiling.",
     {
         "analyzer": "groq/openai/gpt-oss-120b",
         "constitution": "groq/openai/gpt-oss-120b",
         "downstream": "groq/openai/gpt-oss-120b",
         "evaluator": "groq/openai/gpt-oss-120b"
     }),
    ("heterogeneous_analyzer_fast", "Cross-Model Exp 2: Lightweight Security Analyzer",
     "Decoupling the security analyzer to a lightweight model (Llama-3.1-8B) reduces gateway latency while evaluating detection trade-offs against heavier models.",
     {
         "analyzer": "groq/llama-3.1-8b-instant",
         "constitution": "groq/openai/gpt-oss-120b",
         "downstream": "groq/openai/gpt-oss-120b",
         "evaluator": "groq/openai/gpt-oss-120b"
     }),
    ("heterogeneous_constitution_heavy", "Cross-Model Exp 3: High-Capacity Constitution Checker",
     "Assigning a high-capacity model (Llama-3.3-70B) to the constitution module improves structured verdict accuracy and reduces false positives.",
     {
         "analyzer": "groq/openai/gpt-oss-120b",
         "constitution": "groq/llama-3.3-70b-versatile",
         "downstream": "groq/openai/gpt-oss-120b",
         "evaluator": "groq/openai/gpt-oss-120b"
     }),
    ("heterogeneous_decoupled_target", "Cross-Model Exp 4: Decoupled Downstream Target Agent",
     "Running the gateway against a distinct downstream architecture (Mixtral-8x7B) tests whether gateway detection generalizes regardless of target model vulnerability.",
     {
         "analyzer": "groq/openai/gpt-oss-120b",
         "constitution": "groq/openai/gpt-oss-120b",
         "downstream": "groq/mixtral-8x7b-32768",
         "evaluator": "groq/openai/gpt-oss-120b"
     }),
    ("full_heterogeneous_pipeline", "Cross-Model Exp 5: Fully Heterogeneous Gateway Pipeline",
     "Heterogeneous model assignment across all 4 roles verifies that AURA Shield's risk engine and policy surface remain transfer-invariant.",
     {
         "analyzer": "groq/llama-3.1-8b-instant",
         "constitution": "groq/llama-3.3-70b-versatile",
         "downstream": "groq/mixtral-8x7b-32768",
         "evaluator": "groq/openai/gpt-oss-120b"
     })
]

for exp_id, name, hypothesis, roles in experiments:
    spec = {
        "experiment_id": exp_id,
        "experiment_name": name,
        "hypothesis": hypothesis,
        "independent_variables": ["model_analyzer", "model_constitution", "model_downstream", "model_evaluator"],
        "dependent_variables": ["precision", "recall", "f1", "fpr", "cross_model_transferability", "latency_ms"],
        "control_baseline": "G_full_blended",
        "dataset_split": "dev",
        "dataset_files": DEV_FILES,
        "model_roles": roles,
        "baseline_config": "G_full_blended",
        "tags": ["cross_model", "heterogeneous", "phase_5"]
    }
    spec_path = CROSS_DIR / f"{exp_id}.json"
    with open(spec_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(spec, indent=2) + "\n")
    print(f"Created cross-model spec: {spec_path.name}")

print("\nCross-model specifications successfully generated in experiments/cross_model/")
