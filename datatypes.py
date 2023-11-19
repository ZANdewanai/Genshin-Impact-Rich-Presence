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
    activity_data: `Location` object
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


class Activity:
    def __init__(
        self,
        activity_type: ActivityType,
        activity_data: Union[Activity, Boss, Character, Domain, Location, None, bool],
    ):
        self.activity_type = activity_type
        """
        Contents of `activity_data` depends on `activity_type`.
        
        See documentation for entries in `ActivityType` for what `activity_data` should contain.
        """

        self.activity_data = activity_data
        self.start_time = time.time()

    def is_idle(self) -> bool:
        """
        Idle activities are activity states where no active character can be found.
        """
        return self.activity_type in [ActivityType.PAUSED, ActivityType.PARTY_SETUP]

    def to_update_params_dict(self) -> dict:
        """
        Creates a dictionary with parameters for `Presence.update`.

        Small image and timestamp not included and should be added later.
        """
        match self.activity_type:
            case ActivityType.LOADING:
                return {
                    "state": "Loading"
                    if not self.activity_data
                    else "Somewhere in Teyvat",
                    "large_image": "icon_paimon",
                }
            case ActivityType.PAUSED:
                return {
                    "state": "Game paused",
                    "large_image": "icon_paimon",
                }
            case ActivityType.PARTY_SETUP:
                return {
                    "state": "Party Setup",
                    "large_image": "icon_party_setup",
                }
            case ActivityType.DOMAIN:
                return {
                    "details": self.activity_data.domain_name,
                    "state": f"Clearing a {self.activity_data.domain_type}",
                    "large_image": self.activity_data.image_key,
                    "large_text": str(self.activity_data.domain_type),
                }
            case ActivityType.LOCATION:
                if self.activity_data.subarea == "":
                    state = self.activity_data.country
                elif self.activity_data.country == "":
                    state = self.activity_data.subarea
                else:
                    state = (
                        f"{self.activity_data.subarea}, {self.activity_data.country}"
                    )
                return {
                    "details": f"In {self.activity_data.location_name}",
                    "state": state,
                    "large_image": self.activity_data.image_key,
                }
            case ActivityType.COMMISSION:
                return {
                    "state": "Doing commissions",
                    "details": f"In {self.activity_data.location_name}, {self.activity_data.country}"
                    if self.activity_data != None
                    else "",
                    "large_image": "icon_commission",
                }
            case ActivityType.WORLD_BOSS:
                return {
                    "state": f"Fighting a boss",
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

    bosses_shortest_search = 0
    characters_shortest_search = 0
    domains_shortest_search = 0
    locations_shortest_search = 0

    party_capture_cache = {}
    world_boss_capture_cache = {}
    domain_capture_cache = {}
    location_capture_cache = {}

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

        location_match = [l for l in self.locations if l.search_str in loc_text.lower()]
        location_match.sort(key=lambda l: len(l.search_str), reverse=True)

        loc = None

        if len(location_match) > 0:
            loc = location_match[0]

        self.location_capture_cache[loc_text.lower()] = loc

        if DEBUG_MODE:
            if len(location_match) > 1:
                print(
                    f'WARN: Multiple locations matched for "{loc_text}": {[l.location_name for l in location_match]}'
                )
                print("Picking longest match")
            print(
                f'Added "{loc_text.lower()}" to cache: {loc and loc.location_name} ({len(self.location_capture_cache)})'
            )
        return loc

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
                        print(
                            f"locations.csv modified. Updated locations: {len(self.locations)} locations."
                        )
                except Exception as e:
                    print(f"Error loading data/locations.csv: {e}")


if __name__ == "__main__":
    print("Debugging Data class")
    data = Data()
    while True:
        time.sleep(1)
