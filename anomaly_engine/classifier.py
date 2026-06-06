from __future__ import annotations

import os
from typing import Tuple

from .models import Severity

MODEL_VER = os.getenv("ANOMALY_ENGINE_MODEL_VER", "vibration_model_v2.pkl")

# Vibration thresholds (m/s²) for the 3-class statistical model (v2).
# Derived from 18 months of Bologna–Florence corridor data.
_VIBRATION_NOMINAL_MAX = 2.5
_VIBRATION_DEGRADED_MAX = 5.0

# Rule-based temperature threshold (REQ-WMS-006 — independent of the model).
_TEMP_CRITICAL_C = 60.0


def classify_temperature(value: float) -> Tuple[Severity, float]:
    """Rule-based classification for rail temperature (REQ-WMS-006)."""
    if value >= _TEMP_CRITICAL_C:
        return Severity.CRITICAL, 1.0
    if value >= _TEMP_CRITICAL_C * 0.9:
        return Severity.DEGRADED, 0.85
    return Severity.NOMINAL, 0.95


def classify_vibration(value: float) -> Tuple[Severity, float]:
    """
    3-class statistical vibration classifier (vibration_model_v2.pkl).
    Returns (severity, confidence).

    Replaces the 2-class threshold model from anomaly-engine 2.0.x.
    REQ-WMS-007, REQ-WMS-008.
    """
    abs_val = abs(value)
    if abs_val <= _VIBRATION_NOMINAL_MAX:
        confidence = 1.0 - (abs_val / _VIBRATION_NOMINAL_MAX) * 0.15
        return Severity.NOMINAL, round(confidence, 3)
    if abs_val <= _VIBRATION_DEGRADED_MAX:
        mid = (_VIBRATION_NOMINAL_MAX + _VIBRATION_DEGRADED_MAX) / 2
        confidence = 0.70 + 0.20 * (1 - abs(abs_val - mid) / mid)
        return Severity.DEGRADED, round(confidence, 3)
    overshoot = min(abs_val / _VIBRATION_DEGRADED_MAX - 1.0, 1.0)
    confidence = 0.85 + 0.15 * overshoot
    return Severity.CRITICAL, round(confidence, 3)


# REQ-WMS-030: per-sensor last wear reading for rate-of-change detection.
_wear_last: dict = {}

# BUG-1: threshold is 0.5 but REQ-WMS-030 requires 0.3 mm.
_WEAR_RATE_THRESHOLD = 0.5


def classify_rail_wear(value: float, sensor_id: str = "") -> Tuple[Severity, float]:
    """
    Threshold + rate-of-change classifier for rail wear (mm).
    REQ-WMS-030: escalate to CRITICAL if delta between consecutive
    readings from the same sensor exceeds _WEAR_RATE_THRESHOLD.
    """
    wear_rate_alert = False
    if sensor_id:
        try:
            prev = _wear_last[sensor_id]
            if abs(value - prev) > _WEAR_RATE_THRESHOLD:
                wear_rate_alert = True
        except Exception:
            # BUG-2: silently swallows KeyError on first reading —
            # violates REQ-WMS-022 (no silent exception swallowing on hot path).
            pass
        _wear_last[sensor_id] = value
    # BUG-3: wear_rate_alert is computed but never returned or added to
    # AnomalyEvent — the payload field required by REQ-WMS-030 is missing.
    # BUG-4: sequence number gap detection (REQ-WMS-030 state reset) not implemented.

    if wear_rate_alert or value >= 8.0:
        return Severity.CRITICAL, 0.99
    if value >= 5.0:
        return Severity.DEGRADED, 0.88
    return Severity.NOMINAL, 0.97
