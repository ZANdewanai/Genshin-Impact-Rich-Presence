"""Sensor coordinator: consumes blackboard JSONs and runs the activity state
machine.

All transition/latch-prevention rules live here:
 - GAMEMENU/PARTY_SETUP exits on missing label (+ HUD evidence or timeout)
 - LOADING -> LOCATION promotion on party validation
 - active-character switching only into known slots
"""

import os
import time

from core.blackboard import (
    read_json,
    CHAR_MAX_AGE_COORDINATOR,
    CHAR_MAX_AGE_HUD,
    LOCATION_MAX_AGE,
    MENU_MAX_AGE,
)
from core.datatypes import Activity, ActivityType, Character, GamemenuType, DEBUG_MODE
from core.log_utils import log
from core.sensors import CharSensor, LocationSensor, MenuSensor
from core.domain_handler import DomainHandler
from core import state as state_module
from core.state import (
    state_lock,
    update_activity,
    update_character,
    set_active_character,
    get_current_characters,
    gui_callback,
)

# Exit-timing thresholds (seconds without supporting evidence). These are the
# elapsed-time equivalents of the previous miss-count rules (which assumed a
# ~0.25s coordinator tick) - time-based so they stay correct regardless of
# actual tick rate or error-path slowdowns.
PARTY_SETUP_EXIT_AFTER = 5.0        # must exceed the MenuSensor refresh
                                    # cadence (2s) so a single missed label
                                    # OCR can't flap the state
