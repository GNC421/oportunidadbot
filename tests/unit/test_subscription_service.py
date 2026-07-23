from __future__ import annotations

from datetime import datetime, timezone

from app.services.subscription_service import SubscriptionService
from app.subscriptions.catalog import SubscriptionCatalog
from app.subscriptions.entities import Plan, SubscriptionStatus


def _build_service(user_payload: dict, feed_count: int) -> SubscriptionService:
    catalog = SubscriptionCatalog(
        starter_price="9.90",
        professional_price="24.90",
        enterprise_price="79.00",
        currency="EUR",
    )

    return SubscriptionService(
        catalog=catalog,
        user_reader=lambda _user_id: user_payload,
        feed_count_reader=lambda _user_id: feed_count,
    )


def test_get_current_subscription_uses_user_fields() -> None:
    service = _build_service(
        {
            "plan": "professional",
            "subscription_status": "active",
            "stripe_customer_id": "cus_123",
            "stripe_subscription_id": "sub_123",
            "current_period_end": "2026-07-31T00:00:00Z",
            "cancel_at_period_end": True,
        },
        feed_count=4,
    )

    subscription = service.get_current_subscription(101)

    assert subscription.plan == Plan.PROFESSIONAL
    assert subscription.status == SubscriptionStatus.ACTIVE
    assert subscription.stripe_customer_id == "cus_123"
    assert subscription.stripe_subscription_id == "sub_123"
    assert subscription.current_period_end == datetime(2026, 7, 31, 0, 0, tzinfo=timezone.utc)
    assert subscription.cancel_at_period_end is True


def test_can_add_source_respects_plan_limit() -> None:
    service = _build_service(
        {
            "plan": "starter",
            "subscription_status": "active",
        },
        feed_count=3,
    )

    assert service.can_add_source(101) is False
    assert service.get_remaining_sources(101) == 0


def test_can_add_source_unlimited_plan() -> None:
    service = _build_service(
        {
            "plan": "enterprise",
            "subscription_status": "active",
        },
        feed_count=200,
    )

    assert service.can_add_source(101) is True
    assert service.get_remaining_sources(101) is None


def test_can_add_source_denied_by_status() -> None:
    service = _build_service(
        {
            "plan": "professional",
            "subscription_status": "canceled",
        },
        feed_count=1,
    )

    assert service.can_add_source(101) is False


def test_can_use_feature_checks_catalog_features_case_insensitive() -> None:
    service = _build_service(
        {
            "plan": "starter",
            "subscription_status": "active",
        },
        feed_count=0,
    )

    assert service.can_use_feature(101, "Alertas por Telegram") is True
    assert service.can_use_feature(101, "alertas por telegram") is True
    assert service.can_use_feature(101, "Dashboards avanzados (proximamente)") is False


def test_invalid_plan_and_status_fallback_to_defaults() -> None:
    service = _build_service(
        {
            "plan": "unknown",
            "subscription_status": "not-valid",
        },
        feed_count=0,
    )

    subscription = service.get_current_subscription(101)

    assert subscription.plan == Plan.STARTER
    assert subscription.status == SubscriptionStatus.ACTIVE
