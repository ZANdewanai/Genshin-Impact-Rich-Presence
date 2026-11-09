"""Mocked unit tests for core engine logic.

Run with the embedded interpreter from the repo root:
    python3.12.8_embedded\\python.exe tools\\test_core_units.py

Covers: Blackboard freshness, SearchIndex matching, _PriorityLock ordering,
_ConfigFlag live reads, Data.check_reload hot-reload, CharSensor frame-skip
helper, and the gui_shared_data.json schema.
"""
import json
import os
import sys
import tempfile
import threading
import time
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.chdir(Path(__file__).resolve().parent.parent)

FAILURES = []


def check(name, cond, extra=""):
    if cond:
        print(f"  ok  {name}")
    else:
        FAILURES.append(name)
        print(f" FAIL {name} {extra}")


# ---------------------------------------------------------------- blackboard
from core.blackboard import Blackboard

bb = Blackboard()
bb.write("ch", {"x": 1})
check("blackboard fresh read", bb.read("ch", max_age=5.0)["x"] == 1)
check("blackboard stale read", bb.read("ch", max_age=-1) is None)
check("blackboard missing", bb.read("nope") is None)

# ---------------------------------------------------------------- search index
from core.search_index import SearchIndex


def _obj(**kw):
    return types.SimpleNamespace(**kw)


data = types.SimpleNamespace(
    bosses=[_obj(search_str="anemo hypostasis", boss_name="Anemo Hypostasis", image_key="b1")],
    characters=[
        _obj(search_str="kamisato ayaka", character_display_name="Kamisato Ayaka", image_key="c1"),
        _obj(search_str="ayaka", character_display_name="Ayaka Alt", image_key="c2"),
    ],
    domains=[_obj(search_str="domain of forgery", domain_name="Domain of Forgery", image_key="d1")],
    locations=[_obj(search_str="mondstadt", location_name="Mondstadt", subarea="", country="", image_key="l1")],
    gamemenus=[_obj(search_str="party setup", gamemenu_name="Party Setup", image_key="g1")],
)
si = SearchIndex(data)
check("search longest match wins",
      si.search_character("kamisato ayaka").character_display_name == "Kamisato Ayaka")
check("search substring match", si.search_boss("the anemo hypostasis world boss") is not None)
check("search no match", si.search_location("atoc sharp") is None)
check("search gamemenu", si.search_gamemenu("open party setup menu") is not None)

# refresh_after_reload rebuilds precomputed match lists
data.bosses.append(_obj(search_str="all-seeing wiki", boss_name="All-Seeing Wiki", image_key="b2"))
check("pre-refresh misses new boss", si.search_boss("all-seeing wiki") is None)
si.refresh_after_reload()
check("post-refresh finds new boss",
      si.search_boss("all-seeing wiki").boss_name == "All-Seeing Wiki")
check("char variants precomputed",
      any(c.character_display_name == "Kamisato Ayaka"
          and "kamisatoayaka" in vs for c, vs in si.character_variants()))

# ------------------------------------------------------------- priority lock
from core.state import _PriorityLock


def test_priority_lock2():
    lock = _PriorityLock()
    order = []
    lock.acquire()  # main holds

    def normal():
        with lock:
            order.append("normal")

    tn = threading.Thread(target=normal)
    tn.start()
    time.sleep(0.1)  # normal is now queued

    acquired = []

    def prio():
        lock.acquire(priority=True)
        acquired.append("prio")
        order.append("prio")
        lock.release()

    tp = threading.Thread(target=prio)
    tp.start()
    time.sleep(0.1)  # prio is queued ahead of normal
    lock.release()   # hand off: prio should win
    tp.join(2)
    tn.join(2)
    check("priority lock: prio before normal", order == ["prio", "normal"], str(order))
    check("priority lock: prio acquired", acquired == ["prio"])


test_priority_lock2()

# non-priority still works and timeout path returns False
lock2 = _PriorityLock()
lock2.acquire()
check("priority lock timeout", lock2.acquire(timeout=0.05) is False)
lock2.release()
check("priority lock acquire after release", lock2.acquire() is True)
lock2.release()

# ------------------------------------------------------------- config flags
import core.shared_config as sc
from core.models import DEBUG_MODE, DEBUG_CHARACTER_MODE, DEBUG_SAVE_IMAGES

