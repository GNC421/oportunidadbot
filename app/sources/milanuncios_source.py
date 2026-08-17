from __future__ import annotations

from typing import Optional
import re
import unicodedata
from urllib.parse import urljoin, urlparse
import json

from bs4 import BeautifulSoup, Tag

from .base import BaseSource
from .item import Item


class MilanunciosSource(BaseSource):
    """Fuente HTML para listados de milanuncios.com."""

    def _fetch_html(self) -> Optional[str]:
        return self._request_text(self.url)

    def _normalize_for_match(self, s: str) -> str:
        s = s or ""
        s = unicodedata.normalize("NFKD", s)
        s = "".join(ch for ch in s if not unicodedata.combining(ch))
        s = s.lower().strip()
        s = re.sub(r"[^a-z0-9]+", " ", s)
        s = re.sub(r"\s+", " ", s)
        return s

    def _slugify(self, text: str) -> str:
        if not text:
            return ""
        text = unicodedata.normalize("NFKD", text)
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        text = text.lower()
        text = re.sub(r"[^a-z0-9]+", "-", text)
        text = re.sub(r"-+", "-", text).strip("-")
        return text

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
        # try several common attributes used to store the id
        external_id = str(
            article.get("data-id")
            or article.get("data-adid")
            or article.get("data-item-id")
            or article.get("item_id")
            or ""
        ).strip()
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

        # final attempt: if a products map was attached to the article (via attribute), use it
        products_map = getattr(article, "_milan_products_map", None)
        if not external_id and products_map and title:
            key = self._normalize_for_match(title)
            found = products_map.get(key)
            if found:
                external_id = found

        # use class helper

        # Build a stable link using external_id + slug when href is missing or doesn't contain id
        constructed_link = ""
        try:
            if external_id and title:
                title_slug = self._slugify(title)
                if url:
                    # if the extracted url already contains the id, keep it
                    if re.search(rf"[-/]({re.escape(external_id)})((?:\.htm|\.html)?)$", url):
                        constructed_link = url
                    else:
                        # derive parent path from the href and append new slug-id
                        parsed_href = urlparse(url)
                        parent = "/".join(parsed_href.path.split("/")[:-1])
                        if not parent.startswith("/"):
                            parent = "/" + parent
                        new_path = f"{parent}/{title_slug}-{external_id}.htm"
                        base = f"{parsed_href.scheme or urlparse(self.url).scheme}://{parsed_href.netloc or urlparse(self.url).netloc}"
                        constructed_link = urljoin(base, new_path)
                else:
                    # fallback: use domain from feed url and generate simple path
                    base = f"{urlparse(self.url).scheme}://{urlparse(self.url).netloc}"
                    constructed_link = urljoin(base, f"/{title_slug}-{external_id}.htm")
        except Exception:
            constructed_link = url or ""

        if constructed_link:
            url = constructed_link

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
        products_map = self._extract_products_map(html)
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
            # attach products map to the article node for title-based id matching
            try:
                setattr(article, "_milan_products_map", products_map)
            except Exception:
                pass
            parsed = self._parse_article(article)
            if parsed is not None:
                items.append(parsed)
            if len(items) >= limit:
                break

        self._inc_metric("items_extracted", len(items))

        return items

    def _extract_products_map(self, html: str) -> dict:
        """Extrae la lista de products desde trackingData en el HTML y devuelve
        un mapa {normalized_title: id} para emparejar con anuncios.
        """
        if not html:
            return {}

        try:
            # buscar el array "products": [ ... ] dentro del HTML/JS
            m = re.search(r'"products"\s*:\s*(\[\s*[\s\S]*?\])', html)
            products = None
            if m:
                products = json.loads(m.group(1))
            else:
                # intentar encontrar window.trackingData = {...}
                m2 = re.search(r'trackingData\s*=\s*(\{[\s\S]*?\})', html)
                if m2:
                    try:
                        obj = json.loads(m2.group(1))
                        products = obj.get("products") or []
                    except Exception:
                        products = None

            # Si no hay products, intentar extraer window.__INITIAL_PROPS__ JSON.parse("..."), que contiene ad lists
            if products is None:
                m3 = re.search(r'window\.__INITIAL_PROPS__\s*=\s*JSON\.parse\((?P<q>["\'])(?P<data>[\s\S]*?)(?P=q)\)', html)
                if m3:
                    raw = m3.group('data')
                    try:
                        # unescape the JSON string inside JSON.parse('...')
                        decoded = bytes(raw, "utf-8").decode("unicode_escape")
                        obj = json.loads(decoded)
                        # drill into known structure: adListPagination -> adList -> ads
                        ads = None
                        if isinstance(obj, dict):
                            ap = obj.get("adListPagination") or {}
                            if isinstance(ap, dict):
                                adlist = ap.get("adList") or {}
                                if isinstance(adlist, dict):
                                    ads = adlist.get("ads")
                        # fallback: try top-level 'ads'
                        if not ads:
                            ads = obj.get("ads")
                        if ads:
                            products = []
                            for a in ads:
                                # map fields to a common shape
                                products.append({
                                    "id": a.get("id") or a.get("itemId") or a.get("item_id") or a.get("id"),
                                    "title": a.get("title") or a.get("seoTitle") or a.get("name") or "",
                                })
                    except Exception:
                        products = None

            # reuse class normalizer

            mapping: dict[str, str] = {}
            if not products:
                return {}

            for prod in products:
                try:
                    pid = str(prod.get("id") or prod.get("item_id") or prod.get("itemId") or "").strip()
                    title = prod.get("title") or prod.get("name") or prod.get("titleRaw") or ""
                    norm = self._normalize_for_match(title)
                    if pid and norm:
                        mapping[norm] = pid
                except Exception:
                    continue
            return mapping
        except Exception:
            return {}

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
