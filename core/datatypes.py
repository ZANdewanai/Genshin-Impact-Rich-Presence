"""
Contains data types modelling .csv files in ./data/

The constructors for these classes must have arguments listed in the same order as the columns in the .csv files.
"""

from __future__ import annotations
from enum import Enum, auto
from typing import Optional, Union
from CONFIG import DEBUG_MODE, MC_AETHER, WANDERER_NAME, USERNAME
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler, FileModifiedEvent
import csv
import time
import os
import difflib


class Boss:
    """
    World bosses in bosses.csv
    """

    def __init__(self, search_str, boss_name, image_key):
        self.search_str = search_str
        self.boss_name = boss_name
        self.image_key = image_key

    def __eq__(self, other: Boss) -> bool:
        if not isinstance(other, Boss):
            return False
        return (
            self.search_str == other.search_str
            and self.boss_name == other.boss_name
            and self.image_key == other.image_key
        )


class Character:
    """
    Playable characters in characters.csv
    """

    def __init__(self, search_str, image_key, character_display_name):
        self.search_str = search_str
        self.image_key = image_key
        self.character_display_name = character_display_name

    def __eq__(self, other: Character) -> bool:
        if not isinstance(other, Character):
            return False

        return (
            self.search_str == other.search_str
            and self.image_key == other.image_key
            and self.character_display_name == other.character_display_name
        )


class DomainType(Enum):
    FORGERY = 0
    BLESSING = 1
    MASTERY = 2
    TROUNCE = 3
    LIMITED_EVENT = 4  # limited time event
    ONE_TIME = 5
    """
    One time domains include story quest domains.
    """

    def from_str(domain_type_str: str) -> DomainType:
        """
        NOTE: The domain type values in domains.csv must match the strings here.
        """
        match domain_type_str.lower():
            case "forgery":
                return DomainType.FORGERY
            case "blessing":
                return DomainType.BLESSING
            case "mastery":
                return DomainType.MASTERY
            case "trounce":
                return DomainType.TROUNCE
            case "limited":
                return DomainType.LIMITED_EVENT
            case "one-time":
                return DomainType.ONE_TIME

    def __str__(self) -> str:
        match self.name:
            case "FORGERY":
                return "Domain of Forgery"
            case "BLESSING":
                return "Domain of Blessing"
            case "MASTERY":
                return "Domain of Mastery"
            case "TROUNCE":
                return "Trounce Domain"
            case "LIMITED_EVENT":
                return "Limited-Time Event Domain"
            case "ONE_TIME":
                return "Domain"


class Domain:
    """
    From domains.csv.

    THe domain type values must match string values in `DomainType.from_str`
    """

    def __init__(self, search_str, domain_name, domain_type, image_key):
        self.search_str = search_str
        self.domain_name = domain_name
        self.domain_type = DomainType.from_str(domain_type)
        self.image_key = image_key

    def __eq__(self, other: Domain) -> bool:
        if not isinstance(other, Domain):
            return False

        return (
            self.search_str == other.search_str
            and self.domain_name == other.domain_name
            and self.domain_type == other.domain_type
            and self.image_key == other.image_key
        )


class Location:
    def __init__(self, search_str, location_name, subarea, country, image_key):
        self.search_str = search_str
        self.location_name = location_name
        self.subarea = subarea
        self.country = country
        self.image_key = image_key

    def __eq__(self, other: Location) -> bool:
        if not isinstance(other, Location):
            return False

        return (
            self.search_str == other.search_str
            and self.location_name == other.location_name
            and self.subarea == other.subarea
            and self.country == other.country
            and self.image_key == other.image_key
        )


class GamemenuType(Enum):
    MENUS = 0
    CUTSCENE = 1
    SPYRAL = 2

    """
    Gamemenu   
    """

    def from_str(gamemenu_type_str: str) -> GamemenuType:
        """
        NOTE: The gamemenu type values in gamemenu.csv must match the strings here.
        """
        match gamemenu_type_str.lower():
            case "in menus":
                return GamemenuType.MENUS
            case "in a cutscene":
                return GamemenuType.CUTSCENE
            case "spyral abyss":
                return GamemenuType.SPYRAL
    def __str__(self) -> str:
        match self.name:
            case "MENUS":
                return "In Menus"
            case "CUTSCENE":
                return "In a Cutscene"
            case "SPYRAL":
                return "Spyral Abyss"

