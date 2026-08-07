from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse


class SourceDisplayNameService:
    """Genera nombres legibles para fuentes a partir de su URL, sin peticiones externas."""

    _WORD_ACCENTS = {
        "alava": "Álava",
        "almeria": "Almería",
        "avila": "Ávila",
        "cadiz": "Cádiz",
        "cordoba": "Córdoba",
        "coruna": "Coruña",
        "jaen": "Jaén",
        "leon": "León",
        "malaga": "Málaga",
        "rioja": "Rioja",
    }

    @classmethod
    def from_url(cls, source_url: str) -> str:
        parsed = urlparse((source_url or "").strip())
        netloc = (parsed.netloc or "").lower()

        if cls._is_tablon_host(netloc):
            return cls._build_tablon_name(parsed.path or "", parsed.query or "")

        reddit_name = cls._build_reddit_name(netloc, parsed.path or "")
        if reddit_name:
            return reddit_name

        host = netloc.replace("www.", "")
        if host:
            return host
        return "Fuente RSS"

    @staticmethod
    def _is_tablon_host(netloc: str) -> bool:
        host = netloc.replace("www.", "")
        return host == "tablondeanuncios.com" or host.endswith(".tablondeanuncios.com")

    @staticmethod
    def _build_reddit_name(netloc: str, path: str) -> str | None:
        if "reddit.com" not in netloc:
            return None

        path_parts = [part for part in path.split("/") if part]
        if len(path_parts) >= 2 and path_parts[0] == "r":
            subreddit = path_parts[1].replace("-", " ").replace("_", " ").strip().title()
            if subreddit:
                return f"Reddit {subreddit}"
        return None

    @classmethod
    def _build_tablon_name(cls, path: str, query: str) -> str:
        path_parts = [part for part in path.split("/") if part]
        if not path_parts:
            return "🏠 Tablón de anuncios"

        raw_slug = re.sub(r"\.[a-zA-Z0-9]+$", "", path_parts[0]).strip("-")
        if not raw_slug:
            return "🏠 Tablón de anuncios"

        category_slug, location_slug = cls._split_category_and_location(raw_slug)
        category_title = cls._humanize_title(category_slug)
        location_title = cls._humanize_title(location_slug) if location_slug else ""

        query_params = parse_qs(query, keep_blank_values=True)
        is_demanda = (query_params.get("demanda") or [""])[0] == "1"

        if is_demanda:
            category_lower = category_title[:1].lower() + category_title[1:] if category_title else "búsqueda"
            if location_title:
                return f"🏠 Demanda {category_lower} · {location_title}"
            return f"🏠 Demanda {category_lower} (España)"

        if location_title:
            return f"🏠 {category_title} · {location_title}"
        return f"🏠 {category_title}"

    @staticmethod
    def _split_category_and_location(slug: str) -> tuple[str, str]:
        if "-en-" not in slug:
            return slug, ""

        category_slug, location_slug = slug.rsplit("-en-", 1)
        return category_slug or slug, location_slug

    @staticmethod
    def _humanize_title(slug: str) -> str:
        text = slug.replace("_", "-").replace("-", " ").strip().lower()
        text = " ".join(part for part in text.split(" ") if part)
        if not text:
            return "Búsqueda"

        words = []
        for raw_word in text.split(" "):
            accented = SourceDisplayNameService._WORD_ACCENTS.get(raw_word)
            if accented:
                words.append(accented)
            else:
                words.append(raw_word)

        normalized = " ".join(words)
        return normalized[:1].upper() + normalized[1:]