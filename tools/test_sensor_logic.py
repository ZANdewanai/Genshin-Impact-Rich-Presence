"""Smoke test for the new CharSensor logic (history-gated ordinal fallback,
active-hint debounce window). Runs with stubbed deps under the system Python;
the real app uses the embedded interpreter which has watchdog installed."""
import sys, types
sys.path.insert(0, '.')

# Stub third-party modules missing from the system interpreter
for name in ["watchdog", "watchdog.observers", "watchdog.events"]:
    sys.modules.setdefault(name, types.ModuleType(name))
sys.modules["watchdog"].observers = sys.modules["watchdog.observers"]
sys.modules["watchdog"].events = sys.modules["watchdog.events"]
class _O:  # minimal Observer stand-in
    def schedule(self, *a, **k): return None
    def start(self): pass
    def stop(self): pass
    def join(self, *a): pass
    def unschedule_all(self): pass
sys.modules["watchdog.observers"].Observer = _O
_ev = sys.modules["watchdog.events"]
_ev.FileSystemEventHandler = object
_ev.PatternMatchingEventHandler = object
_ev.FileModifiedEvent = object

from core.sensors import CharSensor

# --- history-gated ordinal fallback -----------------------------------------
s = CharSensor.__new__(CharSensor)
s._name_ordinal_history = []
assert s._history_ordinal('Hu Tao') is None          # no history -> box index
s._name_ordinal_history.append({'Hu Tao': 2})
assert s._history_ordinal('Hu Tao') == 2             # ONE observation is trusted
s._name_ordinal_history.append({'Hu Tao': 1})
assert s._history_ordinal('Hu Tao') == 1             # most recent wins
print('HISTORY FALLBACK LOGIC OK')

# --- active-hint debounce window --------------------------------------------
# Replicates the Phase-4 window logic to verify its decision semantics.
def run_window(hints, required=CharSensor.HINT_WINDOW_REQUIRED,
               window=CharSensor.HINT_WINDOW_MAX):
    hint_win, confirmed = [], None
    for h in hints:
        prev_confirmed = confirmed
        confirmed = prev_confirmed
        hint_win.append(h)
        if len(hint_win) > window:
            hint_win = hint_win[-window:]
        recent = [x for x in hint_win if x is not None]
        if recent:
            def _rank(c):
                return (recent.count(c), max(
                    i for i, h in enumerate(hint_win) if h == c
                ))
            best = max(set(recent), key=_rank)
            if recent.count(best) >= required:
                confirmed = best
    return confirmed

# Two consecutive -> confirms (same as old rule)
assert run_window([0, 0]) == 0
# Alternating flicker -> deterministic: tie on count (2-2), most recent wins
assert run_window([0, 1, 0, 1]) == 1
assert run_window([1, 0, 1, 0]) == 0
# Single-scan miss between two same hints still confirms (old: deadlock risk)
assert run_window([2, None, 2]) == 2
# Majority beats recency: 0 seen 3x vs 1 seen once
assert run_window([0, 0, 1, 0]) == 0
print('DEBOUNCE WINDOW LOGIC OK')
# --- per-slot sweep staggering (round-robin) ---------------------------------
s = CharSensor.__new__(CharSensor)
s._sweep_cursor = 0
SWEEPS = CharSensor.SWEEPS_PER_ROUND
def next_sweeps(missing):
    n = min(SWEEPS, len(missing))
    picks = [missing[(s._sweep_cursor + k) % len(missing)] for k in range(n)]
    s._sweep_cursor = (s._sweep_cursor + n) % max(1, len(missing))
    return picks

# All 6 slots missing: rounds cover 0-1, then 2-3, then 4-5, then wraps to 0-1
assert next_sweeps([0,1,2,3,4,5]) == [0,1]
assert next_sweeps([0,1,2,3,4,5]) == [2,3]
assert next_sweeps([0,1,2,3,4,5]) == [4,5]
assert next_sweeps([0,1,2,3,4,5]) == [0,1]
# One slot missing: swept every round
assert next_sweeps([2]) == [2]
assert next_sweeps([2]) == [2]
print('SWEEP STAGGERING OK')

# --- OCR non-blocking path releases its lock (regression) ---------------------
# Previously readtext(wait=False) acquired ocr_lock, never ran inference and
# never released - deadlocking every other sensor after one location read.
import threading
import core.state as _state
import core.ocr_engine as _oe

_calls = {"n": 0}
def _fake_reader(img):
    _calls["n"] += 1
    # Mimic RapidOCR's (detections, timings) return shape
    return ([([0, 0, 1, 1], "x", "0.99")], None)

class _FakeLock:
    """Threading.Lock stand-in that tracks hold count."""
    def __init__(self):
        self._l = threading.Lock()
        self.holds = 0
    def acquire(self, timeout=None):
        ok = self._l.acquire(timeout=timeout) if timeout is not None else self._l.acquire()
        if ok:
            self.holds += 1
        return ok
    def release(self):
        assert self.holds > 0, "release without acquire"
        self.holds -= 1
        self._l.release()
    def __enter__(self):
        self.acquire()
        return self
    def __exit__(self, *a):
        self.release()

_reader = _oe.Reader.__new__(_oe.Reader)   # skip GPU validation for this test
_reader.reader = _fake_reader
_state.ocr_lock = _FakeLock()

r1 = _reader.readtext("img", wait=False)
assert r1 and r1[0][1] == "x", "non-wait read must run inference"
assert _state.ocr_lock.holds == 0, f"lock leaked! holds={_state.ocr_lock.holds}"

r2 = _reader.readtext("img")               # blocking path still works
assert r2 and _state.ocr_lock.holds == 0

# Busy lock -> TimeoutError, no acquisition leak
_state.ocr_lock._l.acquire()               # someone else holds it
_state.ocr_lock.holds += 1                 # keep the fake's bookkeeping honest
try:
    _reader.readtext("img", allowlist="x", wait=False)
    raise SystemExit("expected TimeoutError")
except TimeoutError:
    pass
finally:
    _state.ocr_lock.release()
print('OCR LOCK DISCIPLINE OK')



# --- constants sanity --------------------------------------------------------
assert CharSensor.HINT_WINDOW_REQUIRED == 2 and CharSensor.HINT_WINDOW_MAX == 4
assert CharSensor.ACTIVE_BRIGHTNESS_MARGIN > 0
print('CONSTANTS OK')
