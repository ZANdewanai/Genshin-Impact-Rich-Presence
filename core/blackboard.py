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


def write_json(path: str, payload: dict) -> None:
    """Atomically write `payload` with an injected server timestamp."""
    payload = dict(payload)
    payload["written_at"] = time.time()
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(payload, f)
        os.replace(tmp, str(p))
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
