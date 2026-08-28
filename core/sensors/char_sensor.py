"""Independent detector workers ("sensors").

Each sensor runs its own loop, grabs only its own screen regions, skips OCR
when a region is pixel-identical to the previous scan, and publishes its
findings to its own JSON file on the blackboard. Sensors never block each
other; the coordinator (main) consumes the JSON files.

Threading note: ONNX inference releases the GIL, so threads genuinely run in
parallel for OCR work while staying far simpler than multiprocessing.
"""

import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageGrab

from core import keys as K
from core.blackboard import write_json, read_json
from core.datatypes import DEBUG_MODE, DEBUG_CHARACTER_MODE
from core.log_utils import log, record_ocr



from .base import BaseSensor, _looks_same
class CharSensor(BaseSensor):
    """Party name slots + active-slot brightness hint -> characters.json

    Uses the 5 pre-calibrated party size coordinate sets (1P-5P) directly.
    Automatically detects which party size is active by finding the coordinate
    set that yields the most valid character detections. No adaptation, no
    vertical shifting, no 6-party fallback.
    """

    def __init__(self, reader, data, output_path, interval=2.0,
                 party_size=None, menus_path=None):
        super().__init__("CharSensor", output_path, interval)
        self.reader = reader
        self.data = data
        self._party_size = party_size  # If set, use this; if None, auto-detect
        self._menus_path = menus_path  # menus.json for HUD-hidden gating
        self._last_detected_party_size = None  # Cached auto-detected party size
        self._slot_cache = [None] * 5  # Max 5 slots; will be trimmed to actual party_size
        self._last_round_success = False
        self._debounce = {"candidate": None, "confirmed": None}
        # Optional static-screenshot mode: grab regions from a file instead of
        # the live screen. Lets us repro trial/partial/solo party layouts from
        # screenshots users supply, without triggering those in-game ourselves.
        self._static_img = None
        self._load_static_image()

    def _load_static_image(self):
        """Load (or clear) the static debug image per DEBUG_STATIC_IMAGE flag."""
        try:
            from CONFIG import DEBUG_STATIC_IMAGE, DEBUG_STATIC_IMAGE_PATH
            if DEBUG_STATIC_IMAGE and DEBUG_STATIC_IMAGE_PATH:
                from pathlib import Path
                p = Path(__file__).resolve().parent.parent.parent / DEBUG_STATIC_IMAGE_PATH
                if Path(DEBUG_STATIC_IMAGE_PATH).exists():
                    p = Path(DEBUG_STATIC_IMAGE_PATH)
                if p.is_file():
                    self._static_img = Image.open(p).convert("RGB")
                    log(f"[{self.name}] static-image debug mode: {p}")
                    return
        except Exception:
            pass
        self._static_img = None

    def _get_coords_for_party_size(self, party_size):
        """Get names/number coordinates for a specific party size (1-5).

        Uses the resolution-scaled canonical per-party-size coordinate sets
        from CONFIG (NAMES_1P_COORD ... NAMES_5P_COORD).
        """
        from CONFIG import (
            NAMES_1P_COORD, NUMBER_1P_COORD,
            NAMES_2P_COORD, NUMBER_2P_COORD,
            NAMES_3P_COORD, NUMBER_3P_COORD,
            NAMES_4P_COORD, NUMBER_4P_COORD,
            NAMES_5P_COORD, NUMBER_5P_COORD,
        )
        names_map = {
            1: NAMES_1P_COORD,
            2: NAMES_2P_COORD,
            3: NAMES_3P_COORD,
            4: NAMES_4P_COORD,
            5: NAMES_5P_COORD,
        }
        numbers_map = {
            1: NUMBER_1P_COORD,
            2: NUMBER_2P_COORD,
            3: NUMBER_3P_COORD,
            4: NUMBER_4P_COORD,
            5: NUMBER_5P_COORD,
        }
        names_coord = names_map.get(party_size)
        numbers_coord = numbers_map.get(party_size)
        if names_coord is None or numbers_coord is None:
            raise ValueError(f"Invalid party_size: {party_size}. Must be 1-5.")
        return names_coord, numbers_coord

    def _detect_party_size(self, names_coord, numbers_coord):
        """Re-probe all 5 canonical party configurations and pick the one
        whose slots yield the most MATCHED characters.

        Raw OCR text is not enough: menu screens and UI overlap produce
        garbage that would let a wrong layout win. Only names that actually
        resolve to a known character count as a detection.
        """
        best_party_size = None
        best_detections = 0

        # Try each party size from 1 to 5
        for ps in range(1, 6):
            try:
                coords, num_coords = self._get_coords_for_party_size(ps)
                detections = 0
                for i in range(len(coords)):
                    crop = self._grab(coords[i])
                    cur = self._prep(crop)
                    crop.close()
                    t0 = time.perf_counter()
                    try:
                        results = self.reader.readtext(cur)
                    except Exception:
                        results = []
                    record_ocr("CHAR_SLOTS", (time.perf_counter() - t0) * 1000.0)
                    text = self._join_name_fragments(results)
                    # Count as detection only if the text MATCHES a character
                    if text and self._match_character(text) is not None:
                        detections += 1
                if detections > best_detections:
                    best_detections = detections
                    best_party_size = ps
            except Exception:
                continue

        if best_party_size is None and DEBUG_MODE:
            log(f"[{self.name}] Party size probe found no matched characters "
                f"on any layout (HUD likely hidden)")
        return best_party_size

    def _get_coords_provider(self):
        """Get names/number coordinates for the active party size (explicit or auto-detected)."""
        if self._party_size is not None:
            # Explicit party_size provided
            names_coord, numbers_coord = self._get_coords_for_party_size(self._party_size)
            # Ensure slot_cache matches party_size
            if len(self._slot_cache) != self._party_size:
                self._slot_cache = [None] * self._party_size
            return names_coord, numbers_coord

        # Auto-detect party size - re-probed whenever the cached size was
        # invalidated (see Phase 2b in scan() / reset_slot_cache())
        if self._last_detected_party_size is None:
            # Start with 5P (most common) as a probe baseline
            names_coord, numbers_coord = self._get_coords_for_party_size(5)
            detected = self._detect_party_size(names_coord, numbers_coord)
            if detected is not None:
                if detected != self._last_detected_party_size:
                    log(f"[CharSensor] Auto-detected party size: {detected}P")
                self._last_detected_party_size = detected
            else:
                # No layout matched (HUD hidden / menu screen). Fall back to
                # 5P for this round; the next scan re-detects.
                self._last_detected_party_size = 5
                if DEBUG_MODE:
                    log(f"[CharSensor] Party size unknown - defaulting to 5P probe this round")

        # Ensure slot_cache matches detected party size
        if len(self._slot_cache) != self._last_detected_party_size:
            self._slot_cache = [None] * self._last_detected_party_size

        return self._get_coords_for_party_size(self._last_detected_party_size)

    def _grab(self, bbox):
        """Crop from the static debug image when set, else the live screen."""
        if self._static_img is not None:
            return self._static_img.crop(bbox)
        return ImageGrab.grab(bbox=bbox)

    def reset_slot_cache(self):
        """Reset the character slot OCR cache to force fresh reads.
        
        This is called when the game state changes significantly (e.g., exiting
        a cutscene), forcing the CharSensor to re-OCR all character slots instead
        of using potentially stale cached results.
        """
        # Reset auto-detected party size so it re-detects on next scan
        self._last_detected_party_size = None
        # Reset slot cache to max size (5); will be trimmed when party size is detected
        self._slot_cache = [None] * 5
        self._last_round_success = False
        # Drop the active-slot debounce too - the confirmed hint belongs to
        # the OLD party/layout and would otherwise be published until a new
        # candidate confirms.
        self._debounce = {"candidate": None, "confirmed": None}
        if DEBUG_MODE:
            log(f"[{self.name}] Reset character slot cache, will re-detect party size")

    @staticmethod
    def _join_name_fragments(results):
        """Join confident OCR fragments top-to-bottom into one name string.

        Two-line names (Kaedehara Kazuha, Yumemizuki Mizuki, ...) come back
        as separate rows - ALL confident rows are joined so the full name
        substring-matches the CSV's full-name search_str.
        """
        fragments = [
            r for r in results
            if r[2] > 0.6 and len(r[1].strip()) > 2
        ]
        fragments.sort(key=lambda r: r[0][0][1])  # by top y coordinate
        return " ".join(r[1].strip() for r in fragments)

    def _match_character(self, text):
        from core.shared_config import get_shared_config
        cfg = get_shared_config()
        custom = cfg.get("USERNAME")
        if custom and text.strip().lower() == custom.strip().lower():
            # Respect the MC_AETHER traveler choice from shared config
            traveler = "char_lumine" if cfg.get("MC_AETHER") is False else "char_aether"
            return {"name": custom.strip(), "image_key": traveler}
        c = self.data.search_character(text)
        if c is None:
            return None
        return {"name": c.character_display_name, "image_key": c.image_key}

    # Digits shown on the party-member number plates (1-6).
    _NUMBER_DIGITS = "0123456789"

    def _read_number_digit(self, bbox, dy=0):
        """OCR the number plate paired with a name box.

        ``dy`` is the vertical offset the matching name was found at, so the
        plate is read at the SAME shift the name used (they move together).
        Returns the integer party ordinal (1-6), or ``None`` if no confident
        single digit is read. A failed read simply retries next scan.
        """
        x1, y1, x2, y2 = bbox
        y_top = max(0, y1 + dy)
        if y2 + dy <= y_top:  # shifted fully off-screen
            return None
        crop = self._grab((x1, y_top, x2, y2 + dy))
        gray = crop.convert("L")
        crop.close()
        # Number plates are tiny (~30x30): upscale 3x and binarize instead.
        # Use a fixed threshold that works reliably for both polarities.
        up = gray.resize((max(1, gray.width * 3), max(1, gray.height * 3)))
        arr = np.array(up.point(lambda x: 0 if x < 128 else 255))
        t0 = time.perf_counter()
        try:
            results = self.reader.readtext(arr, allowlist=self._NUMBER_DIGITS)
        except Exception:
            results = []
        record_ocr("CHAR_NUMBERS", (time.perf_counter() - t0) * 1000.0)
        for r in results:
            txt = r[1].strip()
            if r[2] >= 0.5 and len(txt) == 1 and txt.isdigit():
                d = int(txt)
                if 1 <= d <= 6:
                    return d
        return None

    def _plate_brightness(self, bbox, dy=0):
        """Grayscale mean of a number plate (legacy, used as fallback)."""
        x1, y1, x2, y2 = bbox
        y_top = max(0, y1 + dy)
        if y2 + dy <= y_top:
            return 0.0
        c = self._grab((x1, y_top, x2, y2 + dy))
        try:
            return float(np.array(c.convert("L")).mean())
        finally:
            c.close()

    def _triangle_metrics(self, names_coord, dy=0):
        """Detect the active-character ◂ indicator to the right of the name.

        The active character has a solid white left-pointing triangle in the
        leftmost ~8px of the right 40px section of the name box. The rest of
        that 40px strip is the dim background between the name and the number
        plate. Inactive slots show only name-text fragments in that area.

        Returns (col0_count, col0_count) - the caller can apply a column-count
        test (col0_count >= 15) to identify the active slot.
        Returns (0, 0) if the region is off-screen.
        """
        x1, y1, x2, y2 = names_coord
        y_top = max(0, y1 + dy)
        if y2 + dy <= y_top:
            return 0, 0
        c = self._grab((x1, y_top, x2, y2 + dy))
        try:
            arr = np.array(c.convert("L"))
            # Resolution-independent: the ◂ triangle sits in the rightmost
            # ~20% of the name box (the 1440p box is 197px wide, triangle
            # column at x=157 ≈ 0.797). Test the leftmost column of that
            # strip; the active slot's solid white triangle fills it, while
            # inactive slots show only scattered text pixels.
            right_strip_x = int(arr.shape[1] * 157 / 197)
            bright = arr[:, right_strip_x:] > 200
            col0_count = int(bright[:, 0].sum())
            return col0_count, col0_count
        finally:
            c.close()

    def _capture_slot(self, i, names_coord, numbers_coord):
        """Resolve the character shown at physical crop index ``i`` and read
        its paired number plate to learn the TRUE party ordinal.

        The number plate is paired with the name box in the same canonical
        coordinate set, so the digit is authoritative: a character that
        drifts between two calibrated slots (e.g. a sparse/partial party) is
        still placed in its real party slot, and rearranging the party is
        reflected correctly. Returns an entry dict, or ``None`` if nothing
        was found.
        """
        crop = self._grab(names_coord[i])
        cur = self._prep(crop)
        crop.close()
        cache = self._slot_cache[i] or {}

        # Pixel-identical short-circuit: reuse the cached name, but ALWAYS
        # re-read the paired plate so renumbering a stationary bar (party
        # rearranged/shrunk/grown) is still caught, and to keep the active
        # brightness hint fresh.
        if (
            _looks_same(cache.get("fp"), cache.get("sample"), cur)
            and cache.get("name")
        ):
            dy = cache.get("dy", 0)
            digit = self._read_number_digit(numbers_coord[i], dy)
            ordinal = digit if digit else cache.get("ordinal", i + 1)
            tri_col0, _ = self._triangle_metrics(names_coord[i], dy)
            triangle_found = bool(cache.get("triangle_found", False))
            self._slot_cache[i] = {
                **cache, "ordinal": ordinal,
                "tri_col0": tri_col0,
                "triangle_found": triangle_found,
            }
            return {
                "ordinal": ordinal,
                "digit_read": digit is not None,
                "entry": {
                    "name": cache["name"],
                    "image_key": cache.get("image_key"),
                    "cached": True,
                },
                "brightness": self._plate_brightness(numbers_coord[i], dy),
                "tri_col0": tri_col0,
                "triangle_found": triangle_found,
            }

        # Single capture at the canonical coordinates - no shifting.
        attempts = [(names_coord[i], 0)]

        matched = None
        used_dy = 0
        used_cur = None
        for coords, dy in attempts:
            c = self._grab(coords)
            arr = self._prep(c)
            c.close()
            t0 = time.perf_counter()
            try:
                results = self.reader.readtext(arr)
            except Exception:
                results = []
            record_ocr("CHAR_SLOTS", (time.perf_counter() - t0) * 1000.0)
            text = self._join_name_fragments(results)
            if text:
                m = self._match_character(text)
                if m:
                    matched = m
                    used_dy = dy
                    used_cur = arr
                    break
                if DEBUG_CHARACTER_MODE:
                    log(f"[{self.name}] slot{i}: OCR text {text!r} "
                        f"did not match any known character")

        if not matched:
            self._slot_cache[i] = None
            return None

        # Read the paired plate at the SAME offset the name was found, so the
        # ordinal stays bonded to the character even under adaptation.
        digit = self._read_number_digit(numbers_coord[i], used_dy)
        ordinal = digit if digit else i + 1
        tri_col0, _ = self._triangle_metrics(names_coord[i], used_dy)
        # Triangle detected when col 0 of the right strip has >= ~17% of the
        # box height as bright pixels (>200) - 15px at the 1440p box height
        # of 86px. Scales with the resolution-scaled coordinate sets.
        box_height = names_coord[i][3] - names_coord[i][1]
        triangle_found = tri_col0 >= max(5, int(box_height * 15 / 86))
        self._slot_cache[i] = {
            "fp": used_cur,
            "sample": used_cur.ravel()[::4],
            "name": matched["name"],
            "image_key": matched.get("image_key"),
            "ordinal": ordinal,
            "dy": used_dy,
            "tri_col0": tri_col0,
            "triangle_found": triangle_found,
        }
        return {
            "ordinal": ordinal,
            "digit_read": digit is not None,
            "entry": {**matched, "cached": False},
            "brightness": self._plate_brightness(numbers_coord[i], used_dy),
            "tri_col0": tri_col0,
            "triangle_found": triangle_found,
        }


    def _in_known_menu(self) -> bool:
        """True if menus.json currently reports a recognized menu/cutscene.

        During menus and cutscenes the overworld party HUD is guaranteed
        hidden, so the 5-configuration detection probe and slot OCR are
        pure waste - the scan can short-circuit.
        """
        if not self._menus_path:
            return False
        menus = read_json(self._menus_path, max_age=6.0)
        if not menus:
            return False
        # domain label only shows BEFORE entering the domain (HUD hidden
        # during that transition); inside the domain it disappears.
        return bool(
            menus.get(K.GAMEMENU)
            or menus.get(K.PARTY_SETUP)
            or menus.get(K.DOMAIN)
        )

    def scan(self):
        # Short-circuit while a recognized menu/cutscene is on screen: the
        # party HUD cannot be visible, so skip the probe + slot OCR entirely.
        if self._in_known_menu():
            write_json(
                self.output_path,
                {K.SLOTS: [], K.ACTIVE_SLOT_HINT: None, K.HUD_VISIBLE: False},
            )
            return

        names_coord, numbers_coord = self._get_coords_provider()
        slot_count = len(names_coord)
        slots = [None] * (slot_count + 1)  # +1 to allow slot 0 to be unused (party slots are 1-indexed)
        any_success = False
        # Each resolved entry carries the TRUE party ordinal (from the paired
        # number plate), the character entry, and the plate brightness used for
        # the active-slot hint.
        found = []

        # ---- Phase 1: capture at the canonical coordinates -----------------
        # The per-party-size sets are calibrated exactly - no vertical
        # shifting, no ±80 fallback hunting. A miss is a miss: it either
        # means the HUD is hidden or the party layout changed, and Phase 2
        # below handles both by re-probing all 5 configurations.
        for i in range(slot_count):
            res = self._capture_slot(i, names_coord, numbers_coord)
            if res is not None:
                found.append(res)
        any_success = bool(found)
        self._last_round_success = any_success

        # ---- Phase 2: total miss => drop the cached party size -------------
        # The party HUD either vanished (menu/cutscene) or the layout changed
        # (party resized). Either way the cached coordinate set is no longer
        # trustworthy: the next scan must re-probe ALL 5 canonical party
        # configurations via _detect_party_size.
        if not any_success and self._party_size is None and (
            self._last_detected_party_size is not None
        ):
            self._last_detected_party_size = None
            if DEBUG_MODE:
                log(f"[{self.name}] No party found on cached layout - "
                    f"will re-detect party size across all 5 configurations")

        # ---- Phase 3: place into slots by TRUE party ordinal, with dedup ----
        # A lone character sitting between calibrated slots can be caught at
        # several physical boxes; each resolves to (ideally) the SAME ordinal.
        # Guarantee one character occupies exactly one party slot: on a name
        # collision we keep the entry whose ordinal came from a real plate read
        # (more reliable than a fallback to the physical box index).
        placed = []
        placed_names = set()
        seen_slots = set()
        for f in sorted(found, key=lambda x: not x.get("digit_read", False)):
            entry = f.get("entry") or {}
            name = entry.get("name")
            ord_ = f.get("ordinal")
            if not name or not (isinstance(ord_, int) and 1 <= ord_ <= slot_count):
                continue
            if name in placed_names or ord_ in seen_slots or slots[ord_] is not None:
                continue
            slots[ord_] = entry
            placed.append(f)
            placed_names.add(name)
            seen_slots.add(ord_)

        # ---- Phase 4: active-slot hint from the ◂ indicator by ordinal ----
        # The active character has a solid white left-pointing triangle in the
        # leftmost section of the right 40px of the name box. Inactive slots
        # show only name-text fragments there. Use the shape test (left8 mean
        # high AND clearly above mid-section mean) to identify the active slot.
        hint = None
        active_candidates = [f for f in placed if f.get("triangle_found")]
        if len(active_candidates) == 1:
            hint = active_candidates[0]["ordinal"]
        elif len(placed) >= 2:
            # Fallback: if no single triangle detected, use brightness
            srt = sorted(placed, key=lambda t: t["brightness"])
            if (srt[1]["brightness"] - srt[0]["brightness"]) >= max(
                25, int(srt[1]["brightness"] * 0.12)
            ):
                hint = srt[0]["ordinal"]
        elif len(placed) == 1:
            # Single-character party (e.g. trial character story quests):
            # the lone detected character IS the active one.
            hint = placed[0]["ordinal"]

        d = self._debounce
        if hint is not None and hint == d["candidate"]:
            d["confirmed"] = hint
        else:
            d["candidate"] = hint

        write_json(
            self.output_path,
            {
                K.SLOTS: slots,
                K.ACTIVE_SLOT_HINT: d["confirmed"],
                K.HUD_VISIBLE: any_success,
            },
        )