with tempfile.TemporaryDirectory() as td:
    cfg_path = Path(td) / "shared_config.json"
    old_path = sc.SHARED_CONFIG_PATH
    sc.SHARED_CONFIG_PATH = cfg_path
    try:
        cfg_path.write_text(json.dumps({"DEBUG_MODE": True}), encoding="utf-8")
        os.utime(cfg_path, (time.time() + 5, time.time() + 5))
        check("_ConfigFlag live True", bool(DEBUG_MODE) is True)
        check("_ConfigFlag default False", bool(DEBUG_CHARACTER_MODE) is False)
        cfg_path.write_text(json.dumps({"DEBUG_MODE": False}), encoding="utf-8")
        os.utime(cfg_path, (time.time() + 10, time.time() + 10))
        check("_ConfigFlag live flip", bool(DEBUG_MODE) is False)
    finally:
        sc.SHARED_CONFIG_PATH = old_path
        sc._cache = None

# ------------------------------------------------------------- data reload
from core.data_loader import Data

with tempfile.TemporaryDirectory() as td:
    data_dir = Path(td) / "data"
    data_dir.mkdir()
    (data_dir / "characters.csv").write_text(
        "------,x,y\nfoo,ck,Foo\n", encoding="utf-8")
    (data_dir / "domains.csv").write_text(
        "------,a,b,c\n", encoding="utf-8")
    (data_dir / "locations.csv").write_text(
        "------,a,b,c,d\n", encoding="utf-8")
    (data_dir / "gamemenus.csv").write_text(
        "------,a,b,c\n", encoding="utf-8")
    (data_dir / "bosses.csv").write_text(
        "------,a,b\n", encoding="utf-8")
    old_cwd = os.getcwd()
    os.chdir(td)
    try:
        d = Data()
        check("data loaded", len(d.characters) == 1)
        check("no change -> empty", d.check_reload() == set())
        # touch characters.csv -> csv reload
        time.sleep(0.02)
        (data_dir / "characters.csv").write_text(
            "------,x,y\nfoo,ck,Foo\nbar,bk,Bar\n",
            encoding="utf-8")
        os.utime(data_dir / "characters.csv", (time.time() + 20, time.time() + 20))
        changed = d.check_reload()
        check("csv change detected", "csv" in changed, str(changed))
        check("characters reloaded", len(d.characters) == 2)
    finally:
        os.chdir(old_cwd)

# ------------------------------------------------------- char sensor skip
from core.sensors.base import _looks_same
import numpy as np

a = np.zeros((10, 10), dtype=np.uint8)
b = np.zeros((10, 10), dtype=np.uint8)
check("looks_same identical", bool(_looks_same(a, a.ravel()[::4], b)) is True)
c = np.zeros((10, 10), dtype=np.uint8); c[::2, ::2] = 255
check("looks_same different", bool(_looks_same(a, a.ravel()[::4], c)) is False)
check("looks_same no prev", bool(_looks_same(None, None, b)) is False)
check("looks_same shape mismatch", bool(_looks_same(a, a.ravel()[::4], np.zeros((5, 5), np.uint8))) is False)

# ------------------------------------------------------- gui shared data
import core.state as st

with tempfile.TemporaryDirectory() as td:
    out = Path(td) / "gui_shared_data.json"
    old_fn = st._get_shared_data_path
    st._get_shared_data_path = lambda: str(out)
    try:
        with st.state_lock:
            st.current_characters = [None] * 5
            from core.datatypes import Character
            st.current_characters[0] = Character("s", "img_k", "Alice")
            st.current_characters[3] = Character("s2", "img_k2", "Bob")
            st.current_active_character = 4  # 1-indexed slot 4 -> index 3
            st.current_activity = st.Activity(st.ActivityType.LOCATION, None)
            st.game_start_time = 1234.5
        st.write_gui_shared_data()
        payload = json.loads(out.read_text(encoding="utf-8"))
        check("shared data slot-aligned",
              payload["active_characters"] == ["Alice", "None", "None", "Bob", "None"],
              str(payload["active_characters"]))
        check("shared data active index", payload["active_character_index"] == 3)
        for k in ("discord_details", "discord_state", "discord_large_image",
                  "discord_large_text", "discord_small_image", "discord_small_text"):
            check(f"shared data has {k}", k in payload)
    finally:
        st._get_shared_data_path = old_fn
        with st.state_lock:
            st.current_characters = [None] * 5
            st.current_active_character = 0

print()
if FAILURES:
    print(f"{len(FAILURES)} FAILURES: {FAILURES}")
    sys.exit(1)
print("ALL TESTS PASSED")
