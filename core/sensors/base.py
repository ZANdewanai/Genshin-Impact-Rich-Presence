"""Independent detector workers ("sensors").

Each sensor runs its own loop, grabs only its own screen regions, skips OCR
when a region is pixel-identical to the previous scan, and publishes its
findings to its own JSON file on the blackboard. Sensors never block each
other; the coordinator (main) consumes the JSON files.

Threading note: ONNX inference releases the GIL, so threads genuinely run in
parallel for OCR work while staying far simpler than multiprocessing.
"""

import threading
import time

import numpy as np
from PIL import ImageGrab

from core.datatypes import DEBUG_MODE
from core.log_utils import log, record_ocr



def _looks_same(prev_fp, prev_sample, cur) -> bool:
    """True if current grayscale crop is ~identical to the previous one."""
    if prev_fp is None or prev_fp.shape != cur.shape:
        return False
    diff = np.abs(
        cur.ravel()[::4].astype(np.int16) - prev_sample.astype(np.int16)
    ).mean()
    return diff <= 6.0  # tolerance for compression/dithering noise



class BaseSensor(threading.Thread):
    """Common loop scaffolding: interval, stop event, JSON publication."""

    def __init__(self, name: str, output_path: str, interval: float):
        super().__init__(name=name, daemon=True)
        self.output_path = output_path
        self.interval = interval
        self.stop_event = threading.Event()

    def stop(self) -> None:
        self.stop_event.set()

    def run(self) -> None:
        log(f"[{self.name}] started (interval={self.interval}s)")
        was_paused = False
        while not self.stop_event.is_set():
            start = time.perf_counter()
            # Skip scanning entirely while Genshin isn't in the foreground
            try:
                from core import ps_helper
                focused = ps_helper.check_genshin_is_foreground()
            except Exception:
                focused = True
            if not focused:
                if not was_paused:
                    log(f"[{self.name}] paused (game unfocused)")
                    was_paused = True
                self.stop_event.wait(1.0)
                continue
            if was_paused:
                log(f"[{self.name}] resumed")
                was_paused = False
            try:
                self.scan()
            except Exception as e:
                if DEBUG_MODE:
                    log(f"[{self.name}] scan error: {e}")
            elapsed = time.perf_counter() - start
            self.stop_event.wait(max(0.05, self.interval - elapsed))

    def _prep(self, crop):
        gray = crop.convert("L")
        small = gray.resize(
            (max(1, int(gray.width * 0.5)), max(1, int(gray.height * 0.5)))
        )
        return np.array(small)

    def _ocr_text(self, key, bbox, allowlist=None, conf=0.5):
        """OCR a region with unchanged-pixel skip. Returns text ('' if none)."""
        crop = ImageGrab.grab(bbox=bbox)
        cur = self._prep(crop)
        crop.close()
        cache = getattr(self, "_cache", {}).get(key, {})
        if _looks_same(cache.get("fp"), cache.get("sample"), cur):
            return cache.get("text", "")
        t0 = time.perf_counter()
        try:
            results = self.reader.readtext(cur, allowlist=allowlist)
        except Exception:
            results = []
        record_ocr(key.upper(), (time.perf_counter() - t0) * 1000.0)
        text = " ".join(r[1].strip() for r in results if r[2] > conf).strip()
        self._cache[key] = {
            "fp": cur, "sample": cur.ravel()[::4], "text": text
        }
        return text

