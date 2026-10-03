"""app/auth.py — GitHub OAuth login (manual httpx flow, no new dependencies).

Gives approvals authenticated identity: actor = verified GitHub username from
the access token, never a self-typed string. No login infra existed before;
anonymous/empty actors were already rejected, but names were self-asserted.
"""
from __future__ import annotations

import secrets
import urllib.parse

GITHUB_AUTHORIZE = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN = "https://github.com/login/oauth/access_token"
GITHUB_USER = "https://api.github.com/user"


def login_url(client_id: str) -> tuple[str, str]:
    """Return (authorize_url, state). Caller stores state in session for CSRF check."""
    state = secrets.token_hex(16)
    q = urllib.parse.urlencode({"client_id": client_id, "scope": "read:user", "state": state})
    return f"{GITHUB_AUTHORIZE}?{q}", state


def exchange_code(client_id: str, client_secret: str, code: str) -> str:
    """Exchange an OAuth code for an access token. Raises on failure."""
    import httpx

    r = httpx.post(
        GITHUB_TOKEN,
        data={"client_id": client_id, "client_secret": client_secret, "code": code},
        headers={"Accept": "application/json"},
        timeout=20,
    )
    r.raise_for_status()
    token = r.json().get("access_token", "")
    if not token:
        raise RuntimeError("GitHub token exchange returned no access_token")
    return token


def fetch_username(token: str) -> str:
    """Return the verified GitHub login for a token. Raises on failure."""
    import httpx

    r = httpx.get(GITHUB_USER, headers={"Authorization": f"Bearer {token}",
                                        "Accept": "application/vnd.github+json"},
                  timeout=20)
    r.raise_for_status()
    login = (r.json().get("login") or "").strip()
    if not login:
        raise RuntimeError("GitHub user endpoint returned no login")
    return login
