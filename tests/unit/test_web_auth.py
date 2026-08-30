from __future__ import annotations

import hashlib
import hmac
import time

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import database
from app.config import settings
from app.web.routes import router


def _telegram_payload(user_id: int) -> dict:
    payload = {"id": user_id, "first_name": "Ana", "username": "ana", "auth_date": int(time.time())}
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(payload.items()))
    secret = hashlib.sha256(settings.BOT_TOKEN.encode("utf-8")).digest()
    payload["hash"] = hmac.new(secret, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    return payload


def _client(monkeypatch, fake_supabase) -> TestClient:
    monkeypatch.setattr(database, "supabase", fake_supabase)
    monkeypatch.setattr(settings, "WEB_SESSION_SECRET", "test-web-session-secret")
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_telegram_login_allows_professional_user(monkeypatch, fake_supabase):
    fake_supabase.seed("users", [{"id": 101, "username": "ana", "is_active": True, "plan": "professional"}])
    client = _client(monkeypatch, fake_supabase)

    response = client.post("/api/web/auth/telegram", json=_telegram_payload(101))

    assert response.status_code == 200
    assert response.json()["user"]["plan"] == "professional"
    assert "ob_web_session" in response.headers["set-cookie"]


def test_telegram_login_allows_enterprise_user(monkeypatch, fake_supabase):
    fake_supabase.seed("users", [{"id": 102, "username": "empresa", "is_active": True, "plan": "enterprise"}])
    client = _client(monkeypatch, fake_supabase)

    assert client.post("/api/web/auth/telegram", json=_telegram_payload(102)).status_code == 200


def test_telegram_login_rejects_starter_user(monkeypatch, fake_supabase):
    fake_supabase.seed("users", [{"id": 103, "username": "starter", "is_active": True, "plan": "starter"}])
    client = _client(monkeypatch, fake_supabase)

    assert client.post("/api/web/auth/telegram", json=_telegram_payload(103)).status_code == 403


def test_protected_endpoint_rejects_unauthenticated_user(monkeypatch, fake_supabase):
    client = _client(monkeypatch, fake_supabase)

    assert client.get("/api/web/alerts").status_code == 401


def test_alerts_are_isolated_to_authenticated_user(monkeypatch, fake_supabase):
    fake_supabase.seed("users", [{"id": 101, "username": "ana", "is_active": True, "plan": "professional"}])
    fake_supabase.seed("feeds", [{"id": 7, "user_id": 101, "url": "https://source.test/feed", "is_active": True}])
    fake_supabase.seed(
        "alerts",
        [
            {"id": 1, "user_id": 101, "feed_id": 7, "post_title": "Visible", "post_content": "Contenido"},
            {"id": 2, "user_id": 999, "feed_id": 8, "post_title": "Privada", "post_content": "No visible"},
        ],
    )
    client = _client(monkeypatch, fake_supabase)
    assert client.post("/api/web/auth/telegram", json=_telegram_payload(101)).status_code == 200

    response = client.get("/api/web/alerts")

    assert response.status_code == 200
    assert [alert["title"] for alert in response.json()] == ["Visible"]
    assert response.json()[0]["source_url"] == "https://source.test/feed"


def test_alerts_reject_invalid_limit(monkeypatch, fake_supabase):
    fake_supabase.seed("users", [{"id": 101, "username": "ana", "is_active": True, "plan": "professional"}])
    client = _client(monkeypatch, fake_supabase)
    client.post("/api/web/auth/telegram", json=_telegram_payload(101))

    assert client.get("/api/web/alerts?limit=101").status_code == 422