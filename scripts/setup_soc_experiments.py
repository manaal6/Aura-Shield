import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOC_DIR = ROOT / "experiments" / "soc_workflow"
SOC_DIR.mkdir(parents=True, exist_ok=True)

soc_files = [
    "data/benchmark/adaptation/benign_cybersecurity.jsonl",
    "data/benchmark/test/benign_cybersecurity_holdout.jsonl",
    "data/benchmark/test/tool_injection.jsonl",
    "data/benchmark/dev/indirect_injection.jsonl",
]

spec = {
    "experiment_id": "soc_log_analysis_eval",
    "experiment_name": "SOC Analyst Assistant Security & Utility Evaluation",
    "hypothesis": "AURA Shield effectively detects indirect prompt injections and unauthorized tool calls embedded in security telemetry without penalizing legitimate SOC log analysis tasks.",
    "independent_variables": ["telemetry_source", "embedded_payload_presence", "tool_invocation_context"],
    "dependent_variables": ["detection_rate", "benign_utility_rate", "tool_authorization_rate", "fpr", "latency_ms"],
    "control_baseline": "G_full_blended",
    "dataset_split": "test",
    "dataset_files": soc_files,
    "model_roles": {
        "analyzer": "groq/openai/gpt-oss-120b",
        "constitution": "groq/openai/gpt-oss-120b",
        "downstream": "groq/openai/gpt-oss-120b",
        "evaluator": "groq/openai/gpt-oss-120b"
    },
    "baseline_config": "G_full_blended",
    "tags": ["soc_workflow", "cybersecurity", "phase_6"]
}

spec_path = SOC_DIR / "soc_log_analysis_eval.json"
with open(spec_path, "w", encoding="utf-8") as f:
    f.write(json.dumps(spec, indent=2) + "\n")
print(f"Created SOC experiment spec: {spec_path.name}")
