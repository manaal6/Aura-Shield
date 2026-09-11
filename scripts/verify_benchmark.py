import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from research.schemas import PromptRecord

DATA_DIR = ROOT / "data" / "benchmark"
jsonl_files = list(DATA_DIR.rglob("*.jsonl"))

print(f"Found {len(jsonl_files)} JSONL files in {DATA_DIR.relative_to(ROOT)}:\n")

total = 0
all_ids = set()
splits_count = {"dev": 0, "adaptation": 0, "test": 0}
families_count = {}
labels_count = {}

for f in sorted(jsonl_files):
    count = 0
    with open(f, "r", encoding="utf-8") as fp:
        for line_no, line in enumerate(fp, start=1):
            if not line.strip():
                continue
            data = json.loads(line)
            # Validate schema
            record = PromptRecord(**data)
            
            # Uniqueness check
            if record.prompt_id in all_ids:
                raise ValueError(f"Duplicate prompt_id '{record.prompt_id}' in {f.name}:{line_no}")
            all_ids.add(record.prompt_id)
            
            splits_count[record.split.value] += 1
            families_count[record.attack_family.value] = families_count.get(record.attack_family.value, 0) + 1
            labels_count[record.ground_truth_label.value] = labels_count.get(record.ground_truth_label.value, 0) + 1
            count += 1
    total += count
    print(f"  - {f.relative_to(DATA_DIR)}: {count} prompts")

print(f"\nTotal Prompts: {total}")
print(f"By Split: {splits_count}")
print(f"By Label: {labels_count}")
print("\nBy Attack Family:")
for fam, c in sorted(families_count.items()):
    print(f"  - {fam:<25}: {c}")

assert total >= 300, f"Expected at least 300 prompts, got {total}"
assert splits_count["dev"] >= 100
assert splits_count["adaptation"] >= 100
assert splits_count["test"] >= 100
print("\nALL VERIFICATION CHECKS PASSED!")
