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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

SHARED_DATA_FILE = os.path.join(ROOT, "gui_shared_data.json")
SHARED_CONFIG_FILE = os.path.join(ROOT, "shared_config.json")
EMBEDDED_PYTHON = os.path.join(ROOT, "python3.13.11_embedded", "python.exe")
MAIN_PY = os.path.join(ROOT, "main.py")

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

    def _get_python_exe(self):
        return EMBEDDED_PYTHON if os.path.exists(EMBEDDED_PYTHON) else sys.executable

    def _engine_running(self):
        return self.engine_process is not None and self.engine_process.poll() is None

    def _start_engine(self):
        with self._lock:
            if self._engine_running():
                return True
            if not os.path.exists(MAIN_PY):
                print(f"ERROR: main.py not found at {MAIN_PY}")
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
                self.engine_process = subprocess.Popen(
                    [self._get_python_exe(), MAIN_PY],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    env=env,
                    cwd=ROOT,
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

    def shutdown(self):
        """Kill the engine subprocess when the window closes."""
        self._stop_engine()
