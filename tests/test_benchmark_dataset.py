"""
tests/test_benchmark_dataset.py

Validates the full benchmark dataset in data/benchmark/.
Checks:
- Minimum prompt threshold (>= 300)
- Explicit train/adaptation/test split quotas
- PromptRecord Pydantic validation across all rows
- Unique prompt_ids across the entire benchmark
- Attack family taxonomy coverage
"""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest
from research.schemas import AttackFamily, DatasetSplit, GroundTruthLabel, PromptRecord

DATA_DIR = ROOT / "data" / "benchmark"


def test_benchmark_splits_exist():
    assert (DATA_DIR / "dev").is_dir()
    assert (DATA_DIR / "adaptation").is_dir()
    assert (DATA_DIR / "test").is_dir()
    assert (DATA_DIR / "splits.json").is_file()


def test_all_benchmark_prompts_valid_schema():
    jsonl_files = list(DATA_DIR.rglob("*.jsonl"))
    assert len(jsonl_files) == 14

    all_ids = set()
    total_count = 0
    splits_count = {s.value: 0 for s in DatasetSplit}
    families_present = set()

    for f in jsonl_files:
        with open(f, "r", encoding="utf-8") as fp:
            for line_no, line in enumerate(fp, start=1):
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                record = PromptRecord(**data)
                
                # Check uniqueness
                assert record.prompt_id not in all_ids, f"Duplicate prompt_id '{record.prompt_id}' in {f.name}:{line_no}"
                all_ids.add(record.prompt_id)
                
                total_count += 1
                splits_count[record.split.value] += 1
                families_present.add(record.attack_family.value)

    assert total_count >= 300, f"Expected at least 300 prompts, got {total_count}"
    assert splits_count["dev"] >= 100
    assert splits_count["adaptation"] >= 100
    assert splits_count["test"] >= 100

    # Ensure all required attack and benign families from Section 7 are represented
    expected_families = {
        "direct_injection",
        "indirect_injection",
        "jailbreak_persona",
        "jailbreak_encoding",
        "jailbreak_multilingual",
        "multi_turn_manipulation",
        "obfuscation",
        "tool_injection",
        "authorization_attack",
        "context_flooding",
        "policy_targeting",
        "benign_cybersecurity",
        "benign_general",
    }
    assert expected_families.issubset(families_present)
