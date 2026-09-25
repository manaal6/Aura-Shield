"""
app/providers/router.py

Provider router for model routing and role-based execution.
Prioritizes configured free Groq keys, falling back only when configured.
Tracks provider attribution explicitly for research honesty:
- model diversity = evaluated
- provider independence = only claimed if secondary provider was actually executed
"""
from __future__ import annotations

import logging
from typing import Optional
from functools import lru_cache

from app.config import get_settings
from app.providers.base import LLMProvider, ProviderResponse
from app.providers.groq_provider import GroqProvider
from app.providers.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class ProviderRouter:
    def __init__(self):
        self._providers: dict[str, LLMProvider] = {
            "groq": GroqProvider(),
            "openai": OpenAIProvider(),
        }

    def register_provider(self, provider: LLMProvider) -> None:
        self._providers[provider.name] = provider

    def get_provider(self, name: str) -> Optional[LLMProvider]:
        return self._providers.get(name)

    def execute_chat(
        self,
        role: str,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        response_format: Optional[dict[str, str]] = None,
        max_retries: int = 1,
    ) -> ProviderResponse:
        settings = get_settings()
        
        # Determine priority list
        if role == "analyzer":
            order_str = getattr(settings, "analyzer_providers", "groq")
        elif role == "constitution":
            order_str = getattr(settings, "constitution_providers", "groq")
        else:
            order_str = "groq"

        providers_to_try = [p.strip() for p in order_str.split(",") if p.strip()]
        if not providers_to_try:
            providers_to_try = ["groq"]

        last_error = None
        for p_name in providers_to_try:
            prov = self.get_provider(p_name)
            if not prov or not prov.is_available():
                continue

            try:
                # If provider is secondary and model is a groq-specific string, map to fallback model if applicable
                req_model = model
                if p_name == "openai" and "gpt-oss" in model:
                    req_model = getattr(settings, "openai_model", "gpt-4o-mini")

                return prov.chat_completion(
                    model=req_model,
                    messages=messages,
                    temperature=temperature,
                    response_format=response_format,
                    max_retries=max_retries,
                )
            except Exception as exc:
                last_error = exc
                logger.warning("Provider %s failed for role %s: %s", p_name, role, exc)

        if last_error:
            raise last_error
        raise RuntimeError(f"No available provider could fulfill request for role {role}")


@lru_cache
def get_provider_router() -> ProviderRouter:
    return ProviderRouter()
