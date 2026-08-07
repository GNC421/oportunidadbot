from __future__ import annotations

import pytest

from app.jobs import scheduler as scheduler_module


@pytest.mark.asyncio
async def test_scheduler_calls_orchestrator(monkeypatch, fake_scheduler):
    calls = {"n": 0}

    async def _run_feed_checks():
        calls["n"] += 1
        return 2

    monkeypatch.setattr(scheduler_module, "scheduler", fake_scheduler)
    monkeypatch.setattr(scheduler_module, "run_feed_checks", _run_feed_checks)

    scheduler_module.start_scheduler()
    await fake_scheduler.run_all_now()

    assert calls["n"] == 1
