from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from .item import Item


class BaseSource(ABC):
    """Contrato común para cualquier origen de datos (RSS o scraper HTML)."""

    def __init__(self, url: str) -> None:
        self.url = url

    @abstractmethod
    def validate(self) -> dict[str, Any]:
        """Valida que el origen sea usable y devuelve un resultado estructurado."""

    @abstractmethod
    def parse_items(self, limit: int = 10) -> Optional[list[Item]]:
        """Parsea el origen y devuelve una lista de items normalizados."""
