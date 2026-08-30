from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any

from fastapi import HTTPException, Request, status

from app.config import settings
from app.database import get_user
from app.services.subscription_service import get_subscription_service

SESSION_COOKIE_NAME = "ob_web_session"
TELEGRAM_LOGIN_MAX_AGE_SECONDS = 86_400


def verify_telegram_login(payload: dict[str, Any]) -> int:
    """Validates Telegram Login Widget data and returns its immutable user id."""
    received_hash = str(payload.get("hash") or "")
    auth_date = payload.get("auth_date")
    if not received_hash or not isinstance(auth_date, int):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram login")

    if auth_date > int(time.time()) + 60 or int(time.time()) - auth_date > TELEGRAM_LOGIN_MAX_AGE_SECONDS:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Telegram login expired")

    check_fields = {key: value for key, value in payload.items() if key != "hash" and value is not None}
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(check_fields.items()))
    secret_key = hashlib.sha256(settings.BOT_TOKEN.encode("utf-8")).digest()
    expected_hash = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_hash, received_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram login")

    telegram_id = payload.get("id")
    if not isinstance(telegram_id, int) or telegram_id <= 0:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Telegram login")
    return telegram_id


def create_session_token(user_id: int) -> str:
    secret = settings.WEB_SESSION_SECRET
    if not secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Web login is not configured")

    payload = json.dumps({"user_id": user_id, "issued_at": int(time.time())}, separators=(",", ":")).encode("utf-8")
    encoded_payload = base64.urlsafe_b64encode(payload).decode("ascii").rstrip("=")
    signature = hmac.new(secret.encode("utf-8"), encoded_payload.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{encoded_payload}.{signature}"


def get_session_user_id(token: str | None) -> int:
    if not token or not settings.WEB_SESSION_SECRET:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    try:
        encoded_payload, signature = token.rsplit(".", 1)
        expected_signature = hmac.new(
            settings.WEB_SESSION_SECRET.encode("utf-8"), encoded_payload.encode("ascii"), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("invalid signature")

        padded_payload = encoded_payload + "=" * (-len(encoded_payload) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded_payload.encode("ascii")))
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