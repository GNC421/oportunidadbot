from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from datetime import datetime, timezone, timedelta

import pytest


def _load_handlers_module():
    path = Path(__file__).resolve().parents[2] / "app" / "bot" / "handlers.py"
    spec = importlib.util.spec_from_file_location("handlers_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _build_callback_update(callback_data: str, user_id: int = 101) -> tuple[Any, Any, list[dict[str, Any]], list[dict[str, Any]]]:
    replies: list[dict[str, Any]] = []
    edits: list[dict[str, Any]] = []

    async def reply_text(text: str, **kwargs: Any) -> None:
        replies.append({"text": text, "kwargs": kwargs})

    async def answer(*_a: Any, **_k: Any) -> None:
        return None

    async def edit_message_text(text: str, **kwargs: Any) -> None:
        edits.append({"text": text, "kwargs": kwargs})

    message = SimpleNamespace(text="hello", reply_text=reply_text)
    callback_query = SimpleNamespace(
        data=callback_data,
        answer=answer,
        edit_message_text=edit_message_text,
        message=message,
    )
    user = SimpleNamespace(id=user_id, username="tester")
    update = SimpleNamespace(effective_user=user, message=message, callback_query=callback_query)
    context = SimpleNamespace(args=[], matches=[])
    return update, context, replies, edits


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

    monkeypatch.setattr(handlers.SourceFactory, "resolve_registration_url", lambda _u: None)

    await handlers.addgroup_command(update, context)

    assert "plataforma" in replies[-1]["text"].lower()


@pytest.mark.asyncio
async def test_handlers_addgroup_happy_path(fake_update_context, monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context(args=["https://reddit.com/r/python"])

    monkeypatch.setattr(handlers, "_fetch_user_feeds", lambda _uid: [])
    monkeypatch.setattr(handlers.SourceFactory, "resolve_registration_url", lambda _url: "https://feed.local/reddit/r/python")
    monkeypatch.setattr(handlers.feed_parser, "validate_feed_source", lambda _u: {"valid": True})

    calls = {"add_user": 0, "add_feed": 0}
    monkeypatch.setattr(handlers.database, "add_user", lambda *_a, **_k: calls.__setitem__("add_user", 1))
    monkeypatch.setattr(handlers.database, "add_feed", lambda *_a, **_k: 99)

    await handlers.addgroup_command(update, context)

    assert "Feed añadido correctamente" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_addgroup_tablon_uses_source_url_directly(fake_update_context, monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context(args=["https://www.tablondeanuncios.com/inmobiliaria-en-murcia/?demanda=1"])

    monkeypatch.setattr(handlers, "_fetch_user_feeds", lambda _uid: [])
    monkeypatch.setattr(handlers.feed_parser, "validate_feed_source", lambda _u: {"valid": True})

    monkeypatch.setattr(
        handlers.SourceFactory,
        "resolve_registration_url",
        lambda _url: "https://www.tablondeanuncios.com/inmobiliaria-en-murcia/?demanda=1",
    )

    captured: dict[str, str] = {}
    monkeypatch.setattr(handlers.database, "add_user", lambda *_a, **_k: True)

    def _add_feed(*_a, **kwargs):
        captured["url"] = kwargs["url"]
        return 101

    monkeypatch.setattr(handlers.database, "add_feed", _add_feed)

    await handlers.addgroup_command(update, context)

    assert captured["url"] == "https://www.tablondeanuncios.com/inmobiliaria-en-murcia/?demanda=1"
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
async def test_handlers_menu_my_sources_dynamic_cards(fake_update_context, monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context()
    monkeypatch.setattr(
        handlers,
        "_fetch_user_feeds",
        lambda _uid: [
            {
                "id": 10,
                "url": "https://reddit.com/r/murcia",
                "is_active": True,
                "last_check": "2026-07-21T10:00:00+00:00",
            },
            {
                "id": 11,
                "url": "https://reddit.com/r/alicante",
                "is_active": False,
                "last_check": "2026-07-21T10:00:00+00:00",
            },
        ],
    )

    await handlers.handle_menu_my_sources(update, context)

    assert len(replies) == 2
    assert replies[0]["text"].startswith("🟢 Reddit Murcia")
    assert replies[1]["text"].startswith("⏸ Reddit Alicante")
    assert "ID " not in replies[0]["text"]
    assert "ID " not in replies[1]["text"]

    first_buttons = replies[0]["kwargs"]["reply_markup"].inline_keyboard[0]
    second_buttons = replies[1]["kwargs"]["reply_markup"].inline_keyboard[0]
    assert first_buttons[0].callback_data == "feed_pause_10"
    assert first_buttons[1].callback_data == "feed_delete_10"
    assert second_buttons[0].callback_data == "feed_resume_11"
    assert second_buttons[1].callback_data == "feed_delete_11"


@pytest.mark.asyncio
async def test_handlers_menu_my_sources_empty(fake_update_context, monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context()
    monkeypatch.setattr(handlers, "_fetch_user_feeds", lambda _uid: [])

    await handlers.handle_menu_my_sources(update, context)

    assert "No tienes fuentes" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_menu_my_sources_user_missing(fake_update_context):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context()
    update.effective_user = None

    await handlers.handle_menu_my_sources(update, context)

    assert "No pude identificar" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_menu_my_sources_exception_path(fake_update_context, monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context()

    def _boom(_uid):
        raise RuntimeError("db fail")

    monkeypatch.setattr(handlers, "_fetch_user_feeds", _boom)

    await handlers.handle_menu_my_sources(update, context)

    assert "No se pudieron cargar" in replies[-1]["text"]


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


@pytest.mark.asyncio
async def test_handlers_feed_pause_updates_status_and_edits_message(monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies, edits = _build_callback_update("feed_pause_42")
    monkeypatch.setattr(
        handlers,
        "_find_user_feed",
        lambda *_a: {"id": 42, "url": "https://reddit.com/r/murcia", "is_active": True},
    )

    status_calls: list[tuple[int, int, bool]] = []
    monkeypatch.setattr(
        handlers,
        "_update_user_feed_status",
        lambda user_id, feed_id, is_active: status_calls.append((user_id, feed_id, is_active)),
    )

    await handlers.handle_feed_pause_callback(update, context)

    assert status_calls == [(101, 42, False)]
    assert len(replies) == 0
    assert len(edits) == 1
    assert edits[0]["text"].startswith("⏸ Reddit Murcia")
    buttons = edits[0]["kwargs"]["reply_markup"].inline_keyboard[0]
    assert buttons[0].callback_data == "feed_resume_42"
    assert buttons[1].callback_data == "feed_delete_42"


@pytest.mark.asyncio
async def test_handlers_feed_pause_invalid_callback_data(fake_update_context):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context()
    update.callback_query.data = "feed_pause_bad"

    await handlers.handle_feed_pause_callback(update, context)

    assert replies == []


@pytest.mark.asyncio
async def test_handlers_feed_pause_user_missing(fake_update_context):
    handlers = _load_handlers_module()
    update, context, replies, edits = _build_callback_update("feed_pause_42")
    update.effective_user = None

    await handlers.handle_feed_pause_callback(update, context)

    assert len(replies) == 0
    assert len(edits) == 0


@pytest.mark.asyncio
async def test_handlers_feed_pause_update_failure(monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies, edits = _build_callback_update("feed_pause_42")
    monkeypatch.setattr(
        handlers,
        "_find_user_feed",
        lambda *_a: {"id": 42, "url": "https://reddit.com/r/murcia", "is_active": True},
    )

    def _boom(*_a, **_k):
        raise RuntimeError("db fail")

    monkeypatch.setattr(handlers, "_update_user_feed_status", _boom)

    await handlers.handle_feed_pause_callback(update, context)

    assert len(replies) == 0
    assert len(edits) == 0


@pytest.mark.asyncio
async def test_handlers_feed_resume_updates_status_and_edits_message(monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies, edits = _build_callback_update("feed_resume_42")
    monkeypatch.setattr(
        handlers,
        "_find_user_feed",
        lambda *_a: {"id": 42, "url": "https://reddit.com/r/murcia", "is_active": False},
    )

    status_calls: list[tuple[int, int, bool]] = []
    monkeypatch.setattr(
        handlers,
        "_update_user_feed_status",
        lambda user_id, feed_id, is_active: status_calls.append((user_id, feed_id, is_active)),
    )

    await handlers.handle_feed_resume_callback(update, context)

    assert status_calls == [(101, 42, True)]
    assert len(replies) == 0
    assert len(edits) == 1
    assert edits[0]["text"].startswith("🟢 Reddit Murcia")
    buttons = edits[0]["kwargs"]["reply_markup"].inline_keyboard[0]
    assert buttons[0].callback_data == "feed_pause_42"
    assert buttons[1].callback_data == "feed_delete_42"


@pytest.mark.asyncio
async def test_handlers_feed_delete_request_shows_confirmation(monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies, edits = _build_callback_update("feed_delete_42")
    monkeypatch.setattr(
        handlers,
        "_find_user_feed",
        lambda *_a: {"id": 42, "url": "https://reddit.com/r/murcia", "is_active": True},
    )

    await handlers.handle_feed_delete_request(update, context)

    assert len(replies) == 0
    assert len(edits) == 1
    assert "¿Seguro que deseas eliminar esta fuente" in edits[0]["text"]
    assert "Reddit Murcia" in edits[0]["text"]
    assert "no puede deshacerse" in edits[0]["text"]
    keyboard = edits[0]["kwargs"]["reply_markup"].inline_keyboard
    assert keyboard[0][0].callback_data == "feed_delete_confirm_42"
    assert keyboard[1][0].callback_data == "feed_delete_cancel_42"


@pytest.mark.asyncio
async def test_handlers_feed_delete_request_invalid_data(fake_update_context):
    handlers = _load_handlers_module()
    update, context, replies, edits = _build_callback_update("feed_delete_bad")

    await handlers.handle_feed_delete_request(update, context)

    assert len(replies) == 0
    assert len(edits) == 0


@pytest.mark.asyncio
async def test_handlers_feed_delete_request_user_missing(fake_update_context):
    handlers = _load_handlers_module()
    update, context, replies, edits = _build_callback_update("feed_delete_42")
    update.effective_user = None

    await handlers.handle_feed_delete_request(update, context)

    assert len(replies) == 0
    assert len(edits) == 0


@pytest.mark.asyncio
async def test_handlers_feed_delete_cancel_restores_card(monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies, edits = _build_callback_update("feed_delete_cancel_42")
    monkeypatch.setattr(
        handlers,
        "_find_user_feed",
        lambda *_a: {"id": 42, "url": "https://reddit.com/r/murcia", "is_active": True},
    )

    await handlers.handle_feed_delete_cancel(update, context)

    assert len(replies) == 0
    assert len(edits) == 1
    assert edits[0]["text"].startswith("🟢 Reddit Murcia")
    buttons = edits[0]["kwargs"]["reply_markup"].inline_keyboard[0]
    assert buttons[0].callback_data == "feed_pause_42"
    assert buttons[1].callback_data == "feed_delete_42"


@pytest.mark.asyncio
async def test_handlers_feed_delete_confirm_deletes_and_refreshes_remaining(monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies, edits = _build_callback_update("feed_delete_confirm_42")

    monkeypatch.setattr(
        handlers,
        "_find_user_feed",
        lambda *_a: {"id": 42, "url": "https://reddit.com/r/murcia", "is_active": True},
    )

    delete_calls: list[tuple[int, int]] = []
    monkeypatch.setattr(
        handlers,
        "_delete_user_feed",
        lambda user_id, feed_id: delete_calls.append((user_id, feed_id)),
    )
    monkeypatch.setattr(
        handlers,
        "_fetch_user_feeds",
        lambda _uid: [{"id": 77, "url": "https://reddit.com/r/alicante", "is_active": False}],
    )

    await handlers.handle_feed_delete_confirm(update, context)

    assert delete_calls == [(101, 42)]
    assert len(replies) == 0
    assert len(edits) == 1
    assert "Fuente eliminada correctamente" in edits[0]["text"]
    assert "Fuentes restantes" in edits[0]["text"]
    assert "Reddit Alicante" in edits[0]["text"]


@pytest.mark.asyncio
async def test_handlers_feed_delete_confirm_exception_path(monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies, edits = _build_callback_update("feed_delete_confirm_42")
    monkeypatch.setattr(
        handlers,
        "_find_user_feed",
        lambda *_a: {"id": 42, "url": "https://reddit.com/r/murcia", "is_active": True},
    )

    def _boom(*_a, **_k):
        raise RuntimeError("db fail")

    monkeypatch.setattr(handlers, "_delete_user_feed", _boom)

    await handlers.handle_feed_delete_confirm(update, context)

    assert len(replies) == 0
    assert len(edits) == 0


@pytest.mark.asyncio
async def test_handlers_feed_delete_confirm_user_missing(fake_update_context):
    handlers = _load_handlers_module()
    update, context, replies, edits = _build_callback_update("feed_delete_confirm_42")
    update.effective_user = None

    await handlers.handle_feed_delete_confirm(update, context)

    assert len(replies) == 0
    assert len(edits) == 0


@pytest.mark.asyncio
async def test_handlers_feed_delete_confirm_invalid_data(fake_update_context):
    handlers = _load_handlers_module()
    update, context, replies, edits = _build_callback_update("feed_delete_confirm_bad")

    await handlers.handle_feed_delete_confirm(update, context)

    assert len(replies) == 0
    assert len(edits) == 0


@pytest.mark.asyncio
async def test_handlers_feed_delete_confirm_not_found(monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies, edits = _build_callback_update("feed_delete_confirm_42")
    monkeypatch.setattr(handlers, "_find_user_feed", lambda *_a: None)

    await handlers.handle_feed_delete_confirm(update, context)

    assert len(replies) == 0
    assert len(edits) == 0


@pytest.mark.asyncio
async def test_handlers_menu_add_source_enters_waiting_url(fake_update_context):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context()

    state = await handlers.handle_menu_add_source(update, context)

    assert state == handlers.WAITING_URL
    assert "Pega la URL" in replies[-1]["text"]
    assert "/cancel" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_quick_add_enters_waiting_url(fake_update_context):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context()

    state = await handlers.handle_quick_add(update, context)

    assert state == handlers.WAITING_URL
    assert "Pega la URL" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_waiting_url_message_reuses_addgroup_logic(fake_update_context, monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context()
    update.message.text = "https://reddit.com/r/python"

    monkeypatch.setattr(handlers, "_fetch_user_feeds", lambda _uid: [])
    monkeypatch.setattr(handlers.SourceFactory, "resolve_registration_url", lambda _url: "https://feed.local/reddit/r/python")
    monkeypatch.setattr(handlers.feed_parser, "validate_feed_source", lambda _u: {"valid": True})
    monkeypatch.setattr(handlers.database, "add_user", lambda *_a, **_k: True)
    monkeypatch.setattr(handlers.database, "add_feed", lambda *_a, **_k: 77)

    state = await handlers.waiting_url_message(update, context)

    assert state == handlers.ConversationHandler.END
    assert "Feed añadido correctamente" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_cancel_add_source(fake_update_context):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context()

    state = await handlers.cancel_add_source(update, context)

    assert state == handlers.ConversationHandler.END
    assert "cancelada" in replies[-1]["text"].lower()


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


def test_handlers_formatting_helpers():
    handlers = _load_handlers_module()

    assert handlers._normalize_feed_url("") == ""
    assert handlers._feed_display_name("https://www.reddit.com/r/murcia") == "Reddit Murcia"
    assert (
        handlers._feed_display_name("https://www.tablondeanuncios.com/inmobiliaria-en-murcia/?demanda=1")
        == "🏠 Demanda inmobiliaria · Murcia"
    )
    assert handlers._feed_display_name("https://example.com/path") == "example.com"
    assert handlers._feed_display_name("notaurl") == "Fuente RSS"

    assert handlers._parse_iso_datetime("") is None
    assert handlers._parse_iso_datetime("bad-date") is None

    naive = handlers._parse_iso_datetime("2026-07-21T10:00:00")
    assert naive is not None and naive.tzinfo is timezone.utc

    zoned = handlers._parse_iso_datetime("2026-07-21T10:00:00Z")
    assert zoned is not None and zoned.tzinfo is timezone.utc

    now = datetime.now(timezone.utc)
    assert handlers._relative_last_check_text({}) == "Sin revisiones todavía"
    assert handlers._relative_last_check_text({"last_check": (now - timedelta(seconds=10)).isoformat()}) == "Hace menos de un minuto"
    assert handlers._relative_last_check_text({"last_check": (now - timedelta(minutes=5)).isoformat()}) == "Hace 5 minutos"
    assert handlers._relative_last_check_text({"last_check": (now - timedelta(hours=2)).isoformat()}) == "Hace 2 horas"
    assert handlers._relative_last_check_text({"last_check": (now - timedelta(days=3)).isoformat()}) == "Hace 3 días"

    card_text_active, card_markup_active = handlers._build_feed_card({"id": 1, "url": "https://reddit.com/r/murcia", "is_active": True, "last_check": ""})
    assert card_text_active.startswith("🟢 Reddit Murcia")
    assert card_markup_active.inline_keyboard[0][0].callback_data == "feed_pause_1"

    card_text_inactive, card_markup_inactive = handlers._build_feed_card({"id": 2, "url": "https://example.com/feed", "is_active": False, "last_check": ""})
    assert card_text_inactive.startswith("⏸ example.com")
    assert card_markup_inactive.inline_keyboard[0][0].callback_data == "feed_resume_2"

    delete_text, delete_markup = handlers._build_delete_confirmation({"id": 3, "url": "https://reddit.com/r/alicante"})
    assert "¿Seguro que deseas eliminar esta fuente" in delete_text
    assert delete_markup.inline_keyboard[0][0].callback_data == "feed_delete_confirm_3"
    assert delete_markup.inline_keyboard[1][0].callback_data == "feed_delete_cancel_3"

    assert "No te quedan fuentes" in handlers._build_remaining_feeds_text([])
    remaining = handlers._build_remaining_feeds_text([
        {"id": 4, "url": "https://reddit.com/r/murcia", "is_active": True},
        {"id": 5, "url": "https://reddit.com/r/alicante", "is_active": False},
    ])
    assert "📂 Fuentes restantes" in remaining
    assert "🟢 Reddit Murcia" in remaining
    assert "⏸ Reddit Alicante" in remaining

    assert handlers._parse_feed_id_from_callback_data("feed_pause_22", "feed_pause_") == 22
    assert handlers._parse_feed_id_from_callback_data("feed_pause_x", "feed_pause_") is None
    assert handlers._parse_feed_id_from_callback_data("other_22", "feed_pause_") is None


def test_handlers_database_helpers(fake_supabase, monkeypatch):
    handlers = _load_handlers_module()
    monkeypatch.setattr(handlers.database, "supabase", fake_supabase)

    fake_supabase.seed(
        "feeds",
        [
            {"id": 1, "user_id": 10, "url": "https://rss.local/one", "is_active": True},
            {"id": 2, "user_id": 10, "url": "https://rss.local/two", "is_active": False},
        ],
    )

    handlers._delete_user_feed(10, 1)
    handlers._update_user_feed_status(10, 2, True)

    found = handlers._find_user_feed(10, 2)

    assert len(fake_supabase.feeds) == 1
    assert fake_supabase.feeds[0]["id"] == 2
    assert fake_supabase.feeds[0]["is_active"] is True
    assert found is not None and found["id"] == 2


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
    monkeypatch.setattr(handlers.SourceFactory, "resolve_registration_url", lambda _u: "https://feed.local/x")
    monkeypatch.setattr(handlers, "_fetch_user_feeds", lambda _u: [{"id": 1, "url": "https://feed.local/x"}])

    await handlers.addgroup_command(update, context)

    assert "ya está registrado" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_addgroup_limit_reached(fake_update_context, monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context(args=["https://x.com"])
    monkeypatch.setattr(handlers, "MAX_FEEDS_PER_USER", 1)
    monkeypatch.setattr(handlers.SourceFactory, "resolve_registration_url", lambda _u: "https://feed.local/x")
    monkeypatch.setattr(handlers, "_fetch_user_feeds", lambda _u: [{"id": 1, "url": "https://feed.local/other"}])

    await handlers.addgroup_command(update, context)

    assert "límite" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_addgroup_invalid_feed(fake_update_context, monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context(args=["https://x.com"])
    monkeypatch.setattr(handlers, "_fetch_user_feeds", lambda _u: [])
    monkeypatch.setattr(handlers.SourceFactory, "resolve_registration_url", lambda _u: "https://feed.local/x")
    monkeypatch.setattr(handlers.feed_parser, "validate_feed_source", lambda _u: {"valid": False, "error": "bad rss"})

    await handlers.addgroup_command(update, context)

    assert "No pude validar" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_addgroup_db_save_fail(fake_update_context, monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context(args=["https://x.com"])
    monkeypatch.setattr(handlers, "_fetch_user_feeds", lambda _u: [])
    monkeypatch.setattr(handlers.SourceFactory, "resolve_registration_url", lambda _u: "https://feed.local/x")
    monkeypatch.setattr(handlers.feed_parser, "validate_feed_source", lambda _u: {"valid": True})
    monkeypatch.setattr(handlers.database, "add_user", lambda *_a, **_k: True)
    monkeypatch.setattr(handlers.database, "add_feed", lambda *_a, **_k: None)

    await handlers.addgroup_command(update, context)

    assert "No se pudo guardar" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_addgroup_exception_path(fake_update_context, monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context(args=["https://x.com"])
    monkeypatch.setattr(handlers, "_fetch_user_feeds", lambda _u: [])
    monkeypatch.setattr(handlers.SourceFactory, "resolve_registration_url", lambda _u: "https://feed.local/x")
    monkeypatch.setattr(handlers.feed_parser, "validate_feed_source", lambda _u: {"valid": True})
    monkeypatch.setattr(handlers.database, "add_user", lambda *_a, **_k: True)

    def _boom(*_a, **_k):
        raise RuntimeError("db fail")

    monkeypatch.setattr(handlers.database, "add_feed", _boom)

    await handlers.addgroup_command(update, context)

    assert "No se pudo guardar" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_addgroup_empty_raw_url(fake_update_context):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context()

    await handlers._addgroup_from_raw_url(update, "")

    assert "no puede estar vacía" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_groups_exception_path(fake_update_context, monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context()

    def _boom(_uid):
        raise RuntimeError("db fail")

    monkeypatch.setattr(handlers, "_fetch_user_feeds", _boom)

    await handlers.groups_command(update, context)

    assert "No se pudieron cargar" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_removegroup_user_missing(fake_update_context):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context(args=["1"])
    update.effective_user = None

    await handlers.removegroup_command(update, context)

    assert "No pude identificar" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_removegroup_exception_path(fake_update_context, monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context(args=["1"])
    monkeypatch.setattr(handlers, "_find_user_feed", lambda *_a: {"id": 1})

    def _boom(*_a, **_k):
        raise RuntimeError("db fail")

    monkeypatch.setattr(handlers, "_delete_user_feed", _boom)

    await handlers.removegroup_command(update, context)

    assert "No se pudo eliminar" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_pausegroup_user_missing(fake_update_context):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context(args=["1"])
    update.effective_user = None

    await handlers.pausegroup_command(update, context)

    assert "No pude identificar" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_pausegroup_exception_path(fake_update_context, monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context(args=["1"])
    monkeypatch.setattr(handlers, "_find_user_feed", lambda *_a: {"id": 1})

    def _boom(*_a, **_k):
        raise RuntimeError("db fail")

    monkeypatch.setattr(handlers, "_update_user_feed_status", _boom)

    await handlers.pausegroup_command(update, context)

    assert "No se pudo pausar" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_resumegroup_user_missing(fake_update_context):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context(args=["1"])
    update.effective_user = None

    await handlers.resumegroup_command(update, context)

    assert "No pude identificar" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_handlers_resumegroup_exception_path(fake_update_context, monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = fake_update_context(args=["1"])
    monkeypatch.setattr(handlers, "_find_user_feed", lambda *_a: {"id": 1})

    def _boom(*_a, **_k):
        raise RuntimeError("db fail")

    monkeypatch.setattr(handlers, "_update_user_feed_status", _boom)

    await handlers.resumegroup_command(update, context)

    assert "No se pudo reactivar" in replies[-1]["text"]


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
