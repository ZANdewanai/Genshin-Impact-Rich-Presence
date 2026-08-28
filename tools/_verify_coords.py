"""Generate final canonical coordinates for each party size from detected positions."""
import sys
sys.path.insert(0, '.')
from pathlib import Path
from PIL import Image
import numpy as np
import cv2

# Detected y-positions from OCR scan:
# Party 1: ZAndewanai y=515-615 (center ~565)
# Party 2: Zhongli y=395-495, ZAndewanai y=595-635
# Party 3: Zhongli y=375-445, ZAndewanai y=495-565, Columbina y=585-685
# Party 4: Zhongli y=305-375, ZAndewanai y=465-565, Columbina y=575-615, Varesa y=725-795
# Party 5: Zhongli y=275-315, ZAndewanai y=385-425, Columbina y=515-555, Varesa y=665-735, Sucrose y=755-795

def find_x_range(img, y1, y2, target_text):
    """Find the precise x range for a name in the given y band."""
    gray = np.array(img.convert('L'))
    band = gray[y1:y2, 1700:2450]
    if band.size == 0:
        return None
    
    _, thresh = cv2.threshold(band, 180, 255, cv2.THRESH_BINARY)
    x_proj = np.sum(thresh > 0, axis=0)
    min_brightness = (y2 - y1) * 0.08
    cols = np.where(x_proj > min_brightness)[0]
    if len(cols) > 0:
        return (1700 + cols[0] - 15, 1700 + cols[-1] + 15)
    return None

def find_plate_x(img, y1, y2, names_x2):
    """Find the number plate position for a given character."""
    gray = np.array(img.convert('L'))
    search_y1 = y1 - 10
    search_y2 = y2 + 10
    
    plate_roi = gray[search_y1:search_y2, 2400:2560]
    if plate_roi.size == 0:
        return None
    
    _, thresh = cv2.threshold(plate_roi, 160, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 50 < area < 3000:
            x, y, w, h = cv2.boundingRect(cnt)
            cx = 2400 + x + w // 2
            cy = search_y1 + y + h // 2
            return (cx - 15, cy - 15, cx + 15, cy + 15)
    return None


# Canonical coordinates for each party size
# Name boxes: x roughly 1800-2400, y from detected positions
# Number plates: x roughly 2400-2520

coords = {
    1: {
        'names': [(2115, 515, 2380, 600)],
        'plates': [(2450, 545, 2480, 575)],
    },
    2: {
        'names': [(2115, 395, 2380, 480), (2115, 595, 2380, 635)],
        'plates': [(2450, 425, 2480, 455), (2450, 600, 2480, 630)],
    },
    3: {
        'names': [(2115, 375, 2380, 445), (2115, 495, 2380, 565), (2115, 585, 2380, 685)],
        'plates': [(2450, 400, 2480, 420), (2450, 520, 2480, 550), (2450, 630, 2480, 660)],
    },
    4: {
        'names': [(2115, 305, 2380, 375), (2115, 465, 2380, 565), (2115, 575, 2380, 615), (2115, 725, 2380, 795)],
        'plates': [(2450, 335, 2480, 355), (2450, 500, 2480, 530), (2450, 610, 2480, 640), (2450, 755, 2480, 785)],
    },
    5: {
        'names': [(2115, 275, 2380, 315), (2115, 385, 2380, 425), (2115, 515, 2380, 555), (2115, 665, 2380, 735), (2115, 755, 2380, 795)],
        'plates': [(2450, 290, 2480, 300), (2450, 400, 2480, 420), (2450, 530, 2480, 550), (2450, 690, 2480, 710), (2450, 770, 2480, 780)],
    },
}

# Verify coordinates
root = Path('.').resolve()
debug_dir = root / 'debug_images'

print("Verifying coordinates against debug images...")

for n in range(1, 6):
    img_path = debug_dir / f'debug_party_{n}_slots.jpg'
    if not img_path.exists():
        continue
    
    img = Image.open(img_path).convert('RGB')
    gray = np.array(img.convert('L'))
    
    print(f"\n=== Party {n} ===")
    for i, (name_box, plate_box) in enumerate(zip(coords[n]['names'], coords[n]['plates'])):
        x1, y1, x2, y2 = name_box
        name_crop = gray[y1:y2, x1:x2]
        bright = (name_crop > 180).sum()
        total = name_crop.size
        ratio = bright / total if total > 0 else 0
        
        if plate_box:
            px1, py1, px2, py2 = plate_box
            plate_crop = gray[py1:py2, px1:px2]
            plate_bright = (plate_crop > 160).sum()
            plate_ratio = plate_bright / plate_crop.size if plate_crop.size > 0 else 0
        else:
            plate_ratio = -1
        
        print(f"  Slot {i+1}: name bright_ratio={ratio:.3f} plate_bright_ratio={plate_ratio:.3f}")

# Output in CONFIG format
print("\n\n# CANONICAL PARTY HUD COORDINATES - Calibrated from debug images\n")
for n in range(1, 6):
    print(f"BASE_NAMES_{n}P_COORD = [")
    for box in coords[n]['names']:
        print(f"    {box},")
    print(f"]\n")
    print(f"BASE_NUMBER_{n}P_COORD = [")
    for box in coords[n]['plates']:
        print(f"    {box},")
    print(f"]\n")