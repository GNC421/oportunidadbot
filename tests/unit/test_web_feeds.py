from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import database
from app.config import settings
from app.services import feed_parser
from app.web.routes import router


def _client(monkeypatch, fake_supabase) -> TestClient:
    monkeypatch.setattr(database, "supabase", fake_supabase)
    monkeypatch.setattr(settings, "WEB_SESSION_SECRET", "test-web-session-secret")
    monkeypatch.setattr(settings, "WEB_SESSION_COOKIE_SECURE", False)
    monkeypatch.setattr(settings, "WEB_APP_ORIGIN", "https://app.example.test")
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _login(client: TestClient, user_id: int) -> None:
    from app.web.auth import create_session_token
    from app.web.routes import SESSION_COOKIE_NAME

    client.cookies.set(SESSION_COOKIE_NAME, create_session_token(user_id))


def _seed_professional_user(fake_supabase, user_id: int = 101) -> None:
    fake_supabase.seed("users", [{"id": user_id, "username": "ana", "is_active": True, "plan": "professional"}])


def test_list_feeds_requires_authentication(monkeypatch, fake_supabase):
    client = _client(monkeypatch, fake_supabase)

    assert client.get("/api/web/feeds").status_code == 401


def test_list_feeds_only_returns_own_feeds(monkeypatch, fake_supabase):
    _seed_professional_user(fake_supabase)
    fake_supabase.seed(
        "feeds",
        [
            {"id": 1, "user_id": 101, "url": "https://source.test/mine", "is_active": True},
            {"id": 2, "user_id": 999, "url": "https://source.test/other", "is_active": True},
        ],
    )
    client = _client(monkeypatch, fake_supabase)
    _login(client, 101)

    response = client.get("/api/web/feeds")

    assert response.status_code == 200
    assert [feed["url"] for feed in response.json()] == ["https://source.test/mine"]


def test_create_feed_adds_source_for_authenticated_user(monkeypatch, fake_supabase):
    _seed_professional_user(fake_supabase)
    monkeypatch.setattr(feed_parser, "validate_feed_source", lambda url: {"valid": True, "error": "", "title": "t", "entry_count": 1})
    client = _client(monkeypatch, fake_supabase)
    _login(client, 101)

    response = client.post("/api/web/feeds", json={"url": "https://rss.local/feed.xml"})

    assert response.status_code == 201
    body = response.json()
    assert body["url"] == "https://rss.local/feed.xml"
    assert body["is_active"] is True
    assert [feed["url"] for feed in fake_supabase.feeds] == ["https://rss.local/feed.xml"]


def test_create_feed_requires_authentication(monkeypatch, fake_supabase):
    client = _client(monkeypatch, fake_supabase)

    assert client.post("/api/web/feeds", json={"url": "https://rss.local/feed.xml"}).status_code == 401


def test_create_feed_rejects_empty_url(monkeypatch, fake_supabase):
    _seed_professional_user(fake_supabase)
    client = _client(monkeypatch, fake_supabase)
    _login(client, 101)

    assert client.post("/api/web/feeds", json={"url": "   "}).status_code == 422


def test_create_feed_rejects_invalid_url(monkeypatch, fake_supabase):
    _seed_professional_user(fake_supabase)
    client = _client(monkeypatch, fake_supabase)
    _login(client, 101)

    assert client.post("/api/web/feeds", json={"url": "not a url"}).status_code == 422


def test_create_feed_rejects_duplicate(monkeypatch, fake_supabase):
    _seed_professional_user(fake_supabase)
    fake_supabase.seed("feeds", [{"id": 1, "user_id": 101, "url": "https://rss.local/feed.xml", "is_active": True}])
    monkeypatch.setattr(feed_parser, "validate_feed_source", lambda url: {"valid": True, "error": "", "title": "t", "entry_count": 1})
    client = _client(monkeypatch, fake_supabase)
    _login(client, 101)

    response = client.post("/api/web/feeds", json={"url": "https://rss.local/feed.xml"})

    assert response.status_code == 409


def test_create_feed_rejects_when_source_cannot_be_validated(monkeypatch, fake_supabase):
    _seed_professional_user(fake_supabase)
    monkeypatch.setattr(feed_parser, "validate_feed_source", lambda url: {"valid": False, "error": "sin entradas", "title": "", "entry_count": 0})
    client = _client(monkeypatch, fake_supabase)
    _login(client, 101)

    response = client.post("/api/web/feeds", json={"url": "https://rss.local/feed.xml"})

    assert response.status_code == 422
    assert response.json()["detail"] == "sin entradas"


