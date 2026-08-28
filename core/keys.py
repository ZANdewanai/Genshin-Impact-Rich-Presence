"""Canonical blackboard JSON key names.

Sensors publish to their own JSON files; the coordinator reads them. Centralizing
the key names so a rename never silently breaks the sensors <-> coordinator
handoff (which happens across unrelated threads).
"""

# characters.json (CharSensor -> coordinator)
HUD_VISIBLE = "hud_visible"
SLOTS = "slots"
ACTIVE_SLOT_HINT = "active_slot_hint"

# location.json (LocationSensor -> coordinator)
LOCATION = "location"
BOSS = "boss"
BOSS_RAW = "boss_raw"
BOSS_RAW_TS = "boss_raw_ts"
COMMISSION = "commission"
MAP_LOCATION = "map_location"

# menus.json (MenuSensor -> coordinator)
GAMEMENU = "gamemenu"
GAMEMENU_SEARCH = "gamemenu_search"
PARTY_SETUP = "party_setup"
REWARD_CUTSCENE = "reward_cutscene"
DOMAIN = "domain"
DOMAIN_SEARCH = "domain_search"