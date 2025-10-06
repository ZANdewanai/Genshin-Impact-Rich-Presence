"""
Contains data types modelling .csv files in ./data/

The constructors for these classes must have arguments listed in the same order as the columns in the .csv files.
"""

from __future__ import annotations
from enum import Enum, auto
from typing import Optional, Union
from ..CONFIG import DEBUG_MODE, MC_AETHER, WANDERER_NAME, USERNAME
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler, FileModifiedEvent
import csv
import time
import os


class Boss:
    """
    World bosses in bosses.csv
    """

    def __init__(self, search_str, boss_name, image_key, category=None):
        self.search_str = search_str
        self.boss_name = boss_name
        self.image_key = image_key
        self.category = category

    def __eq__(self, other: Boss) -> bool:
        if not isinstance(other, Boss):
            return False
        return (
            self.search_str == other.search_str
            and self.boss_name == other.boss_name
        )


class Character:
    """Played characters in characters.csv"""

    def __init__(self, search_str, name, region, icon, category=None):
        self.search_str = search_str
        self.character_display_name = name
        self.region = region
        self.image_key = f"character_{icon}" if not icon.startswith("character_") else icon
        self.category = category

    def __eq__(self, other: Character) -> bool:
        if not isinstance(other, Character):
            return False

        return (
            self.search_str == other.search_str
            and self.image_key == other.image_key
            and self.character_display_name == other.character_display_name
            and self.category == other.category
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
            and self.country == other.country
            and self.image_key == other.image_key
        )


class GameMenuType(Enum):
    MENUS = 0
    CUTSCENE = 1
    SPYRAL = 2
    INVENTORY = 3
    QUESTS = 4
    TUTORIALS = 5
    ARCHIVE = 6

    @classmethod
    def from_str(cls, game_menu_type_str):
        """
        Safely convert string to GameMenuType with fallback to MENUS.
        Handles various menu type strings found in the game.
        """
        if not game_menu_type_str:
            return cls.MENUS
            
        try:
            menu_str = str(game_menu_type_str).strip().upper()
            
            # Map common variations to known types
            menu_map = {
                'MENUS': cls.MENUS,
                'CUTSCENE': cls.CUTSCENE,
                'IN CUTSCENE': cls.CUTSCENE,
                'IN A CUTSCENE': cls.CUTSCENE,
                'SPYRAL': cls.SPYRAL,
                'SPYRAL ABYSS': cls.SPYRAL,
                'INVENTORY': cls.INVENTORY,
                'QUESTS': cls.QUESTS,
                'TUTORIALS': cls.TUTORIALS,
                'ARCHIVE': cls.ARCHIVE,
                'TYPE': cls.MENUS,  # Default for 'TYPE' which appears in the CSV
            }
            
            # Try direct match first
            if menu_str in menu_map:
                return menu_map[menu_str]
                
            # Try partial matches
            for key, menu_type in menu_map.items():
                if key in menu_str or menu_str in key:
                    return menu_type
                    
            # If we get here, it's an unknown type
            if 'CUTSCENE' in menu_str:
                return cls.CUTSCENE
            elif 'SPYRAL' in menu_str:
                return cls.SPYRAL
                
            return cls.MENUS
            
        except Exception as e:
            if DEBUG_MODE:
                print(f"[DEBUG] Error parsing game menu type '{game_menu_type_str}': {e}")
            return cls.MENUS

    def __str__(self):
        if self == GameMenuType.MENUS:
            return "MENUS"
        elif self == GameMenuType.CUTSCENE:
            return "CUTSCENE"
        elif self == GameMenuType.SPYRAL:
            return "SPYRAL"
        return "UNKNOWN"


class GameMenu:
    """From gamemenu.csv."""

    def __init__(self, search_str, game_menu_name, game_menu_type, image_key):
        self.search_str = str(search_str) if search_str is not None else ""
        self.game_menu_name = str(game_menu_name) if game_menu_name is not None else ""
        
        # Safely handle game_menu_type
        try:
            self.game_menu_type = GameMenuType.from_str(game_menu_type)
        except Exception as e:
            print(f"[WARNING] Error initializing GameMenuType: {e}")
            self.game_menu_type = GameMenuType.MENUS
            
        self.image_key = str(image_key) if image_key is not None else ""

    def __eq__(self, other):
        if not isinstance(other, GameMenu):
            return False
        return all([
            self.search_str == other.search_str,
            self.game_menu_name == other.game_menu_name,
            self.game_menu_type == other.game_menu_type,
            self.image_key == other.image_key
        ])
        
    def __str__(self):
        return f"GameMenu({self.game_menu_name}, type={str(self.game_menu_type)})"