GAMEMENU_EXIT_AFTER = 3.5           # no recent HUD evidence (was: 10 misses)
GAMEMENU_EXIT_FAST = 2.5            # recent HUD evidence (was: 2 misses)
CUTSCENE_EXIT_AFTER = 15.0          # was: 60 misses


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
    def __init__(self, reader, data, output_dir="sensor_data"):
        self.reader = reader
        self.data = data
        import os
        out = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), output_dir
        )
        self.paths = {
            "characters": (out + "/characters.json", CHAR_MAX_AGE_COORDINATOR),
            "location": (out + "/location.json", LOCATION_MAX_AGE),
            "menus": (out + "/menus.json", MENU_MAX_AGE),
        }
        from CONFIG import (
            PARTY_SETUP_COORD,
            DOMAIN_COORD,
        )
        # NOTE: character name/number coords are auto-detected per party
        # size (1P-5P canonical sets) inside CharSensor; location/boss/menu/
        # maploc coords come from core.detection's resolution-updated
        # globals at scan time.

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
            CharSensor(reader, data, self.paths["characters"][0], 2.0,
                       menus_path=self.paths["menus"][0]),
            LocationSensor(
                reader, data, loc_coords, self.paths["location"][0], 0.5,
                boss_every=6,  # ~3s: fast enough to track the domain timer
                characters_path=self.paths["characters"][0],
                menus_path=self.paths["menus"][0],
            ),
            MenuSensor(reader, data, menu_coords, self.paths["menus"][0], 2.0),
        ]
        # Store reference to CharSensor for cache reset during state transitions
        self.char_sensor = self.sensors[0]
        # Domain-session state (label entry, timer keep-alive, reward
        # prompt, grace fallback, retry re-entry) - see DomainHandler
        self.domain_handler = DomainHandler(log)
        # Time-based state-machine timers (see module constants)
        self._party_setup_last_seen = 0.0
        self._gamemenu_last_seen = 0.0
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
    @staticmethod
    def _resolve_by_name(value, search_fn, data_list, name_attr):
        """Resolve a sensor-reported label to its data object.

        Sensors report display names but search_fn matches against search_str;
        the two frequently differ (cutscenes, domains with punctuation...).
        Search first, then fall back to an exact case-insensitive label match.
        """
        if not value:
            return None
        found = search_fn(value)
        if found is not None:
            return found
        v = str(value).strip().lower()
        return next(
            (o for o in data_list
             if str(getattr(o, name_attr)).lower() == v),
            None,
        )

    def _read_shared_config(self) -> dict:
        """mtime-gated shared_config.json reader (see core.shared_config)."""
        from core.shared_config import get_shared_config
        return get_shared_config()

    def _sync_shared_config(self):
        """Sync debug flags from shared_config so GUI toggles take effect
        without restarting the engine."""
        try:
            shared = self._read_shared_config()
            if "DEBUG_MODE" in shared:
                import core.datatypes as _dt
                _dt.DEBUG_MODE.value = bool(shared["DEBUG_MODE"])
            if "DEBUG_CHARACTER_MODE" in shared:
                import core.datatypes as _dt
                _dt.DEBUG_CHARACTER_MODE.value = bool(shared["DEBUG_CHARACTER_MODE"])
            if "DEBUG_STATIC_IMAGE" in shared:
                import CONFIG as _cfg
                if hasattr(_cfg, "DEBUG_STATIC_IMAGE"):
                    _cfg.DEBUG_STATIC_IMAGE = bool(shared["DEBUG_STATIC_IMAGE"])
            new_path = shared.get("DEBUG_STATIC_IMAGE_PATH")
            if new_path is not None and new_path != getattr(self, "_last_static_image_path", None):
                self._last_static_image_path = new_path
                if hasattr(self.char_sensor, "_load_static_image"):
                    self.char_sensor._load_static_image()
        except Exception:
            pass

    def tick(self) -> float:
        """One coordinator iteration. Returns sleep duration."""
        self._sync_shared_config()

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
        if chars and (time.time() - chars.get("written_at", 0)) < CHAR_MAX_AGE_HUD:
            hud_visible = bool(chars.get("hud_visible"))
            # Detected party slot names are themselves strong evidence the
            # party HUD is on screen - count them so a flaky hud_visible OCR
            # check can't wrongly "pause" an active exploration session.
            slots = chars.get("slots") or []
            party_detected = any(s and s.get("name") for s in slots)

        # ---- party slots -------------------------------------------------
        if chars and chars.get("slots"):
            # If the HUD was confirmed visible this round, empty slots are
            # REAL empty slots (party shrunk in the setup screen) - clear the
            # stale characters instead of leaving ghosts behind. On rounds
            # where the HUD wasn't seen we leave state untouched so a single
            # OCR miss can't wipe a real slot.
            hud_confirmed = bool(chars.get("hud_visible"))
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

        # ---- active character --------------------------------------------
        if chars and chars.get("active_slot_hint") is not None:
            hint = chars["active_slot_hint"]
            if 1 <= hint <= len(get_current_characters()):
                cur = get_current_characters()[hint - 1]
                with state_lock:
                    different = hint != state_module.current_active_character
                if different and cur is not None:
                    set_active_character(hint)
                    log(f'Active character: "{cur.character_display_name}"')

        # ---- activity state machine --------------------------------------
        party_flag = bool(menus and menus.get("party_setup"))
        gamemenu = menus.get("gamemenu") if menus else None
        domain = menus.get("domain") if menus else None

        with state_lock:
            current = state_module.current_activity.activity_type

        # ---- party setup enter/exit (time-based: PARTY_SETUP_EXIT_AFTER) ----
        if party_flag:
            self._party_setup_last_seen = time.time()
            if current != ActivityType.PARTY_SETUP:
                new_activity = Activity(
                    ActivityType.PARTY_SETUP, state_module.prev_non_idle_activity
                )
                update_activity(new_activity)
                _notify_gui(new_activity)
                log("Entered Party Setup")
        elif current == ActivityType.PARTY_SETUP:
            if time.time() - getattr(self, "_party_setup_last_seen", time.time()) >= PARTY_SETUP_EXIT_AFTER:
                # The party may have been edited/resized in the setup screen -
                # force a fresh full re-detect across all 5 configurations.
                self.char_sensor.reset_slot_cache()
                self._exit_to_overworld("Left party setup")

        # ---- gamemenu/cutscene enter/exit (time-based timers) ----------------
        if gamemenu:
            self._gamemenu_last_seen = time.time()
            # Prefer the identity the sensor already resolved; fall back to
            # searching, then to an exact label match.
            gm_search = menus.get("gamemenu_search") if menus else None
            gm_obj = self.data.search_gamemenu(gm_search or gamemenu)
            if gm_obj is None:
                gm_obj = self._resolve_by_name(
                    gamemenu, self.data.search_gamemenu,
                    self.data.gamemenus, "gamemenu_name")
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
            recent_party = (time.time() - self._last_valid_party) < 20.0
            # Cutscenes hide their label for long stretches (dialogue without
            # the auto/skip prompt on screen) - require a long absence before
            # declaring exit so they don't flap every few seconds.
            with state_lock:
                _act = state_module.current_activity
                _is_cutscene = (
                    getattr(_act, "activity_data", None) is not None
                    and getattr(_act.activity_data, "gamemenu_type", None)
                    == GamemenuType.CUTSCENE
                )
            allowed_gap = (
                CUTSCENE_EXIT_AFTER if _is_cutscene
                else (GAMEMENU_EXIT_FAST if (hud_visible or recent_party)
                      else GAMEMENU_EXIT_AFTER)
            )
            if time.time() - getattr(self, "_gamemenu_last_seen", time.time()) >= allowed_gap:
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
                was_cutscene = (
                    state_module.current_activity.activity_type == ActivityType.GAMEMENU
                    and getattr(
                        getattr(state_module.current_activity, "activity_data", None),
                        "gamemenu_type",
                        None,
                    )
                    == GamemenuType.CUTSCENE
                )
                # NOTE: no was_domain here - the party HUD coexists with the
                # domain timer; DOMAIN exits are handled by DomainHandler
                # (timer grace / reward prompt), not by HUD visibility.
            # The party HUD never shows during a cutscene - seeing it means we
            # are back in the overworld, so exit immediately regardless of the
            # sticky cutscene timeout.
            if was_cutscene:
                self._gamemenu_last_seen = time.time()
                # Reset CharSensor's OCR cache so it re-reads character
                # slots fresh after a cutscene (trial character parties,
                # party size changes, etc. differ from pre-cutscene state)
                self.char_sensor.reset_slot_cache()
                self._exit_to_overworld("Left cutscene - party HUD visible")
            elif was_map:
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
            found = self._resolve_by_name(
                map_info["name"], self.data.search_location,
                self.data.locations, "location_name")
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
            found = self._resolve_by_name(
                loc["location"]["name"], self.data.search_location,
                self.data.locations, "location_name")
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

        if loc and loc.get("boss") and not self.domain_handler.active:
            # While a domain session is live, top-center text is the domain
            # timer - never let it leak into world-boss detection
            # (DomainHandler.suppresses_boss()).
            found = self._resolve_by_name(
                loc["boss"]["name"], self.data.search_boss,
                self.data.bosses, "boss_name")
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
            d_search = menus.get("domain_search") if menus else None
            found = self.data.search_domain(d_search) if d_search else None
            if found is None:
                found = self._resolve_by_name(
                    domain, self.data.search_domain,
                    self.data.domains, "domain_name")
            if found is not None:
                # Activate/refresh the domain session on the banner label
                self.domain_handler.activate(found)
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

        # ---- DomainHandler tick ---------------------------------------------
        # Feed the observable signals, then run the lifecycle. All domain
        # rules live in the handler; nothing here bleeds into other paths.
        dh = self.domain_handler
        if loc and loc.get("boss_raw_ts"):
            raw_fresh = time.time() - loc["boss_raw_ts"] < 8.0
            dh.feed_timer(bool(raw_fresh and loc.get("boss_raw")))
        if menus and menus.get("reward_cutscene"):
            dh.feed_reward_cutscene(True)
        if dh.tick():
            self._exit_to_overworld("Domain finished - exploring")
        elif (
            not dh.active
            and current in (ActivityType.LOCATION, ActivityType.COMMISSION)
            and not bool(domain)
            and not bool(gamemenu)
            and loc and loc.get("boss_raw_ts")
            and time.time() - loc["boss_raw_ts"] < 8.0
            and dh.matches_timer(loc.get("boss_raw", ""))
        ):
            # Timer digits reappeared outside a session (challenge retry):
            # back to DOMAIN, reusing the remembered domain.
            dh.activate(dh.last_domain)
            new_activity = Activity(
                ActivityType.DOMAIN,
                dh.last_domain or state_module.prev_location,
            )
            update_activity(new_activity)
            _notify_gui(new_activity)
            log("Domain timer re-detected - back in domain")

        # ---- bookkeeping: prev_non_idle + pause state ----------------------
        # PARTY_SETUP counts as evidence for the CLOCK (not as an activity
        # transition) so the 10s no-evidence timer doesn't half-elapsed while
        # the user sits in the setup screen and fire right after they leave.
        any_evidence = (
            hud_visible
            or party_detected
            or party_flag
            or current == ActivityType.PARTY_SETUP
            or bool(gamemenu)
            or bool(domain)
            or dh.active  # domain session owns its own keep-alive/exit rules
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
        # PARTY_SETUP is excluded: its screen shows the party but NOT the
        # overworld HUD the sensors read, so it would false-positive here.
        if not any_evidence and current not in (
            ActivityType.PAUSED,
            ActivityType.LOADING,
            ActivityType.PARTY_SETUP,
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
