from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


def _load_handlers_module():
    path = Path(__file__).resolve().parents[2] / "app" / "bot" / "handlers.py"
    spec = importlib.util.spec_from_file_location("handlers_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


@pytest.mark.asyncio
async def test_handlers_addgroup_requires_url(fake_update_context):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context(args=[])

    await handlers.addgroup_command(update, context)

    assert replies
    assert "Uso: /addgroup [URL]" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_addgroup_invalid_url(fake_update_context, monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context(args=["notaurl"])

    monkeypatch.setattr(handlers.rsshub_resolver, "resolve", lambda _u: None)

    await handlers.addgroup_command(update, context)

    assert "plataforma" in replies[-1]["text"].lower()


@pytest.mark.asyncio
async def test_handlers_addgroup_happy_path(fake_update_context, monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context(args=["https://reddit.com/r/python"])

    monkeypatch.setattr(handlers, "_fetch_user_feeds", lambda _uid: [])
    monkeypatch.setattr(handlers.rsshub_resolver, "resolve", lambda _url: "https://rsshub.local/reddit/r/python")
    monkeypatch.setattr(handlers.feed_parser, "validate_feed_source", lambda _u: {"valid": True})

    calls = {"add_user": 0, "add_feed": 0}
    monkeypatch.setattr(handlers.database, "add_user", lambda *_a, **_k: calls.__setitem__("add_user", 1))
    monkeypatch.setattr(handlers.database, "add_feed", lambda *_a, **_k: 99)

    await handlers.addgroup_command(update, context)

    assert "Feed añadido correctamente" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_groups_no_feeds(fake_update_context, monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context()

    monkeypatch.setattr(handlers, "_fetch_user_feeds", lambda _uid: [])

    await handlers.groups_command(update, context)

    assert "No tienes feeds" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_removegroup_validation(fake_update_context):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context(args=["abc"])

    await handlers.removegroup_command(update, context)

    assert "debe ser un número" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_start_and_help(fake_update_context):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context()

    await handlers.start_command(update, context)
    await handlers.help_command(update, context)

    assert "🏠 OportunidadBot" in replies[0]["text"]
    assert "¿Qué quieres hacer?" in replies[0]["text"]
    assert "Lista de comandos" in replies[1]["text"]


@pytest.mark.asyncio
async def test_handlers_groups_with_data(fake_update_context, monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context()
    monkeypatch.setattr(
        handlers,
        "_fetch_user_feeds",
        lambda _uid: [{"id": 1, "url": "https://rss.local", "is_active": True}],
    )

    await handlers.groups_command(update, context)

    assert "ID 1" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_pause_and_resume(fake_update_context, monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context(args=["1"])
    monkeypatch.setattr(handlers, "_find_user_feed", lambda *_a: {"id": 1})
    monkeypatch.setattr(handlers, "_update_user_feed_status", lambda *_a: None)

    await handlers.pausegroup_command(update, context)
    await handlers.resumegroup_command(update, context)

    assert "pausado" in replies[0]["text"].lower()
    assert "reactivado" in replies[1]["text"].lower()


@pytest.mark.asyncio
async def test_handlers_removegroup_success(fake_update_context, monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context(args=["1"])
    monkeypatch.setattr(handlers, "_find_user_feed", lambda *_a: {"id": 1})
    monkeypatch.setattr(handlers, "_delete_user_feed", lambda *_a: None)

    await handlers.removegroup_command(update, context)

    assert "eliminado" in replies[-1]["text"].lower()


@pytest.mark.asyncio
async def test_handlers_callbacks(fake_update_context):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context()

    await handlers.handle_quick_add(update, context)
    await handlers.handle_tutorial(update, context)
    await handlers.handle_remind_later(update, context)
    await handlers.handle_menu_add_source(update, context)
    await handlers.handle_menu_my_sources(update, context)
    await handlers.handle_menu_help(update, context)
    context.matches = [SimpleNamespace(group=lambda _idx: "9")]
    await handlers.handle_generate_alert(update, context)

    assert len(replies) == 7


def test_handlers_register_handlers():
    handlers = _load_handlers_module()
    added = []

    class FakeApp:
        def add_handler(self, item):
            added.append(item)

        def add_error_handler(self, handler):
            added.append(handler)

    handlers.register_handlers(FakeApp())

    assert len(added) >= 10


def test_handlers_helper_functions():
    handlers = _load_handlers_module()

    assert handlers._normalize_feed_url("example.com/feed") == "https://example.com/feed"
    assert handlers._normalize_feed_url("https://x.com") == "https://x.com"
    assert handlers._get_user_id(SimpleNamespace(effective_user=SimpleNamespace(id=22))) == 22
    assert handlers._get_user_id(SimpleNamespace(effective_user=None)) is None


@pytest.mark.asyncio
async def test_handlers_addgroup_user_missing(fake_update_context):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context(args=["https://x.com"])
    update.effective_user = None

    await handlers.addgroup_command(update, context)

    assert "No pude identificar" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_addgroup_duplicate(fake_update_context, monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context(args=["https://x.com"])
    monkeypatch.setattr(handlers.rsshub_resolver, "resolve", lambda _u: "https://rsshub.local/x")
    monkeypatch.setattr(handlers, "_fetch_user_feeds", lambda _u: [{"id": 1, "url": "https://rsshub.local/x"}])

    await handlers.addgroup_command(update, context)

    assert "ya está registrado" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_addgroup_limit_reached(fake_update_context, monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context(args=["https://x.com"])
    monkeypatch.setattr(handlers, "MAX_FEEDS_PER_USER", 1)
    monkeypatch.setattr(handlers.rsshub_resolver, "resolve", lambda _u: "https://rsshub.local/x")
    monkeypatch.setattr(handlers, "_fetch_user_feeds", lambda _u: [{"id": 1, "url": "https://rsshub.local/other"}])

    await handlers.addgroup_command(update, context)

    assert "límite" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_addgroup_invalid_feed(fake_update_context, monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context(args=["https://x.com"])
    monkeypatch.setattr(handlers, "_fetch_user_feeds", lambda _u: [])
    monkeypatch.setattr(handlers.rsshub_resolver, "resolve", lambda _u: "https://rsshub.local/x")
    monkeypatch.setattr(handlers.feed_parser, "validate_feed_source", lambda _u: {"valid": False, "error": "bad rss"})

    await handlers.addgroup_command(update, context)

    assert "No pude validar" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_addgroup_db_save_fail(fake_update_context, monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context(args=["https://x.com"])
    monkeypatch.setattr(handlers, "_fetch_user_feeds", lambda _u: [])
    monkeypatch.setattr(handlers.rsshub_resolver, "resolve", lambda _u: "https://rsshub.local/x")
    monkeypatch.setattr(handlers.feed_parser, "validate_feed_source", lambda _u: {"valid": True})
    monkeypatch.setattr(handlers.database, "add_user", lambda *_a, **_k: True)
    monkeypatch.setattr(handlers.database, "add_feed", lambda *_a, **_k: None)

    await handlers.addgroup_command(update, context)

    assert "No se pudo guardar" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_pause_resume_and_remove_not_found(fake_update_context, monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context(args=["1"])
    monkeypatch.setattr(handlers, "_find_user_feed", lambda *_a: None)

    await handlers.pausegroup_command(update, context)
    await handlers.resumegroup_command(update, context)
    await handlers.removegroup_command(update, context)

    assert all("No encontré" in item["text"] for item in replies[-3:])


@pytest.mark.asyncio
async def test_handlers_echo_and_error(fake_update_context):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context()

    await handlers.echo_message(update, context)
    await handlers.error_handler(update, SimpleNamespace(error=RuntimeError("x")))

    assert "Echo" in replies[0]["text"]
    assert "error inesperado" in replies[1]["text"].lower()
