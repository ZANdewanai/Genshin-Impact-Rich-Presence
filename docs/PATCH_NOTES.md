# Genshin Impact Rich Presence - Version History

## [v3.0] - Current Stable Release

### Major Changes
- **Complete Architecture Rewrite**: From a single Python script to a multi-process application with a web-based GUI
- **Web-based GUI**: React + Vite + Tailwind CSS v4 frontend served via local HTTP and wrapped in pywebview with Edge Chromium
- **OCR Engine Migration**: Replaced EasyOCR/PyTorch with RapidOCR/ONNX Runtime + DirectML GPU support
- **Dynamic Resolution Detection**: Automatic detection of game window resolution and scaling of OCR coordinates — no manual coordinate configuration needed
- **6-Party Support**: Expanded from 4 to 6 party member detection
- **Separate Engine Process**: OCR and Discord RPC run in a dedicated `RichPresenceEngine.exe` spawned by the GUI
- **Bundled Runtime**: Self-contained distribution with embedded Python — no external Python installation required

### Major Content Updates (from v2.6)
- **Nod-Krai Region**: 38 new locations across 6 sub-regions (Ashveil Peak, Voidsea Outlook, Wavechaser Plain, Lempo Isle, Hiisi Island, Paha Isle), plus 6 new characters
- **Snezhnaya Expansion**: 30+ new locations including Snezhnograd, Zapolyarny Palace, Volkodlak Tundra, Lunar Highlands, and the Dark Side of the Moon, plus 6 new characters
- **Natlan Expansion**: 30+ new locations including Stadium of the Sacred Flame, Ochkanatlan, and Xalac Vale, plus 11 new characters
- **Fontaine Expansion**: 30+ new locations including Fortress of Meropide, Tower of Ipsissimus, and Nostoi Region
- **Expanded Content Database** (v2.6 → v3.0):
  - **Characters**: 80 → 123 (+43)
  - **Domains**: 53 → 258 (+205, reorganized into I-IV difficulty tiers)
  - **Bosses**: 28 → 50 (+22)
  - **Locations**: 255 → 495 (+240)
  - **Game Menus**: 52 → 111 (+59, added reputation systems for all regions, cooking/crafting/forging menus, abyss floors, cutscenes)

### New Features
- **Real-time GUI**: Live status monitoring, connection toggle, log viewer, and Discord Rich Presence preview
- **Settings Tab**: In-app configuration for username, character names, and options — no CONFIG.py editing needed
- **Sensor Worker Architecture**: Character, location, and menu detection run in dedicated worker threads coordinated via a shared blackboard
- **Hot-Reloaded Data**: CSV files in `data/` reload on change — add missing locations/characters while playing without restarting
- **OCR Pause on Focus Loss**: OCR automatically pauses when Genshin loses focus or is minimized
- **Adaptive Character Detection**: Character name regions self-adjust if UI scaling shifts the party HUD

### Technical Improvements
- **GUI**: React + Vite + Tailwind CSS v4 frontend served via local HTTP server on a free port, wrapped in pywebview Edge Chromium
- **Engine**: Separate `RichPresenceEngine.exe` spawned by the GUI for OCR + Discord RPC, communicating via atomic JSON file writes
- **Shared Config**: `shared_config.json` for settings shared between GUI and engine
- **Build System**: PyInstaller-based distribution producing a self-contained folder (~270MB) with two exes and shared `_internal/`
- **Cross-GPU Support**: DirectML works on NVIDIA, AMD, and Intel GPUs

### Breaking Changes & Migration from v2.6
- **Complete Rewrite**: No backwards compatibility — this is a full rewrite with a completely different environment, build system, and architecture
- **No Migration Path**: Old configurations, coordinates, and settings from v2.6 are not compatible with v3.0
- **Clean Installation Required**: Uninstall any previous version completely before installing v3.0
- **Launch Method Changed**: Users launch `GenshinRichPresence.exe` or `start_gui.bat` / `start_gui.ps1`, not `main.py` directly
- **Engine Separation**: OCR and Discord RPC run in a separate `RichPresenceEngine.exe` process spawned by the GUI
- **Bundled Python**: The application includes a bundled Python runtime (~270MB total), eliminating the need for external Python installation

### Known Issues
- Some character names with special characters may not be recognized correctly
- Performance may vary based on system specifications and game settings
- Some very rare character name combinations may still require manual configuration



## [v2.6] - Fontaine Update (Previous Version)
- Fork of euwbah's Genshin Impact Rich Presence reimplementation
- Single-script Python application with no GUI — launched via `StartRichPresence.bat`
- EasyOCR + PyTorch for text recognition, requiring NVIDIA GPU and Python 3.11.1
- pypresence for Discord RPC integration
- Manual CONFIG.py setup with pixel coordinates for specific resolutions (720p, 1080p, 1440p, 2160p)
- 4-party member detection only
- Sequential single-threaded OCR loop
- Hot-reloaded CSV data files via watchdog
- Data coverage: 80 characters, 255 locations, 53 domains, 28 bosses, 52 game menus
