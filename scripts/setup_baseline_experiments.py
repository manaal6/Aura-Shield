import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINES_DIR = ROOT / "experiments" / "baselines"
BASELINES_DIR.mkdir(parents=True, exist_ok=True)

DEV_FILES = [
    "data/benchmark/dev/direct_injection.jsonl",
    "data/benchmark/dev/indirect_injection.jsonl",
    "data/benchmark/dev/jailbreak_persona.jsonl",
    "data/benchmark/dev/benign_general.jsonl",
]

baselines = [
    ("A_rule_only", "Baseline A: Deterministic Rule-Only Detector",
     "Deterministic regex pattern matching provides high precision on literal signatures but exhibits low recall on paraphrased or novel attacks.",
     "A_rule_only"),
    ("B_llm_only", "Baseline B: LLM Semantic Detector Only",
     "LLM semantic analyzer catches paraphrased and novel variants but is vulnerable to adversarial jailbreak framing.",
     "B_llm_only"),
    ("C_constitution_only", "Baseline C: Constitution Checker Only",
     "Per-principle constitutional checking enforces explicit constraints but incurs higher per-request latency.",
     "C_constitution_only"),
    ("D_rule_llm", "Baseline D: Rule + LLM Semantic Detector",
     "Combining fast signature matching with semantic judgment improves recall over rule-only baseline.",
     "D_rule_llm"),
    ("E_rule_constitution", "Baseline E: Rule + Constitution Checker",
     "Evaluating constitutional violations alongside signature rules prevents blatant bypasses without generic semantic analysis.",
     "E_rule_constitution"),
    ("F_llm_constitution", "Baseline F: LLM Semantic + Constitution Checker",
     "Dual LLM reasoning layers provide high coverage against complex injections at the cost of dual inference latency.",
     "F_llm_constitution"),
    ("G_full_blended", "Baseline G: Full Blended AURA Shield Gateway",
     "Layering deterministic rules, semantic judgment, and constitutional verdicts achieves superior F1 and resilience over any single tier.",
     "G_full_blended"),
    ("H_prompt_guardrail", "Baseline H: Monolithic Prompt Guardrail",
     "A single prompt guardrail performs moderately well on overt attacks but fails on obfuscated and indirect attacks.",
     "H_prompt_guardrail"),
    ("I_embedding", "Baseline I: Independent TF-IDF Vector Classifier",
     "Vector similarity classification provides fast, local detection of lexical clusters but fails on semantic paraphrasing.",
     "I_embedding"),
]

for cfg_id, name, hypothesis, enum_val in baselines:
    spec = {
        "experiment_id": f"baseline_{cfg_id.lower()}",
        "experiment_name": name,
        "hypothesis": hypothesis,
        "independent_variables": ["active_detectors", "scoring_pipeline"],
        "dependent_variables": ["precision", "recall", "f1", "fpr", "latency_ms"],
        "control_baseline": "A_rule_only",
        "dataset_split": "dev",
        "dataset_files": DEV_FILES,
        "model_roles": {
            "analyzer": "groq/openai/gpt-oss-120b",
            "constitution": "groq/openai/gpt-oss-120b",
            "downstream": "groq/openai/gpt-oss-120b",
            "evaluator": "groq/openai/gpt-oss-120b"
        },
        "baseline_config": enum_val,
        "tags": ["baseline", "ablation", "phase_4"]
    }
    spec_path = BASELINES_DIR / f"{cfg_id.lower()}.json"
    with open(spec_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(spec, indent=2) + "\n")
    print(f"Created baseline spec: {spec_path.name}")

print("\nBaseline specifications successfully generated in experiments/baselines/")