class Gamemenu:
    """
    From gamemenu.csv.

    THe gamemenu type values must match string values in `GamemenuType.from_str`
    """

    def __init__(self, search_str, gamemenu_name, gamemenu_type, image_key):
        self.search_str = search_str
        self.gamemenu_name = gamemenu_name
        self.gamemenu_type = GamemenuType.from_str(gamemenu_type)
        self.image_key = image_key

    def __eq__(self, other: Gamemenu) -> bool:
        if not isinstance(other, Gamemenu):
            return False

        return (
            self.search_str == other.search_str
            and self.gamemenu_name == other.gamemenu_name
            and self.gamemenu_type == other.gamemenu_type
            and self.image_key == other.image_key
        )
class ActivityType(Enum):
    LOADING = auto()
    """
    activity_data: `False` until active character is found, then `True`.
    If `False`, display game loading message.
    If `True`, display 'Somewhere in Teyvat'.
    """
    PAUSED = auto()
    """
    Idle activity.
    activity_data: previous non-idle `Activity` object.
    """
    PARTY_SETUP = auto()
    """
    Idle activity.
    activity_data: previous non-idle `Activity` object.
    """
    DOMAIN = auto()
    """
    activity data: `Domain` object
    """
    LOCATION = auto()
    """
    activity_data: `Location` object (when actually at a location)
    """
    MAP_LOCATION = auto()
    """
    activity_data: `Location` object (when browsing map/looking at teleport waypoints)
    """
    COMMISSION = auto()
    """
    activity_data: `Location` of last location.

    Assumes commissions are done at the last visited location (which is usually true)
    """
    WORLD_BOSS = auto()
    """
    activity_data: 'Boss' object
    """
    GAMEMENU = auto()
    """
    activity_data: 'Gamemenu' object
    """
class Activity:
    def __init__(
        self,
        activity_type: ActivityType,
        activity_data: Union[Activity, Boss, Character, Domain, Location, GameMenu, None, bool],
    ):
        self.activity_type = activity_type
        """
        Contents of `activity_data` depends on `activity_type`.

        See documentation for entries in `ActivityType` for what `activity_data` should contain.
        """

        self.activity_data = activity_data
        self.start_time = time.time()

    def _get_party_text(self) -> str:
        """Helper function to get formatted party information"""
        # This will be replaced with actual party data in the main loop
        return "PARTY_INFO_MARKER"

    def is_idle(self) -> bool:
        """
        Idle activities are activity states where no active character can be found.
        """
        return self.activity_type in [ActivityType.PAUSED, ActivityType.PARTY_SETUP, ActivityType.GAMEMENU]

    def to_update_params_dict(self) -> dict:
        """
        Creates a dictionary with parameters for `Presence.update`.

        Small image and timestamp not included and should be added later.
        """
        match self.activity_type:
            case ActivityType.LOADING:
                if not self.activity_data:
                    return {
                        "state": "Loading",
                        "large_image": "menu_paimon",
                    }
                else:
                    return {
                        "details": "Somewhere in Teyvat",
                        "state": "PARTY_INFO_MARKER",
                        "large_image": "menu_paimon",
                    }
            case ActivityType.PAUSED:
                return {
                    "state": "Game paused",
                    "large_image": "menu_paimon",
                }
            case ActivityType.PARTY_SETUP:
                return {
                    "state": "Party Setup | PARTY_INFO_MARKER",
                    "large_image": "menu_party_setup",
                }
            case ActivityType.DOMAIN:
                if self.activity_data is None:
                    return {
                        "state": "Clearing a domain",
                        "large_image": "menu_paimon",
                    }
                return {
                    "details": self.activity_data.domain_name,
                    "state": f"Clearing a {self.activity_data.domain_type} | PARTY_INFO_MARKER",
                    "large_image": self.activity_data.image_key,
                    "large_text": str(self.activity_data.domain_type),
                }
            case ActivityType.GAMEMENU:
                if self.activity_data is None:
                    return {
                        "state": "In Menus",
                        "large_image": "menu_paimon",
                    }
                return {
                    "details": self.activity_data.gamemenu_name,
                    "state": f"{self.activity_data.gamemenu_type}",
                    "large_image": self.activity_data.image_key,
                    "large_text": str(self.activity_data.gamemenu_type),
                }
            case ActivityType.LOCATION:
                if self.activity_data is None:
                    return {
                        "details": "Exploring Teyvat",
                        "state": "LOCATION_PARTY_INFO",
                        "large_image": "menu_paimon",
                    }
                # Format location with subregion and region information
                location_parts = []
                if self.activity_data.location_name:
                    location_parts.append(self.activity_data.location_name)
                if hasattr(self.activity_data, 'subarea') and self.activity_data.subarea:
                    location_parts.append(self.activity_data.subarea)
                if hasattr(self.activity_data, 'country') and self.activity_data.country:
                    location_parts.append(self.activity_data.country)

                full_location_name = ", ".join(location_parts) if location_parts else self.activity_data.location_name

                return {
                    "details": f"Exploring {full_location_name}",
                    "state": "LOCATION_PARTY_INFO",  # Special marker for main loop to replace
                    "large_image": self.activity_data.image_key,
                }
            case ActivityType.MAP_LOCATION:
                if self.activity_data is None:
                    return {
                        "details": "Viewing map",
                        "state": "MAP_PARTY_INFO",
                        "large_image": "menu_paimon",
                    }
                # Format location with subregion and region information
                location_parts = []
                if self.activity_data.location_name:
                    location_parts.append(self.activity_data.location_name)
                if hasattr(self.activity_data, 'subarea') and self.activity_data.subarea:
                    location_parts.append(self.activity_data.subarea)
                if hasattr(self.activity_data, 'country') and self.activity_data.country:
                    location_parts.append(self.activity_data.country)

                full_location_name = ", ".join(location_parts) if location_parts else self.activity_data.location_name

                return {
                    "details": f"Thinking of traveling to {full_location_name}",
                    "state": "MAP_PARTY_INFO",  # Special marker for main loop to replace
                    "large_image": self.activity_data.image_key,
                }
            case ActivityType.COMMISSION:
                return {
                    "state": "Doing commissions",
                    "details": f"In {self.activity_data.location_name}, {self.activity_data.country}"
                    if self.activity_data != None
                    else "",
                    "large_image": "menu_commissions",
                }
            case ActivityType.WORLD_BOSS:
                if self.activity_data is None:
                    return {
                        "state": "Fighting a boss | PARTY_INFO_MARKER",
                        "large_image": "menu_paimon",
                    }
                return {
                    "state": f"Fighting a boss | PARTY_INFO_MARKER",
                    "details": self.activity_data.boss_name,
                    "large_image": self.activity_data.image_key,
                    "large_text": self.activity_data.boss_name,
                }
    def __eq__(self, other: Activity) -> bool:
        if not isinstance(other, Activity):
            return False
        return (
            self.activity_type == other.activity_type
            and self.activity_data == other.activity_data
        )


class Data(PatternMatchingEventHandler):
    """
    Model for all game data.

    Automatically updates data if csv files are modified.

    Inherits `PatternMatchingEventHandler` to listen for changes in CSV files in `data/`.
    """

    bosses: list[Boss] = []
    characters: list[Character] = []
    domains: list[Domain] = []
    locations: list[Location] = []
    gamemenus: list[Gamemenu] = []

    bosses_shortest_search = 0
    characters_shortest_search = 0
    domains_shortest_search = 0
    locations_shortest_search = 0
    gamemenus_shortest_search = 0

    party_capture_cache = {}
    world_boss_capture_cache = {}
    domain_capture_cache = {}
    location_capture_cache = {}
    gamemenu_capture_cache = {}

    def __init__(self):
        super().__init__(patterns=["*.csv"])  # init PatternMatchingEventHandler

        self._last_modified = time.time()
        """
        Keep track of the last time on_modified was triggered.
        Weird bug with watchdog makes modification events trigger twice.
        Have a short cooldown period between executing the modification handler.
        """

        try:
            with open("data/characters.csv", "r") as csvfile:
                reader = csv.reader(csvfile, delimiter=",")
                self.characters = []
                for row in reader:
                    c = Character(*row)
                    if (MC_AETHER and c.search_str == "aether") or (
                        not MC_AETHER and c.search_str == "lumine"
                    ):
                        c.search_str = USERNAME.lower()
                        c.character_display_name = USERNAME

                    if c.search_str == "wanderer":
                        c.search_str = WANDERER_NAME.lower()
                        c.character_display_name = WANDERER_NAME

                    self.characters.append(c)

                self.characters_shortest_search = min(
                    [len(character.search_str) for character in self.characters]
                )
                print(f"Loaded characters.csv: {len(self.characters)} characters")
        except Exception as e:
            print(f"Error loading data/characters.csv: {e}")

        try:
            with open("data/domains.csv", "r") as csvfile:
                reader = csv.reader(csvfile, delimiter=",")
                self.domains = [Domain(*row) for row in reader]
                self.domains_shortest_search = min(
                    [len(domain.search_str) for domain in self.domains]
                )
                print(f"Loaded domains.csv: {len(self.domains)} domains")
        except Exception as e:
            print(f"Error loading data/domains.csv: {e}")

        try:
            with open("data/locations.csv", "r") as csvfile:
                reader = csv.reader(csvfile, delimiter=",", escapechar="\\")
                self.locations = [Location(*row) for row in reader]
                self.locations_shortest_search = min(
                    [len(location.search_str) for location in self.locations]
                )
                print(f"Loaded locations.csv: {len(self.locations)} locations")
        except Exception as e:
            print(f"Error loading data/locations.csv: {e}")

        try:
            with open("data/gamemenus.csv", "r") as csvfile:
                reader = csv.reader(csvfile, delimiter=",", escapechar="\\")
                self.gamemenus = [Gamemenu(*row) for row in reader]
                self.gamemenus_shortest_search = min(
                    [len(gamemenu.search_str) for gamemenu in self.gamemenus]
                )
                print(f"Loaded gamemenus.csv: {len(self.gamemenus)} gamemenus")
        except Exception as e:
            print(f"Error loading data/gamemenus.csv: {e}")

        try:
            with open("data/bosses.csv", "r") as csvfile:
                reader = csv.reader(csvfile, delimiter=",")
                self.bosses = [Boss(*row) for row in reader]
                self.bosses_shortest_search = min(
                    [len(boss.search_str) for boss in self.bosses]
                )
                print(f"Loaded bosses.csv: {len(self.bosses)} bosses")
        except Exception as e:
            print(f"Error loading data/bosses.csv: {e}")

        self.file_observer = Observer()
        self.file_observer.daemon = True  # stop observing when closed
        self.file_observer.schedule(self, "data", recursive=False)
        self.file_observer.start()  # creates observer in new thread

    def search_boss(self, boss_text) -> Optional[Boss]:
        """
        Searches for matching world boss based on the best match available.

        Has caching to reduce CPU.
        """
        if len(boss_text) < self.bosses_shortest_search:
            return None

        if boss_text.lower() in self.world_boss_capture_cache:
            return self.world_boss_capture_cache[boss_text.lower()]

        boss_match = [b for b in self.bosses if b.search_str in boss_text.lower()]
        boss_match.sort(key=lambda b: len(b.search_str), reverse=True)
        if DEBUG_MODE and len(boss_match) > 1:
            print(
                f'WARN: Multiple world bosses matched for "{boss_text}": {[b.boss_name for b in boss_match]}'
            )
            print("Picking longest match")
        if len(boss_match) > 0:
            self.world_boss_capture_cache[boss_text.lower()] = boss_match[0]
            return boss_match[0]

        self.world_boss_capture_cache[boss_text.lower()] = None
        return None

    def search_character(self, charname_text) -> Optional[Character]:
        """
        Searches for matching character based on best match available.

        Has caching to reduce CPU.
        """
        if len(charname_text) < self.characters_shortest_search:
            return None

        if charname_text.lower() in self.party_capture_cache:
            return self.party_capture_cache[charname_text.lower()]

        charname_match = [
            c for c in self.characters if c.search_str in charname_text.lower()
        ]
        charname_match.sort(key=lambda c: len(c.search_str), reverse=True)
        if DEBUG_MODE and len(charname_match) > 1:
            print(
                f'WARN: Multiple characters matched for "{charname_text}": {[c.character_name for c in charname_match]}'
            )
            print("Picking longest match")
        if len(charname_match) > 0:
            self.party_capture_cache[charname_text.lower()] = charname_match[0]
            return charname_match[0]

        self.party_capture_cache[charname_text.lower()] = None
        return None

    def search_domain(self, domain_text) -> Optional[Domain]:
        """
        Searches for matching domain based on the best match available.

        Has caching to reduce CPU.
        """
        if len(domain_text) < self.domains_shortest_search:
            return None

        if domain_text.lower() in self.domain_capture_cache:
            return self.domain_capture_cache[domain_text.lower()]

        domain_match = [d for d in self.domains if d.search_str in domain_text.lower()]
        domain_match.sort(key=lambda d: len(d.search_str), reverse=True)

        dom = None

        if len(domain_match) > 0:
            dom = domain_match[0]

        self.domain_capture_cache[domain_text.lower()] = dom

        if DEBUG_MODE:
            if len(domain_match) > 1:
                print(
                    f'WARN: Multiple domains matched for "{domain_text}": {[d.domain_name for d in domain_match]}'
                )
                print("Picking longest match")

        return dom

    def search_location(self, loc_text) -> Optional[Location]:
        """
        Searches for matching location based on the best match available.

        Has caching to reduce CPU.
        """
        if len(loc_text) < self.locations_shortest_search:
            return None

        if loc_text.lower() in self.location_capture_cache:
            return self.location_capture_cache[loc_text.lower()]

        # First try: Exact substring matching (original behavior)
        location_match = [l for l in self.locations if l.search_str in loc_text.lower()]
        location_match.sort(key=lambda l: len(l.search_str), reverse=True)

        # Initialize fuzzy_matches for debug output
        fuzzy_matches = []

        loc = None

        if len(location_match) > 0:
            loc = location_match[0]
        else:
            # Second try: Fuzzy matching if no exact matches found
            for location in self.locations:
                # Calculate similarity ratio using difflib
                # Compare both directions (OCR vs CSV and CSV vs OCR)
                ratio1 = difflib.SequenceMatcher(None, location.search_str.lower(), loc_text.lower()).ratio()
                ratio2 = difflib.SequenceMatcher(None, loc_text.lower(), location.search_str.lower()).ratio()

                # Use the higher ratio and require 75% similarity
                similarity = max(ratio1, ratio2)
                if similarity >= 0.75:  # 75% similarity threshold
                    fuzzy_matches.append((location, similarity))

            if fuzzy_matches:
                # Sort by similarity (highest first)
                fuzzy_matches.sort(key=lambda x: x[1], reverse=True)
                loc = fuzzy_matches[0][0]  # Get the location with highest similarity

                if DEBUG_MODE:
                    print(
                        f'FUZZY: Matched "{loc_text}" to "{loc.location_name}" (similarity: {fuzzy_matches[0][1]:.2f})'
                    )

        self.location_capture_cache[loc_text.lower()] = loc

        if DEBUG_MODE:
            if len(location_match) > 1:
                print(
                    f'WARN: Multiple locations matched for "{loc_text}": {[l.location_name for l in location_match]}'
                )
                print("Picking longest match")
            elif fuzzy_matches and len(fuzzy_matches) > 1:
                print(
                    f'FUZZY WARN: Multiple fuzzy matches for "{loc_text}": {[l[0].location_name for l in fuzzy_matches]}'
                )
                print("Picking highest similarity match")
            print(
                f'Added "{loc_text.lower()}" to cache: {loc and loc.location_name} ({len(self.location_capture_cache)})'
            )
        return loc

    def search_gamemenu(self, gamemenu_text) -> Optional[Gamemenu]:
        """
        Searches for matching gamemenu based on the best match available.

        Has caching to reduce CPU.
        """
        if len(gamemenu_text) < self.gamemenus_shortest_search:
            return None

        if gamemenu_text.lower() in self.gamemenu_capture_cache:
            return self.gamemenu_capture_cache[gamemenu_text.lower()]

        # First try: Find all matches (prioritize longer, more specific matches)
        all_matches = []

        # Primary search: CSV entry is substring of OCR text
        primary_matches = [g for g in self.gamemenus if g.search_str in gamemenu_text.lower()]
        all_matches.extend(primary_matches)

        # Fallback search: Case-insensitive substring matching
        fallback_matches = [g for g in self.gamemenus if g.search_str.lower() in gamemenu_text.lower() and g not in all_matches]
        all_matches.extend(fallback_matches)

        # Sort by length (longest first) to prioritize more specific matches
        gamemenu_match = sorted(all_matches, key=lambda g: len(g.search_str), reverse=True)

        gm = None

        if len(gamemenu_match) > 0:
            gm = gamemenu_match[0]

        self.gamemenu_capture_cache[gamemenu_text.lower()] = gm

        if DEBUG_MODE:
            if len(gamemenu_match) > 1:
                print(
                    f'WARN: Multiple gamemenus matched for "{gamemenu_text}": {[g.gamemenu_name for g in gamemenu_match]}'
                )
                print("Picking longest match")

        return gm

    def on_modified(self, event: FileModifiedEvent):
        """
        Handler for file modified event.

        Immediately reloads data once file is modified.
        """
        # XXX: For some weird reason, watchdog sends
        # file modified events twice in very quick
        # succession. This hack attempts to prevent this,
        # but there's no guarantee of it working.
        if time.time() - self._last_modified < 1:
            self._last_modified = time.time()
            return

        self._last_modified = time.time()

        time.sleep(0.5)  # XXX: Hack to solve race condition

        match os.path.basename(event.src_path):
            case "bosses.csv":
                try:
                    with open("data/bosses.csv", "r") as csvfile:
                        reader = csv.reader(csvfile, delimiter=",")
                        temp = [Boss(*row) for row in reader]
                        self.bosses = temp
                        self.bosses_shortest_search = min(
                            [len(boss.search_str) for boss in self.bosses]
                        )
                        self.world_boss_capture_cache.clear()  # Clear cache when CSV is reloaded
                        print(
                            f"bosses.csv modified. Updated bosses: {len(self.bosses)} bosses."
                        )
                except Exception as e:
                    print(f"Error loading data/bosses.csv: {e}")
            case "characters.csv":
                try:
                    with open("data/characters.csv", "r") as csvfile:
                        reader = csv.reader(csvfile, delimiter=",")
                        temp = []
                        for row in reader:
                            c = Character(*row)
                            if (MC_AETHER and c.search_str == "aether") or (
                                not MC_AETHER and c.search_str == "lumine"
                            ):
                                c.search_str = USERNAME.lower()
                                c.character_display_name = USERNAME

                            if c.search_str == "wanderer":
                                c.search_str = WANDERER_NAME.lower()
                                c.character_display_name = WANDERER_NAME

                            temp.append(c)

                        self.characters = temp
                        self.characters_shortest_search = min(
                            [len(character.search_str) for character in self.characters]
                        )
                        self.party_capture_cache.clear()  # Clear cache when CSV is reloaded
                        print(
                            f"characters.csv modified. Updated characters: {len(self.characters)} characters."
                        )
                except Exception as e:
                    print(f"Error loading data/characters.csv: {e}")
            case "domains.csv":
                try:
                    with open("data/domains.csv", "r") as csvfile:
                        reader = csv.reader(csvfile, delimiter=",")
                        temp = [Domain(*row) for row in reader]
                        self.domains = temp
                        self.domains_shortest_search = min(
                            [len(domain.search_str) for domain in self.domains]
                        )
                        self.domain_capture_cache.clear()  # Clear cache when CSV is reloaded
                        print(
                            f"domains.csv modified. Updated domains: {len(self.domains)} domains."
                        )
                except Exception as e:
                    print(f"Error loading data/domains.csv: {e}")
            case "locations.csv":
                try:
                    with open("data/locations.csv", "r") as csvfile:
                        reader = csv.reader(csvfile, delimiter=",", escapechar="\\")
                        temp = [Location(*row) for row in reader]
                        self.locations = temp
                        self.locations_shortest_search = min(
                            [len(location.search_str) for location in self.locations]
                        )
                        self.location_capture_cache.clear()  # Clear cache when CSV is reloaded
                        print(
                            f"locations.csv modified. Updated locations: {len(self.locations)} locations."
                        )
                except Exception as e:
                    print(f"Error loading data/locations.csv: {e}")
            case "gamemenus.csv":
                try:
                    with open("data/gamemenus.csv", "r") as csvfile:
                        reader = csv.reader(csvfile, delimiter=",", escapechar="\\")
                        temp = [Gamemenu(*row) for row in reader]
                        self.gamemenus = temp
                        self.gamemenus_shortest_search = min(
                            [len(gamemenu.search_str) for gamemenu in self.gamemenus]
                        )
                        self.gamemenu_capture_cache.clear()  # Clear cache when CSV is reloaded
                        print(
                            f"gamemenus.csv modified. Updated gamemenus: {len(self.gamemenus)} gamemenus."
                        )
                except Exception as e:
                    print(f"Error loading data/gamemenus.csv: {e}")


if __name__ == "__main__":
    print("Debugging Data class")
    data = Data()
    while True:
        time.sleep(1)
