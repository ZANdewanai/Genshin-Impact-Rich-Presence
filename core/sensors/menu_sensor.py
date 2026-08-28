"""Independent detector workers ("sensors").

Each sensor runs its own loop, grabs only its own screen regions, skips OCR
when a region is pixel-identical to the previous scan, and publishes its
findings to its own JSON file on the blackboard. Sensors never block each
other; the coordinator (main) consumes the JSON files.

Threading note: ONNX inference releases the GIL, so threads genuinely run in
parallel for OCR work while staying far simpler than multiprocessing.
"""

import difflib
import time

from core.blackboard import write_json, read_json
from core.log_utils import log


from .base import BaseSensor

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
        # Domain reward flow: the "Skip Reward Cutscene" prompt appears while
        # clearing a finished domain's rewards (HUD + timer both hidden).
        is_reward_cutscene = bool(
            menu_text and "skip reward" in menu_text.lower()
        )

        result = {
            "gamemenu": gm.gamemenu_name if gm else None,
            # Ship the resolved identity alongside the label so consumers
            # never have to re-search by a lossy display string - search_str
            # and display name frequently differ (e.g. cutscenes:
            # search_str="auto", name="Currently in a Cutscene").
            "gamemenu_search": gm.search_str if gm else None,
            "party_setup": is_party,
            "reward_cutscene": is_reward_cutscene,
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
