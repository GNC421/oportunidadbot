from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Item:
    """Representa un anuncio normalizado, independiente del origen."""

    title: str
    summary: str
    link: str
    author: str
    published: str
    published_parsed: Any = None

    def to_dict(self) -> dict[str, Any]:
        """Convierte el item al formato de diccionario usado por el pipeline actual."""
        return {
            "title": self.title,
            "summary": self.summary,
            "link": self.link,
            "author": self.author,
            "published": self.published,
            "published_parsed": self.published_parsed,
        }
