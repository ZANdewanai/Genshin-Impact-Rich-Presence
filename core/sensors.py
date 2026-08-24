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
from PIL import ImageGrab

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

    def scan(self):
        names_coord, numbers_coord = self.coords_provider()
        slots = []
        any_success = False
        for i in range(6):
            crop = ImageGrab.grab(bbox=names_coord[i])
            cur = self._prep(crop)
            crop.close()
            cache = self._slot_cache[i] or {}
            if (
                _looks_same(cache.get("fp"), cache.get("sample"), cur)
                and cache.get("name")
            ):
                slots.append({"name": cache["name"], "cached": True})
                continue

            # Cheap failure path: base position only after a failed round.
            attempts = [names_coord[i]]
            if self._last_round_success:
                x1, y1, x2, y2 = names_coord[i]
                attempts.extend([
                    (x1, y1 - 10, x2, y2 - 10),
                    (x1, y1 + 10, x2, y2 + 10),
                ])
            matched = None
            for coords in attempts:
                c = ImageGrab.grab(bbox=coords)
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
                        break
            if matched:
                any_success = True
                slots.append(matched)
                self._slot_cache[i] = {
                    "fp": cur,
                    "sample": cur.ravel()[::4],
                    "name": matched["name"],
                }
            else:
                slots.append(None)
                self._slot_cache[i] = None
        self._last_round_success = any_success

        # Active-slot hint from number-plate brightness (relative winner).
        # Only consider slots that actually have a detected character; empty
        # slots below the party HUD can capture background pixels that are
        # darker than inactive number plates and break the comparison.
        brightness = []
        for i in range(6):
            c = ImageGrab.grab(bbox=numbers_coord[i])
            brightness.append(float(np.array(c.convert("L")).mean()))
            c.close()
        occupied = [i for i, slot in enumerate(slots) if slot and slot.get("name")]
        if len(occupied) >= 2:
            occ_brightness = [(i, brightness[i]) for i in occupied]
            srt = sorted(occ_brightness, key=lambda t: t[1])
            hint = None
            if (srt[1][1] - srt[0][1]) >= max(25, int(srt[1][1] * 0.12)):
                hint = srt[0][0]
        else:
            hint = None
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
            "party_setup": is_party,
            "domain": dom.domain_name if dom else None,
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
