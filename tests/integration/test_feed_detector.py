from __future__ import annotations

from types import SimpleNamespace

from app.services import feed_parser


def test_feed_parser_detector_integration(monkeypatch):
    entries = [
        {"title": "Busco piso", "summary": "zona centro", "link": "https://x/1", "author": "u"},
        {"title": "Offtopic", "summary": "nada", "link": "https://x/2", "author": "u"},
    ]
    fake_feed = SimpleNamespace(bozo=False, entries=entries, feed={"title": "demo"})
    monkeypatch.setattr(feed_parser, "_parse_feed_source", lambda _url: fake_feed)
    monkeypatch.setattr(feed_parser, "detect_question", lambda text: "busco" in text.lower())

    result = feed_parser.check_user_feeds({"id": 1, "user_id": 101, "url": "https://rss.local/feed"})

    assert len(result) == 1
    assert result[0]["url"] == "https://x/1"
