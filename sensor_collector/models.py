from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4


@dataclass(frozen=True)
class SensorReading:
    sensor_id: str
    sensor_type: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    reading_id: str = field(default_factory=lambda: str(uuid4()))
    # REQ-WMS-028: monotonic sequence number assigned by the collector instance.
    # None when the reading originates outside a SensorCollector (e.g. test stubs).
    seq: Optional[int] = None

    def to_event(self) -> dict:
        event = {
            "schema_version": "1.2",
            "reading_id": self.reading_id,
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
        }
        if self.seq is not None:
            event["seq"] = self.seq
        return event
