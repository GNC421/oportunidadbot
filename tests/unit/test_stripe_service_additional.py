from __future__ import annotations

import pytest
from types import SimpleNamespace

from app.services import stripe_service as stripe_service_module
from app.subscriptions.entities import Plan, SubscriptionStatus


class _MinimalFakeStripe:
    def __init__(self) -> None:
        self.checkout = SimpleNamespace(Session=SimpleNamespace(create=lambda **k: SimpleNamespace(id="cs", url="u")))
        self.billing_portal = SimpleNamespace(Session=SimpleNamespace(create=lambda **k: SimpleNamespace(id="bps", url="u")))
        self.Webhook = SimpleNamespace(construct_event=lambda payload, sig_header, secret: {"id": "evt", "type": "checkout.session.completed", "data": {"object": {}}})


def _build_service(monkeypatch) -> stripe_service_module.StripeService:
    # ensure required settings
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_SECRET_KEY", "sk_test", raising=False)
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_WEBHOOK_SECRET", "whsec_test", raising=False)
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_CHECKOUT_SUCCESS_URL", "https://app.local/success", raising=False)
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_CHECKOUT_CANCEL_URL", "https://app.local/cancel", raising=False)
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_PORTAL_RETURN_URL", "https://app.local/account", raising=False)
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_STARTER_PRICE_ID", "price_starter", raising=False)
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_PROFESSIONAL_PRICE_ID", "price_prof", raising=False)
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_ENTERPRISE_PRICE_ID", "price_ent", raising=False)

    return stripe_service_module.StripeService(stripe_client=_MinimalFakeStripe())


def test_resolve_price_id_missing_raises(monkeypatch):
    # configure settings leaving PROFESSIONAL price empty, then construct service directly
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_SECRET_KEY", "sk_test", raising=False)
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_CHECKOUT_SUCCESS_URL", "https://app.local/success", raising=False)
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_CHECKOUT_CANCEL_URL", "https://app.local/cancel", raising=False)
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_PORTAL_RETURN_URL", "https://app.local/account", raising=False)
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_STARTER_PRICE_ID", "price_starter", raising=False)
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_PROFESSIONAL_PRICE_ID", "", raising=False)
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_ENTERPRISE_PRICE_ID", "price_ent", raising=False)

    service = stripe_service_module.StripeService(stripe_client=_MinimalFakeStripe())
    with pytest.raises(stripe_service_module.StripeIntegrationError):
        service._resolve_price_id(Plan.PROFESSIONAL)


def test_construct_webhook_event_missing_webhook_secret_raises(monkeypatch):
    # unset webhook secret and construct service directly
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_SECRET_KEY", "sk_test", raising=False)
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_CHECKOUT_SUCCESS_URL", "https://app.local/success", raising=False)
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_CHECKOUT_CANCEL_URL", "https://app.local/cancel", raising=False)
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_PORTAL_RETURN_URL", "https://app.local/account", raising=False)
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_STARTER_PRICE_ID", "price_starter", raising=False)
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_PROFESSIONAL_PRICE_ID", "price_prof", raising=False)
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_ENTERPRISE_PRICE_ID", "price_ent", raising=False)
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_WEBHOOK_SECRET", "", raising=False)

    service = stripe_service_module.StripeService(stripe_client=_MinimalFakeStripe())
    with pytest.raises(stripe_service_module.StripeIntegrationError):
        service.construct_webhook_event(payload=b"{}", signature="sig")


def test_handle_checkout_completed_without_user_id_does_nothing(monkeypatch):
    service = _build_service(monkeypatch)

    called = {"update": False}
    monkeypatch.setattr(stripe_service_module.database, "update_user_subscription", lambda **k: called.update({"update": True}) or True)

    event = {"id": "e1", "type": "checkout.session.completed", "data": {"object": {"metadata": {}}}}
    # process_webhook_event will call register then dispatch; ensure register returns True
    monkeypatch.setattr(stripe_service_module.database, "register_stripe_webhook_event", lambda *_a, **_k: True)
    monkeypatch.setattr(stripe_service_module.database, "mark_stripe_webhook_event_status", lambda *a, **k: True)

    ok = service.process_webhook_event(event)
    assert ok is True
    assert called["update"] is False


def test_invoice_payment_failed_without_customer_or_subscription_does_nothing(monkeypatch):
    service = _build_service(monkeypatch)

    monkeypatch.setattr(stripe_service_module.database, "register_stripe_webhook_event", lambda *_a, **_k: True)
    monkeypatch.setattr(stripe_service_module.database, "mark_stripe_webhook_event_status", lambda *a, **k: True)
    # ensure get_user_by_stripe_customer_id not called (we'll make it raise if called)
    monkeypatch.setattr(stripe_service_module.database, "get_user_by_stripe_customer_id", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("should not be called")))

    event = {"id": "e2", "type": "invoice.payment_failed", "data": {"object": {}}}
    ok = service.process_webhook_event(event)
    assert ok is True


def test_sync_from_subscription_payload_no_customer_logs_and_ignores(monkeypatch):
    service = _build_service(monkeypatch)

    # simulate subscription object without customer
    subscription_obj = {"id": "sub_x", "status": "active", "items": {"data": []}}

    # patch database.update_user_subscription to detect calls
    called = {"update": False}
    monkeypatch.setattr(stripe_service_module.database, "update_user_subscription", lambda **k: called.update({"update": True}) or True)
    monkeypatch.setattr(stripe_service_module.database, "get_user_by_stripe_customer_id", lambda *_a, **_k: None)

    # call private method directly
    service._sync_from_subscription_payload(subscription_obj=subscription_obj)
    assert called["update"] is False


