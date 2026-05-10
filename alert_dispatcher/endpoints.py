from __future__ import annotations

import json
import logging
import os
import time
import urllib.request
from typing import Any, Dict, List
from urllib.error import URLError

logger = logging.getLogger(__name__)

_WEBHOOK_URLS: List[str] = [
    u for u in os.getenv("ALERT_WEBHOOK_URLS", "").split(",") if u.strip()
]
_MONITOR_WEBHOOK_URLS: List[str] = [
    u for u in os.getenv("MONITOR_WEBHOOK_URLS", "").split(",") if u.strip()
]

_MAX_RETRIES = 3
_BACKOFF_BASE = 0.5  # seconds


def _post(url: str, payload: Dict[str, Any]) -> bool:
    body = json.dumps(payload).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status < 400
    except (URLError, OSError) as exc:
        logger.warning("Delivery failed to %s: %s", url, exc)
        return False


def deliver(payload: Dict[str, Any], severity: str) -> Dict[str, Any]:
    """
    Deliver payload to the appropriate endpoint group with exponential
    back-off retry (REQ-WMS-014). Returns a delivery report.
    """
    targets = _WEBHOOK_URLS if severity == "CRITICAL" else _MONITOR_WEBHOOK_URLS
    results = {}

    for url in targets:
        success = False
        for attempt in range(1, _MAX_RETRIES + 1):
            if _post(url, payload):
                success = True
                logger.info("Delivered to %s (attempt %d)", url, attempt)
                break
            wait = _BACKOFF_BASE * (2 ** (attempt - 1))
            logger.warning("Retry %d/%d for %s in %.1fs", attempt, _MAX_RETRIES, url, wait)
            time.sleep(wait)

        if not success:
            logger.error("All %d attempts failed for %s — writing dead-letter", _MAX_RETRIES, url)
        results[url] = success

    return results
