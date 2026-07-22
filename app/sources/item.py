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
    external_id: str = ""
    url: str = ""
    description: str = ""
    image: str = ""
    price: str = ""
    published_date: str = ""
    category: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convierte el item al formato de diccionario usado por el pipeline actual."""
        return {
            "title": self.title,
            "summary": self.summary,
            "link": self.link,
            "author": self.author,
            "published": self.published,
            "published_parsed": self.published_parsed,
            "external_id": self.external_id,
            "url": self.url or self.link,
            "description": self.description or self.summary,
            "image": self.image,
            "price": self.price,
            "published_date": self.published_date or self.published,
            "category": self.category,
        }
