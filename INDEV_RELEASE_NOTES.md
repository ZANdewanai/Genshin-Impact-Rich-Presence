# Genshin Impact Rich Presence v3.0 - Indev Release Notes

## 🚀 Major Updates
- **Complete GUI Overhaul**: Modern PyQt5 interface with real-time monitoring and user-friendly configuration
- **Embedded Python Runtime**: Self-contained 2GB+ bundle - no external Python installation required (eliminates dependency issues)
- **Natlan & Nod-Krai Support**: Full coverage for newest regions including all characters, domains, bosses, and locations
- **Comprehensive Content Database**:
  - 100+ Characters: Complete coverage from Mondstadt to Nod-Krai (including latest like Chasca, Mavuika, etc.)
  - 250+ Domains: All types (Forgery, Blessing, Mastery, Trounce) across all regions
  - 400+ Locations: Complete location tracking for accurate Rich Presence
  - 40+ Bosses: All world and weekly bosses including latest additions
- **Dynamic Resolution Detection**: Automatic adaptation to any screen resolution (720p to 4K, ultrawide, etc.)
- **Enhanced OCR Engine**: Improved text recognition accuracy with GPU acceleration support

## 🛠️ Technical Improvements
- Modular architecture for better maintainability and future updates
- Optimized memory usage and performance for long-running sessions
- Comprehensive error handling and logging for easier debugging
- Cross-platform Windows compatibility improvements

## 🐛 Bug Fixes
- Fixed character recognition issues with special characters and edge cases
- Resolved location detection problems in newer regions
- Improved stability during extended gaming sessions
- Fixed minor GUI display and responsiveness issues

## ⚠️ Breaking Changes & Migration Notes
- **Complete Rewrite**: No backwards compatibility - full reinstallation required
- **New Configuration System**: All settings now managed through GUI (legacy CONFIG.py mostly obsolete)
- **File Size Increase**: ~2GB due to embedded Python (previously ~20MB) - no external dependencies needed
- **System Requirements Updated**:
  - Windows 7 or later (64-bit recommended)
  - 3GB free storage space
  - 4GB RAM minimum, 8GB recommended
  - NVIDIA GPU recommended for OCR performance

## 📋 Setup & Usage
- **Quick Start**: Double-click `start_gui.bat` for instant GUI launch
- **Configuration**: Use GUI for username, character selection, and settings
- **Alternative Launch**: `python_embedded\python.exe genshin_impact_rich_presence_gui.py`
- **Console Mode**: `python_embedded\python.exe main.py` (OCR only, no Discord integration)

## 🛠️ Known Issues
- Some very rare character name combinations may require manual configuration
- Performance may vary based on system specifications and game settings
- GUI may have minor responsiveness issues on very low-end hardware

---

*This is an in-development release. Features may be unstable or incomplete. Report issues through the project repository.*
