"""
tests/test_provider_router.py

Unit tests for ProviderRouter, provider abstractions, and optional failover logic (W#8).
"""
import pytest
from app.providers.base import LLMProvider, ProviderResponse
from app.providers.router import ProviderRouter


class MockProvider(LLMProvider):
    def __init__(self, name: str, available: bool = True, should_fail: bool = False):
        self._name = name
        self._available = available
        self._should_fail = should_fail
        self.call_count = 0

    @property
    def name(self) -> str:
        return self._name

    def is_available(self) -> bool:
        return self._available

    def chat_completion(self, model, messages, temperature=0.0, response_format=None, max_retries=1):
        self.call_count += 1
        if self._should_fail:
            raise RuntimeError(f"{self._name} simulated failure")
        return ProviderResponse(
            content='{"is_suspicious": false, "confidence": 0.1, "reasoning": "mock clean"}',
            model=model,
            provider_name=self._name,
        )


def test_provider_router_primary_success():
    router = ProviderRouter()
    p1 = MockProvider("groq", available=True, should_fail=False)
    router.register_provider(p1)

    res = router.execute_chat("analyzer", "test-model", [{"role": "user", "content": "hi"}])
    assert res.provider_name == "groq"
    assert p1.call_count == 1


def test_provider_router_fallback_when_primary_fails(monkeypatch):
    from app.config import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "analyzer_providers", "groq,openai")

    router = ProviderRouter()
    p1 = MockProvider("groq", available=True, should_fail=True)
    p2 = MockProvider("openai", available=True, should_fail=False)
    router.register_provider(p1)
    router.register_provider(p2)

    res = router.execute_chat("analyzer", "test-model", [{"role": "user", "content": "hi"}])
    assert res.provider_name == "openai"
    assert p1.call_count == 1
    assert p2.call_count == 1


def test_provider_router_raises_when_all_fail(monkeypatch):
    from app.config import get_settings
    settings = get_settings()
    monkeypatch.setattr(settings, "analyzer_providers", "groq")

    router = ProviderRouter()
    p1 = MockProvider("groq", available=True, should_fail=True)
    router.register_provider(p1)

    with pytest.raises(RuntimeError):
        router.execute_chat("analyzer", "test-model", [{"role": "user", "content": "hi"}])


def test_openai_provider_routes_to_opencode_zen(monkeypatch):
    """With only OPENCODE_ZEN_KEY configured, the 'openai' slot targets Zen."""
    from app.config import get_settings
    from app.providers.openai_provider import OpenAIProvider
    settings = get_settings()
    monkeypatch.setattr(settings, "openai_api_key", "")
    monkeypatch.setattr(settings, "openai_base_url", "")
    monkeypatch.setattr(settings, "opencode_zen_key", "test-zen-key-not-real")
    monkeypatch.setattr(settings, "opencode_zen_base_url", "https://zen.example/v1")
    monkeypatch.setattr(settings, "opencode_zen_model", "space-bunny-free")

    p = OpenAIProvider()
    assert p._get_api_key() == "test-zen-key-not-real"
    assert p._get_base_url() == "https://zen.example/v1"
    assert p.resolve_model("openai/gpt-oss-120b") == "space-bunny-free"


def test_openai_provider_prefers_explicit_openai_credentials(monkeypatch):
    """A real OpenAI key/base URL wins over the Zen fallback slot."""
    from app.config import get_settings
    from app.providers.openai_provider import OpenAIProvider
    settings = get_settings()
    monkeypatch.setattr(settings, "openai_api_key", "sk-real-openai")
    monkeypatch.setattr(settings, "openai_base_url", "https://api.example/v1")
    monkeypatch.setattr(settings, "openai_model", "gpt-4o-mini")
    monkeypatch.setattr(settings, "opencode_zen_key", "test-zen-key-not-real")

    p = OpenAIProvider()
    assert p._get_api_key() == "sk-real-openai"
    assert p._get_base_url() == "https://api.example/v1"
    assert p.resolve_model("openai/gpt-oss-120b") == "gpt-4o-mini"
