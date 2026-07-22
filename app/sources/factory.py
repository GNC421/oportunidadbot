from __future__ import annotations

from typing import Any, Callable, Optional
from urllib.parse import urlparse

from .base import BaseSource
from .reddit_source import RedditSource
from .rss_source import RSSFeedSource
from .tablon_source import TablonSource


class SourceFactory:
    """Resuelve automáticamente el tipo de fuente para una URL dada."""

    _TABLON_HOSTS = ("tablondeanuncios.com",)

    @classmethod
    def _is_tablon_url(cls, url: str) -> bool:
        parsed = urlparse(url.strip())
        host = (parsed.netloc or "").lower()
        return any(host == domain or host.endswith(f".{domain}") for domain in cls._TABLON_HOSTS)

    @staticmethod
    def from_url(url: str, parse_feed_fn: Callable[[str], Optional[Any]]) -> BaseSource:
        if SourceFactory._is_tablon_url(url):
            return TablonSource(url=url)
        if RedditSource.is_reddit_url(url):
            return RedditSource(url=url, parse_feed_fn=parse_feed_fn)
        return RSSFeedSource(url=url, parse_feed_fn=parse_feed_fn)

    @staticmethod
    def resolve_registration_url(url: str) -> Optional[str]:
        normalized = (url or "").strip()
        if not normalized:
            return None
        if RedditSource.is_reddit_url(normalized):
            return RedditSource.build_rss_url(normalized)
        return normalized