def test_create_feed_rejects_when_plan_limit_reached(monkeypatch, fake_supabase):
    _seed_professional_user(fake_supabase)
    fake_supabase.seed(
        "feeds",
        [{"id": i, "user_id": 101, "url": f"https://rss.local/feed{i}.xml", "is_active": True} for i in range(1, 16)],
    )
    monkeypatch.setattr(feed_parser, "validate_feed_source", lambda url: {"valid": True, "error": "", "title": "t", "entry_count": 1})
    client = _client(monkeypatch, fake_supabase)
    _login(client, 101)

    response = client.post("/api/web/feeds", json={"url": "https://rss.local/feed16.xml"})

    assert response.status_code == 403


def test_create_feed_rejects_url_without_host(monkeypatch, fake_supabase):
    _seed_professional_user(fake_supabase)
    client = _client(monkeypatch, fake_supabase)
    _login(client, 101)

    response = client.post("/api/web/feeds", json={"url": "https://"})

    assert response.status_code == 422


def test_create_feed_rejects_unsupported_platform(monkeypatch, fake_supabase):
    from app.web import routes

    _seed_professional_user(fake_supabase)
    monkeypatch.setattr(routes.SourceFactory, "resolve_registration_url", staticmethod(lambda url: None))
    client = _client(monkeypatch, fake_supabase)
    _login(client, 101)

    response = client.post("/api/web/feeds", json={"url": "https://rss.local/feed.xml"})

    assert response.status_code == 422


def test_create_feed_returns_error_when_persistence_fails(monkeypatch, fake_supabase):
    _seed_professional_user(fake_supabase)
    monkeypatch.setattr(feed_parser, "validate_feed_source", lambda url: {"valid": True, "error": "", "title": "t", "entry_count": 1})
    monkeypatch.setattr(database, "add_feed", lambda user_id, url: None)
    client = _client(monkeypatch, fake_supabase)
    _login(client, 101)

    response = client.post("/api/web/feeds", json={"url": "https://rss.local/feed.xml"})

    assert response.status_code == 500


def test_create_feed_returns_error_when_feed_cannot_be_found_after_insert(monkeypatch, fake_supabase):
    _seed_professional_user(fake_supabase)
    monkeypatch.setattr(feed_parser, "validate_feed_source", lambda url: {"valid": True, "error": "", "title": "t", "entry_count": 1})
    monkeypatch.setattr(database, "add_feed", lambda user_id, url: 9999)
    client = _client(monkeypatch, fake_supabase)
    _login(client, 101)

    response = client.post("/api/web/feeds", json={"url": "https://rss.local/feed.xml"})

    assert response.status_code == 500


def test_update_feed_status_pauses_and_resumes_own_feed(monkeypatch, fake_supabase):
    _seed_professional_user(fake_supabase)
    fake_supabase.seed("feeds", [{"id": 1, "user_id": 101, "url": "https://rss.local/feed.xml", "is_active": False}])
    client = _client(monkeypatch, fake_supabase)
    _login(client, 101)

    resume_response = client.patch("/api/web/feeds/1", json={"is_active": True})
    assert resume_response.status_code == 200
    assert resume_response.json()["is_active"] is True
    assert fake_supabase.feeds[0]["is_active"] is True

    pause_response = client.patch("/api/web/feeds/1", json={"is_active": False})
    assert pause_response.status_code == 200
    assert pause_response.json()["is_active"] is False
    assert fake_supabase.feeds[0]["is_active"] is False


def test_update_feed_status_rejects_foreign_feed(monkeypatch, fake_supabase):
    _seed_professional_user(fake_supabase)
    fake_supabase.seed("feeds", [{"id": 1, "user_id": 999, "url": "https://rss.local/feed.xml", "is_active": True}])
    client = _client(monkeypatch, fake_supabase)
    _login(client, 101)

    response = client.patch("/api/web/feeds/1", json={"is_active": False})

    assert response.status_code == 404
    assert fake_supabase.feeds[0]["is_active"] is True


def test_delete_feed_removes_own_feed(monkeypatch, fake_supabase):
    _seed_professional_user(fake_supabase)
    fake_supabase.seed("feeds", [{"id": 1, "user_id": 101, "url": "https://rss.local/feed.xml", "is_active": True}])
    client = _client(monkeypatch, fake_supabase)
    _login(client, 101)

    response = client.delete("/api/web/feeds/1")

    assert response.status_code == 204
    assert fake_supabase.feeds == []


def test_delete_feed_rejects_foreign_feed(monkeypatch, fake_supabase):
    _seed_professional_user(fake_supabase)
    fake_supabase.seed("feeds", [{"id": 1, "user_id": 999, "url": "https://rss.local/feed.xml", "is_active": True}])
    client = _client(monkeypatch, fake_supabase)
    _login(client, 101)

    response = client.delete("/api/web/feeds/1")

    assert response.status_code == 404
    assert len(fake_supabase.feeds) == 1
