"""Inspect a static screenshot as if it were a live party-HUD frame.

This lets us reproduce and debug party layouts (trial one-offs, partial
parties, 1/3/6-member squads) from screenshots users submit — no need to
trigger those states in-game. It dumps each name region and its upscaled +
inverted number plate to PNGs (for visual inspection of the digit), then runs
a single CharSensor.scan in "offline" mode and prints the detected slots.

Usage:
    python tools/debug_static_image.py [image_path]

When CONFIG.DEBUG_STATIC_IMAGE_PATH is set (or image_path is given), the
CharSensor grabs its regions from that file instead of the live screen.
"""# noqa: E501

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from PIL import Image

from core.datatypes import Data


def main():
    image_path = ""
    if len(sys.argv) > 1:
        image_path = sys.argv[1]

    # If a path was passed, point CONFIG at it so CharSensor loads it.
    if image_path:
        import CONFIG
        CONFIG.DEBUG_STATIC_IMAGE_PATH = image_path

    # Load the image up-front to confirm it's real/readable.
    if not image_path:
        import CONFIG
        image_path = CONFIG.DEBUG_STATIC_IMAGE_PATH or ""
    if not image_path:
        print("No image path given and CONFIG.DEBUG_STATIC_IMAGE_PATH is empty.")
        return

    # Resolve path relative to project root or CWD.
    root = Path(__file__).resolve().parent.parent
    p = Path(image_path)
    if not p.exists():
        p = root / image_path
    if not p.exists():
        print(f"Cannot find image: {image_path}")
        return
    img = Image.open(p).convert("RGB")
    print(f"Image: {p}  ({img.width}x{img.height})")

    # Coordinates: CharSensor in static mode crops names/numbers from the image.
    from CONFIG import NAMES_6P_COORD, NUMBER_6P_COORD

    dump_dir = root / "debug_plates"
    dump_dir.mkdir(exist_ok=True)

    # Dump each name region + binarized plate for visual inspection.
    # The plate pipeline mirrors _read_number_digit: upscale 3x, Gaussian blur,
    # Otsu-binarize (auto polarity) so the digit is a clean white glyph on black.
    import cv2
    print("\n=== name regions & plates ===")
    for i in range(6):
        nb = NAMES_6P_COORD[i]
        ns = img.crop(nb)
        ns.save(dump_dir / f"slot{i}_name.png")
        pb = NUMBER_6P_COORD[i]
        ps = img.crop(pb)
        gray = ps.convert("L")
        up = gray.resize((max(1, gray.width * 3), max(1, gray.height * 3)))
        blur = cv2.GaussianBlur(np.array(up), (5, 5), 0)
        _, binarr = cv2.threshold(
            blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )
        Image.fromarray(binarr, "L").save(dump_dir / f"slot{i}_plate_bin.png")
        print(
            f"slot{i}: name_box={nb} plate_box={pb} "
            f"plate_dim={ps.width}x{ps.height}"
        )

    # Actually run the sensor's scan logic offline.
    from CONFIG import DEBUG_STATIC_IMAGE_PATH, USE_GPU
    import os
    if not DEBUG_STATIC_IMAGE_PATH:
        # Fallback: point it at the path we resolved.
        import CONFIG
        CONFIG.DEBUG_STATIC_IMAGE_PATH = str(p)

    from core.ocr_engine import Reader
    from core.sensors import CharSensor
    reader = Reader(["en"], gpu=USE_GPU)

    def char_coords():
        from CONFIG import NAMES_6P_COORD, NUMBER_6P_COORD
        return NAMES_6P_COORD, NUMBER_6P_COORD

    data = Data()
    out = root / "sensor_data" / "characters.json"
    sensor = CharSensor(reader, data, char_coords, str(out), interval=2.0)

    # Force the static image even if CONFIG point is relative.
    sensor._static_img = img.convert("RGB")

    print("\n=== CharSensor.scan() (offline) ===")
    sensor.scan()
    from core.blackboard import read_json
    res = read_json(str(out), max_age=60.0)
    print("slots:", res.get("slots"))
    print("active_slot_hint:", res.get("active_slot_hint"))
    print("\nPlates dumped to:", dump_dir)


if __name__ == "__main__":
    main()