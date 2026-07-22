from __future__ import annotations

from typing import Any, Callable, Optional
from urllib.parse import urlparse, urlunparse

from .base import BaseSource
from .item import Item
from .rss_source import RSSFeedSource


class RedditSource(BaseSource):
    """Source para Reddit que delega parsing al feed RSS oficial."""

    def __init__(self, url: str, parse_feed_fn: Callable[[str], Optional[Any]]) -> None:
        super().__init__(url)
        rss_url = self.build_rss_url(url)
        self._rss_source = RSSFeedSource(url=rss_url, parse_feed_fn=parse_feed_fn)

    @staticmethod
    def is_reddit_url(url: str) -> bool:
        parsed = urlparse((url or "").strip())
        host = (parsed.netloc or "").lower()
        return host == "reddit.com" or host.endswith(".reddit.com")

    @staticmethod
    def build_rss_url(url: str) -> str:
        parsed = urlparse((url or "").strip())
        cleaned_path = "/".join(part for part in (parsed.path or "").split("/") if part)

        if cleaned_path.endswith(".rss"):
            final_path = f"/{cleaned_path}"
        else:
            final_path = f"/{cleaned_path}/.rss" if cleaned_path else "/.rss"

        return urlunparse(
            (
                parsed.scheme,
                parsed.netloc,
                final_path,
                "",
                "",
                "",
            )
        )

    @property
    def rss_url(self) -> str:
        return self._rss_source.url

    def validate(self) -> dict[str, Any]:
        return self._rss_source.validate()

    def parse_items(self, limit: int = 10) -> Optional[list[Item]]:
        return self._rss_source.parse_items(limit=limit)