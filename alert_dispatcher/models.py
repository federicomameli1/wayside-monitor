from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


SCHEMA_VERSION = "1.1"

# Permitted severity values (REQ-WMS-008, REQ-WMS-013).
VALID_SEVERITIES = frozenset({"NOMINAL", "DEGRADED", "CRITICAL"})


@dataclass(frozen=True)
class AlertPayload:
    """
    Outbound alert payload (schema v1.1).
    Backward compatible with 1.0 consumers that ignore unknown fields.
    """

    event_id: str
    sensor_id: str
    severity: str
    value: float
    unit: str
    timestamp: str
    model_ver: str
    confidence: Optional[float] = None

    def __post_init__(self) -> None:
        if self.severity not in VALID_SEVERITIES:
            raise ValueError(
                f"Invalid severity {self.severity!r}. "
                f"Must be one of {sorted(VALID_SEVERITIES)}."
            )

    def to_dict(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "event_id": self.event_id,
            "sensor_id": self.sensor_id,
            "severity": self.severity,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp,
            "model_ver": self.model_ver,
            "confidence": self.confidence,
        }
