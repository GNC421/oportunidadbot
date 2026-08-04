from __future__ import annotations

from types import SimpleNamespace
import importlib.util
from pathlib import Path
import pytest


def _load_handlers_module():
    path = Path(__file__).resolve().parents[2] / "app" / "bot" / "handlers.py"
    spec = importlib.util.spec_from_file_location("handlers_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_format_subscription_status_and_renewal_and_plans(monkeypatch):
    handlers = _load_handlers_module()

    assert handlers._format_subscription_status("active") == "Activa"
    assert handlers._format_subscription_status("unknown") == "unknown"

    from datetime import datetime, timezone

    dt = datetime(2026, 1, 2, tzinfo=timezone.utc)
    assert handlers._format_renewal_date(dt) == "02/01/2026"

    # build subscription summary text
    class FakePlanDef:
        def __init__(self):
            self.name = "Starter"
            self.price = 0
            self.currency = "EUR"
            self.source_limit = 5

    class FakeSubscription:
        def __init__(self):
            self.plan_definition = FakePlanDef()
            self.status = SimpleNamespace(value="active")
            self.current_period_end = None

    monkeypatch.setattr(handlers, "get_subscription_service", lambda: SimpleNamespace(get_current_subscription=lambda uid: FakeSubscription()))
    monkeypatch.setattr(handlers.database, "user_feed_count", lambda uid: 2)

    txt = handlers._build_subscription_summary_text(101)
    assert "Mi suscripción" in txt
    assert "Fuentes utilizadas: 2" in txt

