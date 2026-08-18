from __future__ import annotations

from types import SimpleNamespace
import importlib.util
from pathlib import Path

from app.sources.factory import SourceFactory


def _load_handlers_module():
    path = Path(__file__).resolve().parents[2] / "app" / "bot" / "handlers.py"
    spec = importlib.util.spec_from_file_location("handlers_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_resolve_registration_url_keeps_milanuncios_query():
    url = "https://www.milanuncios.com/venta-de-casas-en-murcia/?demanda=s&vendedor=part&orden=relevance&fromSearch=1&hitOrigin=listing"
    resolved = SourceFactory.resolve_registration_url(url)
    assert resolved == url


async def async_reply_mock(*a, **k):
    pass

def test_addgroup_saves_full_url(monkeypatch):
    handlers = _load_handlers_module()
    update = SimpleNamespace(effective_user=SimpleNamespace(id=101, username="tester"), message=SimpleNamespace(text="x", reply_text=async_reply_mock))
    context = SimpleNamespace(args=["https://www.milanuncios.com/venta-de-casas-en-murcia/?demanda=s&vendedor=part&orden=relevance&fromSearch=1&hitOrigin=listing"], matches=[]) 

    monkeypatch.setattr(handlers, "_fetch_user_feeds", lambda _uid: [])
    # do not monkeypatch resolve_registration_url (should return same URL)
    monkeypatch.setattr(handlers.feed_parser, "validate_feed_source", lambda _u: {"valid": True})

    captured = {}
    monkeypatch.setattr(handlers.database, "add_user", lambda *_a, **_k: True)

    def _add_feed(*_a, **kwargs):
        captured["url"] = kwargs.get("url")
        return 123

    monkeypatch.setattr(handlers.database, "add_feed", _add_feed)

    import asyncio
    asyncio.run(handlers.addgroup_command(update, context))

    assert captured.get("url") == context.args[0]

