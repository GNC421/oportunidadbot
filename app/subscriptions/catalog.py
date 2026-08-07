from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional

from app.config import settings


@dataclass(frozen=True)
class SubscriptionPlan:
    """Immutable subscription plan definition consumed by the bot."""

    identifier: str
    name: str
    price: Decimal
    currency: str
    source_limit: Optional[int]
    features: tuple[str, ...]


class SubscriptionCatalog:
    """Centralized source of truth for subscription plan metadata."""

    def __init__(self, starter_price: str, professional_price: str, enterprise_price: str, currency: str) -> None:
        normalized_currency = (currency or "EUR").strip().upper()
        self._plans = {
            "starter": SubscriptionPlan(
                identifier="starter",
                name="Starter",
                price=self._parse_price(starter_price, "PLAN_STARTER_PRICE"),
                currency=normalized_currency,
                source_limit=3,
                features=(
                    "Hasta 3 fuentes",
                    "Alertas por Telegram",
                    "IA especializada en inmobiliaria",
                ),
            ),
            "professional": SubscriptionPlan(
                identifier="professional",
                name="Professional",
                price=self._parse_price(professional_price, "PLAN_PROFESSIONAL_PRICE"),
                currency=normalized_currency,
                source_limit=15,
                features=(
                    "Hasta 15 fuentes",
                    "Prioridad de procesamiento",
                    "Panel de oportunidades (proximamente)",
                ),
            ),
            "enterprise": SubscriptionPlan(
                identifier="enterprise",
                name="Enterprise",
                price=self._parse_price(enterprise_price, "PLAN_ENTERPRISE_PRICE"),
                currency=normalized_currency,
                source_limit=None,
                features=(
                    "Fuentes ilimitadas",
                    "Equipos y permisos",
                    "Dashboards avanzados (proximamente)",
                    "Soporte prioritario",
                ),
            ),
        }

    @classmethod
    def from_settings(cls) -> "SubscriptionCatalog":
        return cls(
            starter_price=settings.PLAN_STARTER_PRICE,
            professional_price=settings.PLAN_PROFESSIONAL_PRICE,
            enterprise_price=settings.PLAN_ENTERPRISE_PRICE,
            currency=settings.PLAN_CURRENCY,
        )

    @staticmethod
    def _parse_price(raw_price: str, setting_name: str) -> Decimal:
        normalized = (raw_price or "").strip()
        if not normalized:
            raise ValueError(f"{setting_name} must not be empty")

        try:
            parsed = Decimal(normalized)
        except InvalidOperation as exc:
            raise ValueError(f"{setting_name} must be a valid decimal number") from exc

        if parsed < 0:
            raise ValueError(f"{setting_name} must be zero or greater")

        return parsed.quantize(Decimal("0.01"))

    def get_plan(self, identifier: str) -> SubscriptionPlan:
        key = (identifier or "").strip().lower()
        if key not in self._plans:
            raise KeyError(f"Unknown plan identifier: {identifier}")
        return self._plans[key]

    def list_plans(self) -> list[SubscriptionPlan]:
        return [
            self._plans["starter"],
            self._plans["professional"],
            self._plans["enterprise"],
        ]


_catalog = SubscriptionCatalog.from_settings()


def get_subscription_catalog() -> SubscriptionCatalog:
    return _catalog
