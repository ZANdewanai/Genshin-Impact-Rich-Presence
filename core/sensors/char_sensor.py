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
from PIL import Image, ImageGrab

from core import keys as K
from core.blackboard import blackboard, CHAR_MAX_AGE_HUD
from core.datatypes import DEBUG_MODE, DEBUG_CHARACTER_MODE
from core.log_utils import log, record_ocr
from core.search_index import SearchIndex
from CONFIG import BASE_RESOLUTION_WIDTH, BASE_RESOLUTION_HEIGHT, BASE_PARTY_AREA, DETECTED_RESOLUTION


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
        actual_w, actual_h = DETECTED_RESOLUTION
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

    def _detect_triangle_right_of_name(self, merged_bbox, party_offset):
        """Scan the region right of the name text for the white filled triangle (🞀).
        Uses merged bbox right edge (widest line) for horizontal, merged center for vertical."""
        mxs = [p[0] for p in merged_bbox]
        mys = [p[1] for p in merged_bbox]
        mx1, my1, mx2, my2 = min(mxs), min(mys), max(mxs), max(mys)
        
        # Convert crop-relative bbox to screen coordinates
        px, py = party_offset
        mx1 += px
        my1 += py
        mx2 += px
        my2 += py
        
        # Vertical center of merged bbox (triangle sits between lines)
        center_y = (my1 + my2) // 2
        y_start = center_y - 12
        y_end = center_y + 12  # 24px tall
        
        # Triangle is a few pixels right of merged bbox right edge (widest line)
        scan_x1 = mx2 + 2
        scan_x2 = mx2 + 20  # 18px wide - covers the triangle
        
        crop = self._grab((scan_x1, y_start, scan_x2, y_end))
        
        # Save for debugging
        if DEBUG_CHARACTER_MODE:
            ts = int(time.time() * 1000)
            crop.save(_DEBUG_CACHE_DIR / f"triangle_scan_{ts}.png")
        
        try:
            arr = np.array(crop.convert("L"))
            if arr.size == 0:
                return False
            
            # Threshold for PURE WHITE pixels only (245-255)
            white_mask = (arr > 245).astype(np.uint8)
            
            # Proper filled triangle detection (🞀): narrow at top, widening toward bottom
            # Scan columns left-to-right, check vertical profile
            h, w = white_mask.shape
            if w < 8 or h < 16:
                return False
            
            # For each column, count white pixels from top to bottom
            col_profiles = []
            for x in range(w):
                col = white_mask[:, x]
                # Find first and last white pixel
                white_indices = np.where(col)[0]
                if len(white_indices) > 0:
                    top = white_indices[0]
                    bottom = white_indices[-1]
                    height = bottom - top + 1
                    col_profiles.append((x, top, bottom, height))
                else:
                    col_profiles.append((x, -1, -1, 0))
            
            # Look for triangle pattern: consecutive columns with increasing height
            # Triangle is ~16px wide, ~21px tall, filled
            for i in range(len(col_profiles) - 7):
                window = col_profiles[i:i+8]
                heights = [p[3] for p in window]
                tops = [p[1] for p in window]
                bottoms = [p[2] for p in window]
                
                # All columns must have white pixels
                if any(h == 0 for h in heights):
                    continue
                
                # Heights should increase (triangle widening)
                increasing = all(heights[j] <= heights[j+1] for j in range(7))
                
                # Top should be roughly aligned (flat top of triangle)
                top_aligned = max(tops) - min(tops) <= 3
                
                # Bottom should be roughly aligned (flat bottom)
                bottom_aligned = max(bottoms) - min(bottoms) <= 3
                
                # Total height ~21px
                avg_height = sum(heights) / 8
                height_ok = 16 <= avg_height <= 26
                
                if increasing and top_aligned and bottom_aligned and height_ok:
                    if DEBUG_CHARACTER_MODE:
                        log(f"[CharSensor] Filled triangle (🞀) detected at column {i}-{i+7}!")
                    return True
                    
            return False
        finally:
            crop.close()

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
        
        cur = self._prep(crop)
        crop.close()

        t0 = time.perf_counter()
        try:
            results = self.reader.readtext(cur)
        except Exception:
            results = []
        record_ocr("CHAR_PARTY_FULL", (time.perf_counter() - t0) * 1000.0)

        fragments = [
            r for r in results
            if r[2] > 0.6 and len(r[1].strip()) > 2
        ]
        fragments.sort(key=lambda r: r[0][0][1])
        
        # Merge vertically adjacent fragments (multi-line names like "Kamisato Ayaka")
        merged_fragments = []
        for frag in fragments:
            if not merged_fragments:
                merged_fragments.append(frag)
                continue
            
            last = merged_fragments[-1]
            last_bbox = last[0]
            curr_bbox = frag[0]
            
            last_y = (last_bbox[0][1] + last_bbox[2][1]) / 2
            curr_y = (curr_bbox[0][1] + curr_bbox[2][1]) / 2
            y_diff = curr_y - last_y
            
            # If vertically close (within ~40px), merge them
            if y_diff < 40:
                # Merge text
                merged_text = last[1].strip() + " " + frag[1].strip()
                # Merge bbox - expand to cover both
                last_xs = [p[0] for p in last_bbox]
                last_ys = [p[1] for p in last_bbox]
                curr_xs = [p[0] for p in curr_bbox]
                curr_ys = [p[1] for p in curr_bbox]
                merged_bbox = [
                    [min(last_xs + curr_xs), min(last_ys + curr_ys)],
                    [max(last_xs + curr_xs), min(last_ys + curr_ys)],
                    [max(last_xs + curr_xs), max(last_ys + curr_ys)],
                    [min(last_xs + curr_xs), max(last_ys + curr_ys)],
                ]
                merged_fragments[-1] = (merged_bbox, merged_text, max(last[2], frag[2]))
            else:
                merged_fragments.append(frag)
        
        fragments = merged_fragments

        if DEBUG_CHARACTER_MODE:
            for frag in fragments:
                log(f"[CharSensor] Fragment: '{frag[1].strip()}' conf={frag[2]:.2f} y={frag[0][0][1]:.0f}")

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

        found = []
        for i, frag in enumerate(fragments):
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

        any_success = bool(found)
        self._last_round_success = any_success

        found.sort(key=lambda f: f["y_center"])

        slots = [None] * 6
        placed = []
        for i, f in enumerate(found[:5]):
            ordinal = i + 1
            slots[ordinal] = {"name": f["name"], "image_key": f["image_key"]}
            f["ordinal"] = ordinal
            placed.append(f)

        any_success = bool(found)

        # Active slot detection: scan for triangle indicator (▶) on ALL slots
        hint = None
        party_offset = (self._party_area[0], self._party_area[1]) if self._party_area else (0, 0)
        for f in placed:
            has_triangle = self._detect_triangle_right_of_name(f["bbox"], party_offset)
            if has_triangle:
                hint = f["ordinal"]
                if DEBUG_CHARACTER_MODE:
                    log(f"[CharSensor] Active slot: {hint} ({f['name']}) - triangle detected")
                break
        
        if hint is None and DEBUG_CHARACTER_MODE:
            log(f"[CharSensor] No triangle detected on any slot")

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