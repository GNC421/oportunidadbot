"""TraceService high-level API.

Provides a single entrypoint for the application to record trace events
without exposing storage details.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
import traceback as _traceback
from uuid import UUID

from .trace_models import TraceEvent, EventState, EventType
from .trace_repository import InMemoryTraceRepository
from .config import settings


class TraceService:
    """Facade used by the application to create and update trace events.

    All write operations are no-ops when tracing is disabled via config.
    """

    def __init__(self, repository: InMemoryTraceRepository, enabled: bool = True) -> None:
        self._repo = repository
        self._enabled = bool(enabled)

    async def start(self, type: EventType, name: str, input_payload: Any = None, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Start a new event and return its UUID (string).

        The returned id can be used to mark success/error later.
        """
        if not self._enabled:
            return ""
        ev = TraceEvent(type=type, name=name, input_payload=input_payload)
        if metadata:
            ev.metadata.update(metadata)
        await self._repo.add(ev)
        return str(ev.id)

    async def success(self, event_id: str, output_payload: Any = None, metadata: Optional[Dict[str, Any]] = None) -> Optional[TraceEvent]:
        """Mark the event as SUCCESS and attach output/metadata."""
        if not self._enabled:
            return None

        def updater(ev: TraceEvent) -> None:
            ev.finish(EventState.SUCCESS, output=output_payload, metadata=metadata)

        return await self._repo.update(event_id, updater)

    async def error(self, event_id: str, error: Any = None, tb: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Optional[TraceEvent]:
        """Mark the event as ERROR and record traceback and message."""
        if not self._enabled:
            return None

        if tb is None:
            tb = _traceback.format_exc()

        def updater(ev: TraceEvent) -> None:
            ev.finish(EventState.ERROR, output=None, error=str(error) if error is not None else None, tb=tb, metadata=metadata)

        return await self._repo.update(event_id, updater)

    async def get_all(self) -> List[TraceEvent]:
        if not self._enabled:
            return []
        return await self._repo.get_all()

    async def get_by_type(self, type_: EventType) -> List[TraceEvent]:
        if not self._enabled:
            return []
        return await self._repo.get_by_type(type_)

    async def get(self, event_id: str) -> Optional[TraceEvent]:
        if not self._enabled:
            return None
        return await self._repo.get(event_id)

    async def clear(self) -> None:
        if not self._enabled:
            return None
        await self._repo.clear()


def create_default_trace_service() -> TraceService:
    """Factory helper that uses the module `settings` to build a default instance."""
    repo = InMemoryTraceRepository(capacity=settings.capacity)
    return TraceService(repository=repo, enabled=settings.enabled)


# Module-level default instance (singleton) so the entire app can import the same service.
_default_trace_service: Optional[TraceService] = None


def get_trace_service() -> TraceService:
    """Return a shared TraceService instance for the application.

    Uses a module-level singleton to ensure all modules record into the same
    in-memory repository.
    """
    global _default_trace_service
    if _default_trace_service is None:
        _default_trace_service = create_default_trace_service()
    return _default_trace_service

