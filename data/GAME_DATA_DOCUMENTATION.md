# Genshin Impact Rich Presence - Game Data Files Documentation

## 📊 Overview

This folder contains CSV (Comma-Separated Values) data files that define the game's elements for the Rich Presence system. These files are **hot-reloaded**, meaning changes take effect immediately without restarting the application.

Each CSV file contains records of game elements (characters, locations, domains, bosses, etc.) with their attributes separated by commas. The first column is always the **search phrase** - the in-game text the OCR system looks for to identify each element.

> **🔥 Critical**: All search phrases must be **lowercase only**. Refer to [coordinate configuration documentation](../configure%20coordinates.md) for exact in-game text detection details.

## 📋 CSV File Formats & Guidelines

### [Characters](characters.csv)

**Format:**
```csv
lowercase search phrase, character image asset, character display name
traveler,                char_aether,          Aether
lumine,                  char_lumine,          Lumine
```

**Guidelines:**
- Contains all playable characters from Mondstadt to Nod-Krai
- **Search phrase**: Should match character names in the character selection screen (right panel), not full names
- **Image assets**: Located in `../resources/assets/characters/` (e.g., `char_kirara.png` becomes `char_kirara`)
- **Display name**: Human-readable name shown in Discord Rich Presence
- **Tip**: For travelers, use separate entries for Aether (`traveler`) and Lumine (`lumine`)

**Current Coverage:** 100+ characters including latest Natlan additions (Chasca, Mavuika, etc.)

### [Domains](domains.csv)

**Format:**
```csv
lowercase search phrase, domain name,                        domain type, location image asset
obsession,               Tower of Abject Pride | Obsession,  forgery,     domain_forgery_sumeru
```

**Guidelines:**
- Contains Trounce Domains, Domains of Blessing, Mastery, Forgery, and special domains
- **Domain name format**: `<location name> | <challenge name>`
- **Search phrase**: Use only the challenge name (not location name) for detection
- **Domain types** (must match exactly):
  - `mastery` - Domain of Mastery
  - `forgery` - Domain of Forgery
  - `blessing` - Domain of Blessing
  - `trounce` - Trounce Domain (weekly bosses)
  - `one-time` - One-time domains (exploration/story)
  - `limited` - Limited-time event domains
- **Image assets**: Located in `../resources/assets/domains/`

**Current Coverage:** 250+ domains across all regions including Natlan and Nod-Krai

**Notes:**
- Weekly bosses in Trounce Domains are included here
- One-time and event domains may be incomplete
- Long challenge names: Use the front part as search phrase

### [Locations](locations.csv)

**Format:**
```csv
lowercase search phrase, location name, subarea name, country name, location emblem image asset
wuwang hill,             Wuwang Hill,   Bishui Plain, Liyue,        emblem_liyue
```

**Guidelines:**
- Contains locations, subareas, and points of interest
- **Search phrases** detect:
  - Large location pop-ups while traveling (use location name only)
  - Unique in-game text for specific areas (e.g., `tubby` for Serenitea Pot)
- **Image assets**: Located in `../resources/assets/emblems/`
- **Coverage**: Cities, landmarks, special areas, teapot, taverns, etc.

**Current Coverage:** 400+ locations including all regions and special areas

**Tips:**
- Use shortest unique phrase possible for long names
- Include alternative spellings/phrases for better detection
- Reference [Genshin Wiki locations](https://genshin-impact.fandom.com/wiki/Locations) for completeness

### [Bosses](bosses.csv)

**Format:**
```csv
lowercase search phrase, boss name,        boss image asset
anemo hypostasis,        Anemo Hypostasis, boss_anemo_hypostasis
```

**Guidelines:**
- Contains world bosses (not Trounce Domain bosses)
- **Search phrase**: Match the upper boss name in-game
- **Image assets**: Located in `../resources/assets/bosses/`
- **Note**: Trounce Domain bosses are in `domains.csv`, not here

**Current Coverage:** 40+ world bosses including latest additions

**Examples:**
- `anemo hypostasis` (not `beth`)
- `aeonblight drake`
- `emperor of fire and iron`

### [Game Menus](gamemenus.csv)

**Format:**
```csv
lowercase search phrase, menu description,                   context, icon asset
mailbox,                 Looking at the Mailbox,            In Menus, icon_mailbox
```

**Guidelines:**
- Contains UI states, menus, and interactive elements
- **Search phrase**: In-game text for menus, achievements, shops, etc.
- **Description**: Human-readable description shown in Rich Presence
- **Context**: Where the detection occurs (In Menus, In Archive, Spyral Abyss, etc.)
- **Icon assets**: Located in `../resources/assets/icons/`

**Coverage:** Complete menu system including reputation, tutorials, inventory, quests, achievements, etc.

## 🛠️ Editing Guidelines

### Search Phrase Rules
1. **Always lowercase**
2. Remove punctuation or replace with spaces
3. Use shortest unique phrase possible
4. Test in-game to ensure accuracy

### Image Asset Naming
- All lowercase
- No file extensions
- Spaces become underscores
- Example: `Char Kirara.png` → `char_kirara`

### Adding New Entries
1. Test the in-game text appears correctly
2. Use coordinate configuration to verify detection areas
3. Add to appropriate CSV with correct format
4. Changes take effect immediately (hot-reload)

## 📈 Maintenance Notes

- **Incompleteness**: Some areas may be missing (marked with ⚠️)
- **Updates**: As new content is added to Genshin Impact, these files need updating
- **Testing**: Always test new entries in-game before committing
- **Version Control**: These files are tracked in Git for collaborative editing

For questions or contributions, refer to the main project documentation or open an issue in the repository.
