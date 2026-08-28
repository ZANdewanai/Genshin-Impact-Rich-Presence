"""Atomic JSON blackboard for inter-component state exchange.

Each writer owns exactly one file; readers apply staleness checks based on
the embedded timestamp. Files are written atomically (temp + rename) so a
reader never sees a partial write.
"""

import json
import os
import tempfile
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Single source of truth for sensor cadences and blackboard freshness windows.
#
# Every staleness limit is expressed as a multiple of the producing sensor's
# interval, so tuning one interval here automatically keeps all consumers in
# sync (previously these constants were scattered across coordinator.py,
# sensors.py and character_detection.py with unrelated magic numbers).
# ---------------------------------------------------------------------------

# Producer intervals (seconds). Must match the intervals passed to each
# Sensor class constructor in core/coordinator.py.
CHAR_SCAN_INTERVAL = 2.0      # CharSensor
LOCATION_SCAN_INTERVAL = 0.5  # LocationSensor
MENU_SCAN_INTERVAL = 2.0      # MenuSensor

# Consumer freshness windows (values preserve the previously-scattered
# hardcoded limits, now expressed relative to their producer's interval).
CHAR_MAX_AGE_COORDINATOR = 5 * CHAR_SCAN_INTERVAL        # party-slot consumption: 10s
CHAR_MAX_AGE_HUD = 3 * CHAR_SCAN_INTERVAL                # HUD-evidence freshness: 6s
CHAR_MAX_AGE_REGION_MANAGER = 2.5 * CHAR_SCAN_INTERVAL   # detect_occupied_slots: 5s
LOCATION_MAX_AGE = 30 * LOCATION_SCAN_INTERVAL           # location.json: 15s
MENU_MAX_AGE = 2 * MENU_SCAN_INTERVAL                    # menus.json: 4s


def write_json(path: str, payload: dict) -> None:
    """Atomically write `payload` with an injected server timestamp.

    os.replace can transiently fail with WinError 5 (Access denied) when a
    reader holds the destination open at that exact moment on Windows - retry
    briefly before giving up.
    """
    payload = dict(payload)
    payload["written_at"] = time.time()
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(payload, f)
        last_err = None
        for _ in range(4):
            try:
                os.replace(tmp, str(p))
                return
            except OSError as e:
                last_err = e
                time.sleep(0.05)
        raise last_err
    except OSError:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise


def read_json(path: str, max_age: float | None = None) -> dict | None:
    """Read a blackboard file. Returns None if missing/corrupt/too stale."""
    try:
        with open(path, "r") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    if max_age is not None:
        written = data.get("written_at", 0.0)
        if time.time() - written > max_age:
            return None
    return data
