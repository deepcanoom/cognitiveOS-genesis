"""
Tests for Unified Event System.

Tests event serialization and JSON-lines emission.
"""

import json
from datetime import datetime
from pathlib import Path

from genesis.observability.events import Event, EventEmitter, EventType


def test_event_to_dict_serialization():
    """Event serializes to a complete dict with all fields."""
    event = Event(
        event_type=EventType.CAPABILITY_APPROVED,
        timestamp=datetime(2026, 1, 1, 12, 0, 0),
        capability_id="greeting@0.1.0",
        actor="human:operator",
        payload={"reason": "LGTM"},
    )
    data = event.to_dict()
    assert data["event_type"] == "capability.approved"
    assert data["timestamp"] == "2026-01-01T12:00:00"
    assert data["capability_id"] == "greeting@0.1.0"
    assert data["actor"] == "human:operator"
    assert data["payload"] == {"reason": "LGTM"}


def test_event_payload_defaults_to_empty_dict():
    """Payload is optional."""
    event = Event(
        event_type=EventType.CAPABILITY_PLANNED,
        timestamp=datetime.now(),
        capability_id="x@0.1.0",
        actor="genesis",
    )
    assert event.payload == {}


def test_event_emitter_writes_json_lines(tmp_path: Path):
    """Emitter appends one JSON object per line."""
    log_path = tmp_path / "logs" / "events.jsonl"
    emitter = EventEmitter(log_path=log_path)

    event1 = Event(
        event_type=EventType.CAPABILITY_PLANNING_STARTED,
        timestamp=datetime.now(),
        capability_id="a@0.1.0",
        actor="genesis",
    )
    event2 = Event(
        event_type=EventType.CAPABILITY_REGISTERED,
        timestamp=datetime.now(),
        capability_id="a@0.1.0",
        actor="human:operator",
    )
    emitter.emit(event1)
    emitter.emit(event2)

    lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    parsed = [json.loads(line) for line in lines]
    assert parsed[0]["event_type"] == "capability.planning.started"
    assert parsed[1]["event_type"] == "capability.registered"


def test_event_emitter_creates_parent_directories(tmp_path: Path):
    """Emitter creates missing parent directories."""
    emitter = EventEmitter(log_path=tmp_path / "deep" / "nested" / "events.jsonl")
    emitter.emit(
        Event(
            event_type=EventType.CAPABILITY_BUILT,
            timestamp=datetime.now(),
            capability_id="b@0.1.0",
            actor="genesis",
        )
    )
    assert (tmp_path / "deep" / "nested" / "events.jsonl").exists()


def test_event_type_values_are_dotted_names():
    """All event types use dotted lowercase names."""
    for event_type in EventType:
        assert event_type.value == event_type.value.lower()
        assert "." in event_type.value
