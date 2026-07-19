from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from app.services import alert_service


@pytest.mark.asyncio
async def test_alert_service_sends_message_with_markdown_and_buttons(monkeypatch, fake_telegram):
    monkeypatch.setattr(alert_service, "get_user", lambda _uid: {"id": 101})
    sys.modules["app.bot"] = SimpleNamespace(application=SimpleNamespace(bot=fake_telegram))

    post = {"title": "Busco local", "summary": "zona norte", "link": "https://x/post", "author": "Ana"}
    await alert_service.send_alert(101, post, 1)

    assert len(fake_telegram.messages) == 1
    sent = fake_telegram.messages[0]
    assert sent["chat_id"] == 101
    assert sent["parse_mode"] == "Markdown"
    assert sent["buttons"] is not None
    assert "Nueva oportunidad" in sent["message"]


@pytest.mark.asyncio
async def test_alert_service_handles_telegram_error(monkeypatch):
    failing_telegram = SimpleNamespace(send_message=_raise_async)
    monkeypatch.setattr(alert_service, "get_user", lambda _uid: {"id": 101})
    sys.modules["app.bot"] = SimpleNamespace(application=SimpleNamespace(bot=failing_telegram))

    post = {"title": "Busco local", "summary": "zona norte", "link": "https://x/post", "author": "Ana"}
    await alert_service.send_alert(101, post, 1)


@pytest.mark.asyncio
async def test_alert_service_skips_when_user_missing(monkeypatch, fake_telegram):
    monkeypatch.setattr(alert_service, "get_user", lambda _uid: None)
    sys.modules["app.bot"] = SimpleNamespace(application=SimpleNamespace(bot=fake_telegram))

    post = {"title": "Busco local", "summary": "zona norte", "link": "https://x/post", "author": "Ana"}
    await alert_service.send_alert(101, post, 1)

    assert fake_telegram.messages == []


@pytest.mark.asyncio
async def test_send_welcome_message(monkeypatch):
    sent = []

    async def _reply_text(text, **kwargs):
        sent.append({"text": text, "kwargs": kwargs})

    update = SimpleNamespace(
        effective_user=SimpleNamespace(first_name="Guillermo"),
        message=SimpleNamespace(reply_text=_reply_text),
    )

    await alert_service.send_welcome_message(update, SimpleNamespace())

    assert sent
    assert "Hola Guillermo" in sent[0]["text"]
    assert sent[0]["kwargs"]["parse_mode"] == "Markdown"


def _raise_async(*_a, **_k):
    async def _inner():
        raise RuntimeError("telegram error")

    return _inner()
