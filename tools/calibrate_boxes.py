"""Calibrate party HUD bounding boxes from debug images.

Uses the canonical debug images (party_1..5_slots.jpg) as ground truth to
discover the actual name/number plate coordinates for each party size.

Key insight: In Genshin party HUD, the characters are centered vertically in the
screen, and the spacing between slots is constant (~123px). The HUD shifts UP
when party size decreases, so different party sizes have different Y positions.
"""
import sys
sys.path.insert(0, '.')
from pathlib import Path
from PIL import Image
import numpy as np
import cv2


def find_text_bands_in_hud_region(img, x_start=2150, x_end=2520, y_range=(200, 900)):
    """Find character name text bands in the party HUD region."""
    arr = np.array(img.convert('RGB'))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

    # Scan horizontal projection in the HUD region
    h_proj = np.sum(gray[y_range[0]:y_range[1], x_start:x_end] > 180, axis=1)

    # Find bands where brightness exceeds threshold
    threshold = 30  # at least 30 bright pixels per row
    bands = []
    in_band = False
    band_start = 0

    for i, v in enumerate(h_proj):
        y = y_range[0] + i
        if v >= threshold:
            if not in_band:
                in_band = True
                band_start = y
        else:
            if in_band:
                in_band = False
                bands.append((band_start, y))

    if in_band:
        bands.append((band_start, y_range[1]))

    return bands


def find_name_box_for_band(img, band_y1, band_y2, x_end=2362):
    """Find the full name box coordinates for a text band."""
    arr = np.array(img.convert('RGB'))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

    # Find left edge of text in this band
    row = gray[band_y1:band_y2, :x_end]
    h_proj = np.sum(row > 180, axis=0)

    # Find first column with significant brightness
    x1 = 0
    for x in range(len(h_proj)):
        if h_proj[x] >= (band_y2 - band_y1) * 0.1:
            x1 = max(0, x - 15)
            break

    # Find last column with significant brightness
    x2 = x_end
    for x in range(len(h_proj) - 1, -1, -1):
        if h_proj[x] >= (band_y2 - band_y1) * 0.1:
            x2 = min(x_end, x + 15)
            break

    return (x1, band_y1, x2, band_y2)


def find_number_plate(img, name_box_y1, name_box_y2, name_box_x2):
    """Find number plate to the right of a name box.

    Number plates are small (~30px) bright circles with a digit.
    """
    arr = np.array(img.convert('RGB'))
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

    # Search region: right of name box, at same y-level
    search_x1 = name_box_x2 + 50
    search_x2 = 2520
    search_y1 = name_box_y1
    search_y2 = name_box_y2

    if search_x1 >= search_x2:
        return None

    roi = gray[search_y1:search_y2, search_x1:search_x2]
    if roi.size == 0:
        return None

    # Threshold and find contours
    _, thresh = cv2.threshold(roi, 180, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    best = None
    best_area = 0
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 100 < area < 3000:  # reasonable plate size
            x, y, w, h = cv2.boundingRect(cnt)
            # Plates should be roughly square/circular
            aspect = w / h if h > 0 else 0
            if 0.3 < aspect < 3.0:
                cx = search_x1 + x + w // 2
                cy = search_y1 + y + h // 2
                # Make it 30x30
                if area > best_area:
                    best_area = area
                    best = (cx - 15, cy - 15, cx + 15, cy + 15)

    return best


def calibrate_party(image_path, expected_count):
    """Calibrate from one debug image."""
    img = Image.open(image_path).convert('RGB')

    print(f"\n{'='*60}")
    print(f"Party {expected_count}: {image_path.name}")
    print(f"Image size: {img.size}")
    print(f"{'='*60}")

    # Find text bands
    bands = find_text_bands_in_hud_region(img)
    print(f"\nFound {len(bands)} text bands:")

    names = []
    plates = []

    for i, (y1, y2) in enumerate(bands[:expected_count]):  # Only take expected count
        print(f"  Band {i+1}: y={y1}-{y2} (height={y2-y1})")

        # Find name box
        name_box = find_name_box_for_band(img, y1, y2)
        names.append(name_box)
        print(f"    Name box: {name_box}")

        # Find number plate
        plate = find_number_plate(img, y1, y2, name_box[2])
        plates.append(plate)
        if plate:
            print(f"    Plate: {plate}")
        else:
            print(f"    Plate: NOT FOUND")

    return names, plates


def main():
    root = Path('.').resolve()
    debug_dir = root / 'debug_images'

    all_names = {}
    all_plates = {}

    for n in range(1, 6):
        img_path = debug_dir / f'debug_party_{n}_slots.jpg'
        if not img_path.exists():
            print(f"Missing: {img_path}")
            continue

        names, plates = calibrate_party(img_path, n)
        all_names[f'{n}P'] = names
        all_plates[f'{n}P'] = plates

    # Print results in CONFIG format
    print(f"\n\n{'='*60}")
    print("CALIBRATED COORDINATES")
    print(f"{'='*60}")

    for n in range(1, 6):
        key = f'{n}P'
        print(f"\n# Party {n} coordinates:")
        print(f"NAMES_{key}_COORD = [")
        for box in all_names.get(key, []):
            if box:
                print(f"    {box},")
        print(f"]")
        print(f"NUMBER_{key}_COORD = [")
        for plate in all_plates.get(key, []):
            if plate:
                print(f"    {plate},")
        print(f"]")


if __name__ == '__main__':
    main()
