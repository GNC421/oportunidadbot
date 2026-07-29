from __future__ import annotations

from types import SimpleNamespace

from app.services import stripe_service as stripe_service_module
from app.subscriptions.entities import Plan


class _FakeStripe:
    def __init__(self) -> None:
        self.last_checkout_kwargs = None
        self.last_portal_kwargs = None
        self.checkout = SimpleNamespace(Session=SimpleNamespace(create=self._create_checkout))
        self.billing_portal = SimpleNamespace(Session=SimpleNamespace(create=self._create_portal))
        self.Customer = SimpleNamespace(retrieve=self._retrieve_customer)
        self.Subscription = SimpleNamespace(retrieve=self._retrieve_subscription)
        self.Webhook = SimpleNamespace(construct_event=self._construct_event)

    def _create_checkout(self, **kwargs):
        self.last_checkout_kwargs = kwargs
        return SimpleNamespace(id="cs_test_123", url="https://checkout.stripe.com/session/cs_test_123")

    def _create_portal(self, **kwargs):
        self.last_portal_kwargs = kwargs
        return SimpleNamespace(id="bps_test_123", url="https://billing.stripe.com/session/bps_test_123")

    @staticmethod
    def _retrieve_customer(customer_id: str):
        return {"id": customer_id, "object": "customer"}

    @staticmethod
    def _retrieve_subscription(subscription_id: str):
        return {
            "id": subscription_id,
            "status": "active",
            "customer": "cus_123",
            "current_period_end": 1785456000,
            "cancel_at_period_end": False,
            "items": {
                "data": [{"price": {"id": "price_prof"}}],
            },
        }

    @staticmethod
    def _construct_event(payload: bytes, sig_header: str, secret: str):
        assert payload
        assert sig_header == "sig_test"
        assert secret == "whsec_test"
        return {
            "id": "evt_test",
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "metadata": {"user_id": "101", "plan": "starter"},
                    "customer": "cus_123",
                    "subscription": "sub_123",
                }
            },
        }


def _build_service(monkeypatch) -> tuple[stripe_service_module.StripeService, _FakeStripe]:
    fake = _FakeStripe()

    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_SECRET_KEY", "sk_test", raising=False)
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_WEBHOOK_SECRET", "whsec_test", raising=False)
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_CHECKOUT_SUCCESS_URL", "https://app.local/success", raising=False)
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_CHECKOUT_CANCEL_URL", "https://app.local/cancel", raising=False)
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_PORTAL_RETURN_URL", "https://app.local/account", raising=False)
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_STARTER_PRICE_ID", "price_starter", raising=False)
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_PROFESSIONAL_PRICE_ID", "price_prof", raising=False)
    monkeypatch.setattr(stripe_service_module.settings, "STRIPE_ENTERPRISE_PRICE_ID", "price_ent", raising=False)

    return stripe_service_module.StripeService(stripe_client=fake), fake


def test_create_checkout_session_uses_price_from_settings(monkeypatch):
    service, fake = _build_service(monkeypatch)

    result = service.create_checkout_session(user_id=101, plan=Plan.PROFESSIONAL)

    assert result.id == "cs_test_123"
    assert fake.last_checkout_kwargs["line_items"][0]["price"] == "price_prof"
    assert fake.last_checkout_kwargs["metadata"]["user_id"] == "101"
    assert fake.last_checkout_kwargs["metadata"]["plan"] == "professional"


def test_create_customer_portal_session(monkeypatch):
    service, fake = _build_service(monkeypatch)

    result = service.create_customer_portal_session(customer_id="cus_123")

    assert result.id == "bps_test_123"
    assert fake.last_portal_kwargs["customer"] == "cus_123"
    assert fake.last_portal_kwargs["return_url"] == "https://app.local/account"


def test_construct_webhook_event(monkeypatch):
    service, _ = _build_service(monkeypatch)

    event = service.construct_webhook_event(payload=b"{}", signature="sig_test")

    assert event["id"] == "evt_test"
    assert event["type"] == "checkout.session.completed"


def test_process_webhook_checkout_completed_updates_subscription(monkeypatch):
    service, _ = _build_service(monkeypatch)

    calls = []
    monkeypatch.setattr(stripe_service_module.database, "register_stripe_webhook_event", lambda *_a, **_k: True)
    monkeypatch.setattr(stripe_service_module.database, "mark_stripe_webhook_event_status", lambda *args, **kwargs: calls.append((args, kwargs)) or True)
    monkeypatch.setattr(stripe_service_module.database, "get_user_by_stripe_customer_id", lambda _cid: {"id": 101})
    monkeypatch.setattr(
        stripe_service_module.database,
        "update_user_subscription",
        lambda **kwargs: calls.append(("update", kwargs)) or True,
    )

    event = {
        "id": "evt_checkout",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "metadata": {"user_id": "101", "plan": "starter"},
                "customer": "cus_123",
                "subscription": "sub_123",
            }
        },
    }

    ok = service.process_webhook_event(event)

    assert ok is True
    update_call = next(item for item in calls if item[0] == "update")
    assert update_call[1]["user_id"] == 101
    assert update_call[1]["plan"] == "professional"
    assert update_call[1]["stripe_customer_id"] == "cus_123"


def test_process_webhook_duplicate_event_is_idempotent(monkeypatch):
    service, _ = _build_service(monkeypatch)

    monkeypatch.setattr(stripe_service_module.database, "register_stripe_webhook_event", lambda *_a, **_k: False)

    ok = service.process_webhook_event({"id": "evt_dup", "type": "checkout.session.completed", "data": {"object": {}}})
    assert ok is True


def test_process_invoice_payment_failed_updates_status(monkeypatch):
    service, _ = _build_service(monkeypatch)

    updated = []
    monkeypatch.setattr(stripe_service_module.database, "register_stripe_webhook_event", lambda *_a, **_k: True)
    monkeypatch.setattr(stripe_service_module.database, "mark_stripe_webhook_event_status", lambda *_a, **_k: True)
    monkeypatch.setattr(stripe_service_module.database, "get_user_by_stripe_customer_id", lambda _cid: {"id": 101})
    monkeypatch.setattr(stripe_service_module.database, "update_user_subscription", lambda **kwargs: updated.append(kwargs) or True)
    monkeypatch.setattr(
        service,
        "get_subscription",
        lambda _sid: {
            "id": "sub_123",
            "status": "past_due",
            "customer": "cus_123",
            "current_period_end": 1785456000,
            "cancel_at_period_end": False,
            "items": {"data": [{"price": {"id": "price_prof"}}]},
        },
    )

    event = {
        "id": "evt_invoice_failed",
        "type": "invoice.payment_failed",
        "data": {"object": {"customer": "cus_123", "subscription": "sub_123"}},
    }

    ok = service.process_webhook_event(event)

    assert ok is True
    assert updated
    assert updated[0]["subscription_status"] == "past_due"
