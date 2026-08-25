"""pywebview JS-API bridge for the Genshin Impact Rich Presence web GUI.

Contract (unchanged from the Dear PyGui launcher):
  * main.py (detection + Discord RPC engine) runs as a subprocess and
    atomically writes gui_shared_data.json every ~0.7 seconds.
  * This bridge reads that file for display state and spawns/stops the
    engine subprocess when the user presses CONNECT / DISCONNECT.
"""
import csv
import json
import os
import subprocess
import sys
import threading
from collections import deque

# Frozen (PyInstaller exe): __file__ points inside the bundle, so derive the
# project root from the exe's own folder - everything else (gui/dist,
# CONFIG.py, embedded Python) lives next to it.
if getattr(sys, "frozen", False):
    ROOT = os.path.dirname(os.path.abspath(sys.executable))
else:
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

SHARED_DATA_FILE = os.path.join(ROOT, "gui_shared_data.json")
SHARED_CONFIG_FILE = os.path.join(ROOT, "shared_config.json")
EMBEDDED_PYTHON = os.path.join(ROOT, "python3.12.8_embedded", "python.exe")
MAIN_PY = os.path.join(ROOT, "main.py")
ENGINE_EXE = os.path.join(ROOT, "RichPresenceEngine.exe")

# Ring buffer of recent engine output lines (oldest at index 0).
LOG_BUFFER_MAX = 400
_log_buffer = deque(maxlen=LOG_BUFFER_MAX)
_LOG_LOCK = threading.Lock()


def _drain_stream(stream):
    """Read engine stdout/stderr lines into the shared ring buffer."""
    for line in stream:
        try:
            text = line.decode("utf-8", "replace")
        except AttributeError:  # already str
            text = line
        text = text.rstrip("\n").rstrip("\r")
        if text:
            with _LOG_LOCK:
                _log_buffer.append(text)


