"""
app/providers/base.py

Abstract base interface for LLM providers.
Enables clean model-diversity and optional multi-provider execution
without requiring paid subscriptions (Groq remains primary free provider).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel, Field


class ProviderResponse(BaseModel):
    content: str
    model: str
    provider_name: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the provider (e.g. 'groq', 'openai', 'huggingface')."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is configured and available."""
        pass

    @abstractmethod
    def chat_completion(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.0,
        response_format: Optional[dict[str, str]] = None,
        max_retries: int = 1,
    ) -> ProviderResponse:
        """Execute chat completion request."""
        pass
