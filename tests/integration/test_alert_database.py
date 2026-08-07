from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from app import database
from app.services import alert_service


@pytest.mark.asyncio
async def test_alert_then_database_mark_sent(monkeypatch, fake_supabase, fake_telegram):
    monkeypatch.setattr(database, "supabase", fake_supabase)
    monkeypatch.setattr(alert_service, "get_user", lambda _uid: {"id": 101})
    sys.modules["app.bot"] = SimpleNamespace(application=SimpleNamespace(bot=fake_telegram))

    payload = {"title": "A", "summary": "B", "link": "https://post/1", "author": "u"}
    alert_id = database.save_alert(101, 1, payload)

    await alert_service.send_alert(101, payload, 1)
    database.mark_alert_sent(alert_id)

    saved = database.get_alert_by_url("https://post/1")
    assert len(fake_telegram.messages) == 1
    assert saved is not None
    assert saved.get("sent_at")
