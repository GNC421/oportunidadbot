from __future__ import annotations

import importlib

from app import database


def test_database_module_reload_for_import_coverage():
    reloaded = importlib.reload(database)
    assert hasattr(reloaded, "add_user")


def test_database_save_and_get_feed(monkeypatch, fake_supabase):
    monkeypatch.setattr(database, "supabase", fake_supabase)

    feed_id = database.add_feed(101, "https://rss.local/feed")
    feeds = database.get_user_feeds(101)

    assert feed_id is not None
    assert len(feeds) == 1
    assert feeds[0]["url"] == "https://rss.local/feed"


def test_database_save_alert_and_get_duplicate(monkeypatch, fake_supabase):
    monkeypatch.setattr(database, "supabase", fake_supabase)

    payload = {"title": "A", "summary": "B", "link": "https://p/1", "author": "x"}
    alert_id = database.save_alert(101, 1, payload)
    duplicate = database.get_alert_by_url("https://p/1")

    assert alert_id is not None
    assert duplicate is not None
    assert duplicate["post_title"] == "A"


def test_database_mark_alert_sent(monkeypatch, fake_supabase):
    monkeypatch.setattr(database, "supabase", fake_supabase)
    payload = {"title": "A", "summary": "B", "link": "https://p/2", "author": "x"}
    alert_id = database.save_alert(101, 1, payload)

    database.mark_alert_sent(alert_id)

    row = database.get_alert_by_url("https://p/2")
    assert row["sent_at"]


def test_database_add_or_update_user(monkeypatch, fake_supabase):
    monkeypatch.setattr(database, "supabase", fake_supabase)

    assert database.add_user(101, "first") is True
    assert database.add_user(101, "updated") is True
    user = database.get_user(101)

    assert user is not None
    assert user["username"] == "updated"


def test_database_feed_status_and_exists(monkeypatch, fake_supabase):
    monkeypatch.setattr(database, "supabase", fake_supabase)
    feed_id = database.add_feed(101, "https://rss.local/feed")

    assert database.feed_exists(101, "https://rss.local/feed") is True
    assert database.user_feed_count(101) == 1
    assert database.disable_feed(101, feed_id) is True
    assert database.enable_feed(101, feed_id) is True


def test_database_get_active_feeds_and_delete(monkeypatch, fake_supabase):
    monkeypatch.setattr(database, "supabase", fake_supabase)
    feed_a = database.add_feed(101, "https://rss.local/a")
    feed_b = database.add_feed(101, "https://rss.local/b")
    database.disable_feed(101, feed_b)

    active = database.get_active_feeds()
    assert len(active) == 1
    assert active[0]["id"] == feed_a

    assert database.delete_feed(101, feed_a) is True


def test_database_update_feed_last_check(monkeypatch, fake_supabase):
    monkeypatch.setattr(database, "supabase", fake_supabase)
    feed_id = database.add_feed(101, "https://rss.local/check")

    database.update_feed_last_check(feed_id)

    saved = fake_supabase.table("feeds").select("*").eq("id", feed_id).execute().data[0]
    assert saved.get("last_check")


def test_database_init_db_ok(monkeypatch, fake_supabase):
    monkeypatch.setattr(database, "supabase", fake_supabase)

    assert database.init_db() is True


def test_database_init_db_error(monkeypatch):
    class BrokenQuery:
        def select(self, *_a, **_k):
            return self

        def limit(self, *_a, **_k):
            return self

        def execute(self):
            raise RuntimeError("db error")

    class BrokenSupabase:
        def table(self, *_a, **_k):
            return BrokenQuery()

    monkeypatch.setattr(database, "supabase", BrokenSupabase())

    assert database.init_db() is False


def test_database_error_paths_return_safe_defaults(monkeypatch):
    class BrokenQuery:
        def select(self, *_a, **_k):
            return self

        def insert(self, *_a, **_k):
            return self

        def update(self, *_a, **_k):
            return self

        def delete(self, *_a, **_k):
            return self

        def eq(self, *_a, **_k):
            return self

        def execute(self):
            raise RuntimeError("broken")

    class BrokenSupabase:
        def table(self, *_a, **_k):
            return BrokenQuery()

    monkeypatch.setattr(database, "supabase", BrokenSupabase())

    assert database.add_user(1, "x") is False
    assert database.get_user(1) is None
    assert database.add_feed(1, "u") is None
    assert database.get_user_feeds(1) == []
    assert database.delete_feed(1, 1) is False
    assert database.enable_feed(1, 1) is False
    assert database.disable_feed(1, 1) is False
    assert database.feed_exists(1, "u") is False
    assert database.user_feed_count(1) == 0
    assert database.get_active_feeds() == []
    database.update_feed_last_check(1)
    assert database.save_alert(1, 1, {}) is None
    assert database.get_alert_by_url("x") is None
    database.mark_alert_sent(1)
