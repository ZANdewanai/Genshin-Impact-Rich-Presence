import sys; sys.path.insert(0, ".")
import os, time
os.environ["DEBUG_MODE"] = "0"
import numpy as np
from PIL import Image
from core.ocr_engine import Reader
from core.datatypes import Data
from core.sensors import CharSensor
from core.blackboard import read_json
from CONFIG import USE_GPU, MAX_PARTY_SLOTS

reader = Reader(["en"], gpu=USE_GPU)
data = Data()
out = "sensor_data/_test_chars.json"
if os.path.exists(out): os.unlink(out)

def coords():
    from CONFIG import NAMES_6P_COORD, NUMBER_6P_COORD
    return list(NAMES_6P_COORD), list(NUMBER_6P_COORD)

s = CharSensor(reader, data, coords, out, interval=2.0)
s._layouts = s._load_party_layouts()

for n in range(1, 6):
    p = "debug_images/debug_party_%d_slots.jpg" % n
    if not os.path.exists(p): continue
    s._static_img = Image.open(p).convert("RGB")
    s._slot_cache = [None] * MAX_PARTY_SLOTS
    s._hint_window = []
    s._debounce = {"candidate": None, "confirmed": None}
    s._name_ordinal_history = []
    s._last_round_success = False
    s._sweep_cursor = 0
    s.scan()
    res = read_json(out, max_age=60.0)
    slots = res.get("slots") if res else None
    print("party_%d  hint=%s" % (n, res.get("active_slot_hint") if res else None))
    if slots:
        for i, sl in enumerate(slots):
            if i == 0: continue
            if sl: print("  slot%d: %s cached=%s" % (i, sl.get("name"), sl.get("cached")))
            else:  print("  slot%d: <missing>" % i)
