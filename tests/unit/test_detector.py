from __future__ import annotations

from types import SimpleNamespace
import pytest

from app.services.ai_classifier import AIClassifier


@pytest.mark.asyncio
async def test_detector_positive_response(monkeypatch):
    detector = AIClassifier()
    monkeypatch.setattr(detector, "_call_nvidia", lambda *_a, **_k: _async_value("true"))

    assert await detector.is_business_opportunity("titulo", "resumen") is True


@pytest.mark.asyncio
async def test_detector_negative_response(monkeypatch):
    detector = AIClassifier()
    monkeypatch.setattr(detector, "_call_nvidia", lambda *_a, **_k: _async_value("false"))

    assert await detector.is_business_opportunity("titulo", "resumen") is False


@pytest.mark.asyncio
async def test_detector_timeout_returns_false(monkeypatch):
    detector = AIClassifier()

    async def _timeout(*_a, **_k):
        raise TimeoutError("timeout")

    monkeypatch.setattr(detector, "_call_nvidia", _timeout)

    assert await detector.is_business_opportunity("titulo", "resumen") is False


@pytest.mark.asyncio
async def test_detector_invalid_response_returns_false(monkeypatch):
    detector = AIClassifier()
    monkeypatch.setattr(detector, "_call_nvidia", lambda *_a, **_k: _async_value("maybe"))

    assert await detector.is_business_opportunity("titulo", "resumen") is False


@pytest.mark.asyncio
async def test_detector_http500_retries_and_fails(monkeypatch):
    detector = AIClassifier()
    calls = {"n": 0}
    class FakeCompletions:
        def __init__(self, calls):
            self.calls = calls

        async def create(self, *_a, **_k):
            self.calls["n"] += 1
            raise Exception("server error")

    fake_sdk = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions(calls)))
    detector._sdk_client = fake_sdk
    monkeypatch.setattr("app.services.ai_classifier.asyncio.sleep", lambda *_a, **_k: _async_value(None))

    response = await detector._call_nvidia("t", "s")

    assert response is None
    assert calls["n"] == detector._max_retries


@pytest.mark.asyncio
async def test_detector_retries_until_success(monkeypatch):
    detector = AIClassifier()
    calls = {"n": 0}
    class FakeCompletions:
        def __init__(self, calls):
            self.calls = calls

        async def create(self, *_a, **_k):
            self.calls["n"] += 1
            if self.calls["n"] == detector._max_retries:
                return {"choices": [{"message": {"content": "true"}}]}
            raise Exception("boom")

    fake_sdk = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions(calls)))
    detector._sdk_client = fake_sdk
    monkeypatch.setattr("app.services.ai_classifier.asyncio.sleep", lambda *_a, **_k: _async_value(None))

    response = await detector._call_nvidia("t", "s")

    assert response == "true"
    assert calls["n"] == detector._max_retries


@pytest.mark.asyncio
async def test_detector_ai_disabled_returns_true():
    detector = AIClassifier()
    detector._ai_enabled = False

    assert await detector.is_business_opportunity("t", "s") is True


@pytest.mark.asyncio
async def test_detector_empty_input_returns_false():
    detector = AIClassifier()

    assert await detector.is_business_opportunity("", "") is False


@pytest.mark.asyncio
async def test_detector_without_api_key_returns_false():
    detector = AIClassifier()
    detector._api_key = None

    assert await detector.is_business_opportunity("t", "s") is False


@pytest.mark.asyncio
async def test_detector_cache_hit(monkeypatch):
    detector = AIClassifier()
    detector._cache[detector._build_cache_key("t", "s")] = True

    called = {"value": False}

    async def _should_not_call(*_a, **_k):
        called["value"] = True
        return "false"

    monkeypatch.setattr(detector, "_call_nvidia", _should_not_call)

    assert await detector.is_business_opportunity("t", "s") is True
    assert called["value"] is False


def test_detector_parse_response_none():
    detector = AIClassifier()
    assert detector._parse_response(None) is False


@pytest.mark.asyncio
async def test_detector_call_nvidia_without_key_returns_none():
    detector = AIClassifier()
    detector._api_key = None

    assert await detector._call_nvidia("t", "s") is None


@pytest.mark.asyncio
async def test_detector_call_nvidia_without_choices(monkeypatch):
    detector = AIClassifier()
    class FakeCompletions:
        async def create(self, *_a, **_k):
            return {"choices": []}

    fake_sdk = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    detector._sdk_client = fake_sdk

    assert await detector._call_nvidia("t", "s") is None


def test_detector_get_sdk_client_initialized():
    detector = AIClassifier()
    assert getattr(detector, "_sdk_client", None) is not None


def test_detector_cache_eviction():
    detector = AIClassifier()
    detector._cache_limit = 1
    detector._set_cached_result("a", True)
    detector._set_cached_result("b", False)

    assert detector._get_cached_result("a") is None
    assert detector._get_cached_result("b") is False


def test_detector_parse_response_exception_path():
    detector = AIClassifier()

    class BadValue:
        def strip(self):
            raise RuntimeError("bad")

    assert detector._parse_response(BadValue()) is False


def _async_value(value):
    async def _inner():
        return value

    return _inner()
