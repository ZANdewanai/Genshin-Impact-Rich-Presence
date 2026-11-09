"""In-memory blackboard for inter-component state exchange.

Replaces file-based JSON blackboard with thread-safe shared state.
"""

import time
import threading
from dataclasses import dataclass, field
from typing import Any, Optional


# Producer intervals (seconds). Must match the intervals passed to each
# Sensor class constructor in core/coordinator.py.
CHAR_SCAN_INTERVAL = 2.0      # CharSensor
LOCATION_SCAN_INTERVAL = 0.5  # LocationSensor
MENU_SCAN_INTERVAL = 2.0      # MenuSensor

# Consumer freshness windows (multiples of producer interval).
CHAR_MAX_AGE_COORDINATOR = 5 * CHAR_SCAN_INTERVAL        # party-slot consumption: 10s
CHAR_MAX_AGE_HUD = 3 * CHAR_SCAN_INTERVAL                # HUD-evidence freshness: 6s
CHAR_MAX_AGE_REGION_MANAGER = 2.5 * CHAR_SCAN_INTERVAL   # detect_occupied_slots: 5s
LOCATION_MAX_AGE = 30 * LOCATION_SCAN_INTERVAL           # location.json: 15s
MENU_MAX_AGE = 2 * MENU_SCAN_INTERVAL                    # menus.json: 4s


@dataclass
class BlackboardEntry:
    """A single blackboard entry with timestamp."""
    data: dict = field(default_factory=dict)
    written_at: float = 0.0

    def is_fresh(self, max_age: float) -> bool:
        return self.written_at > 0 and (time.time() - self.written_at) <= max_age

    def get(self, max_age: Optional[float] = None) -> Optional[dict]:
        if max_age is not None and not self.is_fresh(max_age):
            return None
        return self.data if self.written_at > 0 else None


class Blackboard:
    """Thread-safe in-memory blackboard with dynamic channels."""

    def __init__(self):
        self._lock = threading.Lock()
        self._entries = {}

    def _get_entry(self, key: str) -> BlackboardEntry:
        if key not in self._entries:
            self._entries[key] = BlackboardEntry()
        return self._entries[key]

    def write(self, key: str, payload: dict) -> None:
        """Write payload to a channel with current timestamp."""
        with self._lock:
            entry = self._get_entry(key)
            entry.data = dict(payload)
            entry.written_at = time.time()

    def read(self, key: str, max_age: Optional[float] = None) -> Optional[dict]:
        """Read payload from a channel, returning None if stale or empty."""
        with self._lock:
            entry = self._get_entry(key)
            data = entry.get(max_age)
            if data is None:
                return None
            return {**data, "written_at": entry.written_at}

    def clear(self, key: str) -> None:
        """Clear a channel."""
        with self._lock:
            if key in self._entries:
                self._entries[key] = BlackboardEntry()


# Global blackboard instance
blackboard = Blackboard()