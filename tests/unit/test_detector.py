from __future__ import annotations

import pytest

from app.services.ai_classifier import AIClassifier
import app.services.ai_classifier as ai_mod
from tests.mocks.fake_nvidia_http import FakeSSEResponse, make_client_factory


async def _async_value(value):
    return value


def _sse(text: str) -> list[str]:
    return ['data: {"choices":[{"delta":{"content":"%s"}}]}' % text, "data: [DONE]"]


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    monkeypatch.setattr(ai_mod.asyncio, "sleep", lambda *_a, **_k: _async_value(None))


def _new_detector() -> AIClassifier:
    detector = AIClassifier()
    detector._api_key = "test-api-key"
    detector._endpoint = "https://nvidia.local/v1/chat/completions"
    detector._ai_enabled = True
    return detector


@pytest.mark.asyncio
async def test_detector_positive_response(monkeypatch):
    detector = _new_detector()
    monkeypatch.setattr(ai_mod.httpx, "Client", make_client_factory([FakeSSEResponse(lines=_sse("true"))]))

    assert await detector.is_business_opportunity("titulo", "resumen") is True


@pytest.mark.asyncio
async def test_detector_negative_response(monkeypatch):
    detector = _new_detector()
    monkeypatch.setattr(ai_mod.httpx, "Client", make_client_factory([FakeSSEResponse(lines=_sse("false"))]))

    assert await detector.is_business_opportunity("titulo", "resumen") is False


@pytest.mark.asyncio
async def test_detector_timeout_returns_false(monkeypatch):
    detector = _new_detector()

    async def _timeout(*_a, **_k):
        raise TimeoutError("timeout")

    monkeypatch.setattr(detector, "_call_nvidia", _timeout)

    assert await detector.is_business_opportunity("titulo", "resumen") is False


@pytest.mark.asyncio
async def test_detector_invalid_response_returns_false(monkeypatch):
    detector = _new_detector()
    monkeypatch.setattr(ai_mod.httpx, "Client", make_client_factory([FakeSSEResponse(lines=_sse("maybe"))]))

    assert await detector.is_business_opportunity("titulo", "resumen") is False


@pytest.mark.asyncio
async def test_detector_http500_retries_and_fails(monkeypatch):
    detector = _new_detector()
    responses = [FakeSSEResponse(status_code=500, lines=[]) for _ in range(detector._max_retries)]
    factory = make_client_factory(responses)
    monkeypatch.setattr(ai_mod.httpx, "Client", factory)

    response = await detector._call_nvidia("t", "s")

    assert response is None
    assert len(factory.client.calls) == detector._max_retries


@pytest.mark.asyncio
async def test_detector_retries_until_success(monkeypatch):
    detector = _new_detector()
    responses = [FakeSSEResponse(status_code=500, lines=[]) for _ in range(detector._max_retries - 1)]
    responses.append(FakeSSEResponse(status_code=200, lines=_sse("true")))
    factory = make_client_factory(responses)
    monkeypatch.setattr(ai_mod.httpx, "Client", factory)

    response = await detector._call_nvidia("t", "s")

    assert response == "true"
    assert len(factory.client.calls) == detector._max_retries


@pytest.mark.asyncio
async def test_detector_ai_disabled_returns_true():
    detector = _new_detector()
    detector._ai_enabled = False

    assert await detector.is_business_opportunity("t", "s") is True


@pytest.mark.asyncio
async def test_detector_empty_input_returns_false():
    detector = _new_detector()

    assert await detector.is_business_opportunity("", "") is False


@pytest.mark.asyncio
async def test_detector_without_api_key_returns_false():
    detector = _new_detector()
    detector._api_key = None

    assert await detector.is_business_opportunity("t", "s") is False


@pytest.mark.asyncio
async def test_detector_cache_hit(monkeypatch):
    detector = _new_detector()
    detector._cache[detector._build_cache_key("t", "s")] = True

    called = {"value": False}

    async def _should_not_call(*_a, **_k):
        called["value"] = True
        return "false"

    monkeypatch.setattr(detector, "_call_nvidia", _should_not_call)

    assert await detector.is_business_opportunity("t", "s") is True
    assert called["value"] is False


def test_detector_parse_response_none():
    detector = _new_detector()
    assert detector._parse_response(None) is False


@pytest.mark.asyncio
async def test_detector_call_nvidia_without_key_returns_none():
    detector = _new_detector()
    detector._api_key = None

    assert await detector._call_nvidia("t", "s") is None


@pytest.mark.asyncio
async def test_detector_call_nvidia_without_choices(monkeypatch):
    detector = _new_detector()
    monkeypatch.setattr(ai_mod.httpx, "Client", make_client_factory([FakeSSEResponse(lines=[])]))

    assert await detector._call_nvidia("t", "s") is None


def test_detector_endpoint_configured():
    detector = _new_detector()
    assert detector._endpoint == "https://nvidia.local/v1/chat/completions"


def test_detector_cache_eviction():
    detector = _new_detector()
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
