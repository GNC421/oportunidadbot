from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import database
from app.config import settings
from app.services import stripe_service as stripe_service_module
from app.web.routes import router


def _client(monkeypatch, fake_supabase) -> TestClient:
    monkeypatch.setattr(database, "supabase", fake_supabase)
    monkeypatch.setattr(settings, "WEB_SESSION_SECRET", "test-web-session-secret")
    monkeypatch.setattr(settings, "WEB_SESSION_COOKIE_SECURE", False)
    monkeypatch.setattr(settings, "WEB_APP_ORIGIN", "https://app.example.test")
    monkeypatch.setattr(settings, "PLAN_STARTER_PRICE", "9.90", raising=False)
    monkeypatch.setattr(settings, "PLAN_PROFESSIONAL_PRICE", "24.90", raising=False)
    monkeypatch.setattr(settings, "PLAN_ENTERPRISE_PRICE", "79.00", raising=False)
    monkeypatch.setattr(settings, "PLAN_CURRENCY", "EUR", raising=False)
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def _login(client: TestClient, user_id: int) -> None:
    from app.web.auth import create_session_token
    from app.web.routes import SESSION_COOKIE_NAME

    client.cookies.set(SESSION_COOKIE_NAME, create_session_token(user_id))


def _seed_professional_user(fake_supabase, user_id: int = 101, **extra) -> None:
    user = {"id": user_id, "username": "ana", "is_active": True, "plan": "professional"}
    user.update(extra)
    fake_supabase.seed("users", [user])


def test_get_subscription_requires_authentication(monkeypatch, fake_supabase):
    client = _client(monkeypatch, fake_supabase)

    assert client.get("/api/web/subscription").status_code == 401


def test_get_subscription_returns_plan_and_catalog(monkeypatch, fake_supabase):
    _seed_professional_user(fake_supabase)
    fake_supabase.seed("feeds", [{"id": 1, "user_id": 101, "url": "https://rss.local/feed.xml", "is_active": True}])
    client = _client(monkeypatch, fake_supabase)
    _login(client, 101)

    response = client.get("/api/web/subscription")

    assert response.status_code == 200
    body = response.json()
    assert body["plan"] == "professional"
    assert body["status"] == "active"
    assert body["sources_used"] == 1
    assert body["source_limit"] == 15
    assert body["remaining_sources"] == 14
    assert body["has_stripe_customer"] is False
    assert {plan["identifier"] for plan in body["plans"]} == {"starter", "professional", "enterprise"}


def test_create_checkout_rejects_invalid_plan(monkeypatch, fake_supabase):
    _seed_professional_user(fake_supabase)
    client = _client(monkeypatch, fake_supabase)
    _login(client, 101)

    response = client.post("/api/web/subscription/checkout", json={"plan": "not-a-plan"})

    assert response.status_code == 422


def test_create_checkout_returns_stripe_url(monkeypatch, fake_supabase):
    from app.web import routes

    _seed_professional_user(fake_supabase, stripe_customer_id="cus_123")

    class _FakeStripeService:
        def create_checkout_session(self, **kwargs):
            assert kwargs["customer_id"] == "cus_123"
            assert kwargs["plan"].value == "professional"
            return stripe_service_module.CheckoutSessionResult(id="cs_123", url="https://checkout.stripe.test/cs_123")

    monkeypatch.setattr(routes, "get_stripe_service", lambda: _FakeStripeService())
    client = _client(monkeypatch, fake_supabase)
    _login(client, 101)

    response = client.post("/api/web/subscription/checkout", json={"plan": "professional"})

    assert response.status_code == 200
    assert response.json()["url"] == "https://checkout.stripe.test/cs_123"


def test_create_checkout_surfaces_stripe_integration_error(monkeypatch, fake_supabase):
    from app.web import routes

    _seed_professional_user(fake_supabase)

    class _FakeStripeService:
        def create_checkout_session(self, **kwargs):
            raise stripe_service_module.StripeIntegrationError("STRIPE_SECRET_KEY no configurado")

    monkeypatch.setattr(routes, "get_stripe_service", lambda: _FakeStripeService())
    client = _client(monkeypatch, fake_supabase)
    _login(client, 101)

    response = client.post("/api/web/subscription/checkout", json={"plan": "professional"})

    assert response.status_code == 503


def test_create_checkout_requires_authentication(monkeypatch, fake_supabase):
    client = _client(monkeypatch, fake_supabase)

    assert client.post("/api/web/subscription/checkout", json={"plan": "professional"}).status_code == 401


def test_create_portal_requires_stripe_customer(monkeypatch, fake_supabase):
    _seed_professional_user(fake_supabase)
    client = _client(monkeypatch, fake_supabase)
    _login(client, 101)

    response = client.post("/api/web/subscription/portal")

    assert response.status_code == 409


def test_create_portal_returns_stripe_url(monkeypatch, fake_supabase):
    from app.web import routes

    _seed_professional_user(fake_supabase, stripe_customer_id="cus_123")

    class _FakeStripeService:
        def create_customer_portal_session(self, customer_id):
            assert customer_id == "cus_123"
            return stripe_service_module.PortalSessionResult(id="bps_123", url="https://billing.stripe.test/bps_123")

    monkeypatch.setattr(routes, "get_stripe_service", lambda: _FakeStripeService())
    client = _client(monkeypatch, fake_supabase)
    _login(client, 101)

    response = client.post("/api/web/subscription/portal")

    assert response.status_code == 200
    assert response.json()["url"] == "https://billing.stripe.test/bps_123"


def test_create_portal_requires_authentication(monkeypatch, fake_supabase):
    client = _client(monkeypatch, fake_supabase)

    assert client.post("/api/web/subscription/portal").status_code == 401