class Api:
    def __init__(self):
        self.engine_process = None
        self._lock = threading.Lock()
        self.character_meta = {}
        self._load_character_meta()
        try:
            from CONFIG import ASSET_BASE_URL, USE_URL_ASSETS
            self.use_url_assets = bool(USE_URL_ASSETS)
            self.asset_base_url = ASSET_BASE_URL or ""
        except ImportError:
            self.use_url_assets = False
            self.asset_base_url = ""
        try:
            import CONFIG as _cfg
            self._config_defaults = {
                "USERNAME": _cfg.USERNAME,
                "MC_AETHER": _cfg.MC_AETHER,
                "WANDERER_NAME": _cfg.WANDERER_NAME,
                "MANEKIN_NAME": _cfg.MANEKIN_NAME,
                "MANEKINA_NAME": _cfg.MANEKINA_NAME,
            }
        except ImportError:
            self._config_defaults = {}
        self._ensure_shared_config()

    def _ensure_shared_config(self):
        """Create shared_config.json with defaults if it doesn't exist yet.

        The engine reads its username/character-name settings from this file
        at startup; without it a fresh install would fall back to placeholder
        values and the Traveler slot could never be detected.
        """
        if os.path.exists(SHARED_CONFIG_FILE):
            return
        data = {
            **self._config_defaults,
            "GAME_RESOLUTION": 1080,
            "USE_GPU": True,
            "USE_LARGE_IMAGE": True,
        }
        try:
            temp = SHARED_CONFIG_FILE + ".tmp"
            with open(temp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            os.replace(temp, SHARED_CONFIG_FILE)
            print(f"[OK] Created default config: {SHARED_CONFIG_FILE}")
        except OSError as e:
            print(f"Warning: could not create {SHARED_CONFIG_FILE}: {e}")

    def _load_character_meta(self):
        """Load rarity/element metadata keyed by lowercase character name."""
        self.character_meta = {}
        try:
            path = os.path.join(ROOT, "data", "character_meta.csv")
            if not os.path.exists(path):
                return
            with open(path, "r", encoding="utf-8") as f:
                for row in csv.reader(f, delimiter=","):
                    if not row or row[0].strip().lower() in ("", "------"):
                        continue
                    name = row[0].strip().lower()
                    meta = {}
                    if len(row) > 1 and row[1].strip():
                        try:
                            meta["rarity"] = int(row[1].strip())
                        except ValueError:
                            pass
                    if len(row) > 2 and row[2].strip():
                        meta["element"] = row[2].strip().lower()
                    if meta:
                        self.character_meta[name] = meta
        except (OSError, csv.Error) as e:
            print(f"Warning: could not load character_meta.csv: {e}")

    def _lookup_meta(self, name):
        key = str(name).strip().lower()
        meta = self.character_meta.get(key)
        if meta:
            return meta
        parts = key.split()
        first = parts[0] if parts else key
        return self.character_meta.get(first)

    def _asset_url(self, image_key):
        """Resolve an image_key to a portrait URL (URL-assets mode only).

        Reuses core.discord_rpc.get_asset_url so prefix-to-subfolder mapping
        stays in sync with what Discord itself displays. Returns an empty
        string when unavailable (frontend shows the EMPTY slot).
        """
        if not image_key or not self.use_url_assets or not self.asset_base_url:
            return ""
        try:
            from core.discord_rpc import get_asset_url
            url = get_asset_url(image_key)
            return url if url.startswith("http") else ""
        except Exception:
            return ""

    def _get_engine_command(self):
        """Command used to spawn the OCR engine.

        Preference order:
        1. GenshinEngine.exe sitting next to the GUI (fully-bundled mode,
           no embedded Python needed)
        2. Embedded Python running main.py (classic portable layout)
        3. The current interpreter running main.py (dev fallback)
        """
        if os.path.exists(ENGINE_EXE):
            return [ENGINE_EXE]
        if os.path.exists(EMBEDDED_PYTHON):
            return [EMBEDDED_PYTHON, MAIN_PY]
        return [sys.executable, MAIN_PY]

    def _engine_running(self):
        return self.engine_process is not None and self.engine_process.poll() is None

    def _start_engine(self):
        with self._lock:
            if self._engine_running():
                return True
            cmd = self._get_engine_command()
            # main.py is only needed when spawning via a Python interpreter;
            # RichPresenceEngine.exe carries its own entrypoint.
            if len(cmd) > 1 and not os.path.exists(cmd[1]):
                print(f"ERROR: engine script not found at {cmd[1]}")
                return False
            try:
                use_gpu = True
                try:
                    with open(SHARED_CONFIG_FILE, "r", encoding="utf-8") as f:
                        use_gpu = bool(json.load(f).get("USE_GPU", True))
                except (OSError, ValueError):
                    pass
                env = os.environ.copy()
                env["CUDA_VISIBLE_DEVICES"] = "0" if use_gpu else ""
                # CREATE_NO_WINDOW: when the GUI itself runs windowless
                # (pythonw), the engine subprocess would otherwise allocate a
                # new visible console. Its output is piped to the UI anyway.
                creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                self.engine_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    env=env,
                    cwd=ROOT,
                    creationflags=creationflags,
                )
                # Drain output into the ring buffer so the UI can show it.
                for stream in (self.engine_process.stdout,):
                    threading.Thread(
                        target=_drain_stream, args=(stream,), daemon=True
                    ).start()
                return True
            except OSError as e:
                print(f"ERROR starting engine: {e}")
                self.engine_process = None
                return False

    def _stop_engine(self):
        with self._lock:
            proc = self.engine_process
            self.engine_process = None
        if proc is None:
            return
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except (OSError, subprocess.TimeoutExpired):
            try:
                proc.kill()
            except OSError:
                pass

    def get_state(self):
        """Return live display state; safe to call every poll interval."""
        state = {
            "running": self._engine_running(),
            "location": "Unknown",
            "activity": "None",
            "timestamp": None,
            "party": [None, None, None, None, None, None],
            "active_character_index": -1,
        }
        data = {}
        try:
            if os.path.exists(SHARED_DATA_FILE):
                with open(SHARED_DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
        except (OSError, ValueError):
            data = {}  # atomic rewrite in progress; retry next poll

        names = data.get("active_characters") or []
        keys = data.get("active_character_image_keys") or []
        party = []
        for i in range(6):
            name = names[i] if i < len(names) else None
            if not name or name == "None":
                party.append(None)
                continue
            meta = self._lookup_meta(name) or {}
            image_key = keys[i] if i < len(keys) else ""
            party.append({
                "name": name,
                "element": meta.get("element", "empty"),
                "rarity": meta.get("rarity"),
                "imageUrl": self._asset_url(image_key),
            })
        state["party"] = party
        state["location"] = data.get("location") or "Unknown"
        state["activity"] = data.get("activity") or "None"
        ts = data.get("timestamp")
        state["timestamp"] = ts if isinstance(ts, (int, float)) else None
        idx = data.get("active_character_index", -1)
        state["active_character_index"] = idx if isinstance(idx, int) else -1
        return state

    def toggle_connection(self):
        """Start the engine if stopped, stop it if running. Returns new state."""
        if self._engine_running():
            self._stop_engine()
            return {"running": False}
        return {"running": self._start_engine()}

    # Identity settings keys exposed to the frontend. All of them live in
    # shared_config.json and are hot-swapped by detection.py every cycle.
    IDENTITY_KEYS = (
        ("username", "USERNAME"),
        ("mcAether", "MC_AETHER"),
        ("wandererName", "WANDERER_NAME"),
        ("manekinName", "MANEKIN_NAME"),
        ("manekinaName", "MANEKINA_NAME"),
    )

    def get_settings(self):
        """Return current identity settings for the frontend."""
        shared = self._read_json(SHARED_CONFIG_FILE)
        result = {}
        for js_key, cfg_key in self.IDENTITY_KEYS:
            val = shared.get(cfg_key)
            if val is None or (isinstance(val, str) and not val.strip()):
                # Fall back to the CONFIG.py default when unset/blank
                val = self._config_defaults.get(cfg_key, "")
            result[js_key] = val
        return result

    def save_settings(self, settings):
        """Persist an identity settings patch into shared_config.json.

        detection.py re-reads these every detection cycle, so changes apply
        live while the engine is running (no restart needed). Blank strings
        are ignored so they never wipe out CONFIG.py defaults.
        """
        if not isinstance(settings, dict):
            return {"ok": False}
        shared = self._read_json(SHARED_CONFIG_FILE)
        for js_key, cfg_key in self.IDENTITY_KEYS:
            if js_key not in settings or settings[js_key] is None:
                continue
            val = settings[js_key]
            if isinstance(val, str) and not val.strip():
                continue
            shared[cfg_key] = val
        try:
            with open(SHARED_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(shared, f, indent=4)
        except OSError as e:
            print(f"Warning: could not save shared_config.json: {e}")
        return {"ok": True}

    def _read_json(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def get_logs(self):
        """Return captured engine output lines (newest last)."""
        with _LOG_LOCK:
            return list(_log_buffer)

    # ── Debug logging toggle ─────────────────────────────────────
    # The GUI flips these instead of logging always being on. They mirror
    # CONFIG.DEBUG_MODE / DEBUG_CHARACTER_MODE so the engine honours them.
    def get_debug(self):
        """Return the current debug-flag state (live shared_config, else CONFIG)."""
        shared = self._read_json(SHARED_CONFIG_FILE)
        try:
            import CONFIG as _cfg
            dflt_mode = bool(_cfg.DEBUG_MODE)
            dflt_char = bool(_cfg.DEBUG_CHARACTER_MODE)
        except ImportError:
            dflt_mode = False
            dflt_char = False
        return {
            "debugMode": bool(shared.get("DEBUG_MODE", dflt_mode)),
            "debugCharacterMode": bool(shared.get("DEBUG_CHARACTER_MODE", dflt_char)),
        }

    def set_debug(self, debug_mode, debug_character_mode):
        """Persist debug flags to shared_config.json (live) and CONFIG.py (canonical)."""
        debug_mode = bool(debug_mode)
        debug_character_mode = bool(debug_character_mode)
        shared = self._read_json(SHARED_CONFIG_FILE)
        shared["DEBUG_MODE"] = debug_mode
        shared["DEBUG_CHARACTER_MODE"] = debug_character_mode
        try:
            with open(SHARED_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(shared, f, indent=4)
        except OSError as e:
            print(f"Warning: could not save shared_config.json: {e}")
        # Keep CONFIG.py canonical so a fresh engine start inherits the choice.
        self._write_config_debug(debug_mode, debug_character_mode)
        return {"ok": True}

    def _write_config_debug(self, debug_mode, debug_character_mode):
        """Rewrite the DEBUG_MODE / DEBUG_CHARACTER_MODE lines in CONFIG.py in place."""
        try:
            import re
            cfg_path = os.path.join(ROOT, "CONFIG.py")
            with open(cfg_path, "r", encoding="utf-8") as f:
                text = f.read()
            text = re.sub(
                r"^DEBUG_MODE\s*=.*$",
                f"DEBUG_MODE = {str(debug_mode)}",
                text, count=1, flags=re.M,
            )
            text = re.sub(
                r"^DEBUG_CHARACTER_MODE\s*=.*$",
                f"DEBUG_CHARACTER_MODE = {str(debug_character_mode)}",
                text, count=1, flags=re.M,
            )
            with open(cfg_path, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception as e:
            print(f"Warning: could not update CONFIG.py debug flags: {e}")

    def shutdown(self):
        """Kill the engine subprocess when the window closes."""
        self._stop_engine()
