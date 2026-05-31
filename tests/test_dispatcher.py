from __future__ import annotations

import time
import pytest
from unittest.mock import patch
from alert_dispatcher.dispatcher import AlertDispatcher
from alert_dispatcher.models import AlertPayload, VALID_SEVERITIES


def _payload(**kwargs):
    defaults = {
        "event_id": "evt-001",
        "sensor_id": "S-001",
        "severity": "CRITICAL",
        "value": 65.0,
        "unit": "celsius",
        "timestamp": "2026-05-10T10:00:00+00:00",
        "model_ver": "vibration_model_v2.pkl",
        "confidence": 0.97,
    }
    return AlertPayload(**{**defaults, **kwargs})


class TestAlertPayload:
    def test_valid_severities_accepted(self):
        """REQ-WMS-013, REQ-WMS-008: only NOMINAL, DEGRADED, CRITICAL are valid."""
        for sev in ("NOMINAL", "DEGRADED", "CRITICAL"):
            p = _payload(severity=sev)
            assert p.severity == sev

    def test_invalid_severity_raises(self):
        with pytest.raises(ValueError, match="Invalid severity"):
            _payload(severity="WARNING")

    def test_to_dict_contains_required_fields(self):
        """REQ-WMS-013: all required fields must be present in the payload."""
        required = {"event_id", "sensor_id", "severity", "value", "unit", "timestamp", "model_ver"}
        p = _payload()
        d = p.to_dict()
        assert required.issubset(d.keys())

    def test_confidence_forwarded(self):
        """REQ-WMS-010: confidence is passed through to outbound payload."""
        p = _payload(confidence=0.91)
        assert p.to_dict()["confidence"] == 0.91

    def test_schema_version_is_1_1(self):
        p = _payload()
        assert p.to_dict()["schema_version"] == "1.1"

    def test_valid_severities_set(self):
        assert VALID_SEVERITIES == frozenset({"NOMINAL", "DEGRADED", "CRITICAL"})


def _event(**kwargs):
    defaults = {
        "event_id": "evt-001",
        "sensor_id": "S-001",
        "severity": "CRITICAL",
        "value": 65.0,
        "unit": "celsius",
        "timestamp": "2026-05-10T10:00:00+00:00",
        "model_ver": "vibration_model_v2.pkl",
        "confidence": 0.97,
    }
    return {**defaults, **kwargs}


class TestAlertDeduplication:
    """REQ-WMS-026: CRITICAL alert storm prevention."""

    def _make_dispatcher(self):
        d = AlertDispatcher()
        # Stub deliver so no real HTTP calls are made.
        with patch("alert_dispatcher.dispatcher.deliver", return_value={"test": True}):
            yield d

    def test_first_critical_is_dispatched(self):
        dispatcher = AlertDispatcher()
        with patch("alert_dispatcher.dispatcher.deliver", return_value={"test": True}):
            result = dispatcher.dispatch(_event())
        assert result is not None
        assert dispatcher.stats()["dispatched"] == 1
        assert dispatcher.stats()["suppressed"] == 0

    def test_second_critical_within_window_is_suppressed(self):
        dispatcher = AlertDispatcher()
        with patch("alert_dispatcher.dispatcher.deliver", return_value={"test": True}):
            dispatcher.dispatch(_event(event_id="e1"))
            dispatcher.dispatch(_event(event_id="e2"))
        stats = dispatcher.stats()
        assert stats["dispatched"] == 1
        assert stats["suppressed"] == 1

    def test_multiple_suppressed_within_window(self):
        dispatcher = AlertDispatcher()
        with patch("alert_dispatcher.dispatcher.deliver", return_value={"test": True}):
            for i in range(5):
                dispatcher.dispatch(_event(event_id=f"e{i}"))
        stats = dispatcher.stats()
        assert stats["dispatched"] == 1
        assert stats["suppressed"] == 4

    def test_different_sensor_not_suppressed(self):
        """REQ-WMS-026: dedup is per sensor_id — different sensors are independent."""
        dispatcher = AlertDispatcher()
        with patch("alert_dispatcher.dispatcher.deliver", return_value={"test": True}):
            dispatcher.dispatch(_event(sensor_id="S-001"))
            dispatcher.dispatch(_event(sensor_id="S-002"))
        stats = dispatcher.stats()
        assert stats["dispatched"] == 2
        assert stats["suppressed"] == 0

    def test_critical_after_window_expires_is_dispatched(self):
        dispatcher = AlertDispatcher()
        with patch("alert_dispatcher.dispatcher.deliver", return_value={"test": True}):
            dispatcher.dispatch(_event(event_id="e1"))
            # Manually expire the window by backdating the last dispatch time.
            dispatcher._last_critical["S-001"] -= 31.0
            dispatcher.dispatch(_event(event_id="e2"))
        stats = dispatcher.stats()
        assert stats["dispatched"] == 2
        assert stats["suppressed"] == 0

    def test_non_critical_alerts_never_suppressed(self):
        """REQ-WMS-026 applies only to CRITICAL — DEGRADED/NOMINAL always pass through."""
        dispatcher = AlertDispatcher()
        with patch("alert_dispatcher.dispatcher.deliver", return_value={"test": True}):
            for i in range(3):
                dispatcher.dispatch(_event(severity="DEGRADED", event_id=f"e{i}"))
        stats = dispatcher.stats()
        assert stats["dispatched"] == 3
        assert stats["suppressed"] == 0

    def test_stats_returns_all_counters(self):
        """REQ-WMS-027: stats() exposes dispatched, suppressed, dead_lettered."""
        dispatcher = AlertDispatcher()
        stats = dispatcher.stats()
        assert set(stats.keys()) == {"dispatched", "suppressed", "dead_lettered"}
