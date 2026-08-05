from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Tuple, Union

from bs4 import BeautifulSoup, Tag
from urllib.parse import urljoin
from loguru import logger

from .base import BaseSource
from .item import Item
from app.debug.trace_service import get_trace_service
from app.debug.trace_models import EventType


def _maybe_run_async(coro):
    try:
        import asyncio

        loop = asyncio.get_running_loop()
        loop.create_task(coro)
        return ""
    except RuntimeError:
        import asyncio

        return asyncio.run(coro)


SelectorType = Union[str, Tuple[str, ...]]


@dataclass
class HTMLSelectors:
    """Configuración de selectores CSS para un scraper HTML.

    Los campos pueden ser una cadena única o una tupla de selectores
    para permitir fallbacks sin que `HTMLSource` conozca detalles del sitio.
    """

    item_selector: SelectorType
    title_selector: SelectorType
    description_selector: Optional[SelectorType] = None
    price_selector: Optional[SelectorType] = None
    location_selector: Optional[SelectorType] = None
    image_selector: Optional[SelectorType] = None
    link_selector: Optional[SelectorType] = None
    published_selector: Optional[SelectorType] = None
    author_selector: Optional[SelectorType] = None
    category_selector: Optional[SelectorType] = None


class HTMLSource(BaseSource):
    """Base para scrapers HTML.

    Proporciona:
    - descarga de HTML (usando BaseSource._request_text)
    - creación de BeautifulSoup
    - localización de artículos usando `selectors.item_selector`
    - extractores reutilizables con fallbacks
    - integración con TraceService, métricas y logging centralizado

    Subclases solo deben definir `selectors: HTMLSelectors` y
    `build_item(self, article: Tag, extracted: dict) -> Item`.
    """

    selectors: HTMLSelectors

    def _fetch_html(self) -> Optional[str]:
        return self._request_text(self.url)

    def _soup_from_html(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "lxml")

    @staticmethod
    def _to_tuple(selectors: Optional[SelectorType]) -> Tuple[str, ...]:
        if selectors is None:
            return tuple()
        if isinstance(selectors, tuple):
            return selectors
        return (selectors,)

    def _find_articles(self, soup: BeautifulSoup) -> Tuple[list[Tag], bool]:
        primary_tuple = self._to_tuple(self.selectors.item_selector)
        articles: list[Tag] = []
        used_fallback = False
        matched_selector = None

        for sel in primary_tuple:
            articles = soup.select(sel)
            if articles:
                matched_selector = sel
                break

        # if no articles found, attempt a very generic fallback (any article tag)
        if not articles:
            matched_selector = "article"
            articles = soup.select("article") or []

        # consider fallback used when the matched selector is not the first primary selector
        first_primary = primary_tuple[0] if primary_tuple else None
        if matched_selector and first_primary and matched_selector != first_primary:
            used_fallback = True

        return articles, used_fallback

    def _record_fallback(self, primary: str, fallback: str, matches: int) -> None:
        self._inc_metric("html_structure_fallbacks")
        self._source_logger().warning(
            "Primary selector missing, using fallback selector",
            primary_selector=primary,
            fallback_selector=fallback,
            fallback_matches=matches,
        )

    def _extract_text(self, root: Tag, selectors: Optional[SelectorType]) -> str:
        for sel in self._to_tuple(selectors):
            node = root.select_one(sel)
            if node:
                text = node.get_text(" ", strip=True)
                if text:
                    return text
        return ""

    def _extract_link(self, root: Tag, selectors: Optional[SelectorType]) -> str:
        for sel in self._to_tuple(selectors):
            node = root.select_one(sel)
            if node and node.get("href"):
                return urljoin(self.url, str(node.get("href")))

        # try common anchor attributes inside the article
        node = root.select_one("a[href]")
        if node and node.get("href"):
            return urljoin(self.url, str(node.get("href")))

        return ""

    def _extract_image(self, root: Tag, selectors: Optional[SelectorType]) -> str:
        for sel in self._to_tuple(selectors):
            node = root.select_one(sel)
            if node:
                for attr in ("src", "data-src", "data-original"):
                    val = node.get(attr)
                    if val:
                        return urljoin(self.url, str(val))

        # generic img
        node = root.select_one("img")
        if node:
            for attr in ("src", "data-src", "data-original"):
                val = node.get(attr)
                if val:
                    return urljoin(self.url, str(val))
        return ""

    def _extract_external_id(self, root: Tag) -> str:
        return str(root.get("id") or "").strip()

    def _extract_price(self, root: Tag, selectors: Optional[SelectorType]) -> str:
        return self._extract_text(root, selectors)

    def _extract_date(self, root: Tag, selectors: Optional[SelectorType]) -> str:
        date = self._extract_text(root, selectors)
        if not date:
            time_node = root.select_one("time[datetime]")
            if time_node:
                date = str(time_node.get("datetime") or "").strip()
        return date

    def _extract_location(self, root: Tag, selectors: Optional[SelectorType]) -> str:
        return self._extract_text(root, selectors)

    def validate(self) -> dict[str, Any]:
        trace = get_trace_service()
        event_id = _maybe_run_async(trace.start(type=EventType.HTML, name=f"{self.source_name} validate", input_payload={"url": self.url}))

        html = self._fetch_html()
        if html is None:
            try:
                _maybe_run_async(trace.error(event_id, error="no content"))
            except Exception:
                pass
            return {"valid": False, "error": "No se pudo obtener el contenido de la fuente", "title": "", "entry_count": 0}

        soup = self._soup_from_html(html)
        articles, used_fallback = self._find_articles(soup)
        if used_fallback and articles:
            self._record_fallback(primary=str(self.selectors.item_selector), fallback="article", matches=len(articles))

        if not articles:
            try:
                _maybe_run_async(trace.error(event_id, error="no entries"))
            except Exception:
                pass
            return {"valid": False, "error": "La fuente no contiene anuncios válidos", "title": "", "entry_count": 0}

        return {"valid": True, "error": None, "title": self.source_name, "entry_count": len(articles)}

    def parse_items(self, limit: int = 10) -> Optional[list[Item]]:
        trace = get_trace_service()
        event_id = _maybe_run_async(trace.start(type=EventType.HTML, name=f"{self.source_name} parse", input_payload={"url": self.url, "limit": limit}))
        try:

            html = self._fetch_html()
            if html is None:
                self._source_logger().warning("Skipping parse because HTML could not be fetched")
                try:
                    _maybe_run_async(trace.error(event_id, error="no content"))
                except Exception:
                    pass
                return None

            soup = self._soup_from_html(html)
            articles, used_fallback = self._find_articles(soup)
            if used_fallback and articles:
                self._record_fallback(primary=str(self.selectors.item_selector), fallback="article", matches=len(articles))
                try:
                    _maybe_run_async(trace.start(type=EventType.HTML, name=f"{self.source_name} structure_fallback", input_payload={"primary": str(self.selectors.item_selector), "fallback": "article", "matches": len(articles)}))
                except Exception:
                    pass

            items: list[Item] = []
            self._inc_metric("parse_runs")
            for article in articles:
                extracted: dict[str, Any] = {}
                extracted["external_id"] = self._extract_external_id(article)
                extracted["title"] = self._extract_text(article, self.selectors.title_selector)
                extracted["link"] = self._extract_link(article, self.selectors.link_selector)
                extracted["description"] = self._extract_text(article, self.selectors.description_selector)
                extracted["price"] = self._extract_price(article, self.selectors.price_selector)
                extracted["published_date"] = self._extract_date(article, self.selectors.published_selector)
                extracted["location"] = self._extract_location(article, self.selectors.location_selector)
                extracted["image"] = self._extract_image(article, self.selectors.image_selector)
                extracted["author"] = self._extract_text(article, self.selectors.author_selector)
                extracted["category"] = self._extract_text(article, self.selectors.category_selector)

                # ensure title presence as a minimum
                if not extracted["title"]:
                    continue

                try:
                    item = self.build_item(article, extracted)
                    if item is not None:
                        items.append(item)
                except Exception as exc:
                    self._source_logger().warning("Error building item", error=str(exc))

                if len(items) >= limit:
                    break

            self._inc_metric("items_extracted", len(items))
            self._source_logger().info(
                "Source parsed successfully",
                parsed_entries=len(items),
                metrics=self.get_metrics(),
            )
            try:
                _maybe_run_async(trace.success(event_id, output_payload={"parsed_entries": len(items)}))
            except Exception:
                pass
            return items
        except Exception as exc:
            self._source_logger().error("Error parsing HTML source", error=str(exc))
            try:
                _maybe_run_async(trace.error(event_id, error=str(exc)))
            except Exception:
                pass
            return None

    def build_item(self, article: Tag, extracted: dict) -> Item:  # pragma: no cover - must be implemented by subclass
        raise NotImplementedError()
