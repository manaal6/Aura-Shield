"""training/dpo_lm/train.py — GENUINE model-level DPO on a small HF causal LM.

Policy = sshleifer/tiny-gpt2 (102,714 params, CPU). Reference = frozen copy.
Manual DPO objective (Rafailov et al. 2023) on response log-probs:

  L = -E log sigmoid( beta * [ (logpi_ch - logref_ch) - (logpi_rej - logref_rej) ] )

Backprop updates POLICY ONLY. Proof of training: sha256 param hashes of
policy and reference before/after + changed-parameter counts
(required invariant: policy changed TRUE, reference changed FALSE).
Saves a real checkpoint + training record with full provenance.
"""
from __future__ import annotations

import hashlib
import json
import platform
import random
import sys
import time
from pathlib import Path

import torch
import yaml
from transformers import AutoModelForCausalLM, AutoTokenizer

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
from training.dpo_lm.dataset import load_train  # noqa: E402
from training.dpo.dataset import file_hash  # noqa: E402
from training.dpo_lm.hardware import get_recommended_model_config  # noqa: E402
from training.dpo_lm.augment import BENIGN_PRESERVATION_PAIRS  # noqa: E402


def param_hash(model) -> str:
    h = hashlib.sha256()
    for p in model.parameters():
        h.update(p.detach().cpu().numpy().tobytes())
    return h.hexdigest()


def seq_logprob(model, tok, prompt: str, response: str, max_len: int) -> torch.Tensor:
    enc_p = tok(prompt, add_special_tokens=False)["input_ids"]
    enc_r = tok(response, add_special_tokens=False)["input_ids"]
    ids = (enc_p + enc_r)[-max_len:]
    rlen = min(len(enc_r), max_len)
    inp = torch.tensor([ids])
    with torch.set_grad_enabled(model.training):
        logits = model(inp).logits[0]  # [T, V]
    logp = torch.log_softmax(logits, dim=-1)
    targets = torch.tensor(ids[1:] + [tok.eos_token_id])
    lp = logp[torch.arange(len(ids)), targets]
    return lp[-rlen:].sum()


def main() -> dict:
    cfg = yaml.safe_load((REPO / "training" / "dpo_lm" / "config.yaml").read_text())
    hw_cfg = get_recommended_model_config(cfg)
    random.seed(cfg["seed"]); torch.manual_seed(cfg["seed"])
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(cfg["model"])
    tok.pad_token = tok.eos_token
    policy = AutoModelForCausalLM.from_pretrained(cfg["model"])
    ref = AutoModelForCausalLM.from_pretrained(cfg["model"])
    for p in ref.parameters():
        p.requires_grad_(False)
    ref.eval()
    n_params = sum(p.numel() for p in policy.parameters())
    n_trainable = sum(p.numel() for p in policy.parameters() if p.requires_grad)
    h_pol_before, h_ref_before = param_hash(policy), param_hash(ref)

    train = load_train() + BENIGN_PRESERVATION_PAIRS
    opt = torch.optim.AdamW(policy.parameters(), lr=cfg["lr"])
    beta, bs, max_len = cfg["beta"], cfg["batch_size"], cfg["max_seq_len"]
    first_loss = None
    policy.train()
    for ep in range(cfg["epochs"]):
        random.shuffle(train)
        tot, nb = 0.0, 0
        for i in range(0, len(train), bs):
            batch = train[i:i + bs]
            opt.zero_grad()
            margins = []
            for p in batch:
                lpi_ch = seq_logprob(policy, tok, p["prompt"], p["chosen"], max_len)
                lpi_rej = seq_logprob(policy, tok, p["prompt"], p["rejected"], max_len)
                with torch.no_grad():
                    lref_ch = seq_logprob(ref, tok, p["prompt"], p["chosen"], max_len)
                    lref_rej = seq_logprob(ref, tok, p["prompt"], p["rejected"], max_len)
                margins.append((lpi_ch - lref_ch) - (lpi_rej - lref_rej))
            loss = -torch.log(torch.sigmoid(beta * torch.stack(margins)) + 1e-12).mean()
            if first_loss is None:
                first_loss = float(loss)
            loss.backward(); opt.step()
            tot += float(loss) * len(batch); nb += len(batch)
        print(f"epoch {ep+1}/{cfg['epochs']} loss={tot/nb:.4f}", flush=True)
    last_loss = tot / nb

    h_pol_after, h_ref_after = param_hash(policy), param_hash(ref)
    # changed counts via state dict compare against fresh load
    fresh = AutoModelForCausalLM.from_pretrained(cfg["model"])
    sd_p, sd_f = policy.state_dict(), fresh.state_dict()
    changed = sum(1 for k in sd_p if not torch.equal(sd_p[k].cpu(), sd_f[k].cpu()))
    total_tensors = len(sd_p)

    out = REPO / "results" / "kaust_three_pillars" / "dpo_lm"
    out.mkdir(parents=True, exist_ok=True)
    ckpt = out / "checkpoint"
    policy.save_pretrained(ckpt); tok.save_pretrained(ckpt)
    ckpt_file = ckpt / "model.safetensors" if (ckpt / "model.safetensors").exists() else ckpt / "pytorch_model.bin"
    rec = {
        "status": "FULL MODEL-LEVEL DPO (tiny CPU causal LM)",
        "model": cfg["model"], "tokenizer": cfg["model"],
        "n_params": n_params, "n_trainable": n_trainable,
        "beta": beta, "lr": cfg["lr"], "batch_size": bs,
        "epochs": cfg["epochs"], "max_seq_len": max_len,
        "optimizer": cfg["optimizer"], "scheduler": cfg["scheduler"], "seed": cfg["seed"],
        "dataset": cfg["dataset"], "dataset_hash": file_hash(REPO / cfg["dataset"]),
        "n_train": len(train),
        "policy_hash_before": h_pol_before[:16], "policy_hash_after": h_pol_after[:16],
        "reference_hash_before": h_ref_before[:16], "reference_hash_after": h_ref_after[:16],
        "policy_changed": h_pol_before != h_pol_after,
        "reference_changed": h_ref_before != h_ref_after,
        "changed_tensors": changed, "total_tensors": total_tensors,
        "checkpoint": str(ckpt.relative_to(REPO)), "checkpoint_hash": file_hash(ckpt_file),
        "loss_first": round(first_loss, 4), "loss_last": round(last_loss, 4),
        "train_seconds": round(time.time() - t0, 1),
        "hardware": f"CPU ({platform.processor() or platform.machine})",
        "hardware_discovered": hw_cfg["hardware_discovered"],
        "torch_version": torch.__version__,
    }
    assert rec["policy_changed"] is True and rec["reference_changed"] is False, "training invariant violated"
    (out / "dpo_lm_record.json").write_text(json.dumps(rec, indent=2))
    print(json.dumps(rec, indent=2))
    return rec


if __name__ == "__main__":
    main()
