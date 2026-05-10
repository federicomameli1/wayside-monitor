from __future__ import annotations

import pytest
from anomaly_engine.engine import AnomalyEngine
from anomaly_engine.models import Severity
from anomaly_engine.classifier import classify_vibration, classify_temperature


def _make_engine():
    events = []
    engine = AnomalyEngine(publish=lambda stream, event: events.append(event))
    return engine, events


def _sensor_event(sensor_type="TEMPERATURE", value=25.0, sensor_id="S-001"):
    return {
        "reading_id": "r-001",
        "sensor_id": sensor_id,
        "sensor_type": sensor_type,
        "value": value,
        "unit": "celsius",
        "timestamp": "2026-05-10T10:00:00+00:00",
    }


class TestTemperatureClassifier:
    def test_above_60_is_critical(self):
        """REQ-WMS-006: temperature >= 60°C must be CRITICAL."""
        severity, confidence = classify_temperature(65.0)
        assert severity == Severity.CRITICAL
        assert confidence == 1.0

    def test_below_threshold_is_nominal(self):
        severity, _ = classify_temperature(30.0)
        assert severity == Severity.NOMINAL

    def test_boundary_is_critical(self):
        severity, _ = classify_temperature(60.0)
        assert severity == Severity.CRITICAL


class TestVibrationClassifier:
    def test_three_classes_exist(self):
        """REQ-WMS-008: classifier must produce exactly NOMINAL, DEGRADED, CRITICAL."""
        results = {classify_vibration(v)[0] for v in [1.0, 3.5, 7.0]}
        assert results == {Severity.NOMINAL, Severity.DEGRADED, Severity.CRITICAL}

    def test_nominal_range(self):
        severity, confidence = classify_vibration(1.0)
        assert severity == Severity.NOMINAL
        assert 0.0 <= confidence <= 1.0

    def test_degraded_range(self):
        severity, _ = classify_vibration(3.5)
        assert severity == Severity.DEGRADED

    def test_critical_range(self):
        severity, confidence = classify_vibration(7.0)
        assert severity == Severity.CRITICAL
        assert confidence > 0.8

    def test_confidence_is_in_range(self):
        """REQ-WMS-010: confidence must be in [0.0, 1.0]."""
        for v in [-10.0, -2.0, 0.0, 1.5, 3.5, 6.0, 12.0]:
            _, conf = classify_vibration(v)
            assert 0.0 <= conf <= 1.0, f"confidence out of range for value={v}"


class TestAnomalyEngine:
    def test_temperature_event_published(self):
        engine, events = _make_engine()
        engine.process(_sensor_event("TEMPERATURE", 65.0))
        assert len(events) == 1
        assert events[0]["severity"] == "CRITICAL"

    def test_model_ver_present_in_output(self):
        """REQ-WMS-011: model_ver must be present in every emitted event."""
        engine, events = _make_engine()
        engine.process(_sensor_event("VIBRATION", 1.0))
        assert "model_ver" in events[0]
        assert events[0]["model_ver"]

    def test_confidence_present_in_output(self):
        """REQ-WMS-010: confidence score must be attached to every result."""
        engine, events = _make_engine()
        engine.process(_sensor_event("VIBRATION", 1.0))
        assert events[0]["confidence"] is not None

    def test_unknown_sensor_type_is_skipped(self):
        engine, events = _make_engine()
        result = engine.process({**_sensor_event(), "sensor_type": "UNKNOWN"})
        assert result is None
        assert len(events) == 0

    def test_health_ok_by_default(self):
        engine, _ = _make_engine()
        assert engine.health()["status"] == "ok"
