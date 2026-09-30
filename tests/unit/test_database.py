from __future__ import annotations

import importlib

from app import database


def _seed_subscribed_user(fake_supabase, user_id: int = 101) -> None:
    fake_supabase.seed(
        "users",
        [
            {
                "id": user_id,
                "plan": "starter",
                "subscription_status": "active",
                "stripe_subscription_id": f"sub_{user_id}",
            }
        ],
    )


def test_database_module_reload_for_import_coverage():
    reloaded = importlib.reload(database)
    assert hasattr(reloaded, "add_user")


def test_database_save_and_get_feed(monkeypatch, fake_supabase):
    monkeypatch.setattr(database, "supabase", fake_supabase)
    _seed_subscribed_user(fake_supabase)

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
    assert user["plan"] == "starter"
    assert user["subscription_status"] == "inactive"
    assert user["cancel_at_period_end"] is False


def test_database_update_user_subscription(monkeypatch, fake_supabase):
    monkeypatch.setattr(database, "supabase", fake_supabase)
    database.add_user(101, "tester")

    ok = database.update_user_subscription(
        user_id=101,
        plan="professional",
        subscription_status="active",
        stripe_customer_id="cus_1",
        stripe_subscription_id="sub_1",
        current_period_end="2026-07-31T00:00:00+00:00",
        cancel_at_period_end=True,
    )

    user = database.get_user(101)
    assert ok is True
    assert user is not None
    assert user["plan"] == "professional"
    assert user["subscription_status"] == "active"
    assert user["stripe_customer_id"] == "cus_1"
    assert user["stripe_subscription_id"] == "sub_1"
    assert user["current_period_end"] == "2026-07-31T00:00:00+00:00"
    assert user["cancel_at_period_end"] is True


def test_database_get_user_by_stripe_customer_id(monkeypatch, fake_supabase):
    monkeypatch.setattr(database, "supabase", fake_supabase)
    database.add_user(101, "tester")
    database.update_user_subscription(
        user_id=101,
        plan="starter",
        subscription_status="active",
        stripe_customer_id="cus_123",
        stripe_subscription_id="sub_123",
    )

    user = database.get_user_by_stripe_customer_id("cus_123")
    assert user is not None
    assert user["id"] == 101


def test_database_reserves_starter_trial_via_atomic_rpc(monkeypatch):
    class _RpcCall:
        data = [{"status": "pending", "idempotency_key": "starter-trial:101"}]

        def execute(self):
            return self

    class _RpcSupabase:
        def rpc(self, name, params):
            assert name == "reserve_starter_trial"
            assert params == {"p_user_id": 101}
            return _RpcCall()

    monkeypatch.setattr(database, "supabase", _RpcSupabase())

    reservation = database.reserve_starter_trial(101)

    assert reservation == {"status": "pending", "idempotency_key": "starter-trial:101"}


def test_database_reads_and_syncs_trial_history(monkeypatch, fake_supabase):
    monkeypatch.setattr(database, "supabase", fake_supabase)
    fake_supabase.seed("subscription_trials", [{"user_id": 101, "status": "trial_active"}])
    rpc_calls = []

    class _RpcCall:
        data = []

        def execute(self):
            return self

    def fake_rpc(name, params):
        rpc_calls.append((name, params))
        return _RpcCall()

    fake_supabase.rpc = fake_rpc

    assert database.get_starter_trial(101)["status"] == "trial_active"
    assert database.sync_starter_trial(
        user_id=101,
        status="trial_used",
        checkout_session_id="cs_101",
        subscription_id="sub_101",
        trial_started_at="2026-09-01T00:00:00+00:00",
        trial_ends_at="2026-10-01T00:00:00+00:00",
        event_created_at="2026-09-01T00:00:00+00:00",
    ) is True
    assert rpc_calls[0][0] == "sync_starter_trial"
    assert rpc_calls[0][1]["p_status"] == "trial_used"


def test_database_trial_helpers_fail_closed(monkeypatch):
    monkeypatch.setattr(database, "supabase", object())

    assert database.reserve_starter_trial(101) is None
    assert database.get_starter_trial(101) is None
    assert database.sync_starter_trial(101, "trial_used", None, None, None, None, None) is False


def test_database_register_and_mark_stripe_webhook_event(monkeypatch, fake_supabase):
    monkeypatch.setattr(database, "supabase", fake_supabase)

    first = database.register_stripe_webhook_event(
        event_id="evt_1",
        event_type="checkout.session.completed",
        payload={"id": "evt_1"},
    )
    duplicated = database.register_stripe_webhook_event(
        event_id="evt_1",
        event_type="checkout.session.completed",
        payload={"id": "evt_1"},
    )
    updated = database.mark_stripe_webhook_event_status("evt_1", status="processed")

    assert first is True
    assert duplicated is False
    assert updated is True

    rows = fake_supabase.table("stripe_webhook_events").select("*").eq("event_id", "evt_1").execute().data
    assert len(rows) == 1
    assert rows[0]["status"] == "processed"


def test_database_feed_status_and_exists(monkeypatch, fake_supabase):
    monkeypatch.setattr(database, "supabase", fake_supabase)
    _seed_subscribed_user(fake_supabase)
    feed_id = database.add_feed(101, "https://rss.local/feed")

    assert database.feed_exists(101, "https://rss.local/feed") is True
    assert database.user_feed_count(101) == 1
    assert database.disable_feed(101, feed_id) is True
    assert database.enable_feed(101, feed_id) is True


def test_database_add_feed_respects_subscription_limits(monkeypatch, fake_supabase):
    monkeypatch.setattr(database, "supabase", fake_supabase)

    class _BlockingSubscriptionService:
        def can_add_source(self, _user_id: int) -> bool:
            return False

    monkeypatch.setattr(
        "app.services.subscription_service.get_subscription_service",
        lambda: _BlockingSubscriptionService(),
    )

    feed_id = database.add_feed(101, "https://rss.local/blocked")
    assert feed_id is None
    assert database.get_user_feeds(101) == []


def test_database_get_active_feeds_and_delete(monkeypatch, fake_supabase):
    monkeypatch.setattr(database, "supabase", fake_supabase)
    _seed_subscribed_user(fake_supabase)
    feed_a = database.add_feed(101, "https://rss.local/a")
    feed_b = database.add_feed(101, "https://rss.local/b")
    database.disable_feed(101, feed_b)

    active = database.get_active_feeds()
    assert len(active) == 1
    assert active[0]["id"] == feed_a

    assert database.delete_feed(101, feed_a) is True


def test_database_update_feed_last_check(monkeypatch, fake_supabase):
    monkeypatch.setattr(database, "supabase", fake_supabase)
    _seed_subscribed_user(fake_supabase)
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
