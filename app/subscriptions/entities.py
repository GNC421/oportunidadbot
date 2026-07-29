from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from .catalog import SubscriptionPlan


class Plan(str, Enum):
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    TRIALING = "trialing"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    UNPAID = "unpaid"


@dataclass(frozen=True)
class Subscription:
    user_id: int
    plan: Plan
    status: SubscriptionStatus
    stripe_customer_id: Optional[str]
    stripe_subscription_id: Optional[str]
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool
    plan_definition: SubscriptionPlan
