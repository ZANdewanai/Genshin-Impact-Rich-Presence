"""
Search index for Genshin Impact Rich Presence.

Match lists are pre-sorted once per data load - longest ``search_str`` first,
stable so CSV row order breaks ties (identical to the old per-query
filter+sort). Each search is then a single first-hit scan. Character name
variants used by CharSensor's fuzzy matching are precomputed here too, so
they are built once per reload instead of once per OCR fragment.
"""
from __future__ import annotations
import re
from typing import Optional

from .models import (
    Boss, Character, Domain, Location, Gamemenu, DEBUG_MODE
)


def _normal_key(text: str) -> str:
    return " ".join(str(text).lower().split())


def _compact_key(text: str) -> str:
    return "".join(ch for ch in _normal_key(text) if ch.isalnum())


_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _token_set(text: str) -> frozenset:
    return frozenset(_TOKEN_RE.findall(str(text).lower()))


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
        self._match_entries = {}
        for attr in self._LIST_ATTRS:
            items = getattr(self.data, attr, [])
            items = sorted(items, key=lambda o: len(o.search_str), reverse=True)
            setattr(self, f"_{attr}", items)
            self._match_entries[attr] = [
                (o, _normal_key(o.search_str), _compact_key(o.search_str))
                for o in items
            ]

        # Location OCR can reorder words ("Fontaine Court of") and often
        # shows only part of a canonical name ("Good Hunter" for "Good
        # Hunter Restaurant"). Keep token sets for longer names so
        # search_location can fall back to an order-insensitive subset
        # match after exact/compact matching fails.
        self._location_token_entries = []
        for o in self._locations:
            tokens = _token_set(o.search_str)
            if len(tokens) >= 2:
                self._location_token_entries.append((o, tokens))

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

    def _match(self, attr, key, label, name_attr, text, ocr_fuzzy=False):
        """First hit in the pre-sorted list.

        ``key`` is matched literally first; entries also get a compact
        alphanumeric fallback so OCR output that drops spaces or punctuation
        ("PalaisMermonia") still matches "palais mermonia". Location searches
        can enable ``ocr_fuzzy`` for OCR that truncates the end of a name
        ("Palais Mermoni") or only captures the start of a longer name
        ("Court of Fontaine" -> "Court of Fontaine Region").
        Under DEBUG_MODE the full match list is built anyway so ambiguous
        matches can be logged; otherwise this is a single early-exit scan.
        """
        match_key = _normal_key(key)
        compact_key = _compact_key(key)
        entries = self._match_entries[attr]

        def exact(entry):
            obj, needle, compact = entry
            return needle in match_key or (
                len(compact) >= 8 and compact in compact_key
            )

        def fuzzy(entry):
            obj, needle, compact = entry
            if len(compact) < 12 or not compact_key:
                return False
            if compact[:-1] in compact_key:
                return True
            if len(compact) >= 14 and compact[:-2] in compact_key:
                return True
            return (
                10 <= len(compact_key) <= len(compact)
                and len(compact) - len(compact_key) <= 6
                and compact.startswith(compact_key)
            )

        if DEBUG_MODE:
            matches = [entry[0] for entry in entries if exact(entry)]
            if not matches and ocr_fuzzy:
                matches = [entry[0] for entry in entries if fuzzy(entry)]
            if len(matches) > 1:
                print(
                    f'WARN: Multiple {label} matched for "{text}": '
                    f"{[getattr(o, name_attr) for o in matches]}"
                )
                print("Picking longest match")
            return matches[0] if matches else None
        for entry in entries:
            if exact(entry):
                return entry[0]
        if ocr_fuzzy:
            for entry in entries:
                if fuzzy(entry):
                    return entry[0]
        return None

    # ---- Boss search ----
    def search_boss(self, boss_text) -> Optional[Boss]:
        return self._match(
            "bosses", boss_text.lower(),
            "world bosses", "boss_name", boss_text,
        )

    # ---- Character search ----
    def search_character(self, charname_text) -> Optional[Character]:
        normalized_text = charname_text.lower().replace('\n', ' ').replace('\r', ' ')
        normalized_text = ' '.join(normalized_text.split())
        return self._match(
            "characters", normalized_text,
            "characters", "character_display_name", charname_text,
        )

    # ---- Domain search ----
    def search_domain(self, domain_text) -> Optional[Domain]:
        return self._match(
            "domains", domain_text.lower(),
            "domains", "domain_name", domain_text,
        )

    # ---- Location search ----
    def _match_location_tokens(self, loc_text) -> Optional[Location]:
        ocr_tokens = _token_set(loc_text)
        if len(ocr_tokens) < 2:
            return None
        matches = [
            o for o, tokens in self._location_token_entries
            if ocr_tokens <= tokens and len(tokens) - len(ocr_tokens) <= 3
        ]
        if not matches:
            return None
        if DEBUG_MODE and len(matches) > 1:
            print(
                f'WARN: Multiple locations matched for "{loc_text}": '
                f"{[o.location_name for o in matches]}"
            )
            print("Picking longest match")
        return matches[0]

    def search_location(self, loc_text) -> Optional[Location]:
        found = self._match(
            "locations", loc_text.lower(),
            "locations", "location_name", loc_text, ocr_fuzzy=True,
        )
        if found is not None:
            return found
        return self._match_location_tokens(loc_text)

    # ---- Gamemenu search ----
    def search_gamemenu(self, gamemenu_text) -> Optional[Gamemenu]:
        return self._match(
            "gamemenus", gamemenu_text.lower(),
            "gamemenus", "gamemenu_name", gamemenu_text,
        )
