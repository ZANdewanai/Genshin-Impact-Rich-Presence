# Full Project Audit - Genshin Impact Rich Presence

**Date:** 2026-04-02  
**Version:** v3.0 INDEV  
**Auditor:** Kilo (Automated)

---

## Executive Summary

This is a Python-based Discord Rich Presence application for Genshin Impact that uses OCR (EasyOCR) to detect in-game activity from screen captures and displays it via Discord RPC. The project has a GUI (PyQt5) wrapper around a console-based detection engine. The codebase is reasonably well-structured with a modular `core/` package, but has several issues ranging from critical security concerns to code quality problems.

**Overall Risk Level: MEDIUM**

---

## 1. CRITICAL ISSUES

### 1.1 `shared_config.json` Leaked to Git Despite `.gitignore` [SECURITY]

- **File:** `shared_config.json`
- **Issue:** The file contains personal data (`"USERNAME": "ZANdewanai"`) and is tracked by git despite being listed in `.gitignore`. This happens because the file was committed *before* the `.gitignore` entry was added. Once tracked, `.gitignore` no longer applies.
- **Impact:** Personal username data is publicly exposed in the repository.
- **Fix:** Run `git rm --cached shared_config.json` to untrack it. The `.gitignore` entry will then take effect.

### 1.2 Unsafe Global State Mutations [CODE QUALITY / THREAD SAFETY]

- **File:** `core/detection.py:131-132, 542-547`
- **Issue:** `detect_characters_with_adaptation()` and `run_detection_iteration()` declare and modify many `global` variables (`current_characters`, `current_active_character`, `last_active_character`, `game_paused`, etc.) without always holding `state_lock`. Some globals are modified directly (e.g., `current_characters = current_characters.copy()`) outside of lock protection.
- **Impact:** Race conditions between the main detection loop, RPC thread, and GUI monitoring thread. Could lead to corrupted state or crashes.
- **Fix:** Ensure all global state reads and writes are protected by `state_lock`. Consider encapsulating state in a class with thread-safe methods.

### 1.3 Unsafe `os._exit(0)` Call [SHUTDOWN]

- **File:** `main.py:236`
- **Issue:** `signal_handler` calls `os._exit(0)` which bypasses Python's normal cleanup, potentially leaving resources open, locks held, or files in inconsistent state.
- **Impact:** Minor - acceptable for a desktop utility, but could leave `shared_config.json` or `gui_shared_data.json` in a corrupted state if written mid-operation.
- **Fix:** Consider using `sys.exit(0)` with proper cleanup, or at minimum ensure file writes are flushed before `_exit`.

---

## 2. HIGH ISSUES

### 2.1 Duplicate `_ensure_image_cache_dir` Method [BUG]

- **File:** `genshin_impact_rich_presence_gui.py:1344-1346` and `genshin_impact_rich_presence_gui.py:1380-1383`
- **Issue:** The `GenshinRichPresenceApp` class defines `_ensure_image_cache_dir` twice. The first definition (line 1344) creates a cache in `%APPDATA%\GenshinImpactRichPresence\images`, while the second (line 1380) creates it in `<project_dir>\cache\image_cache`. The second definition silently overrides the first.
- **Impact:** Image caching may not work as intended; downloaded images may be stored in unexpected locations.
- **Fix:** Remove one of the duplicate definitions. The project-dir version is more appropriate for a portable application.

### 2.2 Dead Code After Method Definition [BUG]

- **File:** `genshin_impact_rich_presence_gui.py:1481-1491`
- **Issue:** Lines 1481-1491 contain orphaned code after `_update_status_image` method that references undefined variable `activity`. This code appears to be leftover from a merge/refactoring and would cause a `NameError` if ever reached.
- **Impact:** The code is unreachable (it's after a `return` or at the end of a method that doesn't call it), but it's dead code that should be cleaned up.
- **Fix:** Remove lines 1481-1491.

### 2.3 Missing Character Slot in GUI Non-1080p Scaling [BUG]

- **File:** `genshin_impact_rich_presence_gui.py:171-175`
- **Issue:** When `GAME_RESOLUTION != 1080` and no adapted coordinates are available, `CHARACTER_NUMBER_COORDINATES` only has 3 entries instead of 4. Character 2's coordinates are missing from the non-1080p fallback path.
- **Impact:** Character slot 2 would never be detected in non-1080p resolutions without adapted coordinates.
- **Fix:** Add the missing Character 2 entry: `(int(2484 * scale), int(481 * scale))`.

### 2.4 No Input Validation on User-Supplied Text [SECURITY]

- **File:** `genshin_impact_rich_presence_gui.py` (username_entry, wanderer_entry), `CONFIG.py:11,34`
- **Issue:** User-supplied strings (username, wanderer name) are used directly in string operations without sanitization. While the attack surface is limited (local application), no length limits or character filtering is applied.
- **Impact:** Extremely long strings could cause performance issues; special characters could break CSV parsing if the username is used in data operations.
- **Fix:** Add reasonable length limits (e.g., 32 chars) and basic character validation.

### 2.5 Hardcoded GitHub URLs [MAINTENABILITY]

- **File:** `CONFIG.py:289`, `genshin_impact_rich_presence_gui.py:1390, 1419, 1427`
- **Issue:** GitHub raw content URLs are hardcoded to specific branches (`main`) and user (`ZANdewanai`). Multiple different URL patterns exist for the same purpose.
- **Impact:** If the repository is forked, moved, or the branch changes, all image loading breaks. Multiple fallback URL patterns create confusion.
- **Fix:** Centralize URL construction into a single utility function. Make the base URL configurable.

---

## 3. MEDIUM ISSUES

### 3.1 Duplicate Dependencies in `requirements.txt`

- **File:** `requirements.txt:18-19, 36, 46`
- **Issue:** `imageio==2.37.0` appears twice (lines 18 and 36). `scipy==1.16.2` appears twice (lines 17 and 46).
- **Impact:** Confusing; pip will just install the same version twice (no-op). Not a functional issue.
- **Fix:** Remove duplicate entries.

### 3.2 `opencv-python` and `opencv-python-headless` Both Listed

- **File:** `requirements.txt:14-15`
- **Issue:** Both `opencv-python` and `opencv-python-headless` are listed. These are mutually exclusive packages - you should use one or the other.
- **Impact:** Potential conflicts; the headless version is typically preferred for non-GUI applications.
- **Fix:** Remove `opencv-python` and keep only `opencv-python-headless` (or vice versa, depending on whether OpenCV GUI features are needed).

### 3.3 Unused Imports

- **File:** `genshin_impact_rich_presence_gui.py:8-13` (multiprocessing, subprocess imported multiple times), `core/ocr_engine.py:7` (sys unused after initial path setup)
- **Issue:** Several modules have unused or redundant imports.
- **Impact:** Minor code quality issue.
- **Fix:** Clean up unused imports.

### 3.4 `customtkinter` Listed But Never Used

- **File:** `requirements.txt:56`
- **Issue:** `customtkinter==5.2.2` is listed as a dependency but the application uses PyQt5. The comment says "Optional GUI enhancements" but it's never imported.
- **Impact:** Adds ~5MB of unnecessary dependencies to the embedded Python environment.
- **Fix:** Remove from requirements.txt.

### 3.5 Bare `except:` Clauses

- **File:** `main.py:230`
- **Issue:** `except: pass` in the signal handler silently swallows all exceptions including `KeyboardInterrupt` and `SystemExit`.
- **Impact:** Could hide critical errors during shutdown.
- **Fix:** Use `except Exception:` at minimum.

### 3.6 Race Condition in Shared File I/O

- **File:** `main.py:406-407` (write), `genshin_impact_rich_presence_gui.py:1142-1143` (read)
- **Issue:** The main process writes `gui_shared_data.json` and the GUI reads it concurrently. There's no file locking, atomic rename, or write-to-temp-then-move pattern.
- **Impact:** The GUI could read a partially-written JSON file, causing `json.JSONDecodeError`. The code handles this with try/except but may miss data updates.
- **Fix:** Write to a temp file and atomically rename, or use file locking.

### 3.7 Inconsistent Timer/Resolution Values Between CONFIG and GUI Defaults

- **File:** `CONFIG.py` vs `genshin_impact_rich_presence_gui.py` Config class
- **Issue:** Default values differ:
  - `OCR_CHARNAMES_ONE_IN`: CONFIG=10, GUI=30
  - `OCR_LOC_ONE_IN`: CONFIG=5, GUI=10
  - `OCR_BOSS_ONE_IN`: CONFIG=30, GUI=20
  - `PAUSE_STATE_COOLDOWN`: CONFIG=2, GUI=5
  - `INACTIVE_COOLDOWN`: CONFIG=5, GUI=60
  - `ACTIVE_CHARACTER_THRESH`: CONFIG=720, GUI=700
- **Impact:** Different behavior depending on which entry point is used.
- **Fix:** Unify defaults in a single source of truth.

---

## 4. LOW ISSUES

### 4.1 Python 3.14 Cache Files in Repo

- **File:** `__pycache__/CONFIG.cpython-314.pyc`, `__pycache__/main.cpython-314.pyc`
- **Issue:** Python 3.14 bytecode cache files are committed to the repo (the project uses embedded Python 3.13).
- **Impact:** Unnecessary files in the repo; the `__pycache__/` entry in `.gitignore` should prevent this but these were committed before.
- **Fix:** `git rm -r --cached __pycache__/`

### 4.2 `debug_images/` Directory in Repo

