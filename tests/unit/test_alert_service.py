from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from app.services import alert_service


@pytest.mark.asyncio
async def test_alert_service_sends_message_with_markdown_and_buttons(monkeypatch, fake_telegram):
    monkeypatch.setattr(alert_service, "get_user", lambda _uid: {"id": 101})
    sys.modules["app.bot"] = SimpleNamespace(application=SimpleNamespace(bot=fake_telegram))
    post = {"title": "Busco local", "summary": "zona norte", "link": "https://x/post", "author": "Ana", "category": "Alquiler", "price": "300€", "location": "Granada"}
    await alert_service.send_alert(101, post, 1)

    assert len(fake_telegram.messages) == 1
    sent = fake_telegram.messages[0]
    assert sent["chat_id"] == 101
    assert sent["parse_mode"] == "Markdown"
    # Mensaje debe usar nuevo encabezado y no debe incluir "Publicado por"
    assert "🚨 NUEVA OPORTUNIDAD" in sent["message"]
    assert "Publicado por" not in sent["message"]
    # Descripción completa debe aparecer
    assert "📄 Descripción:" in sent["message"]
    assert "zona norte" in sent["message"]
    # Botón único Ver anuncio
    assert sent["buttons"] is not None
    assert len(sent["buttons"]) == 1
    assert len(sent["buttons"][0]) == 1
    btn = sent["buttons"][0][0]
    assert getattr(btn, "text", None) == "🔗 Ver anuncio"
    assert getattr(btn, "url", None) == "https://x/post"


@pytest.mark.asyncio
async def test_alert_service_no_author_field(monkeypatch, fake_telegram):
    monkeypatch.setattr(alert_service, "get_user", lambda _uid: {"id": 102})
    sys.modules["app.bot"] = SimpleNamespace(application=SimpleNamespace(bot=fake_telegram))

    post = {"title": "Sin autor", "summary": "contenido", "link": "https://x/post"}
    await alert_service.send_alert(102, post, 1)
    sent = fake_telegram.messages[-1]
    assert "Publicado por" not in sent["message"]


@pytest.mark.asyncio
async def test_alert_service_no_price(monkeypatch, fake_telegram):
    monkeypatch.setattr(alert_service, "get_user", lambda _uid: {"id": 103})
    sys.modules["app.bot"] = SimpleNamespace(application=SimpleNamespace(bot=fake_telegram))

    post = {"title": "Sin precio", "summary": "contenido", "link": "https://x/post", "location": "Granada"}
    await alert_service.send_alert(103, post, 1)
    sent = fake_telegram.messages[-1]
    assert "💰" not in sent["message"]


@pytest.mark.asyncio
async def test_alert_service_no_location(monkeypatch, fake_telegram):
    monkeypatch.setattr(alert_service, "get_user", lambda _uid: {"id": 104})
    sys.modules["app.bot"] = SimpleNamespace(application=SimpleNamespace(bot=fake_telegram))

    post = {"title": "Sin ubicación", "summary": "contenido", "link": "https://x/post"}
    await alert_service.send_alert(104, post, 1)
    sent = fake_telegram.messages[-1]
    assert "📍" not in sent["message"]


@pytest.mark.asyncio
async def test_alert_service_truncates_long_description(monkeypatch, fake_telegram):
    monkeypatch.setattr(alert_service, "get_user", lambda _uid: {"id": 105})
    sys.modules["app.bot"] = SimpleNamespace(application=SimpleNamespace(bot=fake_telegram))

    long_text = "palabra " * 1000
    post = {"title": "Largo", "summary": long_text, "link": "https://x/post"}
    await alert_service.send_alert(105, post, 1)
    sent = fake_telegram.messages[-1]
    # Mensaje no debe superar el límite razonable (aprox 4000)
    assert len(sent["message"]) <= 4000
    assert sent["message"].endswith("...")


@pytest.mark.asyncio
async def test_alert_service_handles_special_characters(monkeypatch, fake_telegram):
    monkeypatch.setattr(alert_service, "get_user", lambda _uid: {"id": 106})
    sys.modules["app.bot"] = SimpleNamespace(application=SimpleNamespace(bot=fake_telegram))

    post = {"title": "Especial *caracteres* [test]", "summary": "Texto con _subrayado_ y *asteriscos*", "link": "https://x/post"}
    await alert_service.send_alert(106, post, 1)
    sent = fake_telegram.messages[-1]
    # Debe contener palabras clave sin lanzar errores
    assert "Especial" in sent["message"]
    assert "caracteres" in sent["message"]


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
