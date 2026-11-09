"""Independent detector workers ("sensors").

Each sensor runs its own loop, grabs only its own screen regions, skips OCR
when a region is pixel-identical to the previous scan, and publishes its
findings to its own JSON file on the blackboard. Sensors never block each
other; the coordinator (main) consumes the JSON files.

Threading note: ONNX inference releases the GIL, so threads genuinely run in
parallel for OCR work while staying far simpler than multiprocessing.
"""

import time
import csv
from pathlib import Path

import numpy as np
import cv2
from PIL import Image, ImageGrab

from core import keys as K
from core.blackboard import blackboard, CHAR_MAX_AGE_HUD
from core.datatypes import DEBUG_MODE, DEBUG_CHARACTER_MODE
from core.log_utils import log, record_ocr
from core.search_index import SearchIndex
import CONFIG as app_config
from CONFIG import BASE_RESOLUTION_WIDTH, BASE_RESOLUTION_HEIGHT, BASE_PARTY_AREA


from .base import BaseSensor, _looks_same

# Debug image cache for visual inspection
_DEBUG_CACHE_DIR = Path(__file__).resolve().parent.parent.parent / "debug_cache"
_DEBUG_CACHE_DIR.mkdir(exist_ok=True)


class CharSensor(BaseSensor):
    """Party name detection using a single OCR pass over the entire party area.
    
    One bounding box covers the entire party list. Single OCR pass extracts
    all names, party size = count of matched names, slots assigned by 
    vertical order (top-to-bottom). Active character detected via white
    box highlight + triangle indicator.
    """

    def __init__(self, reader, data, search_index, output_key, interval=2.0):
        super().__init__("CharSensor", output_key, interval)
        self.reader = reader
        self.data = data
        self.search_index = search_index
        self._output_key = output_key
        self._last_party_size = None
        self._name_cache = []
        self._last_round_success = False
        self._debounce = {"candidate": None, "confirmed": None}
        self._empty_scans = 0
        self._static_img = None
        self._load_static_image()
        # Load the single party area bounding box
        self._party_area = self._load_party_area()
        # Load special UI text patterns
        self._special_ui = self._load_special_ui()

    def _load_special_ui(self):
        """Load special UI text patterns from CSV."""
        special = []
        try:
            with open("data/special_ui.csv", "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get("search_str", "").startswith("-----"):
                        continue
                    search_str = row.get("search_str", "").lower()
                    if search_str:
                        special.append({
                            "search_str": search_str,
                            "display_name": row.get("display_name", ""),
                            "activity_type": row.get("activity_type", ""),
                            "image_key": row.get("image_key", ""),
                        })
        except Exception as e:
            if DEBUG_MODE:
                log(f"[CharSensor] Failed to load special_ui.csv: {e}")
        return special

    def _load_party_area(self):
        """Load the single party area bounding box from CONFIG."""
        base_coords = BASE_PARTY_AREA
        actual_w, actual_h = self._display_size()
        scale_x = actual_w / BASE_RESOLUTION_WIDTH
        scale_y = actual_h / BASE_RESOLUTION_HEIGHT
        return (
            round(base_coords[0] * scale_x),
            round(base_coords[1] * scale_y),
            round(base_coords[2] * scale_x),
            round(base_coords[3] * scale_y),
        )

    def _load_static_image(self):
        """Load (or clear) the static debug image per DEBUG_STATIC_IMAGE flag."""
        try:
            from core.shared_config import get_shared_config
            shared = get_shared_config()
            try:
                import CONFIG as _cfg
                enabled = shared.get("DEBUG_STATIC_IMAGE", _cfg.DEBUG_STATIC_IMAGE)
                path = shared.get("DEBUG_STATIC_IMAGE_PATH", _cfg.DEBUG_STATIC_IMAGE_PATH)
            except ImportError:
                enabled = shared.get("DEBUG_STATIC_IMAGE", False)
                path = shared.get("DEBUG_STATIC_IMAGE_PATH", "")
            if enabled and path:
                p = Path(path)
                alt = Path(__file__).resolve().parent.parent.parent / path
                if p.is_file():
                    pass
                elif alt.is_file():
                    p = alt
                else:
                    p = None
                if p:
                    self._static_img = Image.open(p).convert("RGB")
                    log(f"[{self.name}] static-image debug mode: {p}")
                    return
        except Exception:
            pass
        self._static_img = None

    def reset_slot_cache(self):
        """Reset internal cache - called by coordinator on state transitions."""
        # New single-box sensor doesn't use per-slot cache, but keep for coordinator compatibility
        pass

    @staticmethod
    def _join_name_fragments(results):
        """Join confident OCR fragments top-to-bottom into one name string."""
        fragments = [
            r for r in results
            if r[2] > 0.6 and len(r[1].strip()) > 2
        ]
        fragments.sort(key=lambda r: r[0][0][1])
        return " ".join(r[1].strip() for r in fragments)

    def _split_and_search_names(self, text):
        """Split merged OCR text into candidate names and search each.
        Returns list of matched character dicts (may be empty)."""
        from core.shared_config import get_shared_config
        cfg = get_shared_config()
        custom = cfg.get("USERNAME")
        
        search_strs = []
        for char in self.search_index.data.characters:
            search_strs.append(char.search_str.lower())
            if " " in char.search_str:
                search_strs.append(char.search_str.lower().replace(" ", ""))
        if custom:
            search_strs.append(custom.lower())
            if " " in custom:
                search_strs.append(custom.lower().replace(" ", ""))
        
        search_strs.sort(key=len, reverse=True)
        
        text_lower = text.lower()
        matched = []
        used_positions = set()
        
        for search_str in search_strs:
            if search_str in text_lower:
                start = text_lower.index(search_str)
                end = start + len(search_str)
                overlap = any(not (end <= s or start >= e) for s, e in used_positions)
                if not overlap:
                    c = self.search_index.search_character(search_str)
                    if c:
                        matched.append({"name": c.character_display_name, "image_key": c.image_key})
                        used_positions.add((start, end))
        
        if len(matched) < 5:
            c = self.search_index.search_character(text)
            if c and not any(m["name"] == c.character_display_name for m in matched):
                matched.append({"name": c.character_display_name, "image_key": c.image_key})
        
        return matched

    def _match_character(self, text):
        from core.shared_config import get_shared_config
        cfg = get_shared_config()
        custom = cfg.get("USERNAME")
        if custom and text.strip().lower() == custom.strip().lower():
            traveler = "char_lumine" if cfg.get("MC_AETHER") is False else "char_aether"
            return {"name": custom.strip(), "image_key": traveler}
        c = self.search_index.search_character(text)
        if c is None:
            return None
        return {"name": c.character_display_name, "image_key": c.image_key}

    def _prep(self, img):
        """Preprocess image for OCR - simple grayscale conversion."""
        return np.array(img.convert("L"))

    def _grab(self, bbox):
        """Crop from the static debug image when set, else the live screen."""
        if self._static_img is not None:
            return self._static_img.crop(bbox)
        return ImageGrab.grab(bbox=bbox)

    def _bbox_to_tuple(self, bbox):
        """Convert OCR polygon bbox [[x1,y1],[x2,y1],[x2,y2],[x1,y2]] to (x1,y1,x2,y2)."""
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        return min(xs), min(ys), max(xs), max(ys)

    def _display_size(self):
        if self._static_img is not None:
            return self._static_img.size
        return getattr(
            app_config, "DETECTED_RESOLUTION", (BASE_RESOLUTION_WIDTH, BASE_RESOLUTION_HEIGHT)
        )

    def _ui_scale(self):
        width, height = self._display_size()
        return (
            width / BASE_RESOLUTION_WIDTH,
            height / BASE_RESOLUTION_HEIGHT,
        )

    def _marker_template(self):
        """Ideal left-pointing triangle (🞀) template, scaled to the UI."""
        tpl = getattr(self, "_marker_tpl", None)
        if tpl is not None:
            return tpl
        sx, sy = self._ui_scale()
        wt = max(8, int(round(14 * sx)))
        ht = max(12, int(round(26 * sy)))
        t = np.zeros((ht, wt), np.float32)
        for yy in range(ht):
            for xx in range(wt):
                if abs(yy - ht / 2) <= (ht / 2) * (xx / wt):
                    t[yy, xx] = 1.0
        tpl = cv2.GaussianBlur(t, (3, 3), 0)
        self._marker_tpl = tpl
        return tpl

    def _marker_candidate(self, bbox, label=""):
        x1, y1, x2, y2 = (int(round(v)) for v in bbox)
        screen_w, screen_h = self._display_size()
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(screen_w, x2), min(screen_h, y2)
        tpl = self._marker_template()
        th, tw = tpl.shape
        if x2 - x1 < tw or y2 - y1 < th:
            return 0.0, None

        crop = self._grab((x1, y1, x2, y2))
        try:
            if DEBUG_CHARACTER_MODE and label:
                ts = int(time.time() * 1000)
                crop.save(_DEBUG_CACHE_DIR / f"marker_scan_{ts}_{label}.png")
            arr = np.asarray(crop.convert("RGB"), dtype=np.float32)
        finally:
            crop.close()
        if arr.size == 0:
            return 0.0, None

        val = arr.mean(2)
        sat = arr.max(2) - arr.min(2)
        border = np.concatenate([val[0, :], val[-1, :], val[:, 0], val[:, -1]])
        bg = float(np.median(border)) if border.size else 0.0
        thr = max(135.0, min(190.0, bg + 55.0))
        roi = ((val > thr) & (sat < 50)).astype(np.float32)
        if not roi.any():
            return 0.0, None

        res = cv2.matchTemplate(roi, tpl, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(res)
        return float(max_val), (x1 + max_loc[0], y1 + max_loc[1], tw, th)

    def _detect_active_marker(self, placed, party_area):
        if not placed:
            return None
        if len(placed) == 1:
            return placed[0]["ordinal"]

        px, py = party_area[0], party_area[1]
        boxes = []
        for f in placed:
            x1, y1, x2, y2 = self._bbox_to_tuple(f["bbox"])
            boxes.append((x1 + px, y1 + py, x2 + px, y2 + py))

        screen_w, screen_h = self._display_size()
        sx, sy = self._ui_scale()
        marker_right = min(
            screen_w,
            int(party_area[2] - max(4, int(6 * sx))),
        )
        gap = max(1, int(3 * sx))
        zone_w = max(30, int(48 * sx))
        scored = []

        for f, box in zip(placed, boxes):
            x1, y1, x2, y2 = box
            height = max(1, y2 - y1)
            center_y = (y1 + y2) // 2
            pad = max(int(16 * sy), int(height * 0.6))
            scan_y1 = max(0, center_y - pad)
            scan_y2 = min(screen_h, center_y + pad + 1)
            scan_x1 = max(0, int(x2 - gap))
            scan_x2 = min(marker_right, int(x2 + zone_w))
            if scan_x2 - scan_x1 < zone_w * 0.5 or scan_y2 <= scan_y1:
                continue
            score, marker_box = self._marker_candidate(
                (scan_x1, scan_y1, scan_x2, scan_y2), label=str(f["ordinal"])
            )
            if score > 0:
                scored.append((score, f, marker_box))

        if not scored:
            if DEBUG_CHARACTER_MODE:
                log("[CharSensor] No active marker candidate found")
            return None

        scored.sort(key=lambda item: item[0], reverse=True)
        best_score, best_f, best_box = scored[0]
        second_score = scored[1][0] if len(scored) > 1 else 0.0
        min_score = 0.62

        if best_score < min_score:
            if DEBUG_CHARACTER_MODE:
                log(f"[CharSensor] Marker score too low: {best_score:.3f} < {min_score}")
            return None
        if second_score and best_score < second_score + 0.10:
            if DEBUG_CHARACTER_MODE:
                log(
                    f"[CharSensor] Ambiguous markers: best={best_score:.3f} "
                    f"second={second_score:.3f}"
                )
            return None

        if DEBUG_CHARACTER_MODE:
            log(
                f"[CharSensor] Active marker on slot {best_f['ordinal']} "
                f"({best_f['name']}), score={best_score:.1f}, box={best_box}"
            )
        return best_f["ordinal"]

    def _in_known_menu(self) -> bool:
        """True if menus blackboard currently reports a recognized menu/cutscene."""
        menus = blackboard.read("menus", max_age=6.0)
        if not menus:
            return False
        return bool(
            menus.get(K.GAMEMENU)
            or menus.get(K.PARTY_SETUP)
            or menus.get(K.DOMAIN)
        )

    def _extract_party_names(self, crop, ocr_key="CHAR_PARTY_FULL"):
        cur = self._prep(crop)
        t0 = time.perf_counter()
        try:
            results = self.reader.readtext(cur)
        except Exception:
            results = []
        record_ocr(ocr_key, (time.perf_counter() - t0) * 1000.0)

        fragments = [
            r for r in results
            if r[2] > 0.6 and len(r[1].strip()) > 2
        ]
        fragments.sort(key=lambda r: r[0][0][1])

        sx, sy = self._ui_scale()
        y_limit = max(28, int(40 * sy))
        x_limit = max(24, int(72 * sx))
        merged_fragments = []
        for frag in fragments:
            if not merged_fragments:
                merged_fragments.append(frag)
                continue

            last = merged_fragments[-1]
            last_box = self._bbox_to_tuple(last[0])
            curr_box = self._bbox_to_tuple(frag[0])
            last_y = (last_box[1] + last_box[3]) / 2
            curr_y = (curr_box[1] + curr_box[3]) / 2
            x_gap = max(last_box[0], curr_box[0]) - min(last_box[2], curr_box[2])

            if abs(curr_y - last_y) < y_limit and x_gap < x_limit:
                all_x = [p[0] for p in last[0]] + [p[0] for p in frag[0]]
                all_y = [p[1] for p in last[0]] + [p[1] for p in frag[0]]
                min_x, max_x = min(all_x), max(all_x)
                min_y, max_y = min(all_y), max(all_y)
                merged_bbox = [
                    [min_x, min_y],
                    [max_x, min_y],
                    [max_x, max_y],
                    [min_x, max_y],
                ]
                merged_fragments[-1] = (
                    merged_bbox,
                    last[1].strip() + " " + frag[1].strip(),
                    max(last[2], frag[2]),
                )
            else:
                merged_fragments.append(frag)

        fragments = merged_fragments

        if DEBUG_CHARACTER_MODE:
            for frag in fragments:
                log(f"[CharSensor] Fragment: '{frag[1].strip()}' conf={frag[2]:.2f} y={frag[0][0][1]:.0f}")

        found = []
        for frag in fragments:
            text = frag[1].strip()
            matched = self._match_character(text)
            if not matched:
                split_matches = self._split_and_search_names(frag[1])
                if split_matches:
                    matched = split_matches[0]

            if matched:
                bbox = frag[0]
                y_center = (bbox[0][1] + bbox[2][1]) / 2
                found.append({
                    "name": matched["name"],
                    "image_key": matched["image_key"],
                    "y_center": y_center,
                    "bbox": bbox,
                })

        return fragments, found

    def _fallback_party_area(self):
        base = self._load_party_area()
        if not base:
            return None
        screen_w, screen_h = self._display_size()
        sx, sy = self._ui_scale()
        bx1, by1, bx2, by2 = base
        bw, bh = bx2 - bx1, by2 - by1
        margin_x = max(int(bw * 0.9), int(120 * sx))
        margin_y = max(int(bh * 0.28), int(90 * sy))
        x1 = max(0, bx1 - margin_x)
        y1 = max(0, by1 - margin_y)
        x2 = min(screen_w, bx2 + margin_x)
        y2 = min(screen_h, by2 + margin_y)
        if x2 - x1 < int(bw * 0.5) or y2 - y1 < int(bh * 0.5):
            return None
        return (int(x1), int(y1), int(x2), int(y2))

    def _area_from_name_boxes(self, found, search_origin):
        base = self._load_party_area()
        screen_w, screen_h = self._display_size()
        sx, sy = self._ui_scale()
        bx1, by1, bx2, by2 = base
        base_w, base_h = bx2 - bx1, by2 - by1

        boxes = []
        for f in found:
            x1, y1, x2, y2 = self._bbox_to_tuple(f["bbox"])
            boxes.append((x1 + search_origin[0], y1 + search_origin[1],
                          x2 + search_origin[0], y2 + search_origin[1]))

        min_x = min(b[0] for b in boxes)
        max_x = max(b[2] for b in boxes)
        min_y = min(b[1] for b in boxes)
        max_y = max(b[3] for b in boxes)
        center_y = (min_y + max_y) / 2
        union_w = max_x - min_x
        union_h = max_y - min_y

        pad_x = max(int(36 * sx), int(base_w * 0.16))
        pad_y = max(int(10 * sy), int(base_h * 0.03))
        width = max(base_w, int(union_w + 2 * pad_x))
        height = max(base_h, int(union_h + 2 * pad_y))
        x1 = int(min_x - pad_x)
        y1 = int(center_y - height / 2)

        x1 = max(0, min(x1, max(0, screen_w - width)))
        y1 = max(0, min(y1, max(0, screen_h - height)))
        return (x1, y1, min(screen_w, x1 + width), min(screen_h, y1 + height))

    @staticmethod
    def _shift_fragments(fragments, dx, dy):
        return [
            ([[p[0] + dx, p[1] + dy] for p in bbox], text, conf)
            for bbox, text, conf in fragments
        ]

    def _find_party_area(self):
        search_area = self._fallback_party_area()
        if not search_area:
            return None
        crop = self._grab(search_area)
        try:
            fragments, found = self._extract_party_names(crop, ocr_key="CHAR_PARTY_SEARCH")
        finally:
            crop.close()
        if not found:
            return None

        new_area = self._area_from_name_boxes(found, search_area[:2])
        dx = search_area[0] - new_area[0]
        dy = search_area[1] - new_area[1]
        fragments = self._shift_fragments(fragments, dx, dy)
        for f in found:
            f["bbox"] = [[p[0] + dx, p[1] + dy] for p in f["bbox"]]
            f["y_center"] += dy
        return new_area, fragments, found

    def scan(self):
        if self._in_known_menu():
            blackboard.write(
                self._output_key,
                {K.SLOTS: [], K.ACTIVE_SLOT_HINT: None, K.HUD_VISIBLE: False},
            )
            return

        party_area = self._party_area
        if not party_area:
            blackboard.write(
                self._output_key,
                {K.SLOTS: [], K.ACTIVE_SLOT_HINT: None, K.HUD_VISIBLE: False},
            )
            return

        crop = self._grab(self._party_area)

        # Save full party area for debugging
        if DEBUG_CHARACTER_MODE:
            ts = int(time.time() * 1000)
            crop.save(_DEBUG_CACHE_DIR / f"party_area_{ts}.png")

        fragments, found = self._extract_party_names(crop)
        crop.close()

        if not found:
            self._empty_scans += 1
            if self._empty_scans == 1 or self._empty_scans % 3 == 0:
                fallback = self._find_party_area()
                if fallback is not None:
                    self._party_area, fragments, found = fallback
                    self._empty_scans = 0
                    if DEBUG_MODE:
                        log(f"[CharSensor] Re-anchored party area to {self._party_area}")
        else:
            self._empty_scans = 0

        # Check for special UI patterns from CSV
        special_match = None
        for frag in fragments:
            text = frag[1].strip().lower()
            for pattern in self._special_ui:
                if pattern["search_str"] in text:
                    special_match = pattern
                    if DEBUG_CHARACTER_MODE:
                        log(f"[CharSensor] Special UI match: {pattern['search_str']} -> {pattern['display_name']}")
                    break
            if special_match:
                break

        found.sort(key=lambda f: f["y_center"])

        any_success = bool(found)
        self._last_round_success = any_success

        slots = [None] * 6
        placed = []
        for i, f in enumerate(found[:5]):
            ordinal = i + 1
            slots[ordinal] = {"name": f["name"], "image_key": f["image_key"]}
            f["ordinal"] = ordinal
            placed.append(f)

        any_success = bool(found)

        # Active slot detection: score the marker strip to the right of each name row
        hint = self._detect_active_marker(placed, self._party_area)

        if hint is None and DEBUG_CHARACTER_MODE:
            log("[CharSensor] No active marker detected on any slot")

        d = self._debounce
        if hint is not None:
            if hint == d["candidate"]:
                d["confirmed"] = hint
            else:
                d["candidate"] = hint
        else:
            d["candidate"] = None

        output_slots = [None] * 6
        for f in found[:5]:
            ordinal = f["ordinal"]
            output_slots[ordinal] = {"name": f["name"], "image_key": f["image_key"]}

        blackboard.write(
            self._output_key,
            {K.SLOTS: output_slots, K.ACTIVE_SLOT_HINT: d["confirmed"], K.HUD_VISIBLE: bool(found),
             "special_ui": special_match},
        )