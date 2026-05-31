from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4


class Severity(str, Enum):
    NOMINAL = "NOMINAL"
    DEGRADED = "DEGRADED"
    CRITICAL = "CRITICAL"


@dataclass(frozen=True)
class AnomalyEvent:
    event_id: str
    sensor_id: str
    sensor_type: str
    value: float
    unit: str
    severity: Severity
    timestamp: datetime
    model_ver: str
    confidence: Optional[float] = None
    source_reading_id: Optional[str] = None
    # REQ-WMS-029: identifies which collector instance emitted this event,
    # enabling silence detection correlation across distributed deployments.
    # Optional — existing consumers on schema_version 1.2 ignore unknown fields.
    source_collector_id: Optional[str] = None

    def to_dict(self) -> dict:
        d = {
            "schema_version": "1.2",
            "event_id": self.event_id,
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type,
            "value": self.value,
            "unit": self.unit,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "model_ver": self.model_ver,
            "confidence": self.confidence,
            "source_reading_id": self.source_reading_id,
        }
        if self.source_collector_id is not None:
            d["source_collector_id"] = self.source_collector_id
        return d
