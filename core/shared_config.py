"""Runtime shared config (GUI <-> engine) with a single mtime-gated cache.

Many modules read shared_config.json every tick/scan (for USERNAME matching,
debug flags, static-image path...). This is the ONE implementation of the
read: repeated callers do one stat() per call and only a full json.parse
when the file's mtime actually changes.
"""
from pathlib import Path

import json

_SCRIPT_DIR = Path(__file__).resolve().parent.parent
SHARED_CONFIG_PATH = _SCRIPT_DIR / "shared_config.json"

# (mtime, dict) cache keyed on the file's mtime
_cache = None


def get_shared_config() -> dict:
    """Return the parsed shared_config dict, or {} if missing/unreadable."""
    global _cache
    try:
        mtime = SHARED_CONFIG_PATH.stat().st_mtime
    except OSError:
        _cache = None
        return {}
    if _cache is not None and _cache[0] == mtime:
        return _cache[1]
    try:
        with open(SHARED_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        cfg = {}
    _cache = (mtime, cfg)
    return cfg