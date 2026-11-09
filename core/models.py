"""
Data models for Genshin Impact Rich Presence.

Contains data types modelling .csv files in ./data/
The constructors for these classes must have arguments listed in the same order as the columns in the .csv files.
"""
from __future__ import annotations
from enum import Enum, auto
from typing import Optional, Union
import time


# Debug flags - live views onto shared_config.json (CONFIG.py = defaults).
from .shared_config import get_shared_config
try:
    import CONFIG as _cfg
except Exception:
    _cfg = None

def _get(key, default):
    shared = get_shared_config()
    if key in shared:
        return shared[key]
    return getattr(_cfg, key, default) if _cfg is not None else default

class _ConfigFlag:
    """Live boolean view of one setting (shared_config > CONFIG > default).

    Imported once via ``from core.datatypes import DEBUG_MODE`` but evaluated
    on every ``bool()``/truthiness check, so it is NOT an import-time
    snapshot. Only supports boolean contexts (``if FLAG:``, ``FLAG and x``).
    """

    __slots__ = ("_key", "_default")

    def __init__(self, key: str, default: bool = False):
        self._key = key
        self._default = default

    def _read(self) -> bool:
        shared = get_shared_config()
        if self._key in shared:
            return bool(shared[self._key])
        if _cfg is not None:
            return bool(getattr(_cfg, self._key, self._default))
        return self._default

    def __bool__(self) -> bool:
        return self._read()

    def __eq__(self, other):
        if isinstance(other, bool):
            return self._read() == other
        return NotImplemented

    def __repr__(self) -> str:
        return repr(self._read())


DEBUG_MODE = _ConfigFlag("DEBUG_MODE", False)
DEBUG_CHARACTER_MODE = _ConfigFlag("DEBUG_CHARACTER_MODE", False)
DEBUG_SAVE_IMAGES = _ConfigFlag("DEBUG_SAVE_IMAGES", False)


def _identity_settings() -> dict:
    """Username / Traveler / renameable-character settings, with defaults.

    shared_config.json (written by the GUI) is authoritative; CONFIG.py
    supplies the defaults for keys it doesn't carry.
    """
    return {
        "USERNAME": _get("USERNAME", "Player"),
        "MC_AETHER": bool(_get("MC_AETHER", True)),
        "WANDERER_NAME": _get("WANDERER_NAME", "Wanderer"),
        "MANEKIN_NAME": _get("MANEKIN_NAME", "Manekin"),
        "MANEKINA_NAME": _get("MANEKINA_NAME", "Manekina"),
    }


class Boss:
    """World bosses in bosses.csv"""

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
    """Playable characters in characters.csv"""

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

    def from_str(domain_type_str: str) -> DomainType:
        """NOTE: The domain type values in domains.csv must match the strings here."""
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
            case _:
                return DomainType.ONE_TIME  # Default fallback for unrecognized types

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
            case _:
                return "Domain"  # Default fallback


class Domain:
    """From domains.csv. The domain type values must match string values in `DomainType.from_str`"""

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
    SPIRAL = 2

    def from_str(gamemenu_type_str: str) -> GamemenuType:
        """NOTE: The gamemenu type values in gamemenu.csv must match the strings here."""
        if not isinstance(gamemenu_type_str, str):
            return GamemenuType.MENUS  # Default fallback for invalid input
        match gamemenu_type_str.lower():
            case "in menus":
                return GamemenuType.MENUS
            case "in a cutscene":
                return GamemenuType.CUTSCENE
            case "spiral abyss":
                return GamemenuType.SPIRAL
            case _:
                return GamemenuType.MENUS  # Default fallback for unrecognized types

    def __str__(self) -> str:
        match self.name:
            case "MENUS":
                return "In Menus"
            case "CUTSCENE":
                return "In a Cutscene"
            case "SPIRAL":
                return "Spiral Abyss"
            case _:
                return "In Menus"  # Default fallback


class Gamemenu:
    """From gamemenu.csv. The gamemenu type values must match string values in `GamemenuType.from_str`"""

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
    """activity_data: `False` until active character is found, then `True`.
    If `False`, display game loading message.
    If `True`, display 'Somewhere in Teyvat'.
    """
    PAUSED = auto()
    """Idle activity. activity_data: previous non-idle `Activity` object."""
    PARTY_SETUP = auto()
    """Idle activity. activity_data: previous non-idle `Activity` object."""
    DOMAIN = auto()
    """activity data: `Domain` object"""
    LOCATION = auto()
    """activity_data: `Location` object (when actually at a location)"""
    MAP_LOCATION = auto()
    """activity_data: `Location` object (when browsing map/looking at teleport waypoints)"""
    COMMISSION = auto()
    """activity_data: `Location` of last location. Assumes commissions are done at the last visited location."""
    WORLD_BOSS = auto()
    """activity_data: 'Boss' object"""
    GAMEMENU = auto()
    """activity_data: 'Gamemenu' object"""


class Activity:
    def __init__(
        self,
        activity_type: ActivityType,
        activity_data: Union[
            Activity, Boss, Character, Domain, Location, Gamemenu, None, bool
        ],
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
        """Idle activities are activity states where no active character can be found."""
        return self.activity_type in [
            ActivityType.PAUSED,
            ActivityType.PARTY_SETUP,
            ActivityType.GAMEMENU,
        ]

    def __eq__(self, other: Activity) -> bool:
        if not isinstance(other, Activity):
            return False
        return (
            self.activity_type == other.activity_type
            and self.activity_data == other.activity_data
        )