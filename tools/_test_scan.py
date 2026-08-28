"""Offline end-to-end test: run CharSensor.scan() on each debug party image
using the new layout-based detection, and print the detected slots.

Usage: python tools/_test_scan.py
"""
import sys
sys.path.insert(0, '.')
from pathlib import Path
from PIL import Image
from core.ocr_engine import Reader
from core.datatypes import Data
from core.sensors import CharSensor
from core.blackboard import read_json

root = Path('.').resolve()

for n in range(1, 6):
    p = root / 'debug_images' / f'debug_party_{n}_slots.jpg'
    if not p.exists():
        continue
    r = Reader(['en'], gpu=True)
    d = Data()
    out = root / 'sensor_data' / '_test_chars.json'
    if out.exists():
        out.unlink()

    s = CharSensor(r, d, str(out), interval=2.0, party_size=n)
    s._static_img = Image.open(p).convert('RGB')
    s._slot_cache = [None] * n  # n slots for n-party
    print(f'--- party_{n} ---')
    s.scan()  # First pass: detect names + triangle
    s.scan()  # Second pass: debounce confirms active slot
    res = read_json(str(out), max_age=60.0)
    slots = res.get('slots') if res else None
    print(f'  active_slot_hint: {res.get("active_slot_hint") if res else None}')
    if slots:
        for i, sl in enumerate(slots):
            if sl and i > 0:  # Skip index 0 (invalid slot)
                print(f'    slot{i}: {sl.get("name")}')