"""Independent detector workers ("sensors").

Each sensor runs its own loop, grabs only its own screen regions, skips OCR
when a region is pixel-identical to the previous scan, and publishes its
findings to its own JSON file on the blackboard. Sensors never block each
other; the coordinator (main) consumes the JSON files.

Threading note: ONNX inference releases the GIL, so threads genuinely run in
parallel for OCR work while staying far simpler than multiprocessing.
"""

import difflib
import json
import threading
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageGrab

from core.blackboard import write_json, read_json
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


class CharSensor(BaseSensor):
    """Party name slots + active-slot brightness hint -> characters.json"""

    def __init__(self, reader, data, coords_provider, output_path, interval=2.0):
        super().__init__("CharSensor", output_path, interval)
        self.reader = reader
        self.data = data
        self.coords_provider = coords_provider  # callable -> (names, numbers)
        self._slot_cache = [None] * 6  # per-slot: {"fp","sample","name"}
        self._last_round_success = False
        self._debounce = {"candidate": None, "confirmed": None}
        # Optional static-screenshot mode: grab regions from a file instead of
        # the live screen. Lets us repro trial/partial/solo party layouts from
        # screenshots users supply, without triggering those in-game ourselves.
        self._static_img = None
        try:
            from CONFIG import DEBUG_STATIC_IMAGE_PATH
            if DEBUG_STATIC_IMAGE_PATH:
                from pathlib import Path
                p = Path(__file__).resolve().parent.parent / DEBUG_STATIC_IMAGE_PATH
                if Path(DEBUG_STATIC_IMAGE_PATH).exists():
                    p = Path(DEBUG_STATIC_IMAGE_PATH)
                if p.is_file():
                    self._static_img = Image.open(p).convert("RGB")
                    log(f"[{self.name}] static-image debug mode: {p}")
        except Exception:
            self._static_img = None

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
        self._slot_cache = [None] * 6
        self._last_round_success = False
        if DEBUG_MODE:
            log(f"[{self.name}] Reset character slot cache")

    def _match_character(self, text):
        try:
            cfg_path = Path(__file__).resolve().parent.parent / "shared_config.json"
            with open(cfg_path, "r") as f:
                cfg = json.load(f)
            custom = cfg.get("USERNAME")
            if custom and text.strip().lower() == custom.strip().lower():
                # Respect the MC_AETHER traveler choice from shared config
                traveler = "char_lumine" if cfg.get("MC_AETHER") is False else "char_aether"
                return {"name": custom.strip(), "image_key": traveler}
        except Exception:
            custom = None
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
        # Number plates are tiny (~30x30): _prep() would shrink them 0.5x and
        # destroy the digit, so upscale 3x and binarize instead. Plates also
        # come in BOTH polarities (bright circles can fade to dark, digits are
        # sometimes dark-on-light, sometimes light-on-dark for inactive slots).
        # Blindly inverting 255-gray is fragile, so Otsu-threshold binarize
        # (auto-picks the "ink" polarity) then upscale. This yields a clean
        # white-glyph-on-black image for OCR regardless of the plate shading.
        import cv2
        up = gray.resize((max(1, gray.width * 3), max(1, gray.height * 3)))
        blur = cv2.GaussianBlur(np.array(up), (5, 5), 0)
        # Otsu-threshold the plate, then choose the "ink" polarity robustly:
        # the digit/glyph is the SMALLER population whether the plate is
        # dark-on-light or light-on-dark. THRESH_BINARY_INV alone would assume
        # the smaller side is always the low side, which fails on faded/muted
        # plates. So pick whichever side has fewer pixels and make it white.
        _, otsu = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        dark_side = (otsu == 0).sum()
        light_side = (otsu == 255).sum()
        if dark_side <= light_side:
            arr = (otsu == 0).astype(np.uint8) * 255       # ink = dark
        else:
            arr = (otsu == 255).astype(np.uint8) * 255    # ink = light
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
        """Grayscale mean of a number plate (used for the active-slot hint)."""
        x1, y1, x2, y2 = bbox
        y_top = max(0, y1 + dy)
        if y2 + dy <= y_top:
            return 0.0
        c = self._grab((x1, y_top, x2, y2 + dy))
        try:
            return float(np.array(c.convert("L")).mean())
        finally:
            c.close()

    def _capture_slot(self, i, names_coord, numbers_coord, fallback=False,
                      steps=None):
        """Resolve the character shown at physical crop index ``i`` and read
        its paired number plate to learn the TRUE party ordinal.

        The number plate moves WITH the name box (the adaptive manager keeps
        them paired), so the digit is authoritative: a character that drifts
        between two calibrated slots (e.g. a sparse/partial party) is still
        placed in its real party slot, and rearranging the party is reflected
        correctly. Returns an entry dict, or ``None`` if nothing was found.
        """
        x1, y1, x2, y2 = names_coord[i]
        crop = self._grab(names_coord[i])
        cur = self._prep(crop)
        crop.close()
        cache = self._slot_cache[i] or {}

        # Pixel-identical short-circuit: reuse the cached name, but ALWAYS
        # re-read the paired plate so renumbering a stationary bar (party
        # rearranged/shrunk/grown) is still caught, and to keep the active
        # brightness hint fresh.
        if not fallback and (
            _looks_same(cache.get("fp"), cache.get("sample"), cur)
            and cache.get("name")
        ):
            dy = cache.get("dy", 0)
            digit = self._read_number_digit(numbers_coord[i], dy)
            ordinal = (digit - 1) if digit else cache.get("ordinal", i)
            self._slot_cache[i] = {**cache, "ordinal": ordinal}
            return {
                "ordinal": ordinal,
                "digit_read": digit is not None,
                "entry": {
                    "name": cache["name"],
                    "image_key": cache.get("image_key"),
                    "cached": True,
                },
                "brightness": self._plate_brightness(numbers_coord[i], dy),
            }

        # Crops to try: base first, then ±10 after a prior success; the
        # incremental fallback adds larger offsets up to ±80 (nearest first).
        attempts = [(names_coord[i], 0)]
        if self._last_round_success and not fallback:
            attempts.extend([
                ((x1, y1 - 10, x2, y2 - 10), -10),
                ((x1, y1 + 10, x2, y2 + 10), 10),
            ])
        if fallback and steps:
            for dy in steps:
                y_top = max(0, y1 + dy)
                if y2 + dy <= y_top:  # shifted fully off-screen
                    continue
                attempts.append(((x1, y_top, x2, y2 + dy), dy))

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
            text = ""
            for r in results:
                if r[2] > 0.6 and len(r[1].strip()) > 2:
                    text = r[1].strip()
                    break
            if text:
                m = self._match_character(text)
                if m:
                    matched = m
                    used_dy = dy
                    used_cur = arr
                    break

        if not matched:
            self._slot_cache[i] = None
            return None

        # Read the paired plate at the SAME offset the name was found, so the
        # ordinal stays bonded to the character even under adaptation.
        digit = self._read_number_digit(numbers_coord[i], used_dy)
        ordinal = (digit - 1) if digit else i
        self._slot_cache[i] = {
            "fp": used_cur,
            "sample": used_cur.ravel()[::4],
            "name": matched["name"],
            "image_key": matched.get("image_key"),
            "ordinal": ordinal,
            "dy": used_dy,
        }
        return {
            "ordinal": ordinal,
            "digit_read": digit is not None,
            "entry": {**matched, "cached": False},
            "brightness": self._plate_brightness(numbers_coord[i], used_dy),
        }


    def scan(self):
        names_coord, numbers_coord = self.coords_provider()
        slots = [None] * 6
        any_success = False
        # Each resolved entry carries the TRUE party ordinal (from the paired
        # number plate), the character entry, and the plate brightness used for
        # the active-slot hint.
        found = []

        # ---- Phase 1: main capture at base (+±10 after a previous success) ----
        for i in range(6):
            res = self._capture_slot(i, names_coord, numbers_coord)
            if res is not None:
                found.append(res)
        any_success = bool(found)
        self._last_round_success = any_success

        # ---- Phase 2: incremental-shift fallback when nothing was found ----
        if not any_success:
            # Interleaved steps so the smallest absolute shift is tried first:
            # -10, +10, -20, +20, …, -80, +80
            steps = []
            for step in range(10, 81, 10):
                steps.append(-step)
                steps.append(step)
            for i in range(6):
                res = self._capture_slot(
                    i, names_coord, numbers_coord, fallback=True, steps=steps
                )
                if res is not None:
                    found.append(res)
            any_success = bool(found)
            self._last_round_success = any_success

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
            if not name or not (isinstance(ord_, int) and 0 <= ord_ <= 5):
                continue
            if name in placed_names or ord_ in seen_slots or slots[ord_] is not None:
                continue
            slots[ord_] = entry
            placed.append(f)
            placed_names.add(name)
            seen_slots.add(ord_)

        # ---- Phase 4: active-slot hint from plate brightness (by ordinal) ----
        # Only consider slots that actually have a detected character; empty
        # slots below the party HUD can capture background pixels that are
        # darker than inactive number plates and break the comparison.
        hint = None
        if len(placed) >= 2:
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
                "slots": slots,
                "active_slot_hint": d["confirmed"],
                "hud_visible": any_success,
            },
        )


class LocationSensor(BaseSensor):
    """Location label + world boss + map location + commission -> location.json"""

    def __init__(self, reader, data, coords_provider, output_path,
                 interval=1.0, boss_every=30, characters_path=None,
                 menus_path=None):
        super().__init__("LocationSensor", output_path, interval)
        self.reader = reader
        self.data = data
        self.coords_provider = coords_provider  # callable -> (loc, boss, maploc)
        self.boss_every = boss_every
        self.characters_path = characters_path
        self.menus_path = menus_path
        self._tick = 0
        self._cache = {}

    def _hud_visible(self) -> bool:
        """Party HUD on screen? Read from the characters blackboard."""
        if not self.characters_path:
            return False
        chars = read_json(self.characters_path, max_age=6.0)
        return bool(chars and chars.get("hud_visible"))

    def _in_known_menu(self) -> bool:
        """True if the menus blackboard currently reports a recognized menu."""
        if not self.menus_path:
            return False
        menus = read_json(self.menus_path, max_age=6.0)
        if not menus:
            return False
        return bool(
            menus.get("gamemenu") or menus.get("party_setup") or menus.get("domain")
        )

    def scan(self):
        self._tick += 1
        loc_bbox, boss_bbox, maploc_bbox = self.coords_provider()

        payload = {"location": None, "boss": None,
                   "commission": False, "map_location": None}

        # Commission check rides on the location region ("mission accept")
        loc_text = self._ocr_text("location", loc_bbox)
        if loc_text:
            if "mission accept" in loc_text.lower():
                payload["commission"] = True
            else:
                found = self.data.search_location(loc_text)
                if found is not None:
                    payload["location"] = {
                        "name": found.location_name,
                        "search_str": found.search_str,
                    }

        if self._tick % self.boss_every == 0:
            boss_text = self._ocr_text("boss", boss_bbox)
            if boss_text:
                found = self.data.search_boss(boss_text)
                if found is not None:
                    payload["boss"] = {
                        "name": found.boss_name,
                        "search_str": found.search_str,
                    }

        # Map location browsing only exists when the party HUD is hidden AND
        # no other menu is recognized (friends list shows 'Offline' text that
        # used to false-positive here).
        if (
            not self._hud_visible()
            and not self._in_known_menu()
            and maploc_bbox
            and self._tick % 3 == 0
        ):
            map_text = self._ocr_text("maploc", maploc_bbox)
            if map_text:
                from core.detection import process_map_text
                cleaned = process_map_text(map_text, self.data)
                if cleaned:
                    found = self.data.search_location(cleaned)
                    if found is not None:
                        payload["map_location"] = {
                            "name": found.location_name,
                            "search_str": found.search_str,
                        }

        write_json(self.output_path, payload)


