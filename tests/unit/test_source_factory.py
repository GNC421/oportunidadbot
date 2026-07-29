from __future__ import annotations

from types import SimpleNamespace

from app.sources.factory import SourceFactory
from app.sources.reddit_source import RedditSource
from app.sources.rss_source import RSSFeedSource
from app.sources.tablon_source import TablonSource


def test_source_factory_tablon_returns_tablon_source():
    source = SourceFactory.from_url(
        "https://www.tablondeanuncios.com/inmobiliaria-en-murcia/?demanda=1",
        parse_feed_fn=lambda _u: None,
    )

    assert isinstance(source, TablonSource)


def test_source_factory_non_tablon_returns_rss_source():
    source = SourceFactory.from_url(
        "https://example.com/feed.xml",
        parse_feed_fn=lambda _u: SimpleNamespace(bozo=False, entries=[{}], feed={}),
    )

    assert isinstance(source, RSSFeedSource)


def test_source_factory_registration_url_tablon_kept_as_is():
    resolved = SourceFactory.resolve_registration_url(
        "https://tablondeanuncios.com/inmobiliaria/venta",
    )

    assert resolved == "https://tablondeanuncios.com/inmobiliaria/venta"


def test_source_factory_registration_url_reddit_subreddit_to_native_rss():
    resolved = SourceFactory.resolve_registration_url(
        "https://www.reddit.com/r/murcia",
    )

    assert resolved == "https://www.reddit.com/r/murcia/.rss"


def test_source_factory_registration_url_reddit_user_to_native_rss():
    resolved = SourceFactory.resolve_registration_url(
        "https://www.reddit.com/r/murcia/",
    )

    assert resolved == "https://www.reddit.com/r/murcia/.rss"


def test_source_factory_registration_url_reddit_host_preserved():
    resolved = SourceFactory.resolve_registration_url(
        "https://reddit.com/r/python",
    )

    assert resolved == "https://reddit.com/r/python/.rss"


def test_source_factory_returns_reddit_source_for_reddit_urls():
    source = SourceFactory.from_url(
        "https://reddit.com/r/python",
        parse_feed_fn=lambda _u: SimpleNamespace(bozo=False, entries=[{}], feed={}),
    )

    assert isinstance(source, RedditSource)
