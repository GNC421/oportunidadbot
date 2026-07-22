from __future__ import annotations

from types import SimpleNamespace

from app.sources.item import Item
from app.sources.reddit_source import RedditSource


def test_reddit_source_build_rss_url_without_trailing_slash():
    rss_url = RedditSource.build_rss_url("https://www.reddit.com/r/murcia")

    assert rss_url == "https://www.reddit.com/r/murcia/.rss"


def test_reddit_source_build_rss_url_with_trailing_slash():
    rss_url = RedditSource.build_rss_url("https://www.reddit.com/r/murcia/")

    assert rss_url == "https://www.reddit.com/r/murcia/.rss"


def test_reddit_source_build_rss_url_preserves_host():
    rss_url = RedditSource.build_rss_url("https://reddit.com/r/python")

    assert rss_url == "https://reddit.com/r/python/.rss"


def test_reddit_source_delegates_parse_to_rss_feed_source(monkeypatch):
    source = RedditSource(
        "https://reddit.com/r/python",
        parse_feed_fn=lambda _u: SimpleNamespace(bozo=False, entries=[{}], feed={}),
    )

    called = {"parse": 0, "url": ""}

    def _fake_parse_items(limit=10):
        called["parse"] += 1
        called["url"] = source.rss_url
        return [Item(title="t", summary="s", link="https://x", author="a", published="p")]

    monkeypatch.setattr(source._rss_source, "parse_items", _fake_parse_items)

    items = source.parse_items(limit=5)

    assert items is not None
    assert len(items) == 1
    assert called["parse"] == 1
    assert called["url"] == "https://reddit.com/r/python/.rss"