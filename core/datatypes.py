"""
Backward-compatible re-exports for core.datatypes.

This module re-exports all public API from the split modules:
- core.models: Data classes, enums, DEBUG flags, _identity_settings
- core.data_loader: Data class (CSV loading + watchdog)
- core.search_index: SearchIndex class (search caches + fuzzy matching)
- core.activity_renderer: render_activity function (patched onto Activity)
"""

# Models (data classes, enums, config flags)
from core.models import (
    Boss,
    Character,
    Domain,
    DomainType,
    Location,
    Gamemenu,
    GamemenuType,
    ActivityType,
    Activity,
    DEBUG_MODE,
    DEBUG_CHARACTER_MODE,
    _identity_settings,
)

# Data loader (CSV loading + watchdog)
from core.data_loader import Data

# Search index (search caches + fuzzy matching)
from core.search_index import SearchIndex

# Activity renderer (already monkey-patched onto Activity.to_update_params_dict)
from core.activity_renderer import render_activity

# Explicit exports for clarity
__all__ = [
    "Boss",
    "Character",
    "Domain",
    "DomainType",
    "Location",
    "Gamemenu",
    "GamemenuType",
    "ActivityType",
    "Activity",
    "DEBUG_MODE",
    "DEBUG_CHARACTER_MODE",
    "_identity_settings",
    "Data",
    "SearchIndex",
    "render_activity",
]