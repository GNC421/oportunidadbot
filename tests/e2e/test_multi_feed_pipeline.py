from __future__ import annotations

import pytest

from app import database
from app.services.orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_multi_feed_pipeline_one_fail_others_continue(monkeypatch, fake_supabase):
    monkeypatch.setattr(database, "supabase", fake_supabase)
    fake_supabase.seed(
        "feeds",
        [
            {"id": 1, "user_id": 101, "url": "https://rss.local/1", "is_active": True},
            {"id": 2, "user_id": 101, "url": "https://rss.local/2", "is_active": True},
            {"id": 3, "user_id": 101, "url": "https://rss.local/3", "is_active": True},
        ],
    )

    monkeypatch.setattr("app.services.orchestrator.get_active_feeds", database.get_active_feeds)
    monkeypatch.setattr("app.services.orchestrator.get_alert_by_url", database.get_alert_by_url)
    monkeypatch.setattr("app.services.orchestrator.save_alert", database.save_alert)
    monkeypatch.setattr("app.services.orchestrator.mark_alert_sent", database.mark_alert_sent)
    monkeypatch.setattr("app.services.orchestrator.update_feed_last_check", lambda _id: None)

    def _check(feed):
        if feed["id"] == 2:
            raise RuntimeError("parser down")
        if feed["id"] == 3:
            return [{"title": "T3", "summary": "S3", "url": "https://post/3", "author": "u", "question": "q"}]
        return [{"title": "T1", "summary": "S1", "url": "https://post/1", "author": "u", "question": "q"}]

    monkeypatch.setattr("app.services.orchestrator.check_user_feeds", _check)

    sent: list[dict] = []

    async def _send_alert(**kwargs):
        if kwargs["feed_id"] == 3:
            raise RuntimeError("telegram exception")
        sent.append(kwargs)

    monkeypatch.setattr("app.services.orchestrator.send_alert", _send_alert)

    orchestrator = Orchestrator()
    count = await orchestrator.run_feed_checks()

    assert count == 1
    assert len(sent) == 1
    assert len(fake_supabase.alerts) == 2

    alert_one = database.get_alert_by_url("https://post/1")
    alert_three = database.get_alert_by_url("https://post/3")
    assert alert_one.get("sent_at")
    assert alert_three.get("sent_at") is None