def test_process_webhook_exception_marks_failed(monkeypatch):
    service = _build_service(monkeypatch)

    captured = {}
    monkeypatch.setattr(stripe_service_module.database, "register_stripe_webhook_event", lambda *_a, **_k: True)

    def fake_mark(event_id, status=None, error_message=None):
        captured["status"] = status
        captured["error_message"] = error_message
        return True

    monkeypatch.setattr(stripe_service_module.database, "mark_stripe_webhook_event_status", fake_mark)

    def raise_dispatch(_etype, _event):
        raise RuntimeError("boom")

    monkeypatch.setattr(service, "_dispatch_webhook_event", raise_dispatch)

    ok = service.process_webhook_event({"id": "e3", "type": "checkout.session.completed", "data": {}})
    assert ok is False
    assert captured.get("status") == "failed"
    assert "boom" in (captured.get("error_message") or "")


def test_resolve_subscription_status_and_plan_fallback(monkeypatch):
    service = _build_service(monkeypatch)

    # unknown status falls back to active
    st = service._resolve_subscription_status("UNKNOWN")
    assert st == SubscriptionStatus.ACTIVE

    # no items -> fallback to starter
    plan = service._resolve_plan_from_subscription({"items": {"data": []}})
    assert plan == Plan.STARTER

    # epoch to iso invalid
    assert service._epoch_to_iso("bad") is None
    assert service._epoch_to_iso(None) is None

    # as_optional_string
    assert service._as_optional_string(None) is None
    assert service._as_optional_string("") is None
    assert service._as_optional_string("  x ") == "x"


def test_dispatch_ignored_marks_ignored(monkeypatch):
    service = _build_service(monkeypatch)

    captured = {}
    monkeypatch.setattr(stripe_service_module.database, "register_stripe_webhook_event", lambda *_a, **_k: True)

    def fake_mark(event_id, status=None, error_message=None):
        captured["status"] = status
        return True

    monkeypatch.setattr(stripe_service_module.database, "mark_stripe_webhook_event_status", fake_mark)

    ok = service.process_webhook_event({"id": "e4", "type": "unknown.event", "data": {}})
    assert ok is True
    assert captured.get("status") == "ignored"


def test_handle_checkout_completed_without_subscription_updates(monkeypatch):
    # event with metadata plan and no subscription id should update user
    service = _build_service(monkeypatch)

    calls = []
    monkeypatch.setattr(stripe_service_module.database, "register_stripe_webhook_event", lambda *_a, **_k: True)
    monkeypatch.setattr(stripe_service_module.database, "mark_stripe_webhook_event_status", lambda *a, **k: True)
    monkeypatch.setattr(stripe_service_module.database, "update_user_subscription", lambda **kwargs: calls.append(kwargs) or True)

    event = {"id": "evt_checkout_no_sub", "type": "checkout.session.completed", "data": {"object": {"metadata": {"user_id": "101", "plan": "starter"}, "customer": "cus_123"}}}

    ok = service.process_webhook_event(event)
    assert ok is True
    assert calls
    assert calls[0]["user_id"] == 101
    assert calls[0]["plan"] == "starter"


def test_handle_subscription_event_updates_user_by_customer(monkeypatch):
    service = _build_service(monkeypatch)

    updated = []
    monkeypatch.setattr(stripe_service_module.database, "register_stripe_webhook_event", lambda *_a, **_k: True)
    monkeypatch.setattr(stripe_service_module.database, "mark_stripe_webhook_event_status", lambda *a, **k: True)
    monkeypatch.setattr(stripe_service_module.database, "get_user_by_stripe_customer_id", lambda _cid: {"id": 200})
    monkeypatch.setattr(stripe_service_module.database, "update_user_subscription", lambda **kwargs: updated.append(kwargs) or True)

    event = {
        "id": "evt_sub_upd",
        "type": "customer.subscription.updated",
        "data": {"object": {"id": "sub_x", "customer": "cus_100", "status": "active", "current_period_end": 1785456000, "items": {"data": [{"price": {"id": "price_prof"}}]} }},
    }

    ok = service.process_webhook_event(event)
    assert ok is True
    assert updated
    assert updated[0]["user_id"] == 200
    assert updated[0]["plan"] == "professional"


def test_sync_from_subscription_with_preferred_user_id_uses_it(monkeypatch):
    service = _build_service(monkeypatch)

    captured = []
    monkeypatch.setattr(stripe_service_module.database, "update_user_subscription", lambda **kwargs: captured.append(kwargs) or True)

    subscription_obj = {"id": "sub_y", "customer": "cus_abc", "status": "active", "current_period_end": 1785456000, "items": {"data": [{"price": {"id": "price_prof"}}]}, "cancel_at_period_end": False}

    service._sync_from_subscription_payload(subscription_obj=subscription_obj, preferred_user_id=500)
    assert captured
    assert captured[0]["user_id"] == 500
    assert captured[0]["plan"] == "professional"


def test_resolve_plan_from_subscription_mapping(monkeypatch):
    service = _build_service(monkeypatch)
    plan = service._resolve_plan_from_subscription({"items": {"data": [{"price": {"id": "price_prof"}}]}})
    assert plan == Plan.PROFESSIONAL
