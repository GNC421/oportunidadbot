from __future__ import annotations

import pytest

from app.services.orchestrator import Orchestrator
from app.services import orchestrator as orchestrator_module


@pytest.mark.asyncio
async def test_orchestrator_happy_path(monkeypatch, feed_factory, alert_factory):
    orchestrator = Orchestrator()
    feed = feed_factory(feed_id=1, user_id=101, url="https://rss.local/feed")
    alert = alert_factory(link="https://post/1")
    sent = []

    monkeypatch.setattr("app.services.orchestrator.get_active_feeds", lambda: [feed])
    monkeypatch.setattr("app.services.orchestrator.check_user_feeds", lambda _f: [alert])
    monkeypatch.setattr("app.services.orchestrator.get_alert_by_url", lambda _u: None)
    monkeypatch.setattr("app.services.orchestrator.save_alert", lambda **_k: 77)
    monkeypatch.setattr("app.services.orchestrator.mark_alert_sent", lambda alert_id: sent.append(alert_id))
    monkeypatch.setattr("app.services.orchestrator.update_feed_last_check", lambda _id: None)

    async def _send_alert(**_kwargs):
        return None

    monkeypatch.setattr("app.services.orchestrator.send_alert", _send_alert)

    result = await orchestrator.run_feed_checks()

    assert result == 1
    assert sent == [77]


@pytest.mark.asyncio
async def test_orchestrator_feed_empty(monkeypatch):
    monkeypatch.setattr("app.services.orchestrator.get_active_feeds", lambda: [])
    orchestrator = Orchestrator()

    assert await orchestrator.run_feed_checks() == 0


@pytest.mark.asyncio
async def test_orchestrator_duplicate(monkeypatch, feed_factory, alert_factory):
    orchestrator = Orchestrator()
    feed = feed_factory()
    alert = alert_factory(link="https://post/dup")

    monkeypatch.setattr("app.services.orchestrator.get_active_feeds", lambda: [feed])
    monkeypatch.setattr("app.services.orchestrator.check_user_feeds", lambda _f: [alert])
    monkeypatch.setattr("app.services.orchestrator.get_alert_by_url", lambda _u: {"id": 1})
    monkeypatch.setattr("app.services.orchestrator.update_feed_last_check", lambda _id: None)

    async def _never_send(**_kwargs):
        raise AssertionError("send_alert should not be called for duplicates")

    monkeypatch.setattr("app.services.orchestrator.send_alert", _never_send)

    assert await orchestrator.run_feed_checks() == 1


@pytest.mark.asyncio
async def test_orchestrator_parser_error(monkeypatch, feed_factory):
    orchestrator = Orchestrator()
    monkeypatch.setattr("app.services.orchestrator.get_active_feeds", lambda: [feed_factory()])

    def _raise(_feed):
        raise RuntimeError("parser fail")

    monkeypatch.setattr("app.services.orchestrator.check_user_feeds", _raise)

    assert await orchestrator.run_feed_checks() == 0


@pytest.mark.asyncio
async def test_orchestrator_error_telegram(monkeypatch, feed_factory, alert_factory):
    orchestrator = Orchestrator()
    monkeypatch.setattr("app.services.orchestrator.get_active_feeds", lambda: [feed_factory()])
    monkeypatch.setattr("app.services.orchestrator.check_user_feeds", lambda _f: [alert_factory(link="https://p/1")])
    monkeypatch.setattr("app.services.orchestrator.get_alert_by_url", lambda _u: None)
    monkeypatch.setattr("app.services.orchestrator.save_alert", lambda **_k: 10)
    monkeypatch.setattr("app.services.orchestrator.update_feed_last_check", lambda _id: None)

    marked: list[int] = []
    monkeypatch.setattr("app.services.orchestrator.mark_alert_sent", lambda alert_id: marked.append(alert_id))

    async def _raise_send(**_kwargs):
        raise RuntimeError("telegram down")

    monkeypatch.setattr("app.services.orchestrator.send_alert", _raise_send)

    assert await orchestrator.run_feed_checks() == 0
    assert marked == []


@pytest.mark.asyncio
async def test_orchestrator_skips_incomplete_feed(monkeypatch):
    monkeypatch.setattr("app.services.orchestrator.get_active_feeds", lambda: [{"id": None, "user_id": 1, "url": "x"}])
    orchestrator = Orchestrator()

    assert await orchestrator.run_feed_checks() == 0


@pytest.mark.asyncio
async def test_orchestrator_wrapper(monkeypatch):
    async def _run():
        return 7

    monkeypatch.setattr(orchestrator_module.orchestrator, "run_feed_checks", _run)

    assert await orchestrator_module.run_feed_checks() == 7
