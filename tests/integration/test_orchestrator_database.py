from __future__ import annotations

import pytest

from app import database
from app.services.orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_orchestrator_database_integration(monkeypatch, fake_supabase):
    monkeypatch.setattr(database, "supabase", fake_supabase)

    fake_supabase.seed("feeds", [{"id": 1, "user_id": 101, "url": "https://rss.local/f", "is_active": True}])

    monkeypatch.setattr("app.services.orchestrator.get_active_feeds", database.get_active_feeds)
    monkeypatch.setattr("app.services.orchestrator.get_alert_by_url", database.get_alert_by_url)
    monkeypatch.setattr("app.services.orchestrator.save_alert", database.save_alert)
    monkeypatch.setattr("app.services.orchestrator.mark_alert_sent", database.mark_alert_sent)
    monkeypatch.setattr("app.services.orchestrator.update_feed_last_check", lambda _id: None)
    monkeypatch.setattr(
        "app.services.orchestrator.check_user_source_entries",
        lambda _feed: [{"title": "A", "summary": "B", "url": "https://post/1", "author": "u", "question": "q"}],
    )

    async def _send_alert(**_kwargs):
        return None

    monkeypatch.setattr("app.services.orchestrator.send_alert", _send_alert)

    orchestrator = Orchestrator()
    sent_count = await orchestrator.run_feed_checks()

    assert sent_count == 1
    assert len(fake_supabase.alerts) == 1
    assert fake_supabase.alerts[0].get("sent_at")
