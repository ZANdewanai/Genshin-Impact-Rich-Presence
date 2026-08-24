"""Standalone sensor test: runs all sensors for N seconds and dumps JSONs.

Usage:
    python tools/test_sensors.py [duration_seconds]

Requires Genshin in the foreground for meaningful reads.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.datatypes import Data, set_config_values

# Enable debug logging so sensor errors are visible during the test
set_config_values(debug_mode=True)

from core.sensors import CharSensor, LocationSensor, MenuSensor
from core.blackboard import read_json
from core.log_utils import log

OUT = Path(__file__).resolve().parent.parent / "sensor_data"
OUT.mkdir(exist_ok=True)


def main():
    duration = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    data = Data()

    # Minimal reader stub: reuse project OCR engine
    from core.ocr_engine import Reader
    from CONFIG import USE_GPU
    log("Initializing OCR...")
    reader = Reader(["en"], gpu=USE_GPU)

    def char_coords():
        from CONFIG import NAMES_6P_COORD, NUMBER_6P_COORD
        return NAMES_6P_COORD, NUMBER_6P_COORD

    def loc_coords():
        from CONFIG import LOCATION_COORD, BOSS_COORD, MAP_LOC_COORD
        return LOCATION_COORD, BOSS_COORD, MAP_LOC_COORD

    def menu_coords():
        from CONFIG import PARTY_SETUP_COORD, DOMAIN_COORD
        return {"gamemenu": PARTY_SETUP_COORD, "domain": DOMAIN_COORD}

    sensors = [
        CharSensor(reader, data, char_coords, str(OUT / "characters.json"), interval=2.0),
        LocationSensor(reader, data, loc_coords, str(OUT / "location.json"), interval=1.0),
        MenuSensor(reader, data, menu_coords, str(OUT / "menus.json"), interval=1.5),
    ]
    for s in sensors:
        s.start()

    log(f"Running sensors for {duration}s - play/move around in Genshin...")
    start = time.time()
    try:
        while time.time() - start < duration:
            time.sleep(2)
            for name, path in [
                ("chars", OUT / "characters.json"),
                ("loc", OUT / "location.json"),
                ("menus", OUT / "menus.json"),
            ]:
                d = read_json(str(path), max_age=10)
                if d is not None:
                    d.pop("written_at", None)
                    log(f"{name}: {d}")
                else:
                    log(f"{name}: <stale/none>")
    finally:
        for s in sensors:
            s.stop()
        for s in sensors:
            s.join(timeout=3)
        log("Sensors stopped.")


if __name__ == "__main__":
    main()
