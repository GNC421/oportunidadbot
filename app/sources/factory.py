from __future__ import annotations

from typing import Any, Callable, Optional
from urllib.parse import urlparse

from .base import BaseSource
from .rss_source import RSSSource
from .tablon_source import TablonSource


class SourceFactory:
    """Resuelve automáticamente el tipo de fuente para una URL dada."""

    _TABLON_HOSTS = ("tablondeanuncios.com",)
    _REDDIT_HOSTS = ("reddit.com",)

    @classmethod
    def _is_tablon_url(cls, url: str) -> bool:
        parsed = urlparse(url.strip())
        host = (parsed.netloc or "").lower()
        return any(host == domain or host.endswith(f".{domain}") for domain in cls._TABLON_HOSTS)

    @classmethod
    def _is_reddit_url(cls, url: str) -> bool:
        parsed = urlparse(url.strip())
        host = (parsed.netloc or "").lower()
        return any(host == domain or host.endswith(f".{domain}") for domain in cls._REDDIT_HOSTS)

    @staticmethod
    def _resolve_reddit_registration_url(url: str) -> str:
        parsed = urlparse(url)
        path = (parsed.path or "").strip("/")
        parts = [part for part in path.split("/") if part]

        if len(parts) >= 2 and parts[0] == "r":
            subreddit = parts[1]
            return f"https://www.reddit.com/r/{subreddit}/.rss"

        if len(parts) >= 2 and parts[0] == "user":
            username = parts[1]
            return f"https://www.reddit.com/user/{username}/.rss"

        normalized = url.rstrip("/")
        if normalized.endswith(".rss"):
            return normalized

        return f"{normalized}/.rss"

    @staticmethod
    def from_url(url: str, parse_feed_fn: Callable[[str], Optional[Any]]) -> BaseSource:
        if SourceFactory._is_tablon_url(url):
            return TablonSource(url=url)
        return RSSSource(url=url, parse_feed_fn=parse_feed_fn)

    @staticmethod
    def resolve_registration_url(url: str) -> Optional[str]:
        normalized = (url or "").strip()
        if not normalized:
            return None
        if SourceFactory._is_reddit_url(normalized):
            return SourceFactory._resolve_reddit_registration_url(normalized)
        return normalized
