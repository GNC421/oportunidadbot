from __future__ import annotations

from typing import Optional
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, Tag
from loguru import logger

from .base import BaseSource
from .item import Item


class TablonSource(BaseSource):
    """Fuente HTML para listados de tablondeanuncios.com."""

    def _fetch_html(self) -> Optional[str]:
        try:
            response = httpx.get(
                self.url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; OportunidadBot/1.0)"},
                timeout=15.0,
                follow_redirects=True,
            )
            response.raise_for_status()
            return response.text
        except Exception as exc:
            logger.warning(f"No se pudo descargar HTML de Tablon: {self.url} ({exc})")
            return None

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
        for selector in ("h2 a[href]", "h3 a[href]", "a[href]"):
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
        external_id = str(article.get("id") or "").strip()
        title = self._extract_text(article, ("h2 a", "h3 a", ".title a", ".item-title a", "a"))
        url = self._extract_link(article, self.url)
        description = self._extract_text(article, (".description", ".item-description", "p"))
        price = self._extract_text(article, (".price", ".item-price", "[class*='price']"))
        published_date = self._extract_text(article, ("time", ".date", ".item-date", "[class*='fecha']"))
        if not published_date:
            time_node = article.select_one("time[datetime]")
            if time_node:
                published_date = str(time_node.get("datetime") or "").strip()
        category = self._extract_text(article, (".category", ".item-category", "[class*='categoria']"))
        image = self._extract_image(article, self.url)

        if not title and not url:
            return None

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
        articles = soup.select("article.result-item")
        if not articles:
            articles = soup.select("article[id]")

        items: list[Item] = []
        for article in articles:
            parsed = self._parse_article(article)
            if parsed is not None:
                items.append(parsed)
            if len(items) >= limit:
                break

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
            "title": "Tablón de Anuncios",
            "entry_count": len(items),
        }

    def parse_items(self, limit: int = 10) -> Optional[list[Item]]:
        validation = self.validate()
        if not validation.get("valid", False):
            logger.warning(f"No se parseará la fuente inválida {self.url}: {validation.get('error')}")
            return None

        html = self._fetch_html()
        if html is None:
            return None

        items = self._extract_items_from_html(html, limit=limit)
        logger.info("Tablon source parsed successfully", url=self.url, parsed_entries=len(items))
        return items
