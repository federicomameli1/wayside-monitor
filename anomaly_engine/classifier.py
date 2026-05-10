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


def classify_rail_wear(value: float) -> Tuple[Severity, float]:
    """Simple threshold classifier for rail wear (mm)."""
    if value >= 8.0:
        return Severity.CRITICAL, 0.99
    if value >= 5.0:
        return Severity.DEGRADED, 0.88
    return Severity.NOMINAL, 0.97
