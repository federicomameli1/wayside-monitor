from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from .models import SensorReading
from .registry import SensorRegistry

logger = logging.getLogger(__name__)

STREAM_NAME = os.getenv("COLLECTOR_STREAM", "wms:sensor-events")
HEALTH_STATUS: Dict[str, Any] = {"status": "ok"}


class SensorCollector:
    """
    Reads raw sensor readings, validates them against the registry,
    and forwards valid ones to the downstream message bus.

    Invalid sensor types are logged as WARN and dropped (REQ-WMS-002).
    """

    def __init__(
        self,
        registry: SensorRegistry,
        publish: Callable[[str, dict], None],
    ) -> None:
        self._registry = registry
        self._publish = publish
        self._accepted = 0
        self._dropped = 0
        self._seq = 0  # REQ-WMS-028: monotonic sequence counter

    def ingest(self, raw: Dict[str, Any]) -> Optional[SensorReading]:
        sensor_type = raw.get("sensor_type", "")
        sensor_id = raw.get("sensor_id", "")

        if not self._registry.is_known(sensor_type):
            logger.warning(
                "Unknown sensor type %r from sensor %s — reading dropped",
                sensor_type,
                sensor_id,
            )
            self._dropped += 1
            return None

        unit = self._registry.unit_for(sensor_type) or raw.get("unit", "")
        self._seq += 1
        reading = SensorReading(
            sensor_id=sensor_id,
            sensor_type=sensor_type,
            value=float(raw["value"]),
            unit=unit,
            timestamp=datetime.fromisoformat(raw["timestamp"])
            if "timestamp" in raw
            else datetime.now(timezone.utc),
            seq=self._seq,  # REQ-WMS-028
        )
        self._publish(STREAM_NAME, reading.to_event())
        self._accepted += 1
        return reading

    def health(self) -> Dict[str, Any]:
        return {
            "status": "ok",
            "accepted": self._accepted,
            "dropped": self._dropped,
        }

    def stats(self) -> Dict[str, int]:
        return {"accepted": self._accepted, "dropped": self._dropped}
