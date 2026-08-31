from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import database
from app.config import settings
from app.web.routes import router


def _client(monkeypatch, fake_supabase) -> TestClient:
    monkeypatch.setattr(database, "supabase", fake_supabase)
    monkeypatch.setattr(settings, "WEB_SESSION_SECRET", "test-web-session-secret")
    monkeypatch.setattr(settings, "WEB_SESSION_COOKIE_SECURE", False)
    monkeypatch.setattr(settings, "WEB_APP_ORIGIN", "https://app.example.test")
    monkeypatch.setattr(settings, "TELEGRAM_LOGIN_CLIENT_ID", "123456")
    monkeypatch.setattr(settings, "TELEGRAM_LOGIN_CLIENT_SECRET", "test-client-secret")
    monkeypatch.setattr(settings, "TELEGRAM_LOGIN_REDIRECT_URI", "https://api.example.test/api/web/auth/telegram/callback")
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def test_telegram_login_start_creates_pkce_state_cookie(monkeypatch, fake_supabase):
    client = _client(monkeypatch, fake_supabase)

    response = client.get("/api/web/auth/telegram/start", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"].startswith("https://oauth.telegram.org/auth?")
    assert "code_challenge=" in response.headers["location"]
    assert "ob_telegram_login" in response.headers["set-cookie"]


def _complete_login(monkeypatch, client: TestClient, user_id: int):
    start = client.get("/api/web/auth/telegram/start", follow_redirects=False)
    state = start.headers["location"].split("state=")[1].split("&")[0]

    async def fake_exchange(_code: str, _verifier: str) -> str:
        return "signed-id-token"

    monkeypatch.setattr("app.web.routes.exchange_telegram_code", fake_exchange)
    monkeypatch.setattr("app.web.routes.verify_telegram_id_token", lambda _token, _nonce: user_id)
    return client.get(f"/api/web/auth/telegram/callback?code=authorization-code&state={state}", follow_redirects=False)


def test_telegram_login_allows_professional_user(monkeypatch, fake_supabase):
    fake_supabase.seed("users", [{"id": 101, "username": "ana", "is_active": True, "plan": "professional"}])
    client = _client(monkeypatch, fake_supabase)

    response = _complete_login(monkeypatch, client, 101)

    assert response.status_code == 302
    assert response.headers["location"] == "https://app.example.test"
    assert "ob_web_session" in response.headers["set-cookie"]


def test_telegram_login_allows_enterprise_user(monkeypatch, fake_supabase):
    fake_supabase.seed("users", [{"id": 102, "username": "empresa", "is_active": True, "plan": "enterprise"}])
    client = _client(monkeypatch, fake_supabase)

    assert _complete_login(monkeypatch, client, 102).status_code == 302


def test_telegram_login_rejects_starter_user(monkeypatch, fake_supabase):
    fake_supabase.seed("users", [{"id": 103, "username": "starter", "is_active": True, "plan": "starter"}])
    client = _client(monkeypatch, fake_supabase)

    assert _complete_login(monkeypatch, client, 103).status_code == 403


def test_telegram_login_rejects_invalid_state(monkeypatch, fake_supabase):
    client = _client(monkeypatch, fake_supabase)
    client.get("/api/web/auth/telegram/start", follow_redirects=False)

    response = client.get("/api/web/auth/telegram/callback?code=authorization-code&state=attacker-state", follow_redirects=False)

    assert response.status_code == 401


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
    assert _complete_login(monkeypatch, client, 101).status_code == 302

    response = client.get("/api/web/alerts")

    assert response.status_code == 200
    assert [alert["title"] for alert in response.json()] == ["Visible"]
    assert response.json()[0]["source_url"] == "https://source.test/feed"


def test_alerts_reject_invalid_limit(monkeypatch, fake_supabase):
    fake_supabase.seed("users", [{"id": 101, "username": "ana", "is_active": True, "plan": "professional"}])
    client = _client(monkeypatch, fake_supabase)
    _complete_login(monkeypatch, client, 101)

    assert client.get("/api/web/alerts?limit=101").status_code == 422