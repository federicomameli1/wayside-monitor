from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional
from uuid import uuid4

from .classifier import MODEL_VER, classify_temperature, classify_vibration, classify_rail_wear
from .models import AnomalyEvent, Severity

logger = logging.getLogger(__name__)

STREAM_NAME = os.getenv("ENGINE_STREAM", "wms:anomaly-events")
_MAX_QUEUE_DEPTH = 1000

_CLASSIFIERS = {
    "TEMPERATURE": classify_temperature,
    "VIBRATION": classify_vibration,
    "RAIL_WEAR": classify_rail_wear,
}


class AnomalyEngine:
    """
    Consumes sensor events from sensor-collector, classifies each
    reading, and publishes AnomalyEvents downstream (REQ-WMS-005 to 011).
    """

    def __init__(self, publish: Callable[[str, dict], None]) -> None:
        self._publish = publish
        self._processed = 0
        self._queue_depth = 0
        self._health_degraded = False

    def process(self, event: Dict[str, Any]) -> Optional[AnomalyEvent]:
        """Classify one sensor event and publish the result."""
        self._queue_depth += 1
        if self._queue_depth > _MAX_QUEUE_DEPTH:
            self._health_degraded = True
            logger.critical(
                "Queue depth %d exceeds limit — back-pressure applied (REQ-WMS-009)",
                self._queue_depth,
            )

        sensor_type = event.get("sensor_type", "")
        classify = _CLASSIFIERS.get(sensor_type)

        if classify is None:
            logger.warning("No classifier for sensor type %r — event skipped", sensor_type)
            self._queue_depth -= 1
            return None

        try:
            value = float(event["value"])
            severity, confidence = classify(value)
            ts = datetime.fromisoformat(event["timestamp"]) if "timestamp" in event else datetime.now(timezone.utc)

            anomaly = AnomalyEvent(
                event_id=str(uuid4()),
                sensor_id=event.get("sensor_id", ""),
                sensor_type=sensor_type,
                value=value,
                unit=event.get("unit", ""),
                severity=severity,
                timestamp=ts,
                model_ver=MODEL_VER,
                confidence=confidence,
                source_reading_id=event.get("reading_id"),
            )
            self._publish(STREAM_NAME, anomaly.to_dict())
            self._processed += 1
            return anomaly
        except Exception:
            logger.exception("Unhandled exception processing event (REQ-WMS-022): %s", event)
            raise
        finally:
            self._queue_depth -= 1

    def health(self) -> Dict[str, Any]:
        if self._health_degraded:
            return {"status": "degraded", "reason": "queue depth exceeded limit"}
        return {"status": "ok", "processed": self._processed}
