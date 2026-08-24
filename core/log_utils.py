"""Timestamped, throttle-aware console logging + lightweight perf counters."""

import threading
import time

_throttle_cache: dict[str, float] = {}

# Per-region OCR performance counters: key -> {"ms": total_ms, "n": calls}
_ocr_stats: dict[str, dict[str, float]] = {}
_stats_lock = threading.Lock()


def record_ocr(key: str, elapsed_ms: float) -> None:
    """Accumulate one OCR call's duration under the given region key."""
    with _stats_lock:
        entry = _ocr_stats.setdefault(key, {"ms": 0.0, "n": 0})
        entry["ms"] += elapsed_ms
        entry["n"] += 1


def format_and_reset_ocr_stats() -> str:
    """Return 'key=avgms(n)' summary of accumulated stats and reset them.

    Called periodically (heartbeat) so each report covers exactly the
    interval since the last one.
    """
    with _stats_lock:
        if not _ocr_stats:
            return ""
        parts = []
        for key, entry in sorted(_ocr_stats.items()):
            n = int(entry["n"])
            avg = entry["ms"] / n if n else 0.0
            parts.append(f"{key}={avg:.0f}ms({n})")
        _ocr_stats.clear()
        return " ".join(parts)


def ts() -> str:
    """Current time as [HH:MM:SS] for log prefixes."""
    return time.strftime("[%H:%M:%S]")


def log(msg: str) -> None:
    """Print a message with a timestamp prefix."""
    print(f"{ts()} {msg}")


def should_log(key: str, interval: float) -> bool:
    """Return True at most once per `interval` seconds for the given key."""
    now = time.time()
    last = _throttle_cache.get(key, 0.0)
    if now - last >= interval:
        _throttle_cache[key] = now
        return True
    return False

