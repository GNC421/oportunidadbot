from __future__ import annotations

import pytest

from app import database
from app.services.orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_full_pipeline_positive(monkeypatch, fake_supabase):
    monkeypatch.setattr(database, "supabase", fake_supabase)
    fake_supabase.seed("feeds", [{"id": 1, "user_id": 101, "url": "https://rss.local/1", "is_active": True}])

    monkeypatch.setattr("app.services.orchestrator.get_active_feeds", database.get_active_feeds)
    monkeypatch.setattr("app.services.orchestrator.get_alert_by_url", database.get_alert_by_url)
    monkeypatch.setattr("app.services.orchestrator.save_alert", database.save_alert)
    monkeypatch.setattr("app.services.orchestrator.mark_alert_sent", database.mark_alert_sent)
    monkeypatch.setattr("app.services.orchestrator.update_feed_last_check", lambda _id: None)
    monkeypatch.setattr(
        "app.services.orchestrator.check_user_feeds",
        lambda _feed: [{"title": "Busco", "summary": "inversión", "url": "https://post/ok", "author": "u", "question": "q"}],
    )

    sent_messages = []

    async def _send_alert(**kwargs):
        sent_messages.append(kwargs)

    monkeypatch.setattr("app.services.orchestrator.send_alert", _send_alert)

    orchestrator = Orchestrator()
    count = await orchestrator.run_feed_checks()

    assert count == 1
    assert len(fake_supabase.alerts) == 1
    assert fake_supabase.alerts[0].get("sent_at")
    assert len(sent_messages) == 1


@pytest.mark.asyncio
async def test_full_pipeline_empty_rss_no_alerts(monkeypatch, fake_supabase):
    monkeypatch.setattr(database, "supabase", fake_supabase)
    fake_supabase.seed("feeds", [{"id": 1, "user_id": 101, "url": "https://rss.local/1", "is_active": True}])

    monkeypatch.setattr("app.services.orchestrator.get_active_feeds", database.get_active_feeds)
    monkeypatch.setattr("app.services.orchestrator.check_user_feeds", lambda _feed: [])
    monkeypatch.setattr("app.services.orchestrator.update_feed_last_check", lambda _id: None)

    orchestrator = Orchestrator()
    count = await orchestrator.run_feed_checks()

    assert count == 0
    assert fake_supabase.alerts == []
