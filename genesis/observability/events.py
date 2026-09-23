"""
Unified Event System

SINGLE CANONICAL LOCATION for all Genesis events.
Design: Structured events for observability and auditing.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any


class EventType(StrEnum):
    """Genesis lifecycle events."""

    CAPABILITY_PLANNING_STARTED = "capability.planning.started"
    CAPABILITY_PLANNED = "capability.planned"
    CAPABILITY_VALIDATED = "capability.validated"
    CAPABILITY_BUILT = "capability.built"
    CAPABILITY_TESTED = "capability.tested"
    CAPABILITY_EVALUATED = "capability.evaluated"
    CAPABILITY_AWAITING_APPROVAL = "capability.awaiting_approval"
    CAPABILITY_APPROVED = "capability.approved"
    CAPABILITY_REJECTED = "capability.rejected"
    CAPABILITY_REGISTERED = "capability.registered"


@dataclass
class Event:
    """Structured event."""

    event_type: EventType
    timestamp: datetime
    capability_id: str
    actor: str
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for logging."""
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "capability_id": self.capability_id,
            "actor": self.actor,
            "payload": self.payload,
        }


class EventEmitter:
    """
    Event emitter with JSON-lines logging.

    Design: Simple file-based logging for v0.1.
    Future: Event streaming infrastructure.
    """

    def __init__(self, log_path: Path | None = None) -> None:
        if log_path is None:
            log_path = Path("logs/events.jsonl")

        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event: Event) -> None:
        """Emit event to log."""
        with open(self.log_path, "a") as f:
            f.write(json.dumps(event.to_dict()) + "\n")