class ActivityType(Enum):
    LOADING = auto()
    """
    activity_data: `False` until active character is found, then `True`.
    If `False`, display game loading message.
{{ ... }}
    If `True`, display 'Somewhere in Teyvat'.
    """
    PAUSED = auto()
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
    GAME_MENU = auto()
    """
    activity_data: 'GameMenu' object
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

    def is_idle(self) -> bool:
        """
        Idle activities are activity states where no active character can be found.
        """
        return self.activity_type in [ActivityType.PAUSED, ActivityType.GAME_MENU]

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
            case ActivityType.DOMAIN:
                return {
                    "details": self.activity_data.domain_name,
                    "state": f"Clearing a {self.activity_data.domain_type}",
                    "large_image": self.activity_data.image_key,
                    "large_text": str(self.activity_data.domain_type),
                }
            case ActivityType.GAME_MENU:
                return {
                    "details": self.activity_data.game_menu_name,
                    "state": f"{self.activity_data.game_menu_type}",
                    "large_image": self.activity_data.image_key,
                    "large_text": str(self.activity_data.gamemenu_type),
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
    game_menus: list[GameMenu] = []

    bosses_shortest_search = 0
    characters_shortest_search = 0
    domains_shortest_search = 0
    locations_shortest_search = 0
    game_menus_shortest_search = 0

    party_capture_cache = {}
    world_boss_capture_cache = {}
    domain_capture_cache = {}
    location_capture_cache = {}
    game_menu_capture_cache = {}

    def __init__(self):
        super().__init__(patterns=["*.csv"])  # init PatternMatchingEventHandler

        self._last_modified = time.time()
        """
        Keep track of the last time on_modified was triggered.
        Weird bug with watchdog makes modification events trigger twice.
        Have a short cooldown period between executing the modification handler.
        """

        try:
            data_path = os.path.join(os.path.dirname(__file__), "../../resources/data/characters.csv")
            with open(data_path, "r") as csvfile:
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
            data_path = os.path.join(os.path.dirname(__file__), "../../resources/data/domains.csv")
            with open(data_path, "r") as csvfile:
                reader = csv.reader(csvfile, delimiter=",")
                self.domains = [Domain(*row) for row in reader]
                self.domains_shortest_search = min(
                    [len(domain.search_str) for domain in self.domains]
                )
                print(f"Loaded domains.csv: {len(self.domains)} domains")
        except Exception as e:
            print(f"Error loading data/domains.csv: {e}")

        try:
            data_path = os.path.join(os.path.dirname(__file__), "../../resources/data/locations.csv")
            with open(data_path, "r") as csvfile:
                reader = csv.reader(csvfile, delimiter=",", escapechar="\\")
                self.locations = [Location(*row) for row in reader]
                self.locations_shortest_search = min(
                    [len(location.search_str) for location in self.locations]
                )
                print(f"Loaded locations.csv: {len(self.locations)} locations")
        except Exception as e:
            print(f"Error loading data/locations.csv: {e}")

        try:
            data_path = os.path.join(os.path.dirname(__file__), "../../resources/data/game_menus.csv")
            with open(data_path, "r") as csvfile:
                reader = csv.reader(csvfile, delimiter=",", escapechar="\\")
                self.game_menus = [GameMenu(*row) for row in reader]
                self.game_menus_shortest_search = min(
                    [len(game_menu.search_str) for game_menu in self.game_menus]
                )
                print(f"Loaded game_menus.csv: {len(self.game_menus)} game menus")
        except Exception as e:
            print(f"Error loading data/game_menus.csv: {e}")

        try:
            data_path = os.path.join(os.path.dirname(__file__), "../../resources/data/bosses.csv")
            with open(data_path, "r") as csvfile:
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
        data_dir = os.path.join(os.path.dirname(__file__), "../../resources/data")
        self.file_observer.schedule(self, data_dir, recursive=False)
        self.file_observer.start()  # creates observer in new thread

    def search_boss(self, search_str: str) -> Optional[Boss]:
        """
        Searches for matching boss based on the best match available.
        Handles common OCR errors and provides flexible matching.

        Has caching to reduce CPU.
        """
        if not search_str or len(search_str) < self.bosses_shortest_search:
            return None

        # Check cache first
        search_str_lower = search_str.lower()
        if search_str_lower in self.world_boss_capture_cache:
            return self.world_boss_capture_cache[search_str_lower]

        # Search through bosses
        for boss in self.bosses:
            if boss.search_str.lower() in search_str_lower:
                self.world_boss_capture_cache[search_str_lower] = boss
                return boss

        return None

    def search_domain(self, search_str: str) -> Optional[Domain]:
        """
        Searches for matching domain based on the best match available.
        Handles common OCR errors and provides flexible matching.

        Has caching to reduce CPU.
        """
        if len(search_str) < self.domains_shortest_search:
            return None

        if search_str in self.domain_capture_cache:
            return self.domain_capture_cache[search_str]

        for domain in self.domains:
            if domain.search_str.lower() in search_str.lower():
                self.domain_capture_cache[search_str] = domain
                return domain

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
        Handles common OCR errors and provides flexible matching.

        Has caching to reduce CPU.
        """
        if not domain_text:
            return None
            
        # Clean up the domain text
        cleaned_text = domain_text.lower().strip()
        
        if DEBUG_MODE:
            print(f"Original domain text: {domain_text}")
            print(f"Cleaned domain text: {cleaned_text}")
        
        # Check cache first (use the original cleaned text for cache key)
        if cleaned_text in self.domain_capture_cache:
            return self.domain_capture_cache[cleaned_text]

        # Try different matching strategies
        domain_match = []
        
        # 1. Try to extract the domain name from common OCR patterns
        domain_part = None
        patterns = [
            r'(?:domainof)?(forgery|blessing|mastery|trounce|event)?([A-Z][a-z]+(?:[A-Z][a-z]*)*)([IVX]+)',  # Matches camelCase patterns like 'DomainofMasterySublimeTurningIV'
            r'(?:domainof)?(forgery|blessing|mastery|trounce|event)?\s*([a-z]+\s*[a-z]*\s*[ivx]+)',  # Matches patterns like 'DomainofForgeryScryingShadowsIV'
            r'([a-z]+\s*[a-z]*\s*[ivx]+)(?:\s*thocraatdragnncarartadmanyvnariiliar)?',  # Matches patterns with garbage at the end
        ]
        
        import re
        for pattern in patterns:
            match = re.search(pattern, cleaned_text, re.IGNORECASE)
            if match:
                # Handle the camelCase pattern match (group 2 is the name, group 3 is the roman numeral)
                if len(match.groups()) >= 3 and match.group(2) and match.group(3):
                    # Convert camelCase to space-separated words and add roman numeral
                    name = re.sub(r'([A-Z])', r' \1', match.group(2)).strip()
                    domain_part = f"{name} {match.group(3)}"
                    break
                # Handle other patterns
                elif match.lastindex > 1 and match.group(2):
                    domain_part = match.group(2).strip()
                    break
                elif match.lastindex > 0 and match.group(1):
                    domain_part = match.group(1).strip()
                    break
        
        if not domain_part:
            domain_part = cleaned_text  # Fall back to the entire text if no pattern matched
        
        # Clean up the domain part
        domain_part = (
            domain_part.replace('\n', ' ')  # Replace newlines with spaces
            .replace('  ', ' ')             # Replace double spaces with single
            .strip()                        # Remove leading/trailing spaces
        )
        
        if DEBUG_MODE:
            print(f"Extracted domain part: {domain_part}")
        
        # 2. Try exact match with domain name (case-insensitive, ignoring spaces)
        domain_match = [
            d for d in self.domains 
            if d.search_str.lower().replace(' ', '') == domain_part.lower().replace(' ', '')
        ]
        
        if DEBUG_MODE and domain_match:
            print(f"Exact match found: {domain_match[0].search_str}")
        
        # 3. Try partial match if no exact match (case-insensitive, ignoring spaces)
        if not domain_match:
            domain_match = [
                d for d in self.domains 
                if domain_part.lower().replace(' ', '') in d.search_str.lower().replace(' ', '')
                or d.search_str.lower().replace(' ', '') in domain_part.lower().replace(' ', '')
            ]
            
            if DEBUG_MODE and domain_match:
                print(f"Partial matches found: {[d.search_str for d in domain_match]}")
        
        # 4. Try matching just the roman numerals if still no match
        if not domain_match and any(c in domain_part.lower() for c in ['i', 'v', 'x']):
            roman_match = re.search(r'([ivx]+)$', domain_part.lower())
            if roman_match:
                roman = roman_match.group(1).upper()
                if DEBUG_MODE:
                    print(f"Trying to match roman numeral: {roman}")
                # Try to find domains with this roman numeral (case-insensitive)
                domain_match = [
                    d for d in self.domains 
                    if f' {roman} '.lower() in d.domain_name.lower() 
                    or f' {roman}'.lower() == d.domain_name.lower()[-len(roman)-1:]
                ]
        
        # Sort matches by relevance (longest match first, then by roman numeral)
        def sort_key(d):
            # Prioritize longer matches
            length_score = len(d.search_str)
            # Then prioritize matches where the roman numeral is at the end
            roman_score = 1 if re.search(r'\b[ivx]+$', d.search_str.lower()) else 0
            return (-length_score, -roman_score)
            
        domain_match.sort(key=sort_key)

        dom = domain_match[0] if domain_match else None
        self.domain_capture_cache[cleaned_text] = dom  # Cache the result with the original cleaned text

        if DEBUG_MODE:
            if domain_match:
                print(f"Matched domain: {domain_match[0].domain_name}")
            else:
                print(f"No domain match found for: {domain_part}")
            if len(domain_match) > 1:
                print(f"Multiple matches found. Using: {domain_match[0].domain_name}")
                print(f"Other matches: {[d.domain_name for d in domain_match[1:3]]}")
        
        return dom

        return dom

    def _get_location_score(self, location_name: str, ocr_text: str) -> float:
        """Calculate a confidence score for a location match (0.0 to 1.0)."""
        ocr_lower = ocr_text.lower()
        loc_lower = location_name.lower()
        
        # Perfect match
        if loc_lower == ocr_lower:
            return 1.0
            
        # Check word by word with some flexibility
        loc_words = set(word for word in loc_lower.split() if len(word) > 2)
        ocr_words = set(word for word in ocr_lower.split() if len(word) > 2)
        
        # Calculate word overlap score
        if loc_words:
            word_overlap = len(loc_words.intersection(ocr_words)) / len(loc_words)
        else:
            word_overlap = 0.0
            
        # Check for partial matches (substrings)
        loc_no_spaces = loc_lower.replace(" ", "")
        ocr_no_spaces = ocr_lower.replace(" ", "")
        
        # Calculate longest common substring ratio
        def lcs_ratio(a, b):
            m = [[0] * (1 + len(b)) for _ in range(1 + len(a))]
            longest = 0
            for i in range(1, 1 + len(a)):
                for j in range(1, 1 + len(b)):
                    if a[i-1] == b[j-1]:
                        m[i][j] = m[i-1][j-1] + 1
                        longest = max(longest, m[i][j])
            return longest / max(len(a), len(b)) if max(len(a), len(b)) > 0 else 0
            
        lcs = max(
            lcs_ratio(loc_lower, ocr_lower),
            lcs_ratio(loc_no_spaces, ocr_no_spaces)
        )
        
        # Combine scores with weights
        score = (word_overlap * 0.6) + (lcs * 0.4)
        
        # Penalize very short location names
        if len(location_name.split()) <= 2 and len(location_name) < 8:
            score *= 0.7  # Reduce confidence for very short names
            
        return score

    def _is_valid_location_text(self, text: str) -> bool:
        """Check if the OCR text looks like a valid location name."""
        if not text or len(text.strip()) < 2:  # At least 2 characters
            if DEBUG_MODE:
                print(f"[DEBUG] _is_valid_location_text: Text too short or empty: '{text}' (len={len(text) if text else 0})")
            return False
            
        if DEBUG_MODE:
            print(f"[DEBUG] _is_valid_location_text: Validating text: '{text}'")
            
        # Check for valid word characters (letters, spaces, hyphens, apostrophes)
        import re
        if not re.match(r'^[\w\s\-\']+$', text, re.UNICODE):
            if DEBUG_MODE:
                print(f"[DEBUG] _is_valid_location_text: Invalid characters found in: '{text}'")
            return False
            
        # Check for minimum word length and valid words
        words = text.split()
        if not words:
            if DEBUG_MODE:
                print(f"[DEBUG] _is_valid_location_text: No words found in: '{text}'")
            return False
            
        # At least one word should be 3+ characters (to avoid matching single letters or short garbage)
        valid_words = [word for word in words if len(word) >= 3]
        if not valid_words:
            if DEBUG_MODE:
                print(f"[DEBUG] _is_valid_location_text: No words >= 3 chars in: '{text}' (words: {words})")
            return False
            
        # Check for excessive special characters or numbers (not common in location names)
        special_chars = sum(1 for c in text if c.isdigit() or c in '!@#$%^&*()_+=[]{}|;:,.<>?/\\')
        if special_chars > len(text) * 0.2:
            if DEBUG_MODE:
                print(f"[DEBUG] _is_valid_location_text: Too many special chars ({special_chars}/{len(text)}) in: '{text}'")
            return False
            
        if DEBUG_MODE:
            print(f"[DEBUG] _is_valid_location_text: Text validation passed for: '{text}'")
        return True
        
    def search_location(self, loc_text, confidence_threshold=0.7) -> Optional[Location]:
        """
        Searches for matching location based on the best match available.
        Uses a confidence-based scoring system to ensure reliable matches.
        
        Args:
            loc_text: The text captured by OCR
            confidence_threshold: Minimum confidence score required (0.0 to 1.0)
            
        Returns:
            Location if a good match is found, None otherwise
        """
        # First, validate the input text
        if not loc_text or not self._is_valid_location_text(loc_text):
            if DEBUG_MODE:
                print(f"[DEBUG] Invalid location text detected and ignored: '{loc_text}'")
            return None
            
        # Create cache key that includes both original and space-stripped versions
        cache_key = loc_text.lower().strip()
        if cache_key in self.location_capture_cache:
            if DEBUG_MODE:
                print(f"[DEBUG] search_location: Using cached result for '{loc_text}'")
            return self.location_capture_cache[cache_key]

        if DEBUG_MODE:
            print(f"[DEBUG] search_location: Searching for location '{loc_text}' with threshold {confidence_threshold}")

        # Get all locations and calculate scores
        scored_locations = []
        for location in self.locations:
            score = self._get_location_score(location.search_str, loc_text)
            # Removed spammy debug output for individual location scores
            # if DEBUG_MODE:
            #     print(f"[DEBUG] search_location: Score for '{location.search_str}': {score:.3f}")
            if score >= confidence_threshold:
                scored_locations.append((location, score))
                
        # Sort by score (highest first)
        scored_locations.sort(key=lambda x: x[1], reverse=True)
        
        if DEBUG_MODE:
            print(f"[DEBUG] search_location: Found {len(scored_locations)} matches above threshold")
            if scored_locations:
                print(f"[DEBUG] search_location: Best match: '{scored_locations[0][0].search_str}' (confidence: {scored_locations[0][1]:.3f})")
        
        # If we have a clear winner, return it
        if scored_locations:
            best_match, confidence = scored_locations[0]
            
            # For debugging
            if DEBUG_MODE and len(scored_locations) > 1:
                print(f"[DEBUG] Top location matches for '{loc_text}':")
                for loc, score in scored_locations[:3]:
                    print(f"[DEBUG]   - '{loc.search_str}': {score:.3f} confidence")
            
            # Only return if we're confident enough
            if confidence >= confidence_threshold:
                self.location_capture_cache[cache_key] = best_match
                if DEBUG_MODE:
                    print(f"[DEBUG] search_location: Match found and cached: '{best_match.location_name}'")
                return best_match
                
        # No good matches found
        if DEBUG_MODE:
            print(f"[DEBUG] No confident match found for: '{loc_text}'")
            if scored_locations:
                print(f"[DEBUG] Best match was '{scored_locations[0][0].search_str}' with confidence {scored_locations[0][1]:.3f}")
                
        return None

    def search_game_menu(self, game_menu_text) -> Optional[GameMenu]:
        """
        Searches for matching game menu based on the best match available.

        Has caching to reduce CPU.
        """
        if len(game_menu_text) < self.game_menus_shortest_search:
            return None

        if game_menu_text.lower() in self.game_menu_capture_cache:
            return self.game_menu_capture_cache[game_menu_text.lower()]

        game_menu_match = [g for g in self.game_menus if g.search_str in game_menu_text.lower()]
        game_menu_match.sort(key=lambda g: len(g.search_str), reverse=True)

        gm = None

        if len(game_menu_match) > 0:
            gm = game_menu_match[0]

        self.game_menu_capture_cache[game_menu_text.lower()] = gm

        if DEBUG_MODE:
            if len(game_menu_match) > 1:
                print(
                    f'WARN: Multiple game menus matched for "{game_menu_text}": {[g.game_menu_name for d in game_menu_match]}'
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
            case "game_menus.csv":
                try:
                    with open("data/game_menus.csv", "r") as csvfile:
                        reader = csv.reader(csvfile, delimiter=",")
                        temp = [GameMenu(*row) for row in reader]
                        self.game_menus = temp
                        self.game_menus_shortest_search = min(
                            [len(game_menu.search_str) for game_menu in self.game_menus]
                        )
                        print(
                            f"game_menus.csv modified. Updated game menus: {len(self.game_menus)} game menus."
                        )
                except Exception as e:
                    print(f"Error loading data/game_menus.csv: {e}")


if __name__ == "__main__":
    print("Debugging Data class")
    data = Data()
    while True:
        time.sleep(1)
