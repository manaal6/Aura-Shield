"""research/dpo_beta_sweep.py — DPO dissection H1 test (CPU, offline, tiny-gpt2).

Question: does a weaker KL constraint (low beta) flip preference rankings?
Configs: beta in {0.1, 0.5, 1.0}, 133-train pairs, 3 epochs each, fixed seed.
Records train/dev/unseen accuracy per beta. H1 predicts flips at low beta.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from training.dpo_lm import train as T  # noqa: E402
from training.dpo_lm import evaluate as E  # noqa: E402


def main() -> dict:
    import yaml
    cfg_path = REPO / "training" / "dpo_lm" / "config.yaml"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    base_beta, base_epochs = cfg["beta"], cfg["epochs"]
    out = {}
    # Preserve canonical tiny artifacts (referenced by reports/dashboard); sweep restores them.
    import shutil
    dpo_dir = REPO / "results" / "kaust_three_pillars" / "dpo_lm"
    import hashlib
    pre_hash = hashlib.sha256((dpo_dir / "dpo_lm_record.json").read_bytes()).hexdigest()
    backup = REPO / "results" / "kaust_three_pillars" / "_dpo_lm_backup"
    if backup.exists():
        shutil.rmtree(backup)
    shutil.copytree(dpo_dir, backup)
    try:
        for beta in (0.1, 0.5, 1.0):
            cfg["beta"] = beta
            cfg["epochs"] = 3
            cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
            T.main()
            rep = E.main()
            out[str(beta)] = {
                "dev": rep["dpo"]["preference_accuracy"] if isinstance(rep["dpo"], dict) else rep["dpo"],
                "unseen": rep["dpo"].get("unseen_pref_accuracy") if isinstance(rep["dpo"], dict) else None,
                "loss": rep["dpo"].get("dpo_loss") if isinstance(rep["dpo"], dict) else None,
            }
            print(f"BETA {beta}: {out[str(beta)]}", flush=True)
    finally:
        cfg["beta"], cfg["epochs"] = base_beta, base_epochs
        cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
        import shutil as _sh
        for f in dpo_dir.glob("*"):
            if f.is_file():
                f.unlink()
            else:
                _sh.rmtree(f)
        for f in backup.glob("*"):
            if f.is_file():
                _sh.copy(f, dpo_dir / f.name)
            else:
                _sh.copytree(f, dpo_dir / f.name)
        _sh.rmtree(backup)
    dest = REPO / "results" / "kaust_three_pillars" / "dpo_lm" / "beta_sweep.json"
    dest.write_text(json.dumps(out, indent=2), encoding="utf-8")
    import hashlib as _hl
    post_hash = _hl.sha256((dpo_dir / "dpo_lm_record.json").read_bytes()).hexdigest()
    assert post_hash == pre_hash, "canonical tiny artifacts were altered by the sweep!"
    return out


if __name__ == "__main__":
    main()
