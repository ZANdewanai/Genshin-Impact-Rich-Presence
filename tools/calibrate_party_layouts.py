"""Generate sensor_data/party_layouts.json from the debug party screenshots.

For each debug_party_N_slots.jpg (N=1..5) we OCR the party-HUD name column in
one pass (RapidOCR returns per-text bounding boxes) and record the vertical
centre of every detected member. All members across all sizes are then fit to
the model

    y_center(k of N) = CENTER + (k - (N-1)/2) * SPACING

which the debug captures show exactly (party HUD is vertically centred at a
fixed y and expands outward as members are added). The fitted parameters are
used to emit per-party-size name-box and number-plate coordinate tables.

Usage:
    python tools/calibrate_party_layouts.py [image_dir]
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
from PIL import Image

from CONFIG import USE_GPU
from core.ocr_engine import Reader

# Party-HUD geometry (name box x-range, number plate x-range, box heights).
NAME_X = (2165, 2362)
NUM_X = (2480, 2510)
NAME_H = 86
NUM_H = 30

# Vertical extent scanned for names/plates.
Y_MIN, Y_MAX = 280, 1110


def _column_centers(reader, img, x1, x2, y1, y2, allowlist=None, upscale=1):
    """OCR a column; return [(y_center, conf), ...] of every detected text."""
    crop = img.crop((x1, y1, x2, y2))
    if upscale > 1:
        w, h = crop.size
        crop = crop.resize((w * upscale, h * upscale), Image.LANCZOS)
    arr = np.array(crop.convert("L"))
    crop.close()
    results = reader.readtext(arr, allowlist=allowlist)
    out = []
    for item in results:
        try:
            bbox, text, conf = item
        except (TypeError, ValueError):
            continue
        text = str(text).strip()
        if not text:
            continue
        try:
            conf = float(conf)
        except (TypeError, ValueError):
            conf = 0.0
        try:
            ys = [p[1] for p in bbox]
            yc = sum(ys) / len(ys) / upscale + y1
        except Exception:
            yc = y1
        out.append((yc, conf))
    return out


def fit(measurements):
    """Least-squares fit CENTER, SPACING to y = C + (k-(N-1)/2)*S.

    measurements: list of (N, k, y_center). k is 0-indexed top-to-bottom.
    Returns (center, spacing).
    """
    A, b = [], []
    for n, k, yc in measurements:
        A.append([1.0, k - (n - 1) / 2.0])
        b.append(yc)
    A = np.array(A, dtype=float)
    b = np.array(b, dtype=float)
    try:
        sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    except Exception:
        sol = np.array([0.0, 0.0])
    return float(sol[0]), float(sol[1])


def build_layout(center, spacing):
    """Return {n: {names:[...], numbers:[...]}} for n in 1..5."""
    layouts = {}
    for n in range(1, 6):
        names, numbers = [], []
        for k in range(n):
            cy = center + (k - (n - 1) / 2.0) * spacing
            ny1 = int(round(cy - NAME_H / 2))
            names.append([NAME_X[0], ny1, NAME_X[1], ny1 + NAME_H])
            py1 = int(round(cy - NUM_H / 2))
            numbers.append([NUM_X[0], py1, NUM_X[1], py1 + NUM_H])
        layouts[str(n)] = {"names": names, "numbers": numbers}
    return layouts


def main():
    img_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("debug_images")
    if not img_dir.exists():
        print(f"image dir not found: {img_dir}")
        return

    reader = Reader(["en"], gpu=USE_GPU)
    measurements = []
    for n in range(1, 6):
        f = img_dir / f"debug_party_{n}_slots.jpg"
        if not f.exists():
            print(f"[SKIP] missing {f}")
            continue
        img = Image.open(f).convert("RGB")
        centers = _column_centers(reader, img, *NAME_X, Y_MIN, Y_MAX)
        # Keep the n highest-confidence hits = the n members.
        centers.sort(key=lambda c: c[1], reverse=True)
        centers = centers[:n]
        centers.sort(key=lambda c: c[0])  # top-to-bottom
        print(f"party_{n}: " + ", ".join(f"y={round(yc)}" for yc, _ in centers))
        for k, (yc, _conf) in enumerate(centers):
            measurements.append((n, k, yc))

    center, spacing = fit(measurements)
    print(f"\nFit: center={center:.1f}px, spacing={spacing:.1f}px")

    layouts = build_layout(center, spacing)
    out = Path("sensor_data") / "party_layouts.json"
    out.parent.mkdir(exist_ok=True)
    payload = {
        "resolution": {"width": 2560, "height": 1440},
        "center": round(center, 1),
        "spacing": round(spacing, 1),
        "name_h": NAME_H,
        "num_h": NUM_H,
        "layouts": layouts,
    }
    with open(out, "w") as fh:
        json.dump(payload, fh, indent=2)
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
