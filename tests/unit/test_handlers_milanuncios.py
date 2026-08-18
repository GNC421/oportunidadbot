from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


def _load_handlers_module():
    path = Path(__file__).resolve().parents[2] / "app" / "bot" / "handlers.py"
    spec = importlib.util.spec_from_file_location("handlers_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _build_context_and_replies():
    replies = []

    async def reply_text(text, **kwargs):
        replies.append({"text": text, "kwargs": kwargs})

    user = SimpleNamespace(id=101, username="tester")
    message = SimpleNamespace(text="hello", reply_text=reply_text)
    update = SimpleNamespace(effective_user=user, message=message)
    context = SimpleNamespace(args=[], matches=[])
    return update, context, replies


def test_handlers_feed_display_name_for_milanuncios():
    handlers = _load_handlers_module()
    # milanuncios is not specially handled by SourceDisplayNameService, so should return host
    display = handlers._feed_display_name("https://www.milanuncios.com/casas-en-murcia/?demanda=s&vendedor=part")
    assert "Demanda Casas" in display


def test_handlers_addgroup_with_milanuncios_url(monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = _build_context_and_replies()

    # Simulate user providing milanuncios url as argument
    context.args = ["https://www.milanuncios.com/casas-en-murcia/?demanda=s&vendedor=part"]

    monkeypatch.setattr(handlers, "_fetch_user_feeds", lambda _uid: [])
    # resolve_registration_url should return the same URL for milanuncios
    monkeypatch.setattr(handlers.SourceFactory, "resolve_registration_url", lambda _u: _u)
    # make validate_feed_source succeed
    monkeypatch.setattr(handlers.feed_parser, "validate_feed_source", lambda _u: {"valid": True})

    added = {}
    monkeypatch.setattr(handlers.database, "add_user", lambda *_a, **_k: True)

    def _add_feed(*_a, **kwargs):
        added["url"] = kwargs.get("url")
        return 123

    monkeypatch.setattr(handlers.database, "add_feed", _add_feed)

    import asyncio

    asyncio.run(handlers.addgroup_command(update, context))

    assert added.get("url") is not None
    assert "Feed añadido correctamente" in replies[-1]["text"]
