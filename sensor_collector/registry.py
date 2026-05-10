from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Set

logger = logging.getLogger(__name__)

_KNOWN_UNITS: Dict[str, str] = {
    "TEMPERATURE": "celsius",
    "VIBRATION": "m/s2",
    "RAIL_WEAR": "mm",
    "CURRENT": "A",
}


class SensorRegistry:
    """Maintains the set of known sensor types and their expected units."""

    def __init__(self, config_path: Optional[Path] = None) -> None:
        self._types: Dict[str, str] = dict(_KNOWN_UNITS)
        if config_path and config_path.exists():
            self._load(config_path)

    def _load(self, path: Path) -> None:
        with path.open() as f:
            overrides = json.load(f)
        self._types.update(overrides.get("sensor_types", {}))
        logger.info("Sensor registry loaded from %s (%d types)", path, len(self._types))

    def reload(self, config_path: Path) -> None:
        self._load(config_path)

    def is_known(self, sensor_type: str) -> bool:
        return sensor_type in self._types

    def unit_for(self, sensor_type: str) -> Optional[str]:
        return self._types.get(sensor_type)

    @property
    def known_types(self) -> Set[str]:
        return set(self._types)
