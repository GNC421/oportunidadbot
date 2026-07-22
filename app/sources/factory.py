from __future__ import annotations

from typing import Any, Callable, Optional
from urllib.parse import urlparse

from .base import BaseSource
from .rss_source import RSSSource
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
        return RSSSource(url=url, parse_feed_fn=parse_feed_fn)

    @staticmethod
    def resolve_registration_url(url: str, rsshub_resolve_fn: Callable[[str], Optional[str]]) -> Optional[str]:
        if SourceFactory._is_tablon_url(url):
            return url
        return rsshub_resolve_fn(url)
