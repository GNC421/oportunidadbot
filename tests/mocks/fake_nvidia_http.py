"""Fakes de httpx para simular el endpoint NVIDIA NIM (SSE) en tests unitarios."""
from __future__ import annotations

from typing import Iterable, List, Union

import httpx


class FakeSSEResponse:
    """Simula una `httpx.Response` en modo streaming."""

    def __init__(self, status_code: int = 200, lines: Iterable[object] | None = None):
        self.status_code = status_code
        self._lines = list(lines or [])
        self.request = httpx.Request("POST", "https://nvidia.local/v1/chat/completions")

    def iter_lines(self):
        yield from self._lines

    def read(self) -> bytes:
        return b""

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(f"HTTP {self.status_code}", request=self.request, response=self)  # type: ignore[arg-type]


class _StreamContext:
    def __init__(self, response: FakeSSEResponse):
        self._response = response

    def __enter__(self) -> FakeSSEResponse:
        return self._response

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


QueueItem = Union[FakeSSEResponse, BaseException]


class FakeHttpxClient:
    """Sustituye a `httpx.Client`. Cada llamada a `.stream()` consume un elemento de la cola."""

    def __init__(self, queue: List[QueueItem] | None = None):
        self._queue: List[QueueItem] = list(queue or [])
        self.calls: List[dict] = []

    def __enter__(self) -> "FakeHttpxClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def stream(self, method: str, url: str, json: dict | None = None, headers: dict | None = None):
        self.calls.append({"method": method, "url": url, "json": json, "headers": headers})
        if not self._queue:
            raise AssertionError("FakeHttpxClient: no quedan respuestas/errores en la cola")
        item = self._queue.pop(0)
        if isinstance(item, BaseException):
            raise item
        return _StreamContext(item)


def make_client_factory(queue: List[QueueItem]):
    """Devuelve un callable que sustituye a `httpx.Client(timeout=...)` reutilizando la misma cola entre reintentos."""
    fake_client = FakeHttpxClient(queue=queue)

    def factory(*_args, **_kwargs):
        return fake_client

    factory.client = fake_client  # type: ignore[attr-defined]
    return factory
