from __future__ import annotations

import asyncio
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from types import SimpleNamespace

import app.debug.routes as routes_mod
from app.services import ai_classifier as ai_mod


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(routes_mod.router)
    return app


def test_missing_parameters(app):
    client = TestClient(app)
    resp = client.post("/api/debug/ai/classify", json={"title": "only title"})
    assert resp.status_code == 422


def test_successful_call(monkeypatch, app):
    # mock the classifier call to return a raw string
    async def fake_call(title, summary):
        return "RAW RESPONSE"

    monkeypatch.setattr(ai_mod.classifier, "_call_nvidia", fake_call)
    client = TestClient(app)
    resp = client.post("/api/debug/ai/classify", json={"title": "t", "summary": "s"})
    assert resp.status_code == 200
    assert resp.json() == {"response": "RAW RESPONSE"}


def test_empty_response_treated_as_error(monkeypatch, app):
    async def fake_call(title, summary):
        return None

    monkeypatch.setattr(ai_mod.classifier, "_call_nvidia", fake_call)
    client = TestClient(app)
    resp = client.post("/api/debug/ai/classify", json={"title": "t", "summary": "s"})
    assert resp.status_code == 502


def test_api_error_from_ai(monkeypatch, app):
    async def fake_call(title, summary):
        raise RuntimeError("http 500")

    monkeypatch.setattr(ai_mod.classifier, "_call_nvidia", fake_call)
    client = TestClient(app)
    resp = client.post("/api/debug/ai/classify", json={"title": "t", "summary": "s"})
    assert resp.status_code == 502


def test_timeout(monkeypatch, app):
    async def fake_call(title, summary):
        await asyncio.sleep(0.2)
        return "ok"

    # set a very small timeout
    monkeypatch.setattr(ai_mod.classifier, "_timeout", 0.01)
    monkeypatch.setattr(ai_mod.classifier, "_call_nvidia", fake_call)
    client = TestClient(app)
    resp = client.post("/api/debug/ai/classify", json={"title": "t", "summary": "s"})
    assert resp.status_code == 504


def test_api_key_not_configured(monkeypatch, app):
    async def fake_call(title, summary):
        return "ok"

    monkeypatch.setattr(ai_mod.classifier, "_api_key", None)
    monkeypatch.setattr(ai_mod.classifier, "_call_nvidia", fake_call)
    client = TestClient(app)
    resp = client.post("/api/debug/ai/classify", json={"title": "t", "summary": "s"})
    assert resp.status_code == 500


def test_does_not_access_db_or_send_telegram(monkeypatch, app):
    async def fake_call(title, summary):
        return "ok"

    # patch DB and alert/telegram related functions to raise if called
    import app.database as database_mod
    import app.services.alert_service as alert_mod

    def _fail(*_a, **_k):
        raise AssertionError("DB or Telegram should not be accessed by this endpoint")

    monkeypatch.setattr(ai_mod.classifier, "_call_nvidia", fake_call)
    monkeypatch.setattr(database_mod, "save_alert", _fail)
    monkeypatch.setattr(database_mod, "get_alert_by_url", _fail)
    monkeypatch.setattr(alert_mod, "send_alert", _fail)

    client = TestClient(app)
    resp = client.post("/api/debug/ai/classify", json={"title": "t", "summary": "s"})
    assert resp.status_code == 200
    assert resp.json() == {"response": "ok"}