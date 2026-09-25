"""
app/providers/openai_provider.py

Optional OpenAI-compatible provider adapter.
Remains completely inactive unless credentials are explicitly provided in environment.
Does not block or require paid usage.
"""
from __future__ import annotations

import logging
from typing import Optional
from app.config import get_settings
from app.providers.base import LLMProvider, ProviderResponse

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        self._explicit_key = api_key

    @property
    def name(self) -> str:
        return "openai"

    def _get_api_key(self) -> str:
        if self._explicit_key:
            return self._explicit_key
        settings = get_settings()
        return getattr(settings, "openai_api_key", "") or ""

    def is_available(self) -> bool:
        settings = get_settings()
        if not getattr(settings, "provider_fallback_enabled", False):
            return False
        return bool(self._get_api_key())

    def chat_completion(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        response_format: Optional[dict[str, str]] = None,
        max_retries: int = 1,
    ) -> ProviderResponse:
        key = self._get_api_key()
        if not key:
            raise RuntimeError("OpenAI API key not configured or provider fallback disabled")

        try:
            from openai import OpenAI
        except ImportError:
            raise RuntimeError("openai package not installed; install to use optional OpenAI adapter")

        client = OpenAI(api_key=key, max_retries=max_retries)
        kwargs: dict = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format and response_format.get("type") == "json_object":
            kwargs["response_format"] = {"type": "json_object"}

        resp = client.chat.completions.create(**kwargs)
        content = resp.choices[0].message.content or ""
        return ProviderResponse(
            content=content,
            model=model,
            provider_name=self.name,
            metadata={"finish_reason": resp.choices[0].finish_reason},
        )
