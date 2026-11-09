"""
Search index for Genshin Impact Rich Presence.

Match lists are pre-sorted once per data load - longest ``search_str`` first,
stable so CSV row order breaks ties (identical to the old per-query
filter+sort). Each search is then a single first-hit scan. Character name
variants used by CharSensor's fuzzy matching are precomputed here too, so
they are built once per reload instead of once per OCR fragment.
"""
from __future__ import annotations
from typing import Optional

from .models import (
    Boss, Character, Domain, Location, Gamemenu, DEBUG_MODE
)


class SearchIndex:
    """Simple search for all game data types."""

    _LIST_ATTRS = ("bosses", "characters", "domains", "locations", "gamemenus")

    def __init__(self, data):
        self.data = data
        self._rebuild()

    def refresh_after_reload(self):
        """Rebuild precomputed match lists after a data CSV reload."""
        self._rebuild()

    def _rebuild(self):
        for attr in self._LIST_ATTRS:
            items = getattr(self.data, attr, [])
            setattr(
                self, f"_{attr}",
                sorted(items, key=lambda o: len(o.search_str), reverse=True),
            )

        # CharSensor party-name matching helpers, precomputed once:
        #  - _char_variants: (character, {search_str, despaced}) per character
        #  - _char_search_strs: every searchable variant, len-desc, deduped
        #    with insertion order preserved for stable tie-breaking.
        self._char_variants = [
            (
                c,
                frozenset({
                    c.search_str.lower(),
                    c.search_str.lower().replace(" ", ""),
                }),
            )
            for c in self.data.characters
        ]
        strs = []
        for c in self.data.characters:
            strs.append(c.search_str.lower())
            if " " in c.search_str:
                strs.append(c.search_str.lower().replace(" ", ""))
        self._char_search_strs = sorted(
            dict.fromkeys(strs), key=len, reverse=True
        )

    def character_variants(self):
        """(character, name-variant set) pairs for fuzzy party-name matching."""
        return self._char_variants

    def character_search_strings(self):
        """Precomputed lowercase search strings (len-desc) for party OCR."""
        return self._char_search_strs

    def _match(self, items, key, label, name_attr, text):
        """First hit in the pre-sorted list.

        Under DEBUG_MODE the full match list is built anyway so ambiguous
        matches can be logged; otherwise this is a single early-exit scan.
        """
        if DEBUG_MODE:
            matches = [o for o in items if o.search_str in key]
            if len(matches) > 1:
                print(
                    f'WARN: Multiple {label} matched for "{text}": '
                    f"{[getattr(o, name_attr) for o in matches]}"
                )
                print("Picking longest match")
            return matches[0] if matches else None
        for o in items:
            if o.search_str in key:
                return o
        return None

    # ---- Boss search ----
    def search_boss(self, boss_text) -> Optional[Boss]:
        return self._match(
            self._bosses, boss_text.lower(),
            "world bosses", "boss_name", boss_text,
        )

    # ---- Character search ----
    def search_character(self, charname_text) -> Optional[Character]:
        normalized_text = charname_text.lower().replace('\n', ' ').replace('\r', ' ')
        normalized_text = ' '.join(normalized_text.split())
        return self._match(
            self._characters, normalized_text,
            "characters", "character_display_name", charname_text,
        )

    # ---- Domain search ----
    def search_domain(self, domain_text) -> Optional[Domain]:
        return self._match(
            self._domains, domain_text.lower(),
            "domains", "domain_name", domain_text,
        )

    # ---- Location search ----
    def search_location(self, loc_text) -> Optional[Location]:
        return self._match(
            self._locations, loc_text.lower(),
            "locations", "location_name", loc_text,
        )

    # ---- Gamemenu search ----
    def search_gamemenu(self, gamemenu_text) -> Optional[Gamemenu]:
        return self._match(
            self._gamemenus, gamemenu_text.lower(),
            "gamemenus", "gamemenu_name", gamemenu_text,
        )
