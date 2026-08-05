from __future__ import annotations

from typing import Optional
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from .base import BaseSource
from .item import Item


class MilanunciosSource(BaseSource):
    """Fuente HTML para listados de milanuncios.com."""

    def _fetch_html(self) -> Optional[str]:
        return self._request_text(self.url)

    @staticmethod
    def _extract_text(root: Tag, selectors: tuple[str, ...]) -> str:
        for selector in selectors:
            node = root.select_one(selector)
            if node:
                text = node.get_text(" ", strip=True)
                if text:
                    return text
        return ""

    @staticmethod
    def _extract_link(root: Tag, base_url: str) -> str:
        for selector in ("a.ma-AdCardListingV2-TitleLink[href]", "a[href]"):
            node = root.select_one(selector)
            if node and node.get("href"):
                return urljoin(base_url, str(node.get("href")))
        return ""

    @staticmethod
    def _extract_image(root: Tag, base_url: str) -> str:
        node = root.select_one("img")
        if not node:
            return ""
        for attr in ("src", "data-src", "data-original"):
            value = node.get(attr)
            if value:
                return urljoin(base_url, str(value))
        return ""

    def _parse_article(self, article: Tag) -> Optional[Item]:
        # milanuncios articles may not expose an explicit id attribute
        external_id = str(article.get("data-id") or article.get("data-adid") or "").strip()
        title = self._extract_text(article, ("a.ma-AdCardListingV2-TitleLink", "h2", "a[title]", "a"))
        url = self._extract_link(article, self.url)
        description = self._extract_text(article, (".ma-AdCardV2-description", ".ma-AdCardV2-description p", "p"))
        price = self._extract_text(article, (".ma-AdPrice-value", ".ma-AdMultiplePrice-priceBlock", "[class*='price']"))
        published_date = self._extract_text(article, (".ma-AdCardV2-time", "time", ".date"))
        category = self._extract_text(article, (".category", "[class*='categoria']"))
        # location is commonly present in milanuncios listings
        location = self._extract_text(article, (".ma-AdLocation-text", ".ma-AdLocation"))
        if not category:
            category = location
        image = self._extract_image(article, self.url)

        if not title and not url:
            return None

        # if external_id is missing, try to extract numeric id from the URL
        if not external_id and url:
            m = re.search(r"-(\d+)(?:\.htm|\.html)?$", url)
            if not m:
                m = re.search(r"/(\d+)(?:\.htm|\.html)?$", url)
            if m:
                external_id = m.group(1)

        return Item(
            title=title,
            summary=description,
            link=url,
            author="",
            published=published_date,
            external_id=external_id,
            url=url,
            description=description,
            image=image,
            price=price,
            published_date=published_date,
            category=category,
        )

    def _extract_items_from_html(self, html: str, limit: int) -> list[Item]:
        soup = BeautifulSoup(html, "lxml")
        # primary selector used in the provided HTML fragment
        articles = soup.select("article.ma-AdCardV2")
        used_fallback = False
        if not articles:
            used_fallback = True
            # fallback to data-testid or any article
            articles = soup.select("article[data-testid='AD_CARD']") or soup.select("article")

        if used_fallback and articles:
            self._inc_metric("html_structure_fallbacks")
            self._source_logger().warning(
                "Primary selector missing, using fallback selector",
                primary_selector="article.ma-AdCardV2",
                fallback_matches=len(articles),
            )

        items: list[Item] = []
        self._inc_metric("parse_runs")
        for article in articles:
            parsed = self._parse_article(article)
            if parsed is not None:
                items.append(parsed)
            if len(items) >= limit:
                break

        self._inc_metric("items_extracted", len(items))

        return items

    def validate(self) -> dict[str, object]:
        html = self._fetch_html()
        if html is None:
            return {
                "valid": False,
                "error": "No se pudo obtener el contenido de la fuente",
                "title": "",
                "entry_count": 0,
            }

        items = self._extract_items_from_html(html, limit=1)
        if not items:
            return {
                "valid": False,
                "error": "La fuente no contiene anuncios válidos",
                "title": "",
                "entry_count": 0,
            }

        return {
            "valid": True,
            "error": None,
            "title": "Milanuncios",
            "entry_count": len(items),
        }

    def parse_items(self, limit: int = 10) -> Optional[list[Item]]:
        html = self._fetch_html()
        if html is None:
            self._source_logger().warning("Skipping parse because HTML could not be fetched")
            return None

        items = self._extract_items_from_html(html, limit=limit)
        if not items:
            self._source_logger().warning("No items extracted from source")
            return None

        self._source_logger().info(
            "Source parsed successfully",
            parsed_entries=len(items),
            metrics=self.get_metrics(),
        )
        return items
