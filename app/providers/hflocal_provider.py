"""
app/providers/hflocal_provider.py

Local HuggingFace provider: runs a small causal LM in-process (CPU) as a
last-resort fallback path. Honest scope: proves ROUTING redundancy and
provider attribution end-to-end. It does NOT prove model independence —
a 100K-param local model is not a capable security judge, and any result
produced through it must be labeled degraded, never equivalent.
"""
from __future__ import annotations

import logging
from typing import Optional

from app.providers.base import LLMProvider, ProviderResponse

logger = logging.getLogger(__name__)

_MODEL = None
_MODEL_NAME = ""


def _load(model_name: str):
    global _MODEL, _MODEL_NAME
    if _MODEL is None or _MODEL_NAME != model_name:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        tok = AutoTokenizer.from_pretrained(model_name)
        if tok.pad_token is None:
            tok.pad_token = tok.eos_token
        model = AutoModelForCausalLM.from_pretrained(model_name)
        model.eval()
        _MODEL, _MODEL_NAME = (model, tok), model_name
    return _MODEL


class HFLocalProvider(LLMProvider):
    """Local CPU fallback. Configure via HFLOCAL_MODEL (default tiny-gpt2)."""

    @property
    def name(self) -> str:
        return "hflocal"

    def is_available(self) -> bool:
        try:
            import transformers  # noqa: F401
            return True
        except Exception:
            return False

    def chat_completion(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        response_format: Optional[dict[str, str]] = None,
        max_retries: int = 1,
    ) -> ProviderResponse:
        import os

        import torch

        model_name = os.environ.get("HFLOCAL_MODEL", "sshleifer/tiny-gpt2")
        prompt = "\n".join(f"{m.get('role', '')}: {m.get('content', '')}" for m in messages)
        loaded_model, tok = _load(model_name)
        ids = tok(prompt, return_tensors="pt", truncation=True, max_length=256)["input_ids"]
        with torch.no_grad():
            out = loaded_model.generate(ids, max_new_tokens=60, do_sample=False,
                                        pad_token_id=tok.eos_token_id)
        text = tok.decode(out[0][ids.shape[1]:], skip_special_tokens=True)
        return ProviderResponse(
            content=text, model=model_name, provider_name="hflocal",
            metadata={"degraded": True, "note": "local fallback; not equivalent to hosted judges"},
        )
