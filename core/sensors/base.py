"""Independent detector workers ("sensors").

Each sensor runs its own loop, grabs the client area once per scan and crops
its own regions from that shared frame, skips OCR
when a region is pixel-identical to the previous scan, and publishes its
findings to its own JSON file on the blackboard. Sensors never block each
other; the coordinator (main) consumes the JSON files.

Threading note: ONNX inference releases the GIL, so threads genuinely run in
parallel for OCR work while staying far simpler than multiprocessing.
"""

import threading
import time

import numpy as np
from PIL import Image, ImageGrab

from core.datatypes import DEBUG_MODE
from core.log_utils import log, record_ocr

# Location labels are rendered in pure white; anything dimmer or tinted is
# world/UI noise that OCR turns into garble. Keep only near-white pixels.
WHITE_MIN_CHANNEL = 240


def _white_mask(crop, scale):
    """Return a grayscale array keeping only bright white pixels."""
    rgb = crop.convert("RGB")
    if scale != 1.0:
        rgb = rgb.resize(
            (max(1, int(rgb.width * scale)), max(1, int(rgb.height * scale))),
            Image.LANCZOS,
        )
    arr = np.asarray(rgb)
    rgb.close()
    keep = (
        (arr[:, :, 0] >= WHITE_MIN_CHANNEL)
        & (arr[:, :, 1] >= WHITE_MIN_CHANNEL)
        & (arr[:, :, 2] >= WHITE_MIN_CHANNEL)
    )
    return (keep * 255).astype(np.uint8)


class ScreenFrame:
    """One client-area grab shared by every region crop in a sensor scan.

    ``image`` is the grabbed Genshin client area and ``origin`` its absolute
    screen coordinate. ``crop(bbox)`` takes absolute screen coords; PIL pads
    out-of-bounds edges with black, so the returned crop's top-left always
    corresponds to ``bbox[:2]`` even when a region hangs off the client.
    """

    __slots__ = ("image", "origin")

    def __init__(self, image, origin):
        self.image = image
        self.origin = origin

    def crop(self, bbox):
        ox, oy = self.origin
        return self.image.crop(
            (bbox[0] - ox, bbox[1] - oy, bbox[2] - ox, bbox[3] - oy)
        )


def grab_screen_frame():
    """Grab the whole Genshin client area once for a sensor scan.

    Returns a ScreenFrame, or None when the window/rect can't be resolved -
    callers then fall back to per-region ImageGrab grabs.
    """
    from core import ps_helper
    rect = ps_helper.get_genshin_client_rect()
    if not rect:
        return None
    left, top, w, h = rect
    if w <= 0 or h <= 0:
        return None
    image = ImageGrab.grab(bbox=(left, top, left + w, top + h))
    return ScreenFrame(image, (left, top))


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
                self._frame = self._grab_frame()
            except Exception:
                self._frame = None
            try:
                self.scan()
            except Exception as e:
                if DEBUG_MODE:
                    log(f"[{self.name}] scan error: {e}")
            finally:
                self._frame = None
            elapsed = time.perf_counter() - start
            self.stop_event.wait(max(0.05, self.interval - elapsed))

    def _prep(self, crop, scale=0.5, white_only=False):
        if white_only:
            return _white_mask(crop, scale)
        gray = crop.convert("L")
        if scale == 1.0:
            arr = np.array(gray)
            gray.close()
            return arr
        small = gray.resize(
            (max(1, int(gray.width * scale)), max(1, int(gray.height * scale))),
            Image.LANCZOS,
        )
        arr = np.array(small)
        gray.close()
        small.close()
        return arr

    @staticmethod
    def _results_text(results, conf, spatial=False):
        items = [r for r in results if r[2] > conf]
        if spatial:
            items = sorted(
                items,
                key=lambda r: (
                    min(p[1] for p in r[0]), min(p[0] for p in r[0])
                ),
            )
        return " ".join(r[1].strip() for r in items).strip()

    def _read_ocr(self, key, image, allowlist=None, priority=False):
        t0 = time.perf_counter()
        try:
            results = self.reader.readtext(
                image, allowlist=allowlist, priority=priority
            )
        except Exception:
            results = []
        record_ocr(key.upper(), (time.perf_counter() - t0) * 1000.0)
        return results

    def _grab_frame(self):
        """Frame source for this scan; override to opt out (e.g. static images)."""
        return grab_screen_frame()

    def _grab_region(self, bbox):
        """Crop a screen region, preferring the shared per-scan frame."""
        frame = getattr(self, "_frame", None)
        if frame is not None:
            return frame.crop(bbox)
        return ImageGrab.grab(bbox=bbox)

    def _ocr_text(self, key, bbox, allowlist=None, conf=0.5, priority=False,
                  empty_retry=0.0, match=None, retry_scales=(),
                  retry_conf=None, white_only=False):
        """OCR a region with unchanged-pixel skip. Returns text ('' if none).

        ``priority=True`` queues ahead of normal OCR waiters so fast sensors
        (location/menu) are not starved behind CharSensor's party sweep.
        ``empty_retry`` re-runs OCR after that many seconds when the cached
        result is empty, so a transient miss on a static region self-heals.
        ``match`` is an optional predicate used to retry the SAME captured
        crop with ``retry_conf`` and/or alternate ``retry_scales`` before the
        frame is discarded - important for fast-disappearing text.
        """
        crop = self._grab_region(bbox)
        try:
            if not hasattr(self, "_cache"):
                self._cache = {}
            cur = self._prep(crop, white_only=white_only)
            cache = self._cache.get(key, {})
            if _looks_same(cache.get("fp"), cache.get("sample"), cur):
                cached_text = cache.get("text", "")
                if (
                    cached_text
                    or not empty_retry
                    or (time.time() - cache.get("ts", 0.0)) < empty_retry
                ):
                    return cached_text

            results = self._read_ocr(
                key, cur, allowlist=allowlist, priority=priority
            )
            text = self._results_text(results, conf)
            matched = match is None or bool(text and match(text))

            if match is not None and not matched:
                def _accept(candidate):
                    nonlocal text, matched
                    if not matched and candidate and match(candidate):
                        text = candidate
                        matched = True

                _accept(self._results_text(results, conf, spatial=True))
                if retry_conf is not None and retry_conf < conf:
                    _accept(self._results_text(results, retry_conf))
                    _accept(self._results_text(results, retry_conf, spatial=True))
                for scale in retry_scales:
                    if matched:
                        break
                    if scale == 0.5:
                        continue
                    alt = self._prep(crop, scale=scale, white_only=white_only)
                    alt_results = self._read_ocr(
                        key, alt, allowlist=allowlist, priority=priority
                    )
                    _accept(self._results_text(alt_results, conf))
                    _accept(self._results_text(alt_results, conf, spatial=True))
                    if retry_conf is not None and retry_conf < conf:
                        _accept(self._results_text(alt_results, retry_conf))
                        _accept(
                            self._results_text(alt_results, retry_conf, spatial=True)
                        )

            self._cache[key] = {
                "fp": cur, "sample": cur.ravel()[::4], "text": text,
                "ts": time.time(),
            }
            return text
        finally:
            crop.close()

