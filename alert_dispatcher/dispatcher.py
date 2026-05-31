from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional

from .endpoints import deliver
from .models import AlertPayload

logger = logging.getLogger(__name__)

DEAD_LETTER_PATH = Path(os.getenv("DEAD_LETTER_PATH", "/tmp/wms-dead-letter.jsonl"))

# REQ-WMS-026: CRITICAL alert deduplication window in seconds.
DEDUP_WINDOW_SECONDS = float(os.getenv("ALERT_DEDUP_WINDOW", "30"))


class AlertDispatcher:
    """
    Receives AnomalyEvent dicts from anomaly-engine, validates them,
    constructs AlertPayload objects, and dispatches to operator endpoints.

    CRITICAL alerts → ALERT_WEBHOOK_URLS (REQ-WMS-012)
    DEGRADED alerts → MONITOR_WEBHOOK_URLS
    NOMINAL  alerts → MONITOR_WEBHOOK_URLS (low priority)

    Duplicate CRITICAL alerts for the same sensor within DEDUP_WINDOW_SECONDS
    are suppressed and counted but never delivered (REQ-WMS-026).
    """

    def __init__(self) -> None:
        self._dispatched = 0
        self._suppressed = 0
        self._dead_lettered = 0
        self._health_degraded = False
        # Maps sensor_id → monotonic timestamp of last dispatched CRITICAL alert.
        self._last_critical: Dict[str, float] = {}

    def dispatch(self, event: Dict[str, Any]) -> Optional[AlertPayload]:
        try:
            payload = AlertPayload(
                event_id=event["event_id"],
                sensor_id=event["sensor_id"],
                severity=event["severity"],
                value=float(event["value"]),
                unit=event.get("unit", ""),
                timestamp=event["timestamp"],
                model_ver=event.get("model_ver", "unknown"),
                confidence=event.get("confidence"),
            )
        except (KeyError, ValueError) as exc:
            logger.error("Invalid event payload, cannot dispatch: %s — %s", exc, event)
            return None

        # REQ-WMS-026: suppress duplicate CRITICAL alerts within the dedup window.
        if payload.severity == "CRITICAL":
            last_ts = self._last_critical.get(payload.sensor_id)
            now = time.monotonic()
            if last_ts is not None and (now - last_ts) < DEDUP_WINDOW_SECONDS:
                self._suppressed += 1
                logger.info(
                    "CRITICAL alert suppressed for sensor %s (dedup window %.0fs, "
                    "%.1fs since last dispatch) — REQ-WMS-026",
                    payload.sensor_id,
                    DEDUP_WINDOW_SECONDS,
                    now - last_ts,
                )
                return payload
            self._last_critical[payload.sensor_id] = time.monotonic()

        payload_dict = payload.to_dict()
        results = deliver(payload_dict, payload.severity)

        if not all(results.values()):
            self._write_dead_letter(payload_dict)
            self._health_degraded = True

        self._dispatched += 1
        return payload

    def _write_dead_letter(self, payload: Dict[str, Any]) -> None:
        import json

        self._dead_lettered += 1
        with DEAD_LETTER_PATH.open("a") as f:
            f.write(json.dumps(payload) + "\n")
        logger.error("Event written to dead-letter log: %s", DEAD_LETTER_PATH)

    def stats(self) -> Dict[str, int]:
        """REQ-WMS-027: delivery counters for the /health/stats endpoint."""
        return {
            "dispatched": self._dispatched,
            "suppressed": self._suppressed,
            "dead_lettered": self._dead_lettered,
        }

    def health(self) -> Dict[str, Any]:
        if self._health_degraded:
            return {
                "status": "degraded",
                "reason": f"delivery failures ({self._dead_lettered} dead-lettered)",
            }
        return {"status": "ok", "dispatched": self._dispatched}