class MenuSensor(BaseSensor):
    """Gamemenu / party-setup / domain labels -> menus.json"""

    def __init__(self, reader, data, coords_provider, output_path, interval=1.5):
        super().__init__("MenuSensor", output_path, interval)
        self.reader = reader
        self.data = data
        self.coords_provider = coords_provider  # callable -> {"gamemenu","domain"}
        self._cache = {}
        self._last_reported: dict | None = None  # only log on change

    def scan(self):
        boxes = self.coords_provider()
        menu_text = self._ocr_text("gamemenu", boxes["gamemenu"]).strip().lower()
        domain_text = self._ocr_text("domain", boxes["domain"]).strip().lower()

        gm = self.data.search_gamemenu(menu_text) if menu_text else None
        dom = self.data.search_domain(domain_text) if domain_text else None
        is_party = bool(
            menu_text
            and (
                "party setup" in menu_text.lower()
                or difflib.SequenceMatcher(
                    None, menu_text.lower().strip(), "party setup"
                ).ratio()
                >= 0.8
            )
        )

        result = {
            "gamemenu": gm.gamemenu_name if gm else None,
            # Ship the resolved identity alongside the label so consumers
            # never have to re-search by a lossy display string - search_str
            # and display name frequently differ (e.g. cutscenes:
            # search_str="auto", name="Currently in a Cutscene").
            "gamemenu_search": gm.search_str if gm else None,
            "party_setup": is_party,
            "domain": dom.domain_name if dom else None,
            "domain_search": dom.search_str if dom else None,
        }

        # Only emit a debug log line when the resolved menu label actually changes
        if result != self._last_reported:
            if result["gamemenu"]:
                log(f"[MenuSensor] {time.time():.0f} → Detected gamemenu: {result['gamemenu']}")
            if result["party_setup"]:
                log(f"[MenuSensor] {time.time():.0f} → Entered Party Setup")
            if result["domain"]:
                log(f"[MenuSensor] {time.time():.0f} → Detected domain: {result['domain']}")
            if not (result["gamemenu"] or result["party_setup"] or result["domain"]):
                log(f"[MenuSensor] {time.time():.0f} → Gamemenu detection: No match found")
            self._last_reported = result

        write_json(self.output_path, result)
