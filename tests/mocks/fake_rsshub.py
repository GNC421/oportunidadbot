from __future__ import annotations


class FakeRSSHub:
    def __init__(self) -> None:
        self.mapping: dict[str, str | None] = {}

    def set_mapping(self, source_url: str, rss_url: str | None) -> None:
        self.mapping[source_url] = rss_url

    def resolve(self, url: str) -> str | None:
        return self.mapping.get(url)
