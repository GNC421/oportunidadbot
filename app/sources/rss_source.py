from __future__ import annotations

from typing import Any, Callable, Optional

from loguru import logger

from .base import BaseSource
from .item import Item


class RSSSource(BaseSource):
    """Implementación de fuente basada en RSS usando feedparser existente."""

    def __init__(self, url: str, parse_feed_fn: Callable[[str], Optional[Any]]) -> None:
        super().__init__(url)
        self._parse_feed_fn = parse_feed_fn

    def validate(self) -> dict[str, Any]:
        parsed_feed = self._parse_feed_fn(self.url)
        if parsed_feed is None:
            return {
                "valid": False,
                "error": "No se pudo obtener el contenido del feed",
                "title": "",
                "entry_count": 0,
            }

        if getattr(parsed_feed, "bozo", False):
            error_detail = getattr(parsed_feed, "bozo_exception", None)
            logger.warning(f"El feed no pudo procesarse como RSS válido: {self.url} ({error_detail})")
            return {
                "valid": False,
                "error": "No se pudo procesar como un RSS válido",
                "title": "",
                "entry_count": 0,
            }

        entries = getattr(parsed_feed, "entries", []) or []
        if not entries:
            logger.warning(f"El feed no tiene entradas: {self.url}")
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

        logger.info(f"Feed RSS válido: {self.url} ({len(entries)} entradas)")
        return {
            "valid": True,
            "error": None,
            "title": feed_title,
            "entry_count": len(entries),
        }

    def parse_items(self, limit: int = 10) -> Optional[list[Item]]:
        validation = self.validate()
        if not validation.get("valid", False):
            logger.warning(f"No se parseará el feed inválido {self.url}: {validation.get('error')}")
            return None

        try:
            parsed_feed = self._parse_feed_fn(self.url)
            if parsed_feed is None:
                return None

            items: list[Item] = []
            for entry in parsed_feed.entries[:limit]:
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

            logger.info("Feed parsed successfully", url=self.url, parsed_entries=len(items))
            return items
        except Exception as exc:
            logger.error(f"Error al parsear feed {self.url}: {exc}")
            return None
