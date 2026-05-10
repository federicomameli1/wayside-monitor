from __future__ import annotations

import pytest
from sensor_collector.collector import SensorCollector
from sensor_collector.registry import SensorRegistry


def _make_collector():
    published = []
    registry = SensorRegistry()
    collector = SensorCollector(registry=registry, publish=lambda stream, event: published.append(event))
    return collector, published


def _raw(sensor_type="TEMPERATURE", value=25.0, sensor_id="S-001"):
    return {"sensor_id": sensor_id, "sensor_type": sensor_type, "value": value}


class TestSensorRegistry:
    def test_known_types_are_valid(self):
        r = SensorRegistry()
        for t in ("TEMPERATURE", "VIBRATION", "RAIL_WEAR", "CURRENT"):
            assert r.is_known(t)

    def test_unknown_type_is_invalid(self):
        r = SensorRegistry()
        assert not r.is_known("UNKNOWN_XR7")


class TestSensorCollector:
    def test_valid_reading_is_forwarded(self):
        collector, published = _make_collector()
        result = collector.ingest(_raw("TEMPERATURE", 30.0))
        assert result is not None
        assert len(published) == 1
        assert published[0]["sensor_type"] == "TEMPERATURE"

    def test_unknown_sensor_type_is_dropped(self):
        """REQ-WMS-002: unknown types must be dropped and not forwarded."""
        collector, published = _make_collector()
        result = collector.ingest(_raw("UNKNOWN_XR7", 1.0))
        assert result is None
        assert len(published) == 0

    def test_stats_track_dropped_readings(self):
        collector, _ = _make_collector()
        collector.ingest(_raw("TEMPERATURE", 20.0))
        collector.ingest(_raw("UNKNOWN_XR7", 1.0))
        stats = collector.stats()
        assert stats["accepted"] == 1
        assert stats["dropped"] == 1

    def test_health_returns_ok(self):
        collector, _ = _make_collector()
        assert collector.health()["status"] == "ok"

    def test_output_event_schema_version(self):
        collector, published = _make_collector()
        collector.ingest(_raw("VIBRATION", 1.5))
        assert published[0]["schema_version"] == "1.2"
