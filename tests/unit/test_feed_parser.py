from __future__ import annotations

from types import SimpleNamespace

from app.services import feed_parser


def test_parse_feed_empty_feed_returns_none(monkeypatch):
    fake_feed = SimpleNamespace(bozo=False, entries=[], feed={"title": "empty"})
    monkeypatch.setattr(feed_parser, "_parse_feed_source", lambda _url: fake_feed)

    assert feed_parser.parse_feed("https://rss.local/empty") is None


def test_parse_feed_ok(monkeypatch):
    entries = [
        {"title": "A", "summary": "B", "link": "https://x/1", "author": "u", "published": "now"}
    ]
    fake_feed = SimpleNamespace(bozo=False, entries=entries, feed={"title": "demo"})
    monkeypatch.setattr(feed_parser, "_parse_feed_source", lambda _url: fake_feed)

    result = feed_parser.parse_feed("https://rss.local/ok")

    assert len(result) == 1
    assert result[0]["title"] == "A"


def test_parse_feed_entry_without_title_or_summary(monkeypatch):
    entries = [{"link": "https://x/no-title"}]
    fake_feed = SimpleNamespace(bozo=False, entries=entries, feed={"title": "demo"})
    monkeypatch.setattr(feed_parser, "_parse_feed_source", lambda _url: fake_feed)

    result = feed_parser.parse_feed("https://rss.local/minimal")

    assert result[0]["title"] == ""
    assert result[0]["summary"] == ""


def test_parse_feed_huge_and_unicode(monkeypatch):
    huge = "á" * 10000
    entries = [{"title": "🏠 oportunidad", "summary": huge, "link": "https://x/unicode"}]
    fake_feed = SimpleNamespace(bozo=False, entries=entries, feed={"title": "demo"})
    monkeypatch.setattr(feed_parser, "_parse_feed_source", lambda _url: fake_feed)

    result = feed_parser.parse_feed("https://rss.local/unicode")

    assert result[0]["title"] == "🏠 oportunidad"
    assert len(result[0]["summary"]) == 10000


def test_parse_feed_without_link(monkeypatch):
    entries = [{"title": "sin link", "summary": "texto"}]
    fake_feed = SimpleNamespace(bozo=False, entries=entries, feed={"title": "demo"})
    monkeypatch.setattr(feed_parser, "_parse_feed_source", lambda _url: fake_feed)

    result = feed_parser.parse_feed("https://rss.local/no-link")

    assert result[0]["link"] == ""


def test_validate_feed_source_empty_url():
    result = feed_parser.validate_feed_source("")

    assert result["valid"] is False


def test_validate_feed_source_invalid_format():
    result = feed_parser.validate_feed_source("notaurl")

    assert result["valid"] is False


def test_validate_feed_source_bozo(monkeypatch):
    fake = SimpleNamespace(bozo=True, bozo_exception=ValueError("bad"), entries=[])
    monkeypatch.setattr(feed_parser, "_parse_feed_source", lambda _url: fake)

    result = feed_parser.validate_feed_source("https://rss.local/bozo")

    assert result["valid"] is False


def test_validate_feed_source_valid(monkeypatch):
    fake = SimpleNamespace(bozo=False, entries=[{"title": "ok"}], feed={"title": "Demo"})
    monkeypatch.setattr(feed_parser, "_parse_feed_source", lambda _url: fake)

    result = feed_parser.validate_feed_source("https://rss.local/ok")

    assert result["valid"] is True
    assert result["entry_count"] == 1


def test_detect_question_empty_returns_false():
    assert feed_parser.detect_question("") is False


def test_detect_question_handles_exception(monkeypatch):
    monkeypatch.setattr(feed_parser, "classifier", SimpleNamespace(is_business_opportunity=_raise_async))

    assert feed_parser.detect_question("hola") is False


def test_check_user_feeds_without_url_returns_empty():
    assert feed_parser.check_user_feeds({"id": 1, "user_id": 10}) == []


def test_check_user_feeds_filters_entries(monkeypatch):
    monkeypatch.setattr(
        feed_parser,
        "parse_feed",
        lambda _u: [
            {"title": "busco", "summary": "local", "link": "https://x/1", "author": "u", "published": "today"},
            {"title": "otro", "summary": "sin oportunidad", "link": "https://x/2", "author": "u", "published": "today"},
        ],
    )
    monkeypatch.setattr(feed_parser, "detect_question", lambda text: "busco" in text)

    result = feed_parser.check_user_feeds({"id": 1, "user_id": 10, "url": "https://rss.local"})

    assert len(result) == 1
    assert result[0]["url"] == "https://x/1"


def test_parse_feed_source_exception(monkeypatch):
    def _boom(_url):
        raise RuntimeError("network down")

    monkeypatch.setattr(feed_parser.feedparser, "parse", _boom)

    assert feed_parser._parse_feed_source("https://rss.local") is None


def test_parse_feed_handles_exception(monkeypatch):
    monkeypatch.setattr(feed_parser, "validate_feed_source", lambda _u: {"valid": True})
    monkeypatch.setattr(feed_parser, "_parse_feed_source", lambda _u: None)

    assert feed_parser.parse_feed("https://rss.local") is None


def test_detect_question_with_title_summary(monkeypatch):
    async def _ok(title, summary):
        return title == "Titulo" and summary == "Resumen"

    monkeypatch.setattr(feed_parser, "classifier", SimpleNamespace(is_business_opportunity=_ok))

    assert feed_parser.detect_question("Titulo\nResumen") is True


def test_check_user_feeds_exception(monkeypatch):
    monkeypatch.setattr(feed_parser, "parse_feed", lambda _u: (_ for _ in ()).throw(RuntimeError("boom")))

    assert feed_parser.check_user_feeds({"id": 1, "user_id": 10, "url": "https://rss.local"}) == []


def _raise_async(*_a, **_k):
    async def _inner():
        raise RuntimeError("classifier error")

    return _inner()
