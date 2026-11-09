"""Inspect a static screenshot as if it were a live party-HUD frame.

This lets us reproduce and debug party layouts (trial one-offs, partial
parties, 1/3/6-member squads) from screenshots users submit — no need to
trigger those states in-game. It dumps the party-area crop to debug_cache/
for visual inspection, then runs a single CharSensor.scan in "offline"
mode and prints the detected slots.

Usage:
    python tools/debug_static_image.py [image_path]

When CONFIG.DEBUG_STATIC_IMAGE_PATH is set (or image_path is given), the
CharSensor grabs its regions from that file instead of the live screen.
"""# noqa: E501

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image

from core.datatypes import Data
from core.blackboard import blackboard
from core.keys import SLOTS, ACTIVE_SLOT_HINT, HUD_VISIBLE


def main():
    image_path = ""
    if len(sys.argv) > 1:
        image_path = sys.argv[1]

    # Resolve path relative to project root or CWD.
    root = Path(__file__).resolve().parent.parent
    p = Path(image_path) if image_path else None
    if p is not None and not p.exists():
        p = root / image_path
    if image_path and (p is None or not p.exists()):
        print(f"Cannot find image: {image_path}")
        return

    if p is None:
        import CONFIG
        image_path = CONFIG.DEBUG_STATIC_IMAGE_PATH or ""
        if not image_path:
            print("No image path given and CONFIG.DEBUG_STATIC_IMAGE_PATH is empty.")
            return
        p = Path(image_path)
        if not p.exists():
            p = root / image_path
        if not p.exists():
            print(f"Cannot find image: {image_path}")
            return

    img = Image.open(p).convert("RGB")
    print(f"Image: {p}  ({img.width}x{img.height})")

    # Point CONFIG at the image and enable static-image mode BEFORE the
    # sensor is constructed so _load_static_image() and _party_area pick it up.
    import CONFIG
    CONFIG.DEBUG_STATIC_IMAGE_PATH = str(p)
    CONFIG.DEBUG_STATIC_IMAGE = True

    # Dump the party-area crop for visual inspection.
    from CONFIG import BASE_PARTY_AREA
    dump_dir = root / "debug_cache"
    dump_dir.mkdir(exist_ok=True)
    crop = img.crop(BASE_PARTY_AREA)
    crop_path = dump_dir / "debug_static_party_area.png"
    crop.save(crop_path)
    print(f"party_area={BASE_PARTY_AREA} -> {crop_path}")

    # Actually run the sensor's scan logic offline.
    from core.ocr_engine import Reader
    from core.search_index import SearchIndex
    from core.sensors import CharSensor
    from CONFIG import USE_GPU

    reader = Reader(["en"], gpu=USE_GPU)
    data = Data()
    search_index = SearchIndex(data)

    sensor = CharSensor(reader, data, search_index, "characters", interval=2.0)

    print("\n=== CharSensor.scan() (offline) ===")
    sensor.scan()
    res = blackboard.read("characters", max_age=60.0) or {}
    print("slots:", res.get(SLOTS))
    print("active_slot_hint:", res.get(ACTIVE_SLOT_HINT))
    print("hud_visible:", res.get(HUD_VISIBLE))
    print("special_ui:", res.get("special_ui"))


if __name__ == "__main__":
    main()
