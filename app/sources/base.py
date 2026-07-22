from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

import httpx
from loguru import logger

from .item import Item


class BaseSource(ABC):
    """Contrato común para cualquier origen de datos (RSS o scraper HTML)."""

    DEFAULT_HTTP_TIMEOUT_SECONDS = 15.0
    DEFAULT_HTTP_MAX_RETRIES = 2
    DEFAULT_HTTP_USER_AGENT = "Mozilla/5.0 (compatible; OportunidadBot/1.0)"

    def __init__(self, url: str) -> None:
        self.url = url
        self._metrics: dict[str, int] = {
            "http_requests": 0,
            "http_retries": 0,
            "http_failures": 0,
            "parse_runs": 0,
            "items_extracted": 0,
            "html_structure_fallbacks": 0,
        }

    @property
    def source_name(self) -> str:
        return self.__class__.__name__

    def _source_logger(self):
        return logger.bind(source=self.source_name, source_url=self.url)

    def _inc_metric(self, key: str, value: int = 1) -> None:
        self._metrics[key] = self._metrics.get(key, 0) + value

    def get_metrics(self) -> dict[str, int]:
        """Devuelve una copia de métricas internas de scraping del source."""
        return dict(self._metrics)

    def _request_text(self, url: Optional[str] = None) -> Optional[str]:
        """Descarga texto HTTP con timeout y reintentos para scrapers HTML."""
        target_url = (url or self.url).strip()
        for attempt in range(self.DEFAULT_HTTP_MAX_RETRIES + 1):
            self._inc_metric("http_requests")
            try:
                response = httpx.get(
                    target_url,
                    headers={"User-Agent": self.DEFAULT_HTTP_USER_AGENT},
                    timeout=self.DEFAULT_HTTP_TIMEOUT_SECONDS,
                    follow_redirects=True,
                )
                response.raise_for_status()
                if attempt > 0:
                    self._source_logger().info(
                        "HTTP request recovered after retry",
                        attempt=attempt,
                        target_url=target_url,
                    )
                return response.text
            except Exception as exc:
                if attempt < self.DEFAULT_HTTP_MAX_RETRIES:
                    self._inc_metric("http_retries")
                    self._source_logger().warning(
                        "HTTP request failed, retrying",
                        attempt=attempt + 1,
                        max_retries=self.DEFAULT_HTTP_MAX_RETRIES,
                        target_url=target_url,
                        error=str(exc),
                    )
                    continue

                self._inc_metric("http_failures")
                self._source_logger().warning(
                    "HTTP request failed after retries",
                    attempts=self.DEFAULT_HTTP_MAX_RETRIES + 1,
                    target_url=target_url,
                    error=str(exc),
                )
                return None

    @abstractmethod
    def validate(self) -> dict[str, Any]:
        """Valida que el origen sea usable y devuelve un resultado estructurado."""

    @abstractmethod
    def parse_items(self, limit: int = 10) -> Optional[list[Item]]:
        """Parsea el origen y devuelve una lista de items normalizados."""
