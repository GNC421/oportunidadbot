from __future__ import annotations

from typing import Any, Callable, Optional

from .base import BaseSource
from .rss_source import RSSSource


class SourceFactory:
    """Resuelve automáticamente el tipo de fuente para una URL dada."""

    @staticmethod
    def from_url(url: str, parse_feed_fn: Callable[[str], Optional[Any]]) -> BaseSource:
        # Fase 1: todas las fuentes se tratan como RSS para mantener compatibilidad.
        return RSSSource(url=url, parse_feed_fn=parse_feed_fn)
