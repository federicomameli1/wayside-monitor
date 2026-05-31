from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set

from .models import SensorReading
from .registry import SensorRegistry

logger = logging.getLogger(__name__)

STREAM_NAME = os.getenv("COLLECTOR_STREAM", "wms:sensor-events")

# REQ-WMS-029: silence detection window.
SILENCE_TIMEOUT_SECONDS = float(
    os.getenv("SENSOR_SILENCE_TIMEOUT_SECONDS", "60")
)


class SensorCollector:
    """
    Reads raw sensor readings, validates them against the registry,
    and forwards valid ones to the downstream message bus.

    Invalid sensor types are logged as WARN and dropped (REQ-WMS-002).
    Tracks per-sensor last-seen timestamps to detect silence (REQ-WMS-029).
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
        # REQ-WMS-029: monotonic timestamp of last valid reading per sensor_id.
        self._last_seen: Dict[str, float] = {}
        self._silent_sensors: Set[str] = set()

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

        # REQ-WMS-029: update last-seen and clear silence alert if previously silent.
        now = time.monotonic()
        if sensor_id in self._silent_sensors:
            logger.info(
                "Sensor %s has resumed reporting — clearing DEGRADED silence alert",
                sensor_id,
            )
            self._silent_sensors.discard(sensor_id)
        self._last_seen[sensor_id] = now

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

    def check_silence(self) -> List[str]:
        """REQ-WMS-029: return sensor_ids that have been silent beyond the timeout.

        Should be called periodically (e.g. every 10 seconds) by the event loop.
        Newly detected silent sensors are logged at DEGRADED level.
        """
        now = time.monotonic()
        newly_silent = []
        for sensor_id, last_ts in self._last_seen.items():
            if (now - last_ts) >= SILENCE_TIMEOUT_SECONDS:
                if sensor_id not in self._silent_sensors:
                    logger.error(
                        "DEGRADED: sensor %s has been silent for %.0f seconds "
                        "(threshold: %.0f s) — REQ-WMS-029",
                        sensor_id,
                        now - last_ts,
                        SILENCE_TIMEOUT_SECONDS,
                    )
                    self._silent_sensors.add(sensor_id)
                    newly_silent.append(sensor_id)
        return newly_silent

    def health(self) -> Dict[str, Any]:
        if self._silent_sensors:
            return {
                "status": "degraded",
                "reason": f"silent sensors: {sorted(self._silent_sensors)}",
                "silent_sensors": sorted(self._silent_sensors),
            }
        return {
            "status": "ok",
            "accepted": self._accepted,
            "dropped": self._dropped,
        }

    def stats(self) -> Dict[str, int]:
        return {"accepted": self._accepted, "dropped": self._dropped}
