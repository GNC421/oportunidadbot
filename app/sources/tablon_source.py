from __future__ import annotations

from typing import Optional
from urllib.parse import urljoin

from bs4 import Tag

from .html_source import HTMLSource, HTMLSelectors
from .item import Item


class TablonSource(HTMLSource):
    """Fuente HTML para listados de tablondeanuncios.com.

    Define únicamente los selectores y el mapeo `build_item`.
    """

    selectors = HTMLSelectors(
        item_selector=("article.result-item", "article[id]"),
        title_selector=("h2 a", "h3 a", ".title a", ".item-title a", "a"),
        description_selector=(".description", ".item-description", "p"),
        price_selector=(".price", ".item-price", "[class*='price']"),
        published_selector=("time", ".date", ".item-date", "[class*='fecha']"),
        category_selector=(".category", ".item-category", "[class*='categoria']"),
        image_selector=("img",),
        link_selector=("h2 a[href]", "h3 a[href]", "a[href]"),
    )

    def _fetch_html(self) -> Optional[str]:
        return self._request_text(self.url)

    def build_item(self, article: Tag, extracted: dict) -> Optional[Item]:
        # normalize link to absolute URL
        url = extracted.get("link") or ""
        if url:
            url = urljoin(self.url, url)

        title = extracted.get("title", "")
        description = extracted.get("description", "")
        price = extracted.get("price", "")
        published_date = extracted.get("published_date", "")
        category = extracted.get("category", "")
        image = extracted.get("image", "")
        external_id = extracted.get("external_id", "")

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
