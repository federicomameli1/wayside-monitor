from __future__ import annotations

import pytest
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
