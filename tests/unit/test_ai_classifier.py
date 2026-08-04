from __future__ import annotations

import asyncio
from types import SimpleNamespace
import pytest

import app.services.ai_classifier as ai_mod


class FakeTrace:
    async def start(self, **_k):
        return "evt"

    async def success(self, *a, **k):
        return None

    async def error(self, *a, **k):
        return None


def test_parse_response_and_cache_behavior():
    # parse_response
    cls = ai_mod.classifier
    assert cls._parse_response(None) is False
    assert cls._parse_response("true") is True
    assert cls._parse_response("False") is False

    # cache set/get/clear
    cls = ai_mod.classifier
    before = cls.clear_cache()
    cls._set_cached_result("k1", True)
    assert cls._get_cached_result("k1") is True
    assert cls.clear_cache() >= 1


@pytest.mark.asyncio
async def test_call_nvidia_stream_and_is_business_cached_and_disabled(monkeypatch):
    cls = ai_mod.classifier

    # monkeypatch trace service
    monkeypatch.setattr(ai_mod, "get_trace_service", lambda: FakeTrace())

    # fake SDK that yields stream chunks as dicts
    class FakeSDK:
        class chat:
            class completions:
                @staticmethod
                def create(**_k):
                    # return iterable of dicts representing stream
                    return [
                        {"choices": [{"delta": {"content": "true"}}]},
                    ]

    monkeypatch.setattr(cls, "_sdk_client", FakeSDK())
    monkeypatch.setattr(cls, "_api_key", "api_key")

    # call the private method
    res = await cls._call_nvidia("t", "s")
    assert isinstance(res, str)
    assert res.lower() == "true"

    # cached behavior: set and call is_business_opportunity
    key = cls._build_cache_key("t", "s")
    cls._set_cached_result(key, True)
    # ensure AI enabled
    monkeypatch.setattr(cls, "_ai_enabled", True)

    out = await cls.is_business_opportunity("t", "s")
    assert out is True

    # disabled AI returns True
    monkeypatch.setattr(cls, "_ai_enabled", False)
    out2 = await cls.is_business_opportunity("t2", "s2")
    assert out2 is True
