from __future__ import annotations

import pytest

from tests.mocks.fake_supabase import FakeSupabase


@pytest.fixture
def db_seed() -> dict:
    return {
        "users": [{"id": 101, "username": "seed_user", "is_active": True}],
        "feeds": [{"id": 1, "user_id": 101, "url": "https://rss.local/feed.xml", "is_active": True}],
        "alerts": [],
    }


@pytest.fixture
def seeded_supabase(db_seed: dict) -> FakeSupabase:
    fake = FakeSupabase()
    fake.seed("users", db_seed["users"])
    fake.seed("feeds", db_seed["feeds"])
    fake.seed("alerts", db_seed["alerts"])
    return fake
