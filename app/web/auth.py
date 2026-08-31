from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any

import httpx
import jwt
from fastapi import HTTPException, Request, status

from app.config import settings
from app.database import get_user
from app.services.subscription_service import get_subscription_service

SESSION_COOKIE_NAME = "ob_web_session"
LOGIN_STATE_COOKIE_NAME = "ob_telegram_login"
LOGIN_STATE_MAX_AGE_SECONDS = 600
TELEGRAM_AUTHORIZATION_URL = "https://oauth.telegram.org/auth"
TELEGRAM_TOKEN_URL = "https://oauth.telegram.org/token"
TELEGRAM_JWKS_URL = "https://oauth.telegram.org/.well-known/jwks.json"
TELEGRAM_ISSUER = "https://oauth.telegram.org"

# simple cache for bot username
_BOT_USERNAME_CACHE: dict[str, int] = {}


async def get_bot_username() -> str | None:
    """Return the bot username using the configured BOT_TOKEN (cached briefly)."""
    from app.config import settings as _settings
    import httpx

    token = _settings.BOT_TOKEN
    if not token:
        return None
    # cache for 60 seconds
    cached = _BOT_USERNAME_CACHE.get("username")
    ts = _BOT_USERNAME_CACHE.get("ts", 0)
    if cached and (time.time() - ts) < 60:
        return cached
    url = f"https://api.telegram.org/bot{token}/getMe"
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            r = await client.get(url)
            r.raise_for_status()
            j = r.json()
            username = j.get("result", {}).get("username")
            if isinstance(username, str) and username:
                _BOT_USERNAME_CACHE["username"] = username
                _BOT_USERNAME_CACHE["ts"] = int(time.time())
                return username
        except Exception:
            return None
    return None


def _require_oidc_config() -> tuple[str, str, str, str]:
    values = (
        settings.TELEGRAM_LOGIN_CLIENT_ID,
        settings.TELEGRAM_LOGIN_CLIENT_SECRET,
        settings.TELEGRAM_LOGIN_REDIRECT_URI,
        settings.WEB_APP_ORIGIN,
    )
    if not all(values):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Telegram Login is not configured")
    return tuple(str(value) for value in values)


def _create_signed_token(payload: dict[str, Any]) -> str:
    secret = settings.WEB_SESSION_SECRET
    if not secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Web login is not configured")
    encoded_payload = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")).decode("ascii").rstrip("=")
    signature = hmac.new(secret.encode("utf-8"), encoded_payload.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{encoded_payload}.{signature}"


def _read_signed_token(token: str | None) -> dict[str, Any]:
    if not token or not settings.WEB_SESSION_SECRET:
        raise ValueError("missing token")
    encoded_payload, signature = token.rsplit(".", 1)
    expected_signature = hmac.new(settings.WEB_SESSION_SECRET.encode("utf-8"), encoded_payload.encode("ascii"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected_signature):
        raise ValueError("invalid signature")
    padded_payload = encoded_payload + "=" * (-len(encoded_payload) % 4)
    payload = json.loads(base64.urlsafe_b64decode(padded_payload.encode("ascii")))
    if not isinstance(payload, dict):
        raise ValueError("invalid payload")
    return payload


def create_login_state() -> tuple[str, str, str, str]:
    """Creates state, nonce and PKCE material stored in a short-lived signed cookie."""
    state = secrets.token_urlsafe(32)
    nonce = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode("ascii")).digest()).decode("ascii").rstrip("=")
    token = _create_signed_token({"state": state, "nonce": nonce, "verifier": verifier, "issued_at": int(time.time())})
    return token, state, nonce, challenge


def read_login_state(token: str | None, returned_state: str) -> tuple[str, str]:
    try:
        payload = _read_signed_token(token)
        if int(time.time()) - int(payload["issued_at"]) > LOGIN_STATE_MAX_AGE_SECONDS:
            raise ValueError("expired state")
        if not hmac.compare_digest(str(payload["state"]), returned_state):
            raise ValueError("invalid state")
        return str(payload["nonce"]), str(payload["verifier"])
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram login state")


async def exchange_telegram_code(code: str, verifier: str) -> str:
    client_id, client_secret, redirect_uri, _ = _require_oidc_config()
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            TELEGRAM_TOKEN_URL,
            data={"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri, "client_id": client_id, "code_verifier": verifier},
            auth=(client_id, client_secret),
        )
    if response.is_error:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Telegram authorization failed")
    id_token = response.json().get("id_token")
    if not isinstance(id_token, str):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Telegram authorization failed")
    return id_token


def verify_telegram_id_token(id_token: str, nonce: str) -> int:
    client_id, _, _, _ = _require_oidc_config()
    try:
        signing_key = jwt.PyJWKClient(TELEGRAM_JWKS_URL).get_signing_key_from_jwt(id_token)
        claims = jwt.decode(
            id_token,
            signing_key.key,
            algorithms=["RS256"],
            audience=client_id,
            issuer=TELEGRAM_ISSUER,
            options={"require": ["exp", "iat", "iss", "aud", "nonce"]},
        )
        if not hmac.compare_digest(str(claims["nonce"]), nonce):
            raise ValueError("invalid nonce")
        telegram_id = int(claims.get("id", claims.get("sub")))
        if telegram_id <= 0:
            raise ValueError("invalid user id")
        return telegram_id
    except (jwt.PyJWTError, KeyError, TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram identity token")


def create_session_token(user_id: int) -> str:
    secret = settings.WEB_SESSION_SECRET
    if not secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Web login is not configured")

    return _create_signed_token({"user_id": user_id, "issued_at": int(time.time())})


def get_session_user_id(token: str | None) -> int:
    if not token or not settings.WEB_SESSION_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    try:
        payload = _read_signed_token(token)
        user_id = payload["user_id"]
        issued_at = payload["issued_at"]
        if not isinstance(user_id, int) or not isinstance(issued_at, int):
            raise ValueError("invalid payload")
        if int(time.time()) - issued_at > settings.WEB_SESSION_MAX_AGE_SECONDS:
            raise ValueError("expired session")
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    return user_id


def require_pro_web_user(request: Request) -> dict[str, Any]:
    user_id = get_session_user_id(request.cookies.get(SESSION_COOKIE_NAME))
    user = get_user(user_id)
    if not user or not user.get("is_active", True):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    if not get_subscription_service().can_access_web_app(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Professional plan or higher required")
    return user


def verify_telegram_widget_data(data: dict[str, Any]) -> int:
    """Verify Telegram Login Widget data (legacy) and return telegram user id.

    Procedure from Telegram docs: build data_check_string from sorted keys
    (except 'hash'), compute SHA256 of bot token as secret_key, then HMAC-SHA256
    of data_check_string and compare hex digest to provided hash.
    """
    token = settings.BOT_TOKEN
    if not token:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Telegram bot token not configured")
    required = ["id", "auth_date", "hash"]
    if not all(k in data for k in required):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid telegram widget payload")
    hash_value = str(data.get("hash"))
    # prepare data_check_string
    items = []
    for k in sorted(k for k in data.keys() if k != "hash"):
        v = data.get(k)
        if v is None:
            continue
        items.append(f"{k}={v}")
    data_check_string = "\n".join(items)
    secret_key = hashlib.sha256(token.encode("utf-8")).digest()
    computed = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(computed, hash_value):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid telegram signature")
    # check timestamp freshness (allow 5 minutes)
    try:
        auth_date = int(data.get("auth_date"))
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid auth_date")
    if int(time.time()) - auth_date > 300:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Stale telegram auth data")
    telegram_id = int(data.get("id"))
    if telegram_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid telegram id")
    return telegram_id