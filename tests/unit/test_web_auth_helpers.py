from __future__ import annotations

import hashlib
import hmac
import time

import pytest
from fastapi import HTTPException

from app.config import settings
from app.web import auth as auth_mod


def _set_secret(monkeypatch, value: str | None = "test-secret") -> None:
    monkeypatch.setattr(settings, "WEB_SESSION_SECRET", value)


def test_create_and_read_signed_token_roundtrip(monkeypatch):
    _set_secret(monkeypatch)
    token = auth_mod._create_signed_token({"hello": "world"})
    payload = auth_mod._read_signed_token(token)
    assert payload == {"hello": "world"}


def test_create_signed_token_requires_secret(monkeypatch):
    _set_secret(monkeypatch, None)
    with pytest.raises(HTTPException) as exc:
        auth_mod._create_signed_token({"a": 1})
    assert exc.value.status_code == 503


def test_read_signed_token_rejects_missing_token(monkeypatch):
    _set_secret(monkeypatch)
    with pytest.raises(ValueError):
        auth_mod._read_signed_token(None)


def test_read_signed_token_rejects_tampered_signature(monkeypatch):
    _set_secret(monkeypatch)
    token = auth_mod._create_signed_token({"a": 1})
    payload, _sig = token.rsplit(".", 1)
    tampered = f"{payload}.deadbeef"
    with pytest.raises(ValueError):
        auth_mod._read_signed_token(tampered)


def test_create_login_state_and_read_back(monkeypatch):
    _set_secret(monkeypatch)
    token, state, nonce, challenge = auth_mod.create_login_state()
    read_nonce, _verifier = auth_mod.read_login_state(token, state)
    assert read_nonce == nonce
    assert challenge


def test_read_login_state_rejects_wrong_state(monkeypatch):
    _set_secret(monkeypatch)
    token, _state, _nonce, _challenge = auth_mod.create_login_state()
    with pytest.raises(HTTPException) as exc:
        auth_mod.read_login_state(token, "someone-elses-state")
    assert exc.value.status_code == 401


def test_read_login_state_rejects_expired_state(monkeypatch):
    _set_secret(monkeypatch)
    monkeypatch.setattr(auth_mod, "LOGIN_STATE_MAX_AGE_SECONDS", -1)
    token, state, _nonce, _challenge = auth_mod.create_login_state()
    with pytest.raises(HTTPException) as exc:
        auth_mod.read_login_state(token, state)
    assert exc.value.status_code == 401


def test_require_oidc_config_raises_when_incomplete(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_LOGIN_CLIENT_ID", None)
    with pytest.raises(HTTPException) as exc:
        auth_mod._require_oidc_config()
    assert exc.value.status_code == 503


def test_create_session_token_requires_secret(monkeypatch):
    _set_secret(monkeypatch, None)
    with pytest.raises(HTTPException) as exc:
        auth_mod.create_session_token(101)
    assert exc.value.status_code == 503


def test_get_session_user_id_requires_token(monkeypatch):
    _set_secret(monkeypatch)
    with pytest.raises(HTTPException) as exc:
        auth_mod.get_session_user_id(None)
    assert exc.value.status_code == 401


def test_get_session_user_id_rejects_expired_session(monkeypatch):
    _set_secret(monkeypatch)
    monkeypatch.setattr(settings, "WEB_SESSION_MAX_AGE_SECONDS", -1)
    token = auth_mod.create_session_token(101)
    with pytest.raises(HTTPException) as exc:
        auth_mod.get_session_user_id(token)
    assert exc.value.status_code == 401


def test_require_pro_web_user_rejects_unknown_user(monkeypatch, fake_supabase):
    from app import database

    monkeypatch.setattr(database, "supabase", fake_supabase)
    _set_secret(monkeypatch)
    token = auth_mod.create_session_token(999)

    class _Request:
        cookies = {auth_mod.SESSION_COOKIE_NAME: token}

    with pytest.raises(HTTPException) as exc:
        auth_mod.require_pro_web_user(_Request())
    assert exc.value.status_code == 401


def test_require_authenticated_user_allows_any_active_user(monkeypatch, fake_supabase):
    from app import database

    monkeypatch.setattr(database, "supabase", fake_supabase)
    fake_supabase.seed("users", [{"id": 55, "username": "starter", "is_active": True, "plan": "starter"}])
    _set_secret(monkeypatch)
    token = auth_mod.create_session_token(55)

    class _Request:
        cookies = {auth_mod.SESSION_COOKIE_NAME: token}

    user = auth_mod.require_authenticated_user(_Request())
    assert user["id"] == 55


def test_require_authenticated_user_rejects_inactive_user(monkeypatch, fake_supabase):
    from app import database

    monkeypatch.setattr(database, "supabase", fake_supabase)
    fake_supabase.seed("users", [{"id": 56, "username": "inactive", "is_active": False, "plan": "starter"}])
    _set_secret(monkeypatch)
    token = auth_mod.create_session_token(56)

    class _Request:
        cookies = {auth_mod.SESSION_COOKIE_NAME: token}

    with pytest.raises(HTTPException) as exc:
        auth_mod.require_authenticated_user(_Request())
    assert exc.value.status_code == 401


def _widget_payload(bot_token: str, **overrides):
    data = {"id": "123", "first_name": "Ana", "auth_date": str(int(time.time()))}
    data.update(overrides)
    items = [f"{k}={v}" for k, v in sorted(data.items()) if v is not None]
    data_check_string = "\n".join(items)
    secret_key = hashlib.sha256(bot_token.encode("utf-8")).digest()
    data["hash"] = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    return data


def test_verify_telegram_widget_data_accepts_valid_payload(monkeypatch):
    monkeypatch.setattr(settings, "BOT_TOKEN", "bot-token")
    payload = _widget_payload("bot-token")

    telegram_id = auth_mod.verify_telegram_widget_data(payload)

    assert telegram_id == 123


def test_verify_telegram_widget_data_requires_bot_token(monkeypatch):
    monkeypatch.setattr(settings, "BOT_TOKEN", None)
    with pytest.raises(HTTPException) as exc:
        auth_mod.verify_telegram_widget_data({"id": "1", "auth_date": "1", "hash": "x"})
    assert exc.value.status_code == 503


def test_verify_telegram_widget_data_requires_fields(monkeypatch):
    monkeypatch.setattr(settings, "BOT_TOKEN", "bot-token")
    with pytest.raises(HTTPException) as exc:
        auth_mod.verify_telegram_widget_data({"id": "1"})
    assert exc.value.status_code == 400


def test_verify_telegram_widget_data_rejects_bad_signature(monkeypatch):
    monkeypatch.setattr(settings, "BOT_TOKEN", "bot-token")
    payload = _widget_payload("bot-token")
    payload["hash"] = "0" * 64
    with pytest.raises(HTTPException) as exc:
        auth_mod.verify_telegram_widget_data(payload)
    assert exc.value.status_code == 401


def test_verify_telegram_widget_data_rejects_stale_auth_date(monkeypatch):
    monkeypatch.setattr(settings, "BOT_TOKEN", "bot-token")
    payload = _widget_payload("bot-token", auth_date=str(int(time.time()) - 10_000))
    with pytest.raises(HTTPException) as exc:
        auth_mod.verify_telegram_widget_data(payload)
    assert exc.value.status_code == 401


def test_verify_telegram_widget_data_rejects_invalid_auth_date(monkeypatch):
    monkeypatch.setattr(settings, "BOT_TOKEN", "bot-token")
    payload = _widget_payload("bot-token")
    payload["auth_date"] = "not-a-number"
    # Recompute hash so the signature itself stays valid up to the auth_date parsing failure.
    data_no_hash = {k: v for k, v in payload.items() if k != "hash"}
    items = [f"{k}={v}" for k, v in sorted(data_no_hash.items()) if v is not None]
    secret_key = hashlib.sha256("bot-token".encode("utf-8")).digest()
    payload["hash"] = hmac.new(secret_key, "\n".join(items).encode("utf-8"), hashlib.sha256).hexdigest()

    with pytest.raises(HTTPException) as exc:
        auth_mod.verify_telegram_widget_data(payload)
    assert exc.value.status_code == 400


def test_verify_telegram_widget_data_rejects_non_positive_id(monkeypatch):
    monkeypatch.setattr(settings, "BOT_TOKEN", "bot-token")
    payload = _widget_payload("bot-token", id="0")

    with pytest.raises(HTTPException) as exc:
        auth_mod.verify_telegram_widget_data(payload)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_get_bot_username_returns_none_without_token(monkeypatch):
    monkeypatch.setattr(settings, "BOT_TOKEN", None)
    auth_mod._BOT_USERNAME_CACHE.clear()
    assert await auth_mod.get_bot_username() is None


@pytest.mark.asyncio
async def test_get_bot_username_fetches_and_caches(monkeypatch):
    monkeypatch.setattr(settings, "BOT_TOKEN", "bot-token")
    auth_mod._BOT_USERNAME_CACHE.clear()

    class _FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {"result": {"username": "MyBot"}}

    class _FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, _url: str):
            return _FakeResponse()

    monkeypatch.setattr(auth_mod.httpx, "AsyncClient", lambda timeout=5.0: _FakeClient())

    username = await auth_mod.get_bot_username()
    assert username == "MyBot"
    # Second call should hit the cache without calling httpx again.
    monkeypatch.setattr(auth_mod.httpx, "AsyncClient", lambda timeout=5.0: (_ for _ in ()).throw(AssertionError("should not be called")))
    assert await auth_mod.get_bot_username() == "MyBot"


@pytest.mark.asyncio
async def test_get_bot_username_returns_none_on_http_error(monkeypatch):
    monkeypatch.setattr(settings, "BOT_TOKEN", "bot-token")
    auth_mod._BOT_USERNAME_CACHE.clear()

    class _FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def get(self, _url: str):
            raise RuntimeError("network down")

    monkeypatch.setattr(auth_mod.httpx, "AsyncClient", lambda timeout=5.0: _FakeClient())

    assert await auth_mod.get_bot_username() is None


@pytest.mark.asyncio
async def test_exchange_telegram_code_returns_id_token(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_LOGIN_CLIENT_ID", "cid")
    monkeypatch.setattr(settings, "TELEGRAM_LOGIN_CLIENT_SECRET", "secret")
    monkeypatch.setattr(settings, "TELEGRAM_LOGIN_REDIRECT_URI", "https://api.example.test/callback")
    monkeypatch.setattr(settings, "WEB_APP_ORIGIN", "https://app.example.test")

    class _FakeResponse:
        is_error = False

        def json(self) -> dict:
            return {"id_token": "signed-token"}

    class _FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, *_args, **_kwargs):
            return _FakeResponse()

    monkeypatch.setattr(auth_mod.httpx, "AsyncClient", lambda timeout=10.0: _FakeClient())

    token = await auth_mod.exchange_telegram_code("auth-code", "verifier")
    assert token == "signed-token"


@pytest.mark.asyncio
async def test_exchange_telegram_code_raises_on_error_response(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_LOGIN_CLIENT_ID", "cid")
    monkeypatch.setattr(settings, "TELEGRAM_LOGIN_CLIENT_SECRET", "secret")
    monkeypatch.setattr(settings, "TELEGRAM_LOGIN_REDIRECT_URI", "https://api.example.test/callback")
    monkeypatch.setattr(settings, "WEB_APP_ORIGIN", "https://app.example.test")

    class _FakeResponse:
        is_error = True

        def json(self) -> dict:
            return {}

    class _FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, *_args, **_kwargs):
            return _FakeResponse()

    monkeypatch.setattr(auth_mod.httpx, "AsyncClient", lambda timeout=10.0: _FakeClient())

    with pytest.raises(HTTPException) as exc:
        await auth_mod.exchange_telegram_code("auth-code", "verifier")
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_exchange_telegram_code_raises_when_id_token_missing(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_LOGIN_CLIENT_ID", "cid")
    monkeypatch.setattr(settings, "TELEGRAM_LOGIN_CLIENT_SECRET", "secret")
    monkeypatch.setattr(settings, "TELEGRAM_LOGIN_REDIRECT_URI", "https://api.example.test/callback")
    monkeypatch.setattr(settings, "WEB_APP_ORIGIN", "https://app.example.test")

    class _FakeResponse:
        is_error = False

        def json(self) -> dict:
            return {}

    class _FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, *_args, **_kwargs):
            return _FakeResponse()

    monkeypatch.setattr(auth_mod.httpx, "AsyncClient", lambda timeout=10.0: _FakeClient())

    with pytest.raises(HTTPException) as exc:
        await auth_mod.exchange_telegram_code("auth-code", "verifier")
    assert exc.value.status_code == 401


def test_verify_telegram_id_token_accepts_valid_claims(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_LOGIN_CLIENT_ID", "cid")
    monkeypatch.setattr(settings, "TELEGRAM_LOGIN_CLIENT_SECRET", "secret")
    monkeypatch.setattr(settings, "TELEGRAM_LOGIN_REDIRECT_URI", "https://api.example.test/callback")
    monkeypatch.setattr(settings, "WEB_APP_ORIGIN", "https://app.example.test")

    class _FakeSigningKey:
        key = "public-key"

    class _FakeJWKClient:
        def __init__(self, _url: str) -> None:
            pass

        def get_signing_key_from_jwt(self, _token: str):
            return _FakeSigningKey()

    monkeypatch.setattr(auth_mod.jwt, "PyJWKClient", _FakeJWKClient)
    monkeypatch.setattr(auth_mod.jwt, "decode", lambda *_a, **_k: {"nonce": "expected-nonce", "id": 777})

    telegram_id = auth_mod.verify_telegram_id_token("some-id-token", "expected-nonce")
    assert telegram_id == 777


def test_verify_telegram_id_token_rejects_mismatched_nonce(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_LOGIN_CLIENT_ID", "cid")
    monkeypatch.setattr(settings, "TELEGRAM_LOGIN_CLIENT_SECRET", "secret")
    monkeypatch.setattr(settings, "TELEGRAM_LOGIN_REDIRECT_URI", "https://api.example.test/callback")
    monkeypatch.setattr(settings, "WEB_APP_ORIGIN", "https://app.example.test")

    class _FakeSigningKey:
        key = "public-key"

    class _FakeJWKClient:
        def __init__(self, _url: str) -> None:
            pass

        def get_signing_key_from_jwt(self, _token: str):
            return _FakeSigningKey()

    monkeypatch.setattr(auth_mod.jwt, "PyJWKClient", _FakeJWKClient)
    monkeypatch.setattr(auth_mod.jwt, "decode", lambda *_a, **_k: {"nonce": "other-nonce", "id": 777})

    with pytest.raises(HTTPException) as exc:
        auth_mod.verify_telegram_id_token("some-id-token", "expected-nonce")
    assert exc.value.status_code == 401


def test_verify_telegram_id_token_rejects_invalid_claims(monkeypatch):
    monkeypatch.setattr(settings, "TELEGRAM_LOGIN_CLIENT_ID", "cid")
    monkeypatch.setattr(settings, "TELEGRAM_LOGIN_CLIENT_SECRET", "secret")
    monkeypatch.setattr(settings, "TELEGRAM_LOGIN_REDIRECT_URI", "https://api.example.test/callback")
    monkeypatch.setattr(settings, "WEB_APP_ORIGIN", "https://app.example.test")

    class _FakeJWKClient:
        def __init__(self, _url: str) -> None:
            pass

        def get_signing_key_from_jwt(self, _token: str):
            raise ValueError("bad token")

    monkeypatch.setattr(auth_mod.jwt, "PyJWKClient", _FakeJWKClient)

    with pytest.raises(HTTPException) as exc:
        auth_mod.verify_telegram_id_token("some-id-token", "expected-nonce")
    assert exc.value.status_code == 401

