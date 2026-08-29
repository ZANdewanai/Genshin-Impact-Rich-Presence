"""Single source of live configuration (GUI <-> engine).

All user-changeable settings live in shared_config.json. This module is the
ONE implementation of the read: repeated callers do one stat() per call and
only a full json.parse when the file's mtime actually changes, so reading a
setting every tick/scan is effectively free.

CONFIG.py remains a read-only defaults file (coordinates, app id, window
names); it is never written to or mutated at runtime.

Default resolution order for every setting:
    shared_config.json  ->  CONFIG.py default  ->  hardcoded fallback
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


def get_setting(key: str, config_default, fallback=None):
    """Read one setting with the standard resolution order.

    shared_config.json wins; if the key is absent, `config_default` (usually
    a CONFIG.py attribute) is used; `fallback` covers CONFIG.py missing too.
    """
    shared = get_shared_config()
    if key in shared:
        return shared[key]
    if config_default is not None:
        return config_default
    return fallback