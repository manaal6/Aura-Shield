"""
app/llm_client.py

Wraps the downstream "protected" LLM call - i.e. the assistant AURA Shield
sits in front of. Kept separate from llm_analyzer.py even though both use
Groq, because conceptually these are two different trust roles: one is
the thing being defended, the other is part of the defense.
"""
import logging
from groq import Groq
from app.config import get_settings

logger = logging.getLogger(__name__)


def call_protected_llm(user_prompt: str, source_content: str | None = None) -> str:
    settings = get_settings()
    if not settings.groq_api_key:
        return "[No Groq API key configured - downstream LLM call skipped in this environment.]"

    prompt = user_prompt if not source_content else f"{user_prompt}\n\nContext:\n{source_content}"

    try:
        client = Groq(api_key=settings.groq_api_key)
        response = client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content
    except Exception as exc:
        logger.error("Downstream LLM call failed: %s", exc)
        return f"[Downstream LLM call failed: {type(exc).__name__}]"
