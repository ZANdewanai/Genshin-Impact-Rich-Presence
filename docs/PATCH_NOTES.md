# Genshin Impact Rich Presence - Version History

## [v3.0] - 2025-10-12

### Major Changes
- **Complete GUI Overhaul**: Replaced command-line configuration with a user-friendly graphical interface
- **Dynamic Resolution Detection**: Automatic detection of game window resolution and scaling of coordinates
- **Enhanced Character Detection**: Improved OCR accuracy and reliability for character recognition
- **Modular Architecture**: Restructured codebase for better maintainability and future updates

### Major Content Updates
- **Natlan Complete Coverage**: Added full support for Natlan region including all characters, domains, bosses, and locations
- **Nod-Krai Region**: Complete implementation of the new Nod-Krai region with all associated content
- **Latest Characters**: Added support for newest characters including:
  - Chasca, Citlali, Iansan, Ifa, Kachina, Kinich, Mavuika, Mualani, Ororon, Varesa, Xilonen
  - Aino, Flins, Ineffa, Lauma, Nefer (new character variants)
- **Expanded Fontaine & Sumeru**: Enhanced coverage with additional domains and locations
- **Content Database Expansion**:
  - **Characters**: 100+ characters now supported (comprehensive coverage from Mondstadt to Nod-Krai)
  - **Domains**: 250+ domains across all types (Forgery, Blessing, Mastery, Trounce)
  - **Bosses**: 40+ world and weekly bosses including latest additions
  - **Locations**: 400+ locations spanning all regions and sub-areas
  - **Game Menus**: Complete menu system coverage with accurate status detection

### New Features
- **Graphical User Interface (GUI)**
  - Real-time status monitoring
  - In-application configuration
  - Visual feedback for detection status
  - Easy settings management

- **Improved OCR Engine**
  - Better text recognition for character names and locations
    - Reduced false positives in text detection

- **Dynamic Coordinate System**
  - Automatic adaptation to different screen resolutions
  - More accurate element detection across different display settings

- **Dynamic GUI Integration**: Improved GUI responsiveness and real-time status monitoring
- **Enhanced Character Detection**: Better OCR accuracy for special characters and edge cases
- **Advanced Location Tracking**: More precise location identification across all regions
- **Performance Optimizations**: Reduced resource usage while maintaining accuracy

### Bug Fixes
- Fixed issues with character detection in certain regions
- Resolved problems with Rich Presence not updating properly
- Improved handling of game window focus and state changes
- Fixed character recognition issues with certain special characters
- Resolved location detection problems in newer regions
- Improved stability during extended gaming sessions
- Fixed minor GUI display issues

### Technical Improvements
- Refactored codebase for better performance
- Added comprehensive error handling
- Improved logging for debugging purposes
- Better resource management
- **Code Architecture**: Further modularization for better maintainability
- **Error Handling**: Enhanced error reporting and recovery mechanisms
- **Memory Management**: Optimized memory usage for long-running sessions
- **Cross-Platform Compatibility**: Improved Windows compatibility and scaling

### Known Issues
- Some character names with special characters may not be recognized correctly
- Performance impact may be higher than previous versions due to enhanced features
- Some very rare character name combinations may still require manual configuration
- Performance impact may vary based on system specifications and game settings

### ⚠️ Breaking Changes & Migration Notes
- **No Backwards Compatibility**: This is a complete rewrite with no automatic migration path
- **New Configuration Required**: All settings must be reconfigured through the new GUI
- **Clean Installation Recommended**: Previous configuration files are not compatible
- **System Requirements Updated**: Ensure your system meets the new requirements
- **Embedded Python Runtime**: The application now includes a built-in Python environment, eliminating the need for external Python installation but significantly increasing file size to 2GB+ (previously ~20MB)

### Important Notes for v2.6 Users
1. Backup any custom configurations from v2.6 if needed
2. Uninstall the previous version completely before installing v3.0
3. The new version uses a different configuration system and file structure
4. Some features may work differently or have been reimplemented






## [v2.6] - Previous Version
### Core Features
- **Rich Presence Integration**: Displayed in-game activity on Discord
- **Multi-Character Detection**: Supported detection of up to 4 party members
- **Location Tracking**: Recognized different regions and domains in Teyvat
- **Basic OCR**: Implemented text recognition for UI elements
- **Automatic Game Detection**: Could detect when Genshin Impact was running

### Technical Implementation
- **Python-based**: Built using Python with pypresence for Discord integration
- **Image Processing**: Utilized OpenCV and Tesseract OCR for text recognition
- **Configuration**: Required manual setup of screen coordinates in CONFIG.py
- **Resolution Support**: Primarily designed for 1080p with manual scaling options

### Limitations
- Required manual coordinate configuration for different resolutions
- Limited character recognition accuracy in some scenarios
- No graphical user interface - all configuration was file-based
- Basic error handling and logging
- No automatic updates or version checking

### System Requirements
- Python 3.7+
- Tesseract OCR installed and in system PATH
- Genshin Impact running in Windowed or Borderless Windowed mode
- Discord desktop client running
