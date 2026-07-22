from __future__ import annotations

from typing import Any, Callable, Optional

from .base import BaseSource
from .item import Item


class RSSSource(BaseSource):
    """Implementación de fuente basada en RSS usando feedparser existente."""

    def __init__(self, url: str, parse_feed_fn: Callable[[str], Optional[Any]]) -> None:
        super().__init__(url)
        self._parse_feed_fn = parse_feed_fn

    def _load_parsed_feed(self) -> Optional[Any]:
        return self._parse_feed_fn(self.url)

    @staticmethod
    def _extract_entries(parsed_feed: Any) -> list[Any]:
        return getattr(parsed_feed, "entries", []) or []

    def validate(self) -> dict[str, Any]:
        parsed_feed = self._load_parsed_feed()
        if parsed_feed is None:
            return {
                "valid": False,
                "error": "No se pudo obtener el contenido del feed",
                "title": "",
                "entry_count": 0,
            }

        if getattr(parsed_feed, "bozo", False):
            error_detail = getattr(parsed_feed, "bozo_exception", None)
            self._source_logger().warning(
                "Invalid RSS payload",
                error_detail=str(error_detail),
            )
            return {
                "valid": False,
                "error": "No se pudo procesar como un RSS válido",
                "title": "",
                "entry_count": 0,
            }

        entries = self._extract_entries(parsed_feed)
        if not entries:
            self._source_logger().warning("RSS feed has no entries")
            return {
                "valid": False,
                "error": "El feed no tiene entradas disponibles",
                "title": "",
                "entry_count": 0,
            }

        feed_title = ""
        feed_data = getattr(parsed_feed, "feed", {}) or {}
        if isinstance(feed_data, dict):
            feed_title = feed_data.get("title", "") or ""

        self._source_logger().info("RSS source validated", entry_count=len(entries))
        return {
            "valid": True,
            "error": None,
            "title": feed_title,
            "entry_count": len(entries),
        }

    def parse_items(self, limit: int = 10) -> Optional[list[Item]]:
        try:
            parsed_feed = self._load_parsed_feed()
            if parsed_feed is None:
                return None

            if getattr(parsed_feed, "bozo", False):
                return None

            entries = self._extract_entries(parsed_feed)
            if not entries:
                return None

            items: list[Item] = []
            for entry in entries[:limit]:
                items.append(
                    Item(
                        title=entry.get("title", ""),
                        summary=entry.get("summary", ""),
                        link=entry.get("link", ""),
                        author=entry.get("author", ""),
                        published=entry.get("published", ""),
                        published_parsed=entry.get("published_parsed"),
                    )
                )

            self._source_logger().info("RSS source parsed successfully", parsed_entries=len(items))
            return items
        except Exception as exc:
            self._source_logger().error("Error parsing RSS source", error=str(exc))
            return None
