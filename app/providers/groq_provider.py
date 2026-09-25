"""
app/providers/groq_provider.py

Primary LLM provider implementation using Groq.
Supports multiple keys rotation from environment if present without leaking secrets.
"""
from __future__ import annotations

import logging
from typing import Optional
from groq import Groq

from app.config import get_settings
from app.providers.base import LLMProvider, ProviderResponse

logger = logging.getLogger(__name__)


class GroqProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None):
        self._explicit_key = api_key

    @property
    def name(self) -> str:
        return "groq"

    def _get_api_key(self) -> str:
        if self._explicit_key:
            return self._explicit_key
        settings = get_settings()
        return settings.groq_api_key or ""

    def is_available(self) -> bool:
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
            raise RuntimeError("Groq API key not configured")

        client = Groq(api_key=key, max_retries=max_retries)
        kwargs: dict = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format:
            kwargs["response_format"] = response_format

        resp = client.chat.completions.create(**kwargs)
        content = resp.choices[0].message.content or ""
        return ProviderResponse(
            content=content,
            model=model,
            provider_name=self.name,
            metadata={"finish_reason": resp.choices[0].finish_reason},
        )
