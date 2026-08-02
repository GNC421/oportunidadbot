"""In-memory repository for trace events.

Implements a simple capped storage that keeps the most recent N events.
This module is intentionally small and encapsulates storage details so the
rest of the system does not need to know how events are persisted.
"""
from __future__ import annotations
from collections import OrderedDict
from typing import List, Optional
import asyncio

from .trace_models import TraceEvent, EventType


class InMemoryTraceRepository:
    """Thread-safe in-memory repository backed by an OrderedDict.

    Keeps insertion order and removes the oldest entries when capacity is
    exceeded.
    """

    def __init__(self, capacity: int = 500) -> None:
        self._capacity = int(capacity)
        self._lock = asyncio.Lock()
        self._events: "OrderedDict[str, TraceEvent]" = OrderedDict()

    async def add(self, event: TraceEvent) -> None:
        """Add a new event to the repository.

        If capacity is exceeded, the oldest item is removed automatically.
        """
        async with self._lock:
            # Store by stringified UUID to make JSON-friendly keys
            key = str(event.id)
            self._events[key] = event
            # pop oldest until capacity
            while len(self._events) > self._capacity:
                self._events.popitem(last=False)

    async def update(self, event_id: str, updater) -> Optional[TraceEvent]:
        """Update an existing event by applying `updater(event)`.

        Returns the updated event or None if not found.
        """
        async with self._lock:
            ev = self._events.get(event_id)
            if ev is None:
                return None
            updater(ev)
            # re-insert to keep insertion order (do not change order)
            self._events[event_id] = ev
            return ev

    async def get(self, event_id: str) -> Optional[TraceEvent]:
        async with self._lock:
            return self._events.get(event_id)

    async def get_all(self) -> List[TraceEvent]:
        async with self._lock:
            return list(self._events.values())[::-1]  # newest first

    async def get_by_type(self, type_: EventType) -> List[TraceEvent]:
        async with self._lock:
            return [e for e in list(self._events.values())[::-1] if e.type == type_]

    async def clear(self) -> None:
        async with self._lock:
            self._events.clear()
