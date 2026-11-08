"""Sensor coordinator: consumes blackboard entries and runs the activity state machine.

Transitions are driven by sensor evidence. Rules:
 - GAMEMENU/PARTY_SETUP exit on missing label (+ HUD evidence or timeout)
 - LOADING -> LOCATION promotion on party validation
 - active-character switching only into known slots
"""

import time
from typing import Callable, Optional

from core.blackboard import (
    blackboard,
    CHAR_MAX_AGE_COORDINATOR,
    CHAR_MAX_AGE_HUD,
    LOCATION_MAX_AGE,
    MENU_MAX_AGE,
)
from core.datatypes import Activity, ActivityType, Character, GamemenuType, DEBUG_MODE
from core.log_utils import log
from core.sensors import CharSensor, LocationSensor, MenuSensor
from core.domain_handler import DomainHandler
from core.search_index import SearchIndex
from core import state as state_module
from core.state import (
    state_lock,
    update_activity,
    update_character,
    set_active_character,
    get_current_characters,
    gui_callback,
)


# Exit-timing thresholds (seconds without supporting evidence)
PARTY_SETUP_EXIT_AFTER = 5.0
GAMEMENU_EXIT_AFTER = 3.5
GAMEMENU_EXIT_FAST = 2.5
CUTSCENE_EXIT_AFTER = 15.0
LOADING_TIMEOUT = 45.0
PAUSE_NO_EVIDENCE_AFTER = 10.0
RECENT_PARTY_WINDOW = 20.0


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
    def __init__(self, reader, data):
        self.reader = reader
        self.data = data
        self.search_index = SearchIndex(data)

        from CONFIG import PARTY_SETUP_COORD, DOMAIN_COORD, MAP_LOC_COORD, LOCATION_COORD, BOSS_COORD

        def loc_coords():
            return LOCATION_COORD, BOSS_COORD, MAP_LOC_COORD

        def menu_coords():
            return {"gamemenu": PARTY_SETUP_COORD, "domain": DOMAIN_COORD}

        self.sensors = [
            CharSensor(reader, data, self.search_index, "characters", 2.0),
            LocationSensor(
                reader, data, self.search_index, loc_coords, "location", 0.5,
                boss_every=6, characters_key="characters", menus_key="menus",
            ),
            MenuSensor(reader, data, self.search_index, menu_coords, "menus", 2.0),
        ]
        self.char_sensor = self.sensors[0]
        self.domain_handler = DomainHandler(log)

        # Time-based timers
        self._party_setup_last_seen = 0.0
        self._gamemenu_last_seen = 0.0
        self._last_valid_party = 0.0
        self._loading_start_time = time.time()
        self._last_evidence_time = time.time()
        self._last_heartbeat = 0.0
        self._last_static_image_key = None
        self._last_special_ui = None

    def start(self):
        for s in self.sensors:
            s.start()

    def stop(self):
        for s in self.sensors:
            s.stop()

    def _read(self, key: str, max_age: float):
        return blackboard.read(key, max_age=max_age)

    def _build_character(self, name):
        c = self.search_index.search_character(name)
        if c is not None:
            return c
        return Character(
            character_display_name=name,
            image_key="char_unknown",
            search_str=name.lower(),
        )

    def _resolve_by_name(self, value, search_fn, data_list, name_attr):
        if not value:
            return None
        found = search_fn(value)
        if found is not None:
            return found
        v = str(value).strip().lower()
        return next(
            (o for o in data_list if str(getattr(o, name_attr)).lower() == v),
            None,
        )

    def _read_shared_config(self) -> dict:
        from core.shared_config import get_shared_config
        return get_shared_config()

    def _sync_shared_config(self):
        try:
            shared = self._read_shared_config()
            new_key = (shared.get("DEBUG_STATIC_IMAGE"), shared.get("DEBUG_STATIC_IMAGE_PATH"))
            if new_key != getattr(self, "_last_static_image_key", None):
                self._last_static_image_key = new_key
                self.char_sensor._load_static_image()
        except Exception:
            pass

    # ---- Actions (side effects) ----
    def _act_enter_party_setup(self, *_):
        new_activity = Activity(ActivityType.PARTY_SETUP, state_module.prev_non_idle_activity)
        update_activity(new_activity)
        _notify_gui(new_activity)
        log("Entered Party Setup")

    def _act_exit_party_setup(self, *_):
        self.char_sensor.reset_slot_cache()
        self._exit_to_overworld("Left party setup")

    def _act_enter_gamemenu(self, co, gm_obj, *_):
        new_activity = Activity(ActivityType.GAMEMENU, gm_obj)
        update_activity(new_activity)
        _notify_gui(new_activity)
        with state_lock:
            state_module.menu_start_time = time.time()
            state_module.current_timer_type = "menu"
        log(f"Detected gamemenu: {gm_obj.gamemenu_name}")

    def _act_exit_gamemenu(self, *_):
        self._exit_to_overworld("Left menu/cutscene")

    def _act_enter_domain(self, co, found, *_):
        co.domain_handler.activate(found)
        new_activity = Activity(ActivityType.DOMAIN, found)
        update_activity(new_activity)
        _notify_gui(new_activity)
        log(f"Domain: {found.domain_name}")

    def _act_exit_domain(self, *_):
        self._exit_to_overworld("Domain finished - exploring")

    def _act_enter_commission(self, *_):
        new_activity = Activity(ActivityType.COMMISSION, state_module.prev_location)
        update_activity(new_activity)
        _notify_gui(new_activity)
        log("Detected doing commissions")

    def _act_enter_map_location(self, co, found, *_):
        new_activity = Activity(ActivityType.MAP_LOCATION, found)
        update_activity(new_activity)
        _notify_gui(new_activity)
        with state_lock:
            state_module.prev_location = found
        log(f"Browsing map: {found.location_name}")

    def _act_enter_location(self, co, found, *_):
        new_activity = Activity(ActivityType.LOCATION, found)
        update_activity(new_activity)
        _notify_gui(new_activity)
        with state_lock:
            state_module.prev_location = found
        log(f"Location: {found.location_name}")

    def _act_enter_world_boss(self, co, found, *_):
        new_activity = Activity(ActivityType.WORLD_BOSS, found)
        update_activity(new_activity)
        _notify_gui(new_activity)
        log(f"Boss: {found.boss_name}")

    def _act_promote_loading(self, *_):
        new_activity = Activity(ActivityType.LOCATION, None)
        update_activity(new_activity)
        _notify_gui(new_activity)
        log("Promoted LOADING to Exploring Teyvat (party visible)")

    def _act_enter_paused(self, *_):
        new_activity = Activity(ActivityType.PAUSED, state_module.prev_non_idle_activity)
        update_activity(new_activity)
        _notify_gui(new_activity)
        log("No activity detected for a while - marking game paused")

    def _act_exit_paused(self, *_):
        self._exit_to_overworld("Activity resumed")

    def _act_update_active_char(self, hint, *_):
        set_active_character(hint)
        cur = get_current_characters()[hint - 1]
        if cur:
            log(f'Active character: "{cur.character_display_name}"')

    def _act_reset_active_char(self, *_):
        set_active_character(0)

    def _exit_to_overworld(self, msg: str):
        new_activity = Activity(ActivityType.LOCATION, state_module.prev_location)
        update_activity(new_activity)
        _notify_gui(new_activity)
        log(msg)

    # ---- Main tick ----
    def tick(self) -> float:
        """One coordinator iteration. Returns sleep duration."""
        self._sync_shared_config()
        now = time.time()

        # Heartbeat with OCR perf stats
        if now - self._last_heartbeat >= 10.0:
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

        chars = self._read("characters", CHAR_MAX_AGE_COORDINATOR)
        loc = self._read("location", LOCATION_MAX_AGE)
        menus = self._read("menus", MENU_MAX_AGE)

        # Check for special UI patterns (e.g., shadow realm)
        special_ui = chars.get("special_ui") if chars else None
        if special_ui and special_ui.get("activity_type") == "shadow_realm":
            from core.datatypes import Location
            shadow_loc = Location(
                search_str=special_ui["search_str"],
                location_name=special_ui["display_name"],
                subarea="",
                country="In Teyvat",
                image_key=special_ui["image_key"]
            )
            new_activity = Activity(ActivityType.LOCATION, shadow_loc)
            update_activity(new_activity)
            _notify_gui(new_activity)
            if self._last_special_ui != "shadow_realm":
                log(f"Special UI detected: {special_ui['display_name']}")
                self._last_special_ui = "shadow_realm"
            return 0.25
        elif self._last_special_ui == "shadow_realm":
            log("Left Shadow Realm")
            self._last_special_ui = None

        # HUD evidence
        hud_visible = False
        party_detected = False
        if chars and (now - chars.get("written_at", 0)) < CHAR_MAX_AGE_HUD:
            hud_visible = bool(chars.get("hud_visible"))
            slots = chars.get("slots") or []
            party_detected = any(s and s.get("name") for s in slots)

        # Party slots
        if chars and chars.get("slots"):
            hud_confirmed = bool(chars.get("hud_visible"))
            self._update_party_slots(chars, hud_confirmed)

        # Active character
        self._eval_active_character(chars)

        with state_lock:
            current = state_module.current_activity.activity_type

        # Transition evaluations (in priority order)
        # 1. Party Setup
        party_flag = bool(menus and menus.get("party_setup"))
        if party_flag:
            self._party_setup_last_seen = now
            if current != ActivityType.PARTY_SETUP:
                self._act_enter_party_setup()
        elif current == ActivityType.PARTY_SETUP and (now - self._party_setup_last_seen >= PARTY_SETUP_EXIT_AFTER):
            self._act_exit_party_setup()

        # 2. Gamemenu
        gamemenu = menus.get("gamemenu") if menus else None
        if gamemenu:
            self._gamemenu_last_seen = now
            gm_search = menus.get("gamemenu_search") if menus else None
            gm_obj = self.search_index.search_gamemenu(gm_search or gamemenu)
            if gm_obj is None:
                gm_obj = self._resolve_by_name(
                    gamemenu, self.search_index.search_gamemenu,
                    self.data.gamemenus, "gamemenu_name")
            if gm_obj is not None:
                with state_lock:
                    act = state_module.current_activity
                    should_update = (
                        act.activity_type != ActivityType.GAMEMENU
                        or _search_str(act) != gm_obj.search_str
                    )
                if should_update:
                    self._act_enter_gamemenu(gm_obj)
        elif current == ActivityType.GAMEMENU and self._g_gamemenu_exit(chars, loc, menus, now):
            self._act_exit_gamemenu()

        # 3. HUD evidence (cutscene/map/loading exit)
        if hud_visible:
            self._last_valid_party = now
            was_cutscene = (
                current == ActivityType.GAMEMENU
                and getattr(getattr(state_module.current_activity, "activity_data", None), "gamemenu_type", None) == GamemenuType.CUTSCENE
            )
            was_map = current == ActivityType.MAP_LOCATION
            is_loading = current == ActivityType.LOADING
            if was_cutscene:
                self._gamemenu_last_seen = now
                self.char_sensor.reset_slot_cache()
                self._exit_to_overworld("Left cutscene - party HUD visible")
            elif was_map:
                self._exit_to_overworld("Closed map - back to exploring")
            elif is_loading:
                self._act_promote_loading()

        # 4. Location / Boss / Commission / Map Location
        if loc:
            if loc.get("commission") and current != ActivityType.COMMISSION:
                self._act_enter_commission()
            elif loc.get("map_location"):
                map_info = loc["map_location"]
                found = self._resolve_by_name(
                    map_info["name"], self.search_index.search_location,
                    self.data.locations, "location_name")
                if found is not None and not hud_visible:
                    with state_lock:
                        act = state_module.current_activity
                        same = (
                            act.activity_type == ActivityType.MAP_LOCATION
                            and _search_str(act) == found.search_str
                        )
                    if not same:
                        self._act_enter_map_location(found)
            elif loc.get("location"):
                found = self._resolve_by_name(
                    loc["location"]["name"], self.search_index.search_location,
                    self.data.locations, "location_name")
                if found is not None:
                    with state_lock:
                        act = state_module.current_activity
                        should_update = (
                            act.activity_type == ActivityType.GAMEMENU
                            or act.activity_type == ActivityType.LOADING
                            or (act.activity_type == ActivityType.LOCATION
                                and _search_str(act) != found.search_str)
                        )
                    if should_update:
                        self._act_enter_location(found)

            if loc.get("boss") and not self.domain_handler.active:
                found = self._resolve_by_name(
                    loc["boss"]["name"], self.search_index.search_boss,
                    self.data.bosses, "boss_name")
                if found is not None:
                    with state_lock:
                        act = state_module.current_activity
                        same = (
                            act.activity_type == ActivityType.WORLD_BOSS
                            and _search_str(act) == found.search_str
                        )
                    if not same:
                        self._act_enter_world_boss(found)

        # 5. Domain
        domain = menus.get("domain") if menus else None
        if domain:
            d_search = menus.get("domain_search") if menus else None
            found = self.search_index.search_domain(d_search) if d_search else None
            if found is None:
                found = self._resolve_by_name(
                    domain, self.search_index.search_domain,
                    self.data.domains, "domain_name")
            if found is not None:
                with state_lock:
                    act = state_module.current_activity
                    same = (
                        act.activity_type == ActivityType.DOMAIN
                        and _search_str(act) == found.search_str
                    )
                if not same:
                    self._act_enter_domain(found)

        # 6. Domain handler (timer-based re-entry)
        dh = self.domain_handler
        if loc and loc.get("boss_raw_ts"):
            raw_fresh = now - loc["boss_raw_ts"] < 8.0
            dh.feed_timer(bool(raw_fresh and loc.get("boss_raw")))
        if menus and menus.get("reward_cutscene"):
            dh.feed_reward_cutscene(True)
        if dh.tick():
            self._act_exit_domain()
        elif (
            not dh.active
            and current in (ActivityType.LOCATION, ActivityType.COMMISSION)
            and not bool(menus and menus.get("domain"))
            and not bool(menus and menus.get("gamemenu"))
            and loc and loc.get("boss_raw_ts")
            and now - loc["boss_raw_ts"] < 8.0
            and dh.matches_timer(loc.get("boss_raw", ""))
        ):
            dh.activate(dh.last_domain)
            new_activity = Activity(
                ActivityType.DOMAIN,
                dh.last_domain or state_module.prev_location,
            )
            update_activity(new_activity)
            _notify_gui(new_activity)
            log("Domain timer re-detected - back in domain")

        # 7. Pause state
        any_evidence = self._any_evidence(chars, loc, menus, current, now)
        if not any_evidence and current not in (ActivityType.PAUSED, ActivityType.LOADING, ActivityType.PARTY_SETUP):
            if now - self._last_evidence_time > PAUSE_NO_EVIDENCE_AFTER:
                self._act_enter_paused()
        elif any_evidence and current == ActivityType.PAUSED:
            self._act_exit_paused()

        # 8. Loading timeout
        if current == ActivityType.LOADING and (now - self._loading_start_time > LOADING_TIMEOUT):
            new_activity = Activity(ActivityType.LOCATION, None)
            update_activity(new_activity)
            _notify_gui(new_activity)
            log("LOADING timeout - assuming exploring Teyvat")
            self._loading_start_time = now
        elif current != ActivityType.LOADING:
            self._loading_start_time = now

        return 0.25

    # ---- Helpers ----
    def _g_gamemenu_exit(self, chars, loc, menus, now):
        gamemenu = menus.get("gamemenu") if menus else None
        with state_lock:
            current = state_module.current_activity.activity_type
        if current != ActivityType.GAMEMENU or gamemenu:
            return False
        recent_party = (now - self._last_valid_party) < RECENT_PARTY_WINDOW
        with state_lock:
            _act = state_module.current_activity
            _is_cutscene = (
                getattr(_act, "activity_data", None) is not None
                and getattr(_act.activity_data, "gamemenu_type", None) == GamemenuType.CUTSCENE
            )
        hud_visible = False
        if chars and (now - chars.get("written_at", 0)) < CHAR_MAX_AGE_HUD:
            hud_visible = bool(chars.get("hud_visible"))
        allowed_gap = (
            CUTSCENE_EXIT_AFTER if _is_cutscene
            else (GAMEMENU_EXIT_FAST if (hud_visible or recent_party) else GAMEMENU_EXIT_AFTER)
        )
        return now - self._gamemenu_last_seen >= allowed_gap

    def _any_evidence(self, chars, loc, menus, current, now):
        hud_visible = False
        party_detected = False
        if chars and (now - chars.get("written_at", 0)) < CHAR_MAX_AGE_HUD:
            hud_visible = bool(chars.get("hud_visible"))
            slots = chars.get("slots") or []
            party_detected = any(s and s.get("name") for s in slots)
        party_flag = bool(menus and menus.get("party_setup"))
        gamemenu = menus.get("gamemenu") if menus else None
        domain = menus.get("domain") if menus else None
        return (
            hud_visible or party_detected or party_flag
            or current == ActivityType.PARTY_SETUP
            or bool(gamemenu) or bool(domain)
            or self.domain_handler.active
        )

    def _update_party_slots(self, chars, hud_confirmed):
        for idx in range(1, len(chars["slots"])):
            slot = chars["slots"][idx]
            if slot and slot.get("name"):
                prev = get_current_characters()[idx - 1]
                if prev is None or prev.character_display_name != slot["name"]:
                    update_character(idx - 1, self._build_character(slot["name"]))
                    log(f"Party slot {idx}: {slot['name']}")
            elif slot is None and hud_confirmed and get_current_characters()[idx - 1] is not None:
                update_character(idx - 1, None)
                log(f"Party slot {idx}: cleared (slot empty)")

    def _eval_active_character(self, chars):
        if chars and chars.get("active_slot_hint") is not None:
            hint = chars["active_slot_hint"]
            if 1 <= hint <= len(get_current_characters()):
                cur = get_current_characters()[hint - 1]
                with state_lock:
                    different = hint != state_module.current_active_character
                if different and cur is not None:
                    self._act_update_active_char(hint)
        elif (
            chars
            and chars.get("active_slot_hint") is None
            and state_module.current_active_character != 0
            and state_module.current_activity.activity_type
            not in (ActivityType.LOADING, ActivityType.PARTY_SETUP)
        ):
            self._act_reset_active_char()