from __future__ import annotations

from types import SimpleNamespace

from app.sources.factory import SourceFactory
from app.sources.rss_source import RSSSource
from app.sources.tablon_source import TablonSource


def test_source_factory_tablon_returns_tablon_source():
    source = SourceFactory.from_url(
        "https://www.tablondeanuncios.com/inmobiliaria-en-murcia/?demanda=1",
        parse_feed_fn=lambda _u: None,
    )

    assert isinstance(source, TablonSource)


def test_source_factory_non_tablon_returns_rss_source():
    source = SourceFactory.from_url(
        "https://reddit.com/r/python",
        parse_feed_fn=lambda _u: SimpleNamespace(bozo=False, entries=[{}], feed={}),
    )

    assert isinstance(source, RSSSource)


def test_source_factory_registration_url_tablon_kept_as_is():
    resolved = SourceFactory.resolve_registration_url(
        "https://tablondeanuncios.com/inmobiliaria/venta",
    )

    assert resolved == "https://tablondeanuncios.com/inmobiliaria/venta"


def test_source_factory_registration_url_reddit_subreddit_to_native_rss():
    resolved = SourceFactory.resolve_registration_url(
        "https://reddit.com/r/python",
    )

    assert resolved == "https://www.reddit.com/r/python/.rss"


def test_source_factory_registration_url_reddit_user_to_native_rss():
    resolved = SourceFactory.resolve_registration_url(
        "https://reddit.com/user/guillermo",
    )

    assert resolved == "https://www.reddit.com/user/guillermo/.rss"
