"""Data models for the tracing framework.

Use dataclasses and enums to represent events and states.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4
from datetime import datetime, timezone


class EventType(str, Enum):
    """Type/category of traced events. Easy to extend with new kinds."""

    AI = "AI"
    RSS = "RSS"
    DATABASE = "DATABASE"
    TELEGRAM = "TELEGRAM"
    SCHEDULER = "SCHEDULER"
    GENERAL = "GENERAL"


class EventState(str, Enum):
    """Lifecycle state of a traced event."""

    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    ERROR = "ERROR"


@dataclass
class TraceEvent:
    """Represents a single trace/observability event.

    Notes:
        - `id` is a stable UUID for correlating calls.
        - `timestamp` is set on creation (UTC).
        - `start_time` is kept internally to compute duration.
    """

    id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    type: EventType = EventType.GENERAL
    name: str = ""
    state: EventState = EventState.RUNNING
    duration: Optional[float] = None  # seconds
    input_payload: Optional[Any] = None
    output_payload: Optional[Any] = None
    error: Optional[str] = None
    traceback: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # Internal: used to compute duration when finishing the event.
    start_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc), repr=False)

    def finish(self, state: EventState, output: Any = None, error: Optional[str] = None, tb: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Mark the event as finished with `state` and record outputs/errors.

        This updates `duration` using the internal `start_time`.
        """
        self.state = state
        now = datetime.now(timezone.utc)
        self.duration = (now - self.start_time).total_seconds()
        if output is not None:
            self.output_payload = output
        if error is not None:
            self.error = error
        if tb is not None:
            self.traceback = tb
        if metadata:
            # merge metadata
            self.metadata.update(metadata)
