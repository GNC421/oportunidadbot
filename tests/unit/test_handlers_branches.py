from __future__ import annotations

from types import SimpleNamespace
import importlib.util
from pathlib import Path
import pytest


def _load_handlers_module():
    path = Path(__file__).resolve().parents[2] / "app" / "bot" / "handlers.py"
    spec = importlib.util.spec_from_file_location("handlers_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _build_message_update(user_id=101):
    replies = []

    async def reply_text(text: str, **kwargs):
        replies.append({"text": text, "kwargs": kwargs})

    message = SimpleNamespace(text="hello", reply_text=reply_text)
    user = SimpleNamespace(id=user_id, username="tester")
    update = SimpleNamespace(effective_user=user, message=message)
    context = SimpleNamespace(args=[], matches=[])
    return update, context, replies


@pytest.mark.asyncio
async def test_start_and_help_commands():
    handlers = _load_handlers_module()
    update, context, replies = _build_message_update()

    await handlers.start_command(update, context)
    assert replies and "OportunidadBot" in replies[-1]["text"]

    await handlers.help_command(update, context)
    assert "Lista de comandos" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_addgroup_various_paths(monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = _build_message_update()

    # no args provided
    await handlers.addgroup_command(update, context)
    assert "Uso: /addgroup" in replies[-1]["text"]

    # invalid URL format
    context.args = ["notaurl"]
    await handlers.addgroup_command(update, context)
    assert "no tiene un formato válido" in replies[-1]["text"] or "No pude" in replies[-1]["text"]

    # resolved_feed_url None
    monkeypatch.setattr(handlers.SourceFactory, "resolve_registration_url", lambda u: None)
    context.args = ["https://example.com/feed"]
    await handlers.addgroup_command(update, context)
    assert "no está soportada" in replies[-1]["text"]

    # existing feed
    monkeypatch.setattr(handlers.SourceFactory, "resolve_registration_url", lambda u: "https://feed.resolved/foo")
    monkeypatch.setattr(handlers, "_fetch_user_feeds", lambda uid: [{"url": "https://feed.resolved/foo"}])
    await handlers.addgroup_command(update, context)
    assert "ya está registrado" in replies[-1]["text"]

    # successful add
    monkeypatch.setattr(handlers, "_fetch_user_feeds", lambda uid: [])
    monkeypatch.setattr(handlers.feed_parser, "validate_feed_source", lambda u: {"valid": True})
    monkeypatch.setattr(handlers.database, "add_user", lambda uid, name: True)
    monkeypatch.setattr(handlers.database, "add_feed", lambda **k: 55)
    await handlers.addgroup_command(update, context)
    assert "Feed añadido correctamente" in replies[-1]["text"]
