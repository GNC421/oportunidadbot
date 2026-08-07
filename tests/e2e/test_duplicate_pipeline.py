from __future__ import annotations

import pytest

from app import database
from app.services.orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_duplicate_pipeline_skips_telegram(monkeypatch, fake_supabase):
    monkeypatch.setattr(database, "supabase", fake_supabase)
    fake_supabase.seed("feeds", [{"id": 1, "user_id": 101, "url": "https://rss.local/1", "is_active": True}])
    fake_supabase.seed(
        "alerts",
        [{"id": 1, "user_id": 101, "feed_id": 1, "post_url": "https://post/dup", "post_title": "dup", "post_content": "x"}],
    )

    monkeypatch.setattr("app.services.orchestrator.get_active_feeds", database.get_active_feeds)
    monkeypatch.setattr("app.services.orchestrator.get_alert_by_url", database.get_alert_by_url)
    monkeypatch.setattr("app.services.orchestrator.save_alert", database.save_alert)
    monkeypatch.setattr("app.services.orchestrator.update_feed_last_check", lambda _id: None)
    monkeypatch.setattr(
        "app.services.orchestrator.check_user_source_entries",
        lambda _feed: [{"title": "A", "summary": "B", "url": "https://post/dup", "author": "u", "question": "q"}],
    )

    async def _fail_send(**_kwargs):
        raise AssertionError("telegram should not run for duplicates")

    monkeypatch.setattr("app.services.orchestrator.send_alert", _fail_send)

    orchestrator = Orchestrator()
    count = await orchestrator.run_feed_checks()

    assert count == 1
    assert len(fake_supabase.alerts) == 1
