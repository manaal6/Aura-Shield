"""
training/dpo_lm/hardware.py

Hardware auto-discovery engine for free compute environments (Kaggle/Colab) (W#2).
Discovers CUDA, VRAM, bfloat16/fp16 capabilities, bitsandbytes availability,
and selects the largest trainable model that genuinely fits the environment.
Never fabricates larger models.
"""
from __future__ import annotations

import platform
import torch


def discover_hardware_profile() -> dict:
    profile = {
        "cuda_available": torch.cuda.is_available(),
        "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "device_name": "CPU",
        "total_vram_gb": 0.0,
        "bf16_supported": False,
        "fp16_supported": False,
        "bitsandbytes_available": False,
        "recommended_tier": "cpu_tiny",
    }

    try:
        import bitsandbytes
        profile["bitsandbytes_available"] = True
    except ImportError:
        profile["bitsandbytes_available"] = False

    if torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        profile["device_name"] = props.name
        profile["total_vram_gb"] = round(props.total_memory / (1024 ** 3), 2)
        profile["bf16_supported"] = torch.cuda.is_bf16_supported()
        profile["fp16_supported"] = True

        vram = profile["total_vram_gb"]
        if vram >= 14.0:
            profile["recommended_tier"] = "gpu_qlora_medium"  # e.g. Tesla P100 / T4: 1.5B - 3B QLoRA
        elif vram >= 7.0:
            profile["recommended_tier"] = "gpu_lora_small"     # 0.5B - 1.5B LoRA
        else:
            profile["recommended_tier"] = "gpu_tiny"
    else:
        profile["device_name"] = f"CPU ({platform.processor() or platform.machine()})"
        profile["recommended_tier"] = "cpu_tiny"

    return profile


def get_recommended_model_config(base_cfg: dict) -> dict:
    """Adapts config based on actual verified hardware."""
    hw = discover_hardware_profile()
    cfg = dict(base_cfg)
    cfg["hardware_discovered"] = hw

    tier = hw["recommended_tier"]
    if tier == "gpu_qlora_medium":
        cfg["model_target"] = "Qwen/Qwen2.5-1.5B"
        cfg["use_peft"] = True
        cfg["peft_type"] = "qlora"
    elif tier == "gpu_lora_small":
        cfg["model_target"] = "Qwen/Qwen2.5-0.5B"
        cfg["use_peft"] = True
        cfg["peft_type"] = "lora"
    else:
        # CPU or lightweight smoke test tier
        cfg["model_target"] = base_cfg.get("model", "sshleifer/tiny-gpt2")
        cfg["use_peft"] = False
        cfg["peft_type"] = "none"

    return cfg
