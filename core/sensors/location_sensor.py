"""Independent detector workers ("sensors").

Each sensor runs its own loop, grabs only its own screen regions, skips OCR
when a region is pixel-identical to the previous scan, and publishes its
findings to its own JSON file on the blackboard. Sensors never block each
other; the coordinator (main) consumes the JSON files.

Threading note: ONNX inference releases the GIL, so threads genuinely run in
parallel for OCR work while staying far simpler than multiprocessing.
"""

import time

from core import keys as K
from core.blackboard import write_json, read_json


from .base import BaseSensor

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
        return bool(chars and chars.get(K.HUD_VISIBLE))

    def _in_known_menu(self) -> bool:
        """True if the menus blackboard currently reports a recognized menu."""
        if not self.menus_path:
            return False
        menus = read_json(self.menus_path, max_age=6.0)
        if not menus:
            return False
        return bool(
            menus.get(K.GAMEMENU) or menus.get(K.PARTY_SETUP) or menus.get(K.DOMAIN)
        )

    def scan(self):
        self._tick += 1
        loc_bbox, boss_bbox, maploc_bbox = self.coords_provider()

        payload = {K.LOCATION: None, K.BOSS: None,
                   K.COMMISSION: False, K.MAP_LOCATION: None}

        # Commission check rides on the location region ("mission accept")
        loc_text = self._ocr_text("location", loc_bbox)
        if loc_text:
            if "mission accept" in loc_text.lower():
                payload[K.COMMISSION] = True
            else:
                found = self.data.search_location(loc_text)
                if found is not None:
                    payload[K.LOCATION] = {
                        "name": found.location_name,
                        "search_str": found.search_str,
                    }

        if self._tick % self.boss_every == 0:
            boss_text = self._ocr_text("boss", boss_bbox)
            self._last_boss_raw = boss_text
            self._last_boss_raw_ts = time.time()
            if boss_text:
                found = self.data.search_boss(boss_text)
                if found is not None:
                    payload[K.BOSS] = {
                        "name": found.boss_name,
                        "search_str": found.search_str,
                    }
        # Domain-handler feed: the in-domain challenge timer lives in the
        # same top-center region as boss names. Publish the raw text every
        # scan (cached between reads) so the coordinator can track timer
        # liveness without re-OCRing. Include the timestamp so consumers
        # can tell fresh reads from stale ones.
        payload[K.BOSS_RAW] = getattr(self, "_last_boss_raw", "")
        payload[K.BOSS_RAW_TS] = getattr(self, "_last_boss_raw_ts", 0.0)

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
                from core.ocr_utils import process_map_text
                cleaned = process_map_text(map_text, self.data)
                if cleaned:
                    found = self.data.search_location(cleaned)
                    if found is not None:
                        payload[K.MAP_LOCATION] = {
                            "name": found.location_name,
                            "search_str": found.search_str,
                        }

        write_json(self.output_path, payload)


