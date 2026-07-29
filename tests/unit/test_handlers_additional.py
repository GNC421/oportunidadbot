from __future__ import annotations

from types import SimpleNamespace
import pytest
import importlib.util
from pathlib import Path


def _load_handlers_module():
    path = Path(__file__).resolve().parents[2] / "app" / "bot" / "handlers.py"
    spec = importlib.util.spec_from_file_location("handlers_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _build_callback_update(callback_data: str, user_id: int = 101):
    replies = []

    async def reply_text(text: str, **kwargs):
        replies.append({"text": text, "kwargs": kwargs})

    async def answer(*_a, **_k):
        return None

    message = SimpleNamespace(text="hello", reply_text=reply_text)
    callback_query = SimpleNamespace(data=callback_data, answer=answer, message=message)
    user = SimpleNamespace(id=user_id, username="tester")
    update = SimpleNamespace(effective_user=user, message=message, callback_query=callback_query)
    context = SimpleNamespace(args=[], matches=[])
    return update, context, replies


@pytest.mark.asyncio
async def test_subscription_checkout_no_user():
    handlers = _load_handlers_module()
    update, context, replies = _build_callback_update("sub_checkout_professional")
    update.effective_user = None

    await handlers.handle_subscription_checkout(update, context)

    assert replies
    assert "No pude identificar tu usuario" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_subscription_checkout_no_selected_plan():
    handlers = _load_handlers_module()
    update, context, replies = _build_callback_update("sub_checkout_")
    # context.matches empty and callback_data has no identifier

    await handlers.handle_subscription_checkout(update, context)

    assert replies
    assert ("No pude identificar el plan" in replies[-1]["text"]) or ("no es válido" in replies[-1]["text"]) 


@pytest.mark.asyncio
async def test_subscription_checkout_invalid_plan(monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = _build_callback_update("sub_checkout_invalid")
    # cause ValueError by using an invalid plan string
    context.matches = []

    # Provide a fake subscription service so code reaches ValueError
    class FakeSubSvc:
        def get_current_subscription(self, _u):
            return SimpleNamespace(stripe_customer_id=None)

    monkeypatch.setattr(handlers, "get_subscription_service", lambda: FakeSubSvc())

    await handlers.handle_subscription_checkout(update, context)

    assert replies
    assert "El plan seleccionado no es válido" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_subscription_checkout_stripe_error(monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = _build_callback_update("sub_checkout_professional")
    context.matches = [SimpleNamespace(group=lambda _idx: "professional")]

    class FakeSubSvc:
        def get_current_subscription(self, _u):
            return SimpleNamespace(stripe_customer_id=None)

    class FakeStripe:
        def create_checkout_session(self, **_k):
            raise handlers.StripeIntegrationError("no stripe")

    monkeypatch.setattr(handlers, "get_subscription_service", lambda: FakeSubSvc())
    monkeypatch.setattr(handlers, "get_stripe_service", lambda: FakeStripe())

    await handlers.handle_subscription_checkout(update, context)

    assert replies
    assert "No pude abrir checkout" in replies[-1]["text"]


@pytest.mark.asyncio
async def test_send_customer_portal_stripe_error(monkeypatch):
    handlers = _load_handlers_module()
    update, context, replies = _build_callback_update("sub_open_portal")

    class FakeSubSvc:
        def get_current_subscription(self, _u):
            return SimpleNamespace(stripe_customer_id="cus_1")

    class FakeStripe:
        def create_customer_portal_session(self, _cid):
            raise handlers.StripeIntegrationError("fail")

    monkeypatch.setattr(handlers, "get_subscription_service", lambda: FakeSubSvc())
    monkeypatch.setattr(handlers, "get_stripe_service", lambda: FakeStripe())

    # call the public handler that uses _send_customer_portal_link
    await handlers.handle_subscription_open_portal(update, context)

    assert replies
    assert "No pude abrir Stripe Portal" in replies[-1]["text"]
