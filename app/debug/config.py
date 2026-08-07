"""Configuration for the tracing framework.

Reads configuration from environment variables. Keep this module minimal
so it can be extended later (e.g., different backends, capacities).
"""
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class TraceConfig:
    """Runtime configuration for the tracing framework.

    Attributes:
        enabled: When False the tracing framework becomes a no-op.
        capacity: Maximum number of events to keep in memory.
    """

    enabled: bool = True
    capacity: int = 500


def load_config() -> TraceConfig:
    enabled_raw = os.getenv("DEBUG_TRACE_ENABLED", "true")
    enabled = enabled_raw.lower() in ("1", "true", "yes", "on")
    capacity_raw = os.getenv("DEBUG_TRACE_CAPACITY")
    try:
        capacity = int(capacity_raw) if capacity_raw is not None else 500
    except ValueError:
        capacity = 500
    return TraceConfig(enabled=enabled, capacity=capacity)


settings = load_config()
