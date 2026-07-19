from __future__ import annotations

import pytest


class FeedBuilder:
    def __init__(self) -> None:
        self._id = 1
        self._user_id = 101
        self._url = "https://rss.local/feed.xml"
        self._is_active = True

    def with_id(self, feed_id: int) -> "FeedBuilder":
        self._id = feed_id
        return self

    def with_user(self, user_id: int) -> "FeedBuilder":
        self._user_id = user_id
        return self

    def with_url(self, url: str) -> "FeedBuilder":
        self._url = url
        return self

    def active(self, value: bool) -> "FeedBuilder":
        self._is_active = value
        return self

    def build(self) -> dict:
        return {
            "id": self._id,
            "user_id": self._user_id,
            "url": self._url,
            "is_active": self._is_active,
        }


@pytest.fixture
def feed_builder() -> FeedBuilder:
    return FeedBuilder()


@pytest.fixture
def sample_feed(feed_builder: FeedBuilder) -> dict:
    return feed_builder.build()
