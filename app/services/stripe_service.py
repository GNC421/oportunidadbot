from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from loguru import logger

from app import database
from app.config import settings
from app.subscriptions.entities import Plan, SubscriptionStatus


class StripeIntegrationError(RuntimeError):
    """Raised when Stripe integration configuration is missing or invalid."""


@dataclass(frozen=True)
class CheckoutSessionResult:
    id: str
    url: str


@dataclass(frozen=True)
class PortalSessionResult:
    id: str
    url: str


class StripeService:
    """Centralized Stripe operations and webhook synchronization."""

    def __init__(self, stripe_client: Any) -> None:
        self._stripe = stripe_client

        self._secret_key = settings.STRIPE_SECRET_KEY
        self._webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        self._success_url = settings.STRIPE_CHECKOUT_SUCCESS_URL
        self._cancel_url = settings.STRIPE_CHECKOUT_CANCEL_URL
        self._portal_return_url = settings.STRIPE_PORTAL_RETURN_URL

        self._price_ids = {
            Plan.STARTER: settings.STRIPE_STARTER_PRICE_ID,
            Plan.PROFESSIONAL: settings.STRIPE_PROFESSIONAL_PRICE_ID,
            Plan.ENTERPRISE: settings.STRIPE_ENTERPRISE_PRICE_ID,
        }

    @staticmethod
    def from_settings() -> "StripeService":
        if not settings.STRIPE_SECRET_KEY:
            raise StripeIntegrationError("STRIPE_SECRET_KEY no configurado")

        try:
            import stripe
        except ImportError as exc:
            raise StripeIntegrationError("Dependencia stripe no instalada") from exc

        stripe.api_key = settings.STRIPE_SECRET_KEY
        return StripeService(stripe_client=stripe)

    def create_checkout_session(self, user_id: int, plan: Plan, customer_id: Optional[str] = None) -> CheckoutSessionResult:
        price_id = self._resolve_price_id(plan)
        success_url = self._require_value(self._success_url, "STRIPE_CHECKOUT_SUCCESS_URL")
        cancel_url = self._require_value(self._cancel_url, "STRIPE_CHECKOUT_CANCEL_URL")

        checkout = self._stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            customer=customer_id,
            metadata={
                "user_id": str(user_id),
                "plan": plan.value,
            },
        )
        return CheckoutSessionResult(id=str(checkout.id), url=str(checkout.url))

    def get_customer(self, customer_id: str) -> Any:
        return self._stripe.Customer.retrieve(customer_id)

    def get_subscription(self, subscription_id: str) -> Any:
        return self._stripe.Subscription.retrieve(subscription_id)

    def create_customer_portal_session(self, customer_id: str) -> PortalSessionResult:
        return_url = self._require_value(self._portal_return_url, "STRIPE_PORTAL_RETURN_URL")
        session = self._stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return PortalSessionResult(id=str(session.id), url=str(session.url))

    def construct_webhook_event(self, payload: bytes, signature: str) -> dict[str, Any]:
        webhook_secret = self._require_value(self._webhook_secret, "STRIPE_WEBHOOK_SECRET")
        event = self._stripe.Webhook.construct_event(payload=payload, sig_header=signature, secret=webhook_secret)
        return dict(event)

    def process_webhook_event(self, event: dict[str, Any]) -> bool:
        event_id = str(event.get("id") or "")
        event_type = str(event.get("type") or "")

        if not event_id or not event_type:
            logger.warning("Evento Stripe inválido: faltan id/type")
            return False

        created = database.register_stripe_webhook_event(event_id, event_type, event)
        if not created:
            logger.info("Evento Stripe ya procesado", event_id=event_id, event_type=event_type)
            return True

        try:
            handled = self._dispatch_webhook_event(event_type, event)
            status = "processed" if handled else "ignored"
            database.mark_stripe_webhook_event_status(event_id, status=status)
            return True
        except Exception as exc:
            logger.exception("Error procesando webhook Stripe", event_id=event_id, event_type=event_type)
            database.mark_stripe_webhook_event_status(event_id, status="failed", error_message=str(exc))
            return False

    def _dispatch_webhook_event(self, event_type: str, event: dict[str, Any]) -> bool:
        if event_type == "checkout.session.completed":
            self._handle_checkout_completed(event)
            return True

        if event_type in {"customer.subscription.updated", "customer.subscription.deleted"}:
            self._handle_subscription_event(event)
            return True

        if event_type == "invoice.payment_failed":
            self._handle_invoice_payment_failed(event)
            return True

        logger.info("Evento Stripe ignorado", event_type=event_type)
        return False

    def _handle_checkout_completed(self, event: dict[str, Any]) -> None:
        obj = event.get("data", {}).get("object", {})
        metadata = obj.get("metadata", {}) or {}
        raw_user_id = metadata.get("user_id")

        if raw_user_id is None:
            logger.warning("checkout.session.completed sin user_id en metadata")
            return

        user_id = int(raw_user_id)
        customer_id = self._as_optional_string(obj.get("customer"))
        subscription_id = self._as_optional_string(obj.get("subscription"))

        if subscription_id:
            subscription = self.get_subscription(subscription_id)
            self._sync_from_subscription_payload(
                subscription_obj=dict(subscription),
                preferred_user_id=user_id,
                fallback_customer_id=customer_id,
            )
            return

        database.update_user_subscription(
            user_id=user_id,
            plan=str(metadata.get("plan") or Plan.STARTER.value),
            subscription_status=SubscriptionStatus.ACTIVE.value,
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription_id,
            current_period_end=None,
            cancel_at_period_end=False,
        )

    def _handle_subscription_event(self, event: dict[str, Any]) -> None:
        subscription_obj = event.get("data", {}).get("object", {})
        self._sync_from_subscription_payload(subscription_obj=subscription_obj)

    def _handle_invoice_payment_failed(self, event: dict[str, Any]) -> None:
        invoice_obj = event.get("data", {}).get("object", {})
        customer_id = self._as_optional_string(invoice_obj.get("customer"))
        subscription_id = self._as_optional_string(invoice_obj.get("subscription"))

        if subscription_id:
            subscription = self.get_subscription(subscription_id)
            self._sync_from_subscription_payload(
                subscription_obj=dict(subscription),
                fallback_customer_id=customer_id,
            )
            return

        if not customer_id:
            logger.warning("invoice.payment_failed sin customer/subscription")
            return

        user = database.get_user_by_stripe_customer_id(customer_id)
        if not user:
            logger.warning("No se encontró usuario para invoice.payment_failed", customer_id=customer_id)
            return

        database.update_user_subscription(
            user_id=int(user["id"]),
            plan=str(user.get("plan") or Plan.STARTER.value),
            subscription_status=SubscriptionStatus.PAST_DUE.value,
            stripe_customer_id=customer_id,
            stripe_subscription_id=self._as_optional_string(user.get("stripe_subscription_id")),
            current_period_end=self._as_optional_string(user.get("current_period_end")),
            cancel_at_period_end=bool(user.get("cancel_at_period_end", False)),
        )

    def _sync_from_subscription_payload(
        self,
        subscription_obj: dict[str, Any],
        preferred_user_id: Optional[int] = None,
        fallback_customer_id: Optional[str] = None,
    ) -> None:
        customer_id = self._as_optional_string(subscription_obj.get("customer")) or fallback_customer_id
        if not customer_id:
            logger.warning("Evento de suscripción sin customer")
            return

        user_id = preferred_user_id
        if user_id is None:
            user = database.get_user_by_stripe_customer_id(customer_id)
            if not user:
                logger.warning("No se encontró usuario para customer", customer_id=customer_id)
                return
            user_id = int(user["id"])

        plan = self._resolve_plan_from_subscription(subscription_obj)
        status = self._resolve_subscription_status(str(subscription_obj.get("status") or "active"))
        current_period_end = self._epoch_to_iso(subscription_obj.get("current_period_end"))
        subscription_id = self._as_optional_string(subscription_obj.get("id"))
        cancel_at_period_end = bool(subscription_obj.get("cancel_at_period_end", False))

        database.update_user_subscription(
            user_id=user_id,
            plan=plan.value,
            subscription_status=status.value,
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription_id,
            current_period_end=current_period_end,
            cancel_at_period_end=cancel_at_period_end,
        )

    def _resolve_price_id(self, plan: Plan) -> str:
        value = self._price_ids.get(plan)
        return self._require_value(value, f"STRIPE_{plan.value.upper()}_PRICE_ID")

    def _resolve_plan_from_subscription(self, subscription_obj: dict[str, Any]) -> Plan:
        items = subscription_obj.get("items", {}).get("data", [])
        if not items:
            logger.warning("Suscripción Stripe sin items, fallback a starter")
            return Plan.STARTER

        price_id = self._as_optional_string(items[0].get("price", {}).get("id"))
        if not price_id:
            logger.warning("Item de suscripción sin price.id, fallback a starter")
            return Plan.STARTER

        for plan, configured_price_id in self._price_ids.items():
            if configured_price_id and configured_price_id == price_id:
                return plan

        logger.warning("price_id no mapeado en settings, fallback a starter", price_id=price_id)
        return Plan.STARTER

    @staticmethod
    def _resolve_subscription_status(raw_status: str) -> SubscriptionStatus:
        value = (raw_status or "").strip().lower()
        try:
            return SubscriptionStatus(value)
        except ValueError:
            return SubscriptionStatus.ACTIVE

    @staticmethod
    def _as_optional_string(value: Any) -> Optional[str]:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _epoch_to_iso(value: Any) -> Optional[str]:
        if value is None:
            return None
        try:
            timestamp = int(value)
        except (TypeError, ValueError):
            return None
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return dt.isoformat()

    @staticmethod
    def _require_value(value: Optional[str], name: str) -> str:
        normalized = (value or "").strip()
        if not normalized:
            raise StripeIntegrationError(f"{name} no configurado")
        return normalized


_stripe_service: Optional[StripeService] = None


def get_stripe_service() -> StripeService:
    global _stripe_service
    if _stripe_service is None:
        _stripe_service = StripeService.from_settings()
    return _stripe_service
