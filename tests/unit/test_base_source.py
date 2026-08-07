from __future__ import annotations

from types import SimpleNamespace

from app.sources.base import BaseSource


class _DummySource(BaseSource):
    def validate(self) -> dict[str, object]:
        return {"valid": True, "error": None, "title": "", "entry_count": 0}

    def parse_items(self, limit: int = 10):
        return []


def test_base_source_request_text_retries_then_succeeds(monkeypatch):
    source = _DummySource("https://example.com")

    attempts = {"n": 0}

    def _fake_get(*_a, **_k):
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise RuntimeError("temporary failure")
        return SimpleNamespace(text="<html>ok</html>", raise_for_status=lambda: None)

    monkeypatch.setattr("app.sources.base.httpx.get", _fake_get)

    html = source._request_text()

    assert html == "<html>ok</html>"
    assert attempts["n"] == 2
    metrics = source.get_metrics()
    assert metrics["http_requests"] == 2
    assert metrics["http_retries"] == 1
    assert metrics["http_failures"] == 0


def test_base_source_request_text_fails_after_retries(monkeypatch):
    source = _DummySource("https://example.com")

    monkeypatch.setattr("app.sources.base.httpx.get", lambda *_a, **_k: (_ for _ in ()).throw(RuntimeError("network down")))

    html = source._request_text()

    assert html is None
    metrics = source.get_metrics()
    assert metrics["http_failures"] == 1
    assert metrics["http_requests"] == source.DEFAULT_HTTP_MAX_RETRIES + 1
