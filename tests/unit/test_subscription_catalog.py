from __future__ import annotations

from decimal import Decimal

import pytest

from app.subscriptions.catalog import SubscriptionCatalog


def test_subscription_catalog_lists_all_plans_in_order() -> None:
    catalog = SubscriptionCatalog(
        starter_price="9.90",
        professional_price="24.90",
        enterprise_price="79.00",
        currency="eur",
    )

    plans = catalog.list_plans()

    assert [plan.identifier for plan in plans] == ["starter", "professional", "enterprise"]
    assert [plan.price for plan in plans] == [Decimal("9.90"), Decimal("24.90"), Decimal("79.00")]
    assert all(plan.currency == "EUR" for plan in plans)


def test_subscription_catalog_contains_limits_and_features() -> None:
    catalog = SubscriptionCatalog(
        starter_price="9.90",
        professional_price="24.90",
        enterprise_price="79.00",
        currency="EUR",
    )

    starter = catalog.get_plan("starter")
    professional = catalog.get_plan("professional")
    enterprise = catalog.get_plan("enterprise")

    assert starter.source_limit == 3
    assert "Alertas por Telegram" in starter.features

    assert professional.source_limit == 15
    assert "Prioridad de procesamiento" in professional.features

    assert enterprise.source_limit is None
    assert "Soporte prioritario" in enterprise.features


def test_subscription_catalog_rejects_invalid_price() -> None:
    with pytest.raises(ValueError, match="PLAN_STARTER_PRICE"):
        SubscriptionCatalog(
            starter_price="abc",
            professional_price="24.90",
            enterprise_price="79.00",
            currency="EUR",
        )


def test_subscription_catalog_rejects_unknown_plan() -> None:
    catalog = SubscriptionCatalog(
        starter_price="9.90",
        professional_price="24.90",
        enterprise_price="79.00",
        currency="EUR",
    )

    with pytest.raises(KeyError):
        catalog.get_plan("premium")
