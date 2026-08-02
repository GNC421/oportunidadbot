from __future__ import annotations

from types import SimpleNamespace
import pytest

from app.services import feed_parser


def test_parse_feed_content_list_and_string(monkeypatch):
    # content as list containing dict with value
    entry = {"title": "t", "summary": "s", "link": "u", "author": "a", "published": "p", "content": [{"value": "c_val"}]}
    monkeypatch.setattr(feed_parser, "parse_feed", lambda url: [entry])
    async def _yes(title, summary):
        return True
    monkeypatch.setattr(feed_parser.classifier, "is_business_opportunity", _yes)

    res = feed_parser.check_user_feeds({"id": 1, "url": "https://example.com/feed"})
    assert isinstance(res, list) and len(res) == 1

    # content as plain string
    entry2 = {"title": "t2", "summary": "s2", "link": "u2", "author": "a2", "published": "p2", "content": "plain text"}
    monkeypatch.setattr(feed_parser, "parse_feed", lambda url: [entry2])
    monkeypatch.setattr(feed_parser.classifier, "is_business_opportunity", lambda t, s: False)
    res2 = feed_parser.check_user_feeds({"id": 1, "url": "https://example.com/feed"})
    assert res2 == []


def test_validate_source_from_factory_exception_traced(monkeypatch):
    # SourceFactory.from_url raises
    def _boom(url, parse_feed_fn=None):
        raise RuntimeError("boom")

    monkeypatch.setattr(feed_parser.SourceFactory, "from_url", _boom)
    # ensure trace calls won't raise
    monkeypatch.setattr(feed_parser, "_maybe_run_async", lambda coro: "")

    res = feed_parser.validate_feed_source("https://example.com/feed")
    assert res["valid"] is False
