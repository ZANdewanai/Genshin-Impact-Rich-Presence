"""
Search index for Genshin Impact Rich Presence.
Simple linear search - no caches, no fuzzy matching.
"""
from __future__ import annotations
from typing import Optional

from .models import (
    Boss, Character, Domain, Location, Gamemenu, DEBUG_MODE
)


class SearchIndex:
    """Simple search for all game data types."""

    def __init__(self, data):
        self.data = data

    def refresh_after_reload(self):
        """No-op - no caches to clear."""
        pass

    # ---- Boss search ----
    def search_boss(self, boss_text) -> Optional[Boss]:
        key = boss_text.lower()
        boss_match = [b for b in self.data.bosses if b.search_str in key]
        boss_match.sort(key=lambda b: len(b.search_str), reverse=True)
        if DEBUG_MODE and len(boss_match) > 1:
            print(
                f'WARN: Multiple world bosses matched for "{boss_text}": {[b.boss_name for b in boss_match]}'
            )
            print("Picking longest match")
        return boss_match[0] if boss_match else None

    # ---- Character search ----
    def search_character(self, charname_text) -> Optional[Character]:
        normalized_text = charname_text.lower().replace('\n', ' ').replace('\r', ' ')
        normalized_text = ' '.join(normalized_text.split())

        charname_match = [
            c for c in self.data.characters if c.search_str in normalized_text
        ]
        charname_match.sort(key=lambda c: len(c.search_str), reverse=True)
        if DEBUG_MODE and len(charname_match) > 1:
            print(
                f'WARN: Multiple characters matched for "{charname_text}": {[c.character_display_name for c in charname_match]}'
            )
            print("Picking longest match")
        return charname_match[0] if charname_match else None

    # ---- Domain search ----
    def search_domain(self, domain_text) -> Optional[Domain]:
        key = domain_text.lower()
        domain_match = [d for d in self.data.domains if d.search_str in key]
        domain_match.sort(key=lambda d: len(d.search_str), reverse=True)
        if DEBUG_MODE and len(domain_match) > 1:
            print(
                f'WARN: Multiple domains matched for "{domain_text}": {[d.domain_name for d in domain_match]}'
            )
            print("Picking longest match")
        return domain_match[0] if domain_match else None

    # ---- Location search ----
    def search_location(self, loc_text) -> Optional[Location]:
        key = loc_text.lower()
        location_match = [l for l in self.data.locations if l.search_str in key]
        location_match.sort(key=lambda l: len(l.search_str), reverse=True)
        if DEBUG_MODE and len(location_match) > 1:
            print(
                f'WARN: Multiple locations matched for "{loc_text}": {[l.location_name for l in location_match]}'
            )
            print("Picking longest match")
        return location_match[0] if location_match else None

    # ---- Gamemenu search ----
    def search_gamemenu(self, gamemenu_text) -> Optional[Gamemenu]:
        key = gamemenu_text.lower()
        all_matches = [
            g for g in self.data.gamemenus if g.search_str in key
        ]
        gamemenu_match = sorted(
            all_matches, key=lambda g: len(g.search_str), reverse=True
        )
        if DEBUG_MODE and len(gamemenu_match) > 1:
            print(
                f'WARN: Multiple gamemenus matched for "{gamemenu_text}": {[g.gamemenu_name for g in gamemenu_match]}'
            )
            print("Picking longest match")
        return gamemenu_match[0] if gamemenu_match else None