"""research/groq_pool.py — safe multi-key rotation (values never logged/printed).

Picks up GROQ_API_KEY, GROQ_API_KEY_2, ..._3 live from the environment on each
call (no caching of secrets beyond the process env). Round-robins across
configured keys; per-key failure blacklists that key for the process lifetime.
Never raises key material into logs, results, or exceptions.
"""
from __future__ import annotations

import itertools
import os
import threading

_lock = threading.Lock()
_dead: set[str] = set()
_order: list[str] = []
_idx = itertools.count()


def _dotenv_values() -> dict[str, str]:
    """Parse GROQ_API_KEY* entries from repo .env (fallback when not in os.environ)."""
    out: dict[str, str] = {}
    try:
        from pathlib import Path as _P
        env = _P(__file__).resolve().parent.parent / ".env"
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("GROQ_API_KEY") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip("'\"")
    except OSError:
        pass
    return out


def _secret(name: str) -> str:
    return os.environ.get(name) or _dotenv_values().get(name, "")


def available_key_names() -> list[str]:
    names = ["GROQ_API_KEY"] + [f"GROQ_API_KEY_{i}" for i in range(2, 10)]
    return [n for n in names if _secret(n)]


def _pool() -> list[str]:
    global _order
    with _lock:
        live = [n for n in available_key_names() if n not in _dead]
        if live != _order:
            _order = live
        return list(_order)


def mark_dead(name: str) -> None:
    with _lock:
        _dead.add(name)


def chat(model: str, messages: list[dict], **kwargs):
    """One chat call with rotation. Returns (key_name, response). Raises RuntimeError if all keys fail."""
    from groq import Groq
    pool = _pool()
    if not pool:
        raise RuntimeError("no live Groq keys (all missing or blacklisted)")
    errors = []
    for _ in pool:
        name = pool[next(_idx) % len(pool)]
        try:
            client = Groq(api_key=_secret(name), max_retries=0)
            return name, client.chat.completions.create(model=model, messages=messages, **kwargs)
        except Exception as exc:  # noqa: BLE001 — key value never included
            # Only blacklist the key for credential/quota failures. A NotFoundError
            # means the MODEL ID is wrong — the key itself is healthy. (B32)
            if type(exc).__name__ in ("NotFoundError",):
                raise RuntimeError(f"model not found: {model} ({type(exc).__name__})")
            mark_dead(name)
            errors.append(f"{name}: {type(exc).__name__}")
    raise RuntimeError(f"all Groq keys failed: {'; '.join(errors)}")
