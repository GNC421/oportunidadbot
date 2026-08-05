from __future__ import annotations

from typing import Optional
from urllib.parse import urljoin

from bs4 import Tag

from .html_source import HTMLSource, HTMLSelectors
from .item import Item


class MilanunciosSource(HTMLSource):
    """Scraper para Milanuncios.

    Define selectores y mapea campos a `Item`. Los selectores incluyen
    alternativas para permitir fallbacks en caso de cambios menores en el DOM.
    """

    selectors = HTMLSelectors(
        # Milanuncios estructura es variada; intentamos varios selectores comunes
        item_selector=("li.ad", "li[item]", "article", ".ad-list-item", ".ad"),
        title_selector=("h2 a", "a.ad-title", ".ad-title", "h2"),
        description_selector=(".ad-description", ".description", "p"),
        price_selector=(".ad-price", ".precio", "[class*='price']"),
        location_selector=(".ad-location", ".location", ".place"),
        image_selector=("img", ".ad-image img"),
        link_selector=("a[href]", "h2 a[href]"),
        published_selector=("time[datetime]", ".date"),
        author_selector=(".seller", ".author"),
        category_selector=(".category", ".ad-category"),
    )

    def _fetch_html(self) -> Optional[str]:
        return self._request_text(self.url)

    def build_item(self, article: Tag, extracted: dict) -> Optional[Item]:
        link = extracted.get("link") or ""
        if link:
            link = urljoin(self.url, link)

        title = extracted.get("title", "")
        description = extracted.get("description", "")
        price = extracted.get("price", "")
        published_date = extracted.get("published_date", "")
        location = extracted.get("location", "")
        image = extracted.get("image", "")
        external_id = extracted.get("external_id", "") or str(article.get("data-id") or "").strip()

        if not title:
            return None

        return Item(
            title=title,
            summary=description,
            link=link,
            author=extracted.get("author") or "",
            published=published_date,
            published_parsed=None,
            external_id=external_id,
            url=link,
            description=description,
            image=image,
            price=price,
            published_date=published_date,
            category=extracted.get("category") or "",
        )
