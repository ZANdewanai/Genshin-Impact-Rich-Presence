# Asset update pipeline

When a new Genshin version adds characters / bosses / domains / locations,
regenerate the Discord image assets in this order:

1. `create_placeholders.py` — stub out image files for every new entry in the
   data CSVs so the engine never references a missing asset.
2. Download real portraits/icons for the new entries:
   - `download_character_portraits_v2.py` (current character downloader)
   - `download_boss_portraits.py` / `download_weekly_boss_portraits.py`
   - `download_wiki_portraits.py` (generic wiki fallback)
3. `rename_to_asset_names.py` — normalize downloaded filenames to image keys.
4. Spot-check hashes/naming (`test_wiki_hashes.py`) and the results in
   `resources/assets/images/`.

Scripts that are superseded or one-off helpers (e.g. the v1 character
downloader, `download_missing_assets.py`, `debug_icons.py`) are kept for
reference but are not part of the routine update flow.

The GUI-side icon pack (`tools/download_icons.py` + its embedded-python .bat
launcher at `tools/`) is separate and already documented at `tools/`.
