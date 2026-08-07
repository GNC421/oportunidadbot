from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any


class FakeScheduler:
    def __init__(self) -> None:
        self.jobs: list[dict[str, Any]] = []
        self.started = False
        self.stopped = False

    def add_job(self, func: Callable[..., Any], **kwargs: Any) -> None:
        self.jobs.append({"func": func, "kwargs": kwargs})

    def start(self) -> None:
        self.started = True

    def shutdown(self, wait: bool = False) -> None:
        self.stopped = True

    async def run_all_now(self) -> list[Any]:
        results = []
        for job in self.jobs:
            result = job["func"]()
            if isinstance(result, Awaitable):
                result = await result
            results.append(result)
        return results
