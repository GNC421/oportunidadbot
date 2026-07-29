from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Optional

from loguru import logger

from app import database
from app.subscriptions import SubscriptionCatalog, get_subscription_catalog
from app.subscriptions.entities import Plan, Subscription, SubscriptionStatus


class SubscriptionService:
    """Centralizes plan limits and subscription permission checks."""

    _ALLOWED_SOURCE_STATUSES = {
        SubscriptionStatus.ACTIVE,
        SubscriptionStatus.TRIALING,
        SubscriptionStatus.PAST_DUE,
    }

    def __init__(
        self,
        catalog: SubscriptionCatalog,
        user_reader: Callable[[int], Optional[dict[str, Any]]],
        feed_count_reader: Callable[[int], int],
    ) -> None:
        self._catalog = catalog
        self._user_reader = user_reader
        self._feed_count_reader = feed_count_reader

    def get_current_subscription(self, user_id: int) -> Subscription:
        user = self._user_reader(user_id) or {}

        plan = self._parse_plan(str(user.get("plan") or Plan.STARTER.value))
        status = self._parse_status(str(user.get("subscription_status") or SubscriptionStatus.ACTIVE.value))

        plan_definition = self._catalog.get_plan(plan.value)
        return Subscription(
            user_id=user_id,
            plan=plan,
            status=status,
            stripe_customer_id=self._as_optional_str(user.get("stripe_customer_id")),
            stripe_subscription_id=self._as_optional_str(user.get("stripe_subscription_id")),
            current_period_end=self._parse_datetime(user.get("current_period_end")),
            cancel_at_period_end=bool(user.get("cancel_at_period_end", False)),
            plan_definition=plan_definition,
        )

    def can_add_source(self, user_id: int) -> bool:
        subscription = self.get_current_subscription(user_id)
        if subscription.status not in self._ALLOWED_SOURCE_STATUSES:
            return False

        remaining = self.get_remaining_sources(user_id)
        return remaining is None or remaining > 0

    def can_use_feature(self, user_id: int, feature_name: str) -> bool:
        normalized_feature = (feature_name or "").strip().lower()
        if not normalized_feature:
            return False

        subscription = self.get_current_subscription(user_id)
        return any(feature.lower() == normalized_feature for feature in subscription.plan_definition.features)

    def get_remaining_sources(self, user_id: int) -> Optional[int]:
        subscription = self.get_current_subscription(user_id)
        source_limit = subscription.plan_definition.source_limit
        if source_limit is None:
            return None

        current_count = self._feed_count_reader(user_id)
        remaining = source_limit - current_count
        return max(0, remaining)

    @staticmethod
    def _parse_plan(raw_plan: str) -> Plan:
        value = (raw_plan or "").strip().lower()
        try:
            return Plan(value)
        except ValueError:
            logger.warning("Unknown plan value detected, fallback to starter", plan=raw_plan)
            return Plan.STARTER

    @staticmethod
    def _parse_status(raw_status: str) -> SubscriptionStatus:
        value = (raw_status or "").strip().lower()
        try:
            return SubscriptionStatus(value)
        except ValueError:
            logger.warning("Unknown subscription status detected, fallback to active", status=raw_status)
            return SubscriptionStatus.ACTIVE

    @staticmethod
    def _as_optional_str(value: Any) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _parse_datetime(raw_value: Any) -> Optional[datetime]:
        if raw_value is None:
            return None

        value = str(raw_value).strip()
        if not value:
            return None

        if value.endswith("Z"):
            value = value[:-1] + "+00:00"

        try:
            return datetime.fromisoformat(value)
        except ValueError:
            logger.warning("Invalid current_period_end format", raw_value=raw_value)
            return None


_subscription_service = SubscriptionService(
    catalog=get_subscription_catalog(),
    user_reader=database.get_user,
    feed_count_reader=database.user_feed_count,
)


def get_subscription_service() -> SubscriptionService:
    return _subscription_service
