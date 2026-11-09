"""
CSV data loader for Genshin Impact Rich Presence.
Loads all game data from CSV files at startup and supports hot-reload:
Data.check_reload() (called periodically by the coordinator) re-reads any
CSV whose mtime changed, and re-applies identity settings when
shared_config.json changes them.
"""
from __future__ import annotations
import csv
from pathlib import Path

from .models import (
    Boss, Character, Domain, Location, Gamemenu,
    _identity_settings
)

# Game-data CSVs watched for hot-reload (paths relative to CWD, matching the
# open() calls below - main.py chdirs to the project root).
_CSV_PATHS = {
    "characters": Path("data/characters.csv"),
    "domains": Path("data/domains.csv"),
    "locations": Path("data/locations.csv"),
    "gamemenus": Path("data/gamemenus.csv"),
    "bosses": Path("data/bosses.csv"),
}


def _mtime(path: Path):
    try:
        return path.stat().st_mtime
    except OSError:
        return None


class Data:
    """Model for all game data. Loads CSVs at startup, reloads on change."""

    def __init__(self):
        self.bosses: list[Boss] = []
        self.characters: list[Character] = []
        self.domains: list[Domain] = []
        self.locations: list[Location] = []
        self.gamemenus: list[Gamemenu] = []

        self.load_all()
        self._sig = self._snapshot()
        self._last_identity = _identity_settings()

    def _snapshot(self) -> dict:
        """Current mtimes of every watched file (None = missing)."""
        sig = {name: _mtime(p) for name, p in _CSV_PATHS.items()}
        try:
            from .shared_config import SHARED_CONFIG_PATH
            sig["shared_config"] = _mtime(SHARED_CONFIG_PATH)
        except Exception:
            pass
        return sig

    def check_reload(self) -> set:
        """Reload whatever changed since the last check.

        Returns a set of change kinds: ``"csv"`` (a data/*.csv changed -
        callers should also refresh coordinate CSVs and sensor static data)
        and/or ``"identity"`` (shared_config identity settings changed -
        characters.csv substitution was re-applied).
        """
        changed = set()
        sig = self._snapshot()
        old = self._sig
        self._sig = sig

        csv_changed = any(
            sig.get(name) != old.get(name) for name in _CSV_PATHS
        )
        if csv_changed:
            self.load_all()
            changed.add("csv")

        # Identity settings are applied while loading characters.csv, so a
        # shared_config change (username/traveler/renameables) needs a
        # character reload even when no CSV file itself changed.
        identity = _identity_settings()
        if identity != self._last_identity:
            self.characters = self._load_characters()
            changed.add("identity")
        self._last_identity = identity

        return changed

    def _load_characters(self):
        """Load characters.csv and apply name substitutions (Traveler/Wanderer/Manekin)."""
        identity = _identity_settings()
        username = identity["USERNAME"]
        wanderer_name = identity["WANDERER_NAME"]
        manekin_name = identity["MANEKIN_NAME"]
        manekina_name = identity["MANEKINA_NAME"]
        with open("data/characters.csv", "r", encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile, delimiter=",")
            characters = []
            for row in reader:
                if not row or row[0] == "------":
                    continue
                c = Character(*row)
                if (identity["MC_AETHER"] and c.search_str == "aether") or (
                    not identity["MC_AETHER"] and c.search_str == "lumine"
                ):
                    c.search_str = username.lower()
                    c.character_display_name = username

                if c.search_str == "wanderer":
                    c.search_str = wanderer_name.lower()
                    c.character_display_name = wanderer_name

                if c.search_str == "wonderland manekin":
                    c.search_str = manekin_name.lower()
                    c.character_display_name = manekin_name

                if c.search_str == "wonderland manekina":
                    c.search_str = manekina_name.lower()
                    c.character_display_name = manekina_name

                characters.append(c)
        return characters

    def load_all(self):
        """Load every data CSV. Called at startup and on hot-reload."""
        self.characters = self._load_characters()
        print(f"Loaded characters.csv: {len(self.characters)} characters")

        try:
            with open("data/domains.csv", "r") as csvfile:
                reader = csv.reader(csvfile, delimiter=",")
                self.domains = [
                    Domain(*row) for row in reader if row and row[0] != "------"
                ]
                print(f"Loaded domains.csv: {len(self.domains)} domains")
        except Exception as e:
            print(f"Error loading data/domains.csv: {e}")

        try:
            with open("data/locations.csv", "r", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile, delimiter=",", escapechar="\\")
                self.locations = [
                    Location(*row) for row in reader if row and row[0] != "------"
                ]
                print(f"Loaded locations.csv: {len(self.locations)} locations")
        except Exception as e:
            print(f"Error loading data/locations.csv: {e}")

        try:
            with open("data/gamemenus.csv", "r", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile, delimiter=",", escapechar="\\")
                self.gamemenus = [
                    Gamemenu(*row) for row in reader if row and row[0] != "------"
                ]
                print(f"Loaded gamemenus.csv: {len(self.gamemenus)} gamemenus")
        except Exception as e:
            print(f"Error loading data/gamemenus.csv: {e}")

        try:
            with open("data/bosses.csv", "r", encoding="utf-8") as csvfile:
                reader = csv.reader(csvfile, delimiter=",")
                self.bosses = [
                    Boss(*row) for row in reader if row and row[0] != "------"
                ]
                print(f"Loaded bosses.csv: {len(self.bosses)} bosses")
        except Exception as e:
            print(f"Error loading data/bosses.csv: {e}")
