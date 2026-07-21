from __future__ import annotations

import asyncio
import os
from types import SimpleNamespace
from typing import Any

import pytest

from tests.mocks.fake_nvidia import FakeNvidia
from tests.mocks.fake_rsshub import FakeRSSHub
from tests.mocks.fake_scheduler import FakeScheduler
from tests.mocks.fake_supabase import FakeSupabase
from tests.mocks.fake_telegram import FakeTelegram

# Evita fallos de import al cargar app.config/settings durante tests.
os.environ.setdefault("BOT_TOKEN", "test-token")
os.environ.setdefault("SUPABASE_URL", "https://test.supabase.local")
os.environ.setdefault("SUPABASE_KEY", "test-key")
os.environ.setdefault("NVIDIA_API_KEY", "nvidia-test-key")
os.environ.setdefault("NVIDIA_BASE_URL", "https://nvidia.local/v1")
os.environ.setdefault("NVIDIA_MODEL", "test-model")
os.environ.setdefault("AI_ENABLED", "true")
os.environ.setdefault("RSSHUB_BASE_URL", "https://rsshub.local")

pytest_plugins = [
    "tests.fixtures.users",
    "tests.fixtures.feeds",
    "tests.fixtures.rss_entries",
    "tests.fixtures.telegram",
    "tests.fixtures.nvidia",
    "tests.fixtures.database",
]


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Asigna markers por carpeta para permitir ejecución selectiva por capa."""
    for item in items:
        path = str(item.fspath).replace("\\", "/")
        if "/tests/unit/" in path:
            item.add_marker(pytest.mark.unit)
        elif "/tests/integration/" in path:
            item.add_marker(pytest.mark.integration)
        elif "/tests/e2e/" in path:
            item.add_marker(pytest.mark.e2e)


@pytest.fixture
def event_loop() -> Any:
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def fake_supabase() -> FakeSupabase:
    return FakeSupabase()


@pytest.fixture
def fake_telegram() -> FakeTelegram:
    return FakeTelegram()


@pytest.fixture
def fake_nvidia() -> FakeNvidia:
    return FakeNvidia()


@pytest.fixture
def fake_rsshub() -> FakeRSSHub:
    return FakeRSSHub()


@pytest.fixture
def fake_scheduler() -> FakeScheduler:
    return FakeScheduler()


@pytest.fixture
def feed_factory() -> Any:
    def _factory(feed_id: int = 1, user_id: int = 101, url: str = "https://rss.local/feed.xml", is_active: bool = True) -> dict:
        return {"id": feed_id, "user_id": user_id, "url": url, "is_active": is_active}

    return _factory


@pytest.fixture
def alert_factory() -> Any:
    def _factory(
        title: str = "Nueva oportunidad",
        summary: str = "Busco inmueble rentable",
        link: str = "https://origin.local/post-1",
        author: str = "Anon",
    ) -> dict:
        return {
            "title": title,
            "summary": summary,
            "url": link,
            "link": link,
            "author": author,
            "question": f"{title} {summary}".strip(),
        }

    return _factory


@pytest.fixture
def fake_update_context() -> Any:
    def _factory(user_id: int = 101, first_name: str = "Tester", username: str = "tester", args: list[str] | None = None) -> tuple[Any, Any, list[dict[str, Any]]]:
        replies: list[dict[str, Any]] = []

        async def reply_text(text: str, **kwargs: Any) -> None:
            replies.append({"text": text, "kwargs": kwargs})

        async def edit_message_text(text: str, **kwargs: Any) -> None:
            replies.append({"text": text, "kwargs": kwargs, "edited": True})

        message = SimpleNamespace(text="hello", reply_text=reply_text)
        user = SimpleNamespace(id=user_id, first_name=first_name, username=username)

        async def answer(*_a: Any, **_k: Any) -> None:
            return None

        callback_query = SimpleNamespace(answer=answer, edit_message_text=edit_message_text, message=message, data="")
        update = SimpleNamespace(effective_user=user, message=message, callback_query=callback_query)
        context = SimpleNamespace(args=args or [], matches=[])
        return update, context, replies

    return _factory
