"""Find the exact triangle position in party 4."""
import sys
sys.path.insert(0, '.')
from pathlib import Path
from PIL import Image
import numpy as np

root = Path('.').resolve()

# Party 4 coords
names = [(2165, 316, 2362, 402), (2165, 440, 2362, 526), (2165, 563, 2362, 649), (2165, 687, 2362, 773)]

p = root / 'debug_images' / 'debug_party_4_slots.jpg'
img = Image.open(p).convert('RGB')

for i, nb in enumerate(names):
    name_crop = img.crop(nb)
    # Crop a wider region to the right of the name
    y1, y2 = nb[1], nb[3]
    # The triangle should be between name end (x=2362) and number plate start (x=2480)
    # But we saw it's actually within the name box's right 40px
    # Let's look at the FULL right 40px area for each slot
    arr = np.array(name_crop.convert("L"))
    right40 = arr[:, 157:]
    
    # For each column in right40, count bright pixels
    bright = right40 > 200
    col_counts = bright.sum(axis=0)
    
    # Find which columns have significant bright pixels (>10)
    significant_cols = [c for c in range(40) if col_counts[c] > 10]
    
    print(f"\nSlot {i+1} ({['Zhongli', 'Columbina', 'Yae Miko', 'Aino'][i]}):")
    print(f"  Significant bright columns (>10px): {significant_cols[:20]}")
    print(f"  Full col_counts: {col_counts.tolist()}")
    
    # Find the leftmost significant column
    if significant_cols:
        print(f"  Leftmost significant col: {significant_cols[0]}")
    
    # Check if there's a solid filled region (high count across multiple consecutive columns)
    # that starts at col 0
    solid_start = col_counts[0] > 15
    print(f"  Solid at col 0 (count={col_counts[0]}): {solid_start}")