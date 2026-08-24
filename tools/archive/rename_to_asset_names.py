#!/usr/bin/env python3
"""
Rename character portraits from display names to asset names (char_* format).
"""
import csv
import os
from pathlib import Path

SOURCE_DIR = Path("D:/GitHub/Repos/Genshin-Impact-Rich-Presence/resources/assets/images/Downloaded-characters")
CSV_FILE = Path("D:/GitHub/Repos/Genshin-Impact-Rich-Presence/data/characters.csv")

def parse_characters(csv_file):
    """Parse CSV and return dict mapping display_name -> asset_name."""
    name_map = {}
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or row[0].startswith('------'):
                continue
            if len(row) >= 3:
                asset_name = row[1]  # e.g., "char_kachina"
                display_name = row[2]  # e.g., "Kachina"
                name_map[display_name] = asset_name
    
    return name_map

def main():
    print("=" * 60)
    print("Renaming Character Portraits to Asset Names")
    print("=" * 60)
    
    if not SOURCE_DIR.exists():
        print(f"Source directory not found: {SOURCE_DIR}")
        return
    
    name_map = parse_characters(CSV_FILE)
    print(f"Loaded {len(name_map)} character mappings\n")
    
    renamed = 0
    skipped = 0
    failed = []
    
    for source_file in SOURCE_DIR.glob("*.png"):
        display_name = source_file.stem
        
        if display_name in name_map:
            asset_name = name_map[display_name]
            target_file = SOURCE_DIR / f"{asset_name}.png"
            
            if target_file.exists():
                print(f"Skipped: {display_name}.png (already renamed)")
                skipped += 1
                continue
            
            try:
                source_file.rename(target_file)
                print(f"Renamed: {display_name}.png -> {asset_name}.png")
                renamed += 1
            except Exception as e:
                print(f"Failed: {display_name}.png -> {asset_name}.png ({e})")
                failed.append(display_name)
        else:
            print(f"Warning: No mapping found for '{display_name}'")
            failed.append(display_name)
    
    print("\n" + "=" * 60)
    print("Rename Summary")
    print("=" * 60)
    print(f"Total files: {len(list(SOURCE_DIR.glob('*.png')))}")
    print(f"Renamed: {renamed}")
    print(f"Skipped: {skipped}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print("\nFailed/Unmatched:")
        for name in failed:
            print(f"  - {name}")

if __name__ == "__main__":
    main()
