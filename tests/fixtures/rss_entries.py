from __future__ import annotations

import pytest


class RSSEntryBuilder:
    def __init__(self) -> None:
        self._title = "Busco piso en alquiler"
        self._summary = "Zona centro, presupuesto 900 EUR"
        self._link = "https://origin.local/post-1"
        self._author = "Anon"
        self._published = "2026-01-01"

    def with_title(self, title: str) -> "RSSEntryBuilder":
        self._title = title
        return self

    def with_summary(self, summary: str) -> "RSSEntryBuilder":
        self._summary = summary
        return self

    def with_link(self, link: str) -> "RSSEntryBuilder":
        self._link = link
        return self

    def build(self) -> dict:
        return {
            "title": self._title,
            "summary": self._summary,
            "link": self._link,
            "author": self._author,
            "published": self._published,
            "published_parsed": None,
        }


@pytest.fixture
def rss_entry_builder() -> RSSEntryBuilder:
    return RSSEntryBuilder()


@pytest.fixture
def sample_rss_entry(rss_entry_builder: RSSEntryBuilder) -> dict:
    return rss_entry_builder.build()


@pytest.fixture
def sample_rss_feed(sample_rss_entry: dict) -> list[dict]:
    return [sample_rss_entry]
