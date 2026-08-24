"""Sensor coordinator: consumes blackboard JSONs and runs the activity state
machine. Replaces the inline sequential scanning of detection.py when
USE_SENSOR_WORKERS is enabled.

All transition/latch-prevention rules live here:
 - GAMEMENU/PARTY_SETUP exits on missing label (+ HUD evidence or timeout)
 - LOADING -> LOCATION promotion on party validation
 - active-character switching only into known slots
"""

import time

from core.blackboard import read_json
from core.datatypes import Activity, ActivityType, Character, DEBUG_MODE
from core.log_utils import log
from core.sensors import CharSensor, LocationSensor, MenuSensor
from core import state as state_module
from core.state import (
    state_lock,
    update_activity,
    update_character,
    set_active_character,
    get_current_characters,
    gui_callback,
)


def _notify_gui(new_activity):
    """Push an activity change to the embedded GUI (legacy parity)."""
    if gui_callback is None:
        return
    try:
        gui_callback(new_activity)
    except Exception as e:
        if DEBUG_MODE:
            log(f"GUI callback error: {e}")


def _search_str(activity) -> str | None:
    d = getattr(activity, "activity_data", None)
    return getattr(d, "search_str", None)


class SensorCoordinator:
    def __init__(self, reader, data, character_region_manager=None,
                 output_dir="sensor_data"):
        self.reader = reader
        self.data = data
        self.character_region_manager = character_region_manager
        import os
        out = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), output_dir
        )
        self.paths = {
            "characters": (out + "/characters.json", 10.0),
            "location": (out + "/location.json", 15.0),
            "menus": (out + "/menus.json", 8.0),
        }
        from CONFIG import (
            PARTY_SETUP_COORD,
            DOMAIN_COORD,
        )
        # NOTE: name/number coords come live from character_region_manager
        # (adaptive), location/boss/menu/maploc coords come from
        # core.detection's resolution-updated globals at scan time.

        def char_coords():
            # Prefer the adaptive manager's live positions when available;
            # fall back to CONFIG-scaled base coordinates.
            mgr = self.character_region_manager
            if mgr is not None:
                return (
                    list(mgr.current_name_positions),
                    list(mgr.current_number_positions),
                )
            from CONFIG import NAMES_6P_COORD, NUMBER_6P_COORD
            return NAMES_6P_COORD, NUMBER_6P_COORD

        def loc_coords():
            # detection.py keeps resolution-updated globals
            from core import detection
            from CONFIG import MAP_LOC_COORD
            return (
                detection.LOCATION_COORD,
                detection.BOSS_COORD,
                MAP_LOC_COORD,
            )

        def menu_coords():
            from core import detection
            return {
                "gamemenu": detection.PARTY_SETUP_COORD,
                "domain": detection.DOMAIN_COORD,
            }

        self.sensors = [
            CharSensor(reader, data, char_coords, self.paths["characters"][0], 4.0),
            LocationSensor(
                reader, data, loc_coords, self.paths["location"][0], 0.5,
                characters_path=self.paths["characters"][0],
                menus_path=self.paths["menus"][0],
            ),
            MenuSensor(reader, data, menu_coords, self.paths["menus"][0], 4.0),
        ]
        self._empty_party_exits = 0
        self._empty_gamemenu = 0
        self._last_valid_party = 0.0
        self._loading_start_time = time.time()

    # ------------------------------------------------------------------ #
    def start(self):
        for s in self.sensors:
            s.start()

    def stop(self):
        for s in self.sensors:
            s.stop()

    def _read(self, key):
        path, max_age = self.paths[key]
        return read_json(path, max_age=max_age)

    def _build_character(self, name):
        """Rebuild a full Character object from a display name."""
        c = self.data.search_character(name)
        if c is not None:
            return c
        # Traveler/custom names aren't in characters.csv under their label;
        # build a generic entry so slots stay populated.
        return Character(
            character_display_name=name,
            image_key="char_unknown",
            search_str=name.lower(),
        )

    def _exit_to_overworld(self, msg: str):
        new_activity = Activity(
            ActivityType.LOCATION, state_module.prev_location
        )
        update_activity(new_activity)
        _notify_gui(new_activity)
        log(msg)

    # ------------------------------------------------------------------ #
    def tick(self) -> float:
        """One coordinator iteration. Returns sleep duration."""
        # Heartbeat with OCR perf stats (same cadence as legacy path)
        now = time.time()
        if now - getattr(self, "_last_heartbeat", 0.0) >= 10.0:
            self._last_heartbeat = now
            from core.log_utils import format_and_reset_ocr_stats
            _ocr_summary = format_and_reset_ocr_stats()
            with state_lock:
                _act = state_module.current_activity.activity_type.name
                _active = state_module.current_active_character
            log(
                f"[HEARTBEAT] activity={_act} "
                f"active_char_slot={_active}"
                + (f" | ocr: {_ocr_summary}" if _ocr_summary else "")
            )

        chars = self._read("characters")
        loc = self._read("location")
        menus = self._read("menus")

        # HUD evidence is only trustworthy when freshly reported - during
        # menu transitions the last overworld scan can linger for seconds.
        hud_visible = False
        party_detected = False
        if chars and (time.time() - chars.get("written_at", 0)) < 6.0:
            hud_visible = bool(chars.get("hud_visible"))
            # Detected party slot names are themselves strong evidence the
            # party HUD is on screen - count them so a flaky hud_visible OCR
            # check can't wrongly "pause" an active exploration session.
            slots = chars.get("slots") or []
            party_detected = any(s and s.get("name") for s in slots)

        # ---- party slots -------------------------------------------------
        if chars and chars.get("slots"):
            for idx, slot in enumerate(chars["slots"]):
                if slot and slot.get("name"):
                    prev = get_current_characters()[idx]
                    if prev is None or prev.character_display_name != slot["name"]:
                        update_character(idx, self._build_character(slot["name"]))
                        log(f"Party slot {idx + 1}: {slot['name']}")

        # ---- active character --------------------------------------------
        if chars and chars.get("active_slot_hint") is not None:
            hint = chars["active_slot_hint"]
            cur = get_current_characters()[hint]
            with state_lock:
                different = hint + 1 != state_module.current_active_character
            if different and cur is not None:
                set_active_character(hint + 1)
                log(f'Active character: "{cur.character_display_name}"')

        # ---- activity state machine --------------------------------------
        party_flag = bool(menus and menus.get("party_setup"))
        gamemenu = menus.get("gamemenu") if menus else None
        domain = menus.get("domain") if menus else None

        with state_lock:
            current = state_module.current_activity.activity_type

        # ---- party setup enter/exit ---------------------------------------
        if party_flag:
            self._empty_party_exits = 0
            if current != ActivityType.PARTY_SETUP:
                new_activity = Activity(
                    ActivityType.PARTY_SETUP, state_module.prev_non_idle_activity
                )
                update_activity(new_activity)
                _notify_gui(new_activity)
                log("Entered Party Setup")
        elif current == ActivityType.PARTY_SETUP:
            self._empty_party_exits += 1
            if self._empty_party_exits >= 3:  # ~4.5s of missing label
                self._empty_party_exits = 0
                self._exit_to_overworld("Left party setup")

        # ---- gamemenu/cutscene enter/exit ----------------------------------
        if gamemenu:
            self._empty_gamemenu = 0
            gm_obj = self.data.search_gamemenu(gamemenu)
            with state_lock:
                act = state_module.current_activity
                should_update = (
                    act.activity_type != ActivityType.GAMEMENU
                    or (
                        gm_obj is not None
                        and _search_str(act) != gm_obj.search_str
                    )
                )
            if should_update and gm_obj is not None:
                new_activity = Activity(ActivityType.GAMEMENU, gm_obj)
                update_activity(new_activity)
                _notify_gui(new_activity)
                with state_lock:
                    state_module.menu_start_time = time.time()
                    state_module.current_timer_type = "menu"
                log(f"Detected gamemenu: {gm_obj.gamemenu_name}")
        elif current == ActivityType.GAMEMENU:
            self._empty_gamemenu += 1
            recent_party = (time.time() - self._last_valid_party) < 20.0
            needed = 2 if (hud_visible or recent_party) else 10
            if self._empty_gamemenu >= needed:
                self._empty_gamemenu = 0
                self._exit_to_overworld("Left menu/cutscene")

        # ---- HUD evidence ---------------------------------------------------
        if hud_visible:
            self._last_valid_party = time.time()
            with state_lock:
                is_loading = (
                    state_module.current_activity.activity_type == ActivityType.LOADING
                )
                was_map = (
                    state_module.current_activity.activity_type
                    == ActivityType.MAP_LOCATION
                )
            if was_map:
                self._exit_to_overworld("Closed map - back to exploring")
            elif is_loading:
                new_activity = Activity(ActivityType.LOCATION, None)
                update_activity(new_activity)
                _notify_gui(new_activity)
                log("Promoted LOADING to Exploring Teyvat (party visible)")

        # ---- location / boss / commission / map location --------------------
        if loc and loc.get("commission"):
            if current != ActivityType.COMMISSION:
                new_activity = Activity(
                    ActivityType.COMMISSION, state_module.prev_location
                )
                update_activity(new_activity)
                _notify_gui(new_activity)
                log("Detected doing commissions")
        elif loc and loc.get("map_location"):
            map_info = loc["map_location"]
            found = self.data.search_location(map_info["name"])
            if found is not None and not hud_visible:
                with state_lock:
                    act = state_module.current_activity
                    same = (
                        act.activity_type == ActivityType.MAP_LOCATION
                        and _search_str(act) == found.search_str
                    )
                if not same:
                    new_activity = Activity(ActivityType.MAP_LOCATION, found)
                    update_activity(new_activity)
                    _notify_gui(new_activity)
                    with state_lock:
                        state_module.prev_location = found
                    log(f"Browsing map: {found.location_name}")
        elif loc and loc.get("location"):
            found = self.data.search_location(loc["location"]["name"])
            if found is not None:
                with state_lock:
                    act = state_module.current_activity
                    should_update = (
                        act.activity_type == ActivityType.GAMEMENU
                        or act.activity_type == ActivityType.LOADING
                        or (
                            act.activity_type == ActivityType.LOCATION
                            and _search_str(act) != found.search_str
                        )
                    )
                if should_update:
                    new_activity = Activity(ActivityType.LOCATION, found)
                    update_activity(new_activity)
                    _notify_gui(new_activity)
                    with state_lock:
                        state_module.prev_location = found
                    log(f"Location: {found.location_name}")

        if loc and loc.get("boss"):
            found = self.data.search_boss(loc["boss"]["name"])
            if found is not None:
                with state_lock:
                    act = state_module.current_activity
                    same = (
                        act.activity_type == ActivityType.WORLD_BOSS
                        and _search_str(act) == found.search_str
                    )
                if not same:
                    new_activity = Activity(ActivityType.WORLD_BOSS, found)
                    update_activity(new_activity)
                    _notify_gui(new_activity)
                    log(f"Boss: {found.boss_name}")

        if domain:
            found = self.data.search_domain(domain)
            if found is not None:
                with state_lock:
                    act = state_module.current_activity
                    same = (
                        act.activity_type == ActivityType.DOMAIN
                        and _search_str(act) == found.search_str
                    )
                if not same:
                    new_activity = Activity(ActivityType.DOMAIN, found)
                    update_activity(new_activity)
                    _notify_gui(new_activity)
                    log(f"Domain: {found.domain_name}")

        # ---- bookkeeping: prev_non_idle + pause state ----------------------
        any_evidence = (
            hud_visible
            or party_detected
            or party_flag
            or bool(gamemenu)
            or bool(domain)
        )
        if any_evidence:
            self._last_evidence_time = time.time()
            with state_lock:
                act = state_module.current_activity
                if not act.is_idle():
                    state_module.prev_non_idle_activity = act

        with state_lock:
            current = state_module.current_activity.activity_type

        # Sustained no-evidence => game paused (menu open, alt-tab overlay...)
        if not any_evidence and current not in (
            ActivityType.PAUSED,
            ActivityType.LOADING,
        ):
            if time.time() - getattr(self, "_last_evidence_time", time.time()) > 10.0:
                new_activity = Activity(
                    ActivityType.PAUSED, state_module.prev_non_idle_activity
                )
                update_activity(new_activity)
                _notify_gui(new_activity)
                log("No activity detected for a while - marking game paused")
        elif any_evidence and current == ActivityType.PAUSED:
            self._exit_to_overworld("Activity resumed")

        # ---- LOADING timeout fallback ----------------------------------------
        # If LOADING persists for > 45 s with no evidence, assume the game is
        # running and transition to LOCATION. This handles cutscenes / UI states
        # where no sensor can see the party HUD or menu text.
        if current == ActivityType.LOADING:
            loading_age = time.time() - self._loading_start_time
            if loading_age > 45.0:
                new_activity = Activity(ActivityType.LOCATION, None)
                update_activity(new_activity)
                _notify_gui(new_activity)
                log("LOADING timeout - assuming exploring Teyvat")
                self._loading_start_time = time.time()
        else:
            self._loading_start_time = time.time()

        return 0.25