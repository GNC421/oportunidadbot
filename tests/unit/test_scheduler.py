from __future__ import annotations

from app.jobs import scheduler as scheduler_module


def test_scheduler_start_sets_job(monkeypatch, fake_scheduler):
    monkeypatch.setattr(scheduler_module, "scheduler", fake_scheduler)

    scheduler_module.start_scheduler()

    assert fake_scheduler.started is True
    assert len(fake_scheduler.jobs) == 1
    assert fake_scheduler.jobs[0]["kwargs"]["id"] == "feed_check_job"


def test_scheduler_stop_shutdown(monkeypatch, fake_scheduler):
    monkeypatch.setattr(scheduler_module, "scheduler", fake_scheduler)

    scheduler_module.stop_scheduler()

    assert fake_scheduler.stopped is True