- **File:** `debug_images/`
- **Issue:** Debug screenshot images are committed to the repository.
- **Impact:** Increases repo size with potentially sensitive game screenshots.
- **Fix:** Add `debug_images/` to `.gitignore` and remove from tracking.

### 4.3 Embedded Python Directory (~2GB+)

- **File:** `python3.13.11_embedded/`
- **Issue:** An entire embedded Python distribution with PyTorch+CUDA (~2GB+) is committed or expected in the repo.
- **Impact:** Massive repo size. Not in `.gitignore` so expected to be distributed this way.
- **Recommendation:** This is a deliberate distribution choice, but consider using Git LFS or a separate download mechanism.

### 4.4 Inconsistent Error Handling Patterns

- **Files:** Throughout codebase
- **Issue:** Some places use `except Exception as e:`, others use bare `except:`, others catch specific exceptions. No consistent error handling strategy.
- **Impact:** Inconsistent behavior; some errors are silently swallowed while others are reported.

### 4.5 `Data` Class Uses Class-Level Mutable Defaults

- **File:** `core/datatypes.py:446-462`
- **Issue:** `Data` class defines mutable class-level attributes like `bosses: list[Boss] = []`, `party_capture_cache = {}`. These are shared across all instances.
- **Impact:** If multiple `Data` instances were created (currently only one), they'd share the same lists/dicts. This is a latent bug.
- **Fix:** Initialize mutable attributes in `__init__` instead of at class level.

### 4.6 Typo: "Spyral Abyss" Should Be "Spiral Abyss"

- **File:** `core/datatypes.py:155, 179, 180`
- **Issue:** `GamemenuType.SPYRAL` and its string representation say "Spyral Abyss" instead of "Spiral Abyss".
- **Impact:** Incorrect display text in Discord Rich Presence.

### 4.7 "Roster" Misspelled as "Roaster"

- **File:** `genshin_impact_rich_presence_gui.py:349, 635, 718` (and related methods)
- **Issue:** Tab is named "Character Roster" but internal variable names use `roaster_tab`, `_setup_roaster_tab`, `_save_roaster_config`.
- **Impact:** Minor naming inconsistency; confusing for developers.

---

## 5. Architecture & Design Notes

### Strengths

- **Modular core package:** Clean separation of concerns (`state.py`, `detection.py`, `discord_rpc.py`, `ocr_engine.py`, `character_detection.py`, `ps_helper.py`)
- **CSV hot-reload:** `watchdog` observer for automatic data file reloading is well-implemented
- **Adaptive character detection:** Clever system for detecting character positions across UI changes
- **URL asset loading:** Bypasses Discord's 300 asset limit with external image hosting
- **Comprehensive data files:** Well-structured CSV data for characters, locations, domains, bosses

### Weaknesses

- **Dual entry points with different behavior:** `main.py` and the GUI have separate code paths, leading to inconsistent defaults and potential drift
- **Global state management:** Heavy reliance on module-level globals rather than encapsulated state objects
- **GUI subprocess architecture:** The GUI spawns `main.py` as a subprocess and communicates via a JSON file. This is fragile compared to in-process communication or proper IPC
- **No tests:** Zero test files found in the project
- **No type checking:** No `mypy` configuration or type stubs; typing annotations are present but not verified

---

## 6. Security Assessment

| Category | Status |
|----------|--------|
| Hardcoded secrets/API keys | Discord App ID (`944346292568596500`) is public, not a secret |
| Personal data in repo | `shared_config.json` contains username, tracked despite .gitignore |
| External URLs | GitHub raw URLs only; no user-controlled URL input |
| File system access | Limited to project directory and `%APPDATA%` for cache |
| Network access | Discord RPC (localhost), GitHub for image downloads |
| Process spawning | Spawns `main.py` subprocess with controlled arguments |
| Screen capture | Captures game window for OCR (expected functionality) |

**No critical security vulnerabilities found.** The application runs locally and doesn't handle sensitive data beyond the Discord App ID (which is public).

---

## 7. Recommendations (Priority Order)

1. **Untrack `shared_config.json` from git** (`git rm --cached shared_config.json`)
2. **Remove `__pycache__/` from git** (`git rm -r --cached __pycache__/`)
3. **Fix the duplicate `_ensure_image_cache_dir` method** in the GUI
4. **Fix the missing character slot 2** in non-1080p GUI scaling
5. **Remove dead code** at `genshin_impact_rich_presence_gui.py:1481-1491`
6. **Unify CONFIG defaults** between `CONFIG.py` and GUI `Config` class
7. **Remove duplicate dependencies** from `requirements.txt`
8. **Remove `customtkinter`** from `requirements.txt`
9. **Add atomic file writes** for `gui_shared_data.json`
10. **Add basic unit tests** for data parsing and character detection logic
11. **Fix "Spyral" typo** to "Spiral"
12. **Consider refactoring** global state into a state manager class
