"""
CSV data loader for Genshin Impact Rich Presence.
Loads all game data from CSV files at startup.
"""
from __future__ import annotations
import csv

from .models import (
    Boss, Character, Domain, Location, Gamemenu,
    _identity_settings
)


class Data:
    """Model for all game data. Loads CSVs once at startup."""

    def __init__(self):
        self.bosses: list[Boss] = []
        self.characters: list[Character] = []
        self.domains: list[Domain] = []
        self.locations: list[Location] = []
        self.gamemenus: list[Gamemenu] = []

        self.load_all()

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
        """Load every data CSV. Called once at startup."""
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