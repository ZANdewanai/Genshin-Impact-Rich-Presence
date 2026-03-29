#!/usr/bin/env python3
"""
Script to download boss portraits from Genshin Impact Wiki.
Uses MD5 hash prefixes to construct correct image URLs.
"""
import csv
import hashlib
import re
import time
import requests
from pathlib import Path
from urllib.parse import quote

# Target directory
TARGET_DIR = Path("D:/GitHub/Repos/Genshin-Impact-Rich-Presence/resources/assets/images/bosses")

# CSV file path
CSV_FILE = Path("D:/GitHub/Repos/Genshin-Impact-Rich-Presence/data/bosses.csv")

# User agent to avoid being blocked
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def get_hash_prefix(filename):
    """Generate the hash prefix for a wiki image URL."""
    md5 = hashlib.md5(filename.encode('utf-8')).hexdigest()
    return md5[0], md5[:2]

def get_wiki_icon_url(boss_name):
    """
    Generate the correct wiki icon URL using MD5 hash.
    Format: https://static.wikia.nocookie.net/gensin-impact/images/[first_char]/[first_two_chars]/[BossName]_Icon.png
    """
    wiki_name = boss_name.replace(' ', '_')
    filename = f"{wiki_name}_Icon.png"
    
    first_char, first_two = get_hash_prefix(filename)
    
    url = f"https://static.wikia.nocookie.net/gensin-impact/images/{first_char}/{first_two}/{quote(filename)}"
    
    return url

def get_all_urls(boss_name):
    """Generate all possible URLs to try."""
    urls = [
        get_wiki_icon_url(boss_name),
    ]
    
    # For names with spaces, also try without spaces
    if ' ' in boss_name:
        no_space_name = boss_name.replace(' ', '')
        urls.append(get_wiki_icon_url(no_space_name))
    
    # For long names, try shorter versions
    parts = boss_name.split()
    if len(parts) > 2:
        # Try with just first and last words
        short_name = f"{parts[0]} {parts[-1]}"
        urls.append(get_wiki_icon_url(short_name))
    
    # Special cases for bosses with different wiki naming
    special_cases = {
        'Rhodeia of Loch': [
            "https://static.wikia.nocookie.net/gensin-impact/images/6/6a/Oceanid_Icon.png",
        ],
        'Boss Prototype Cal. Breguete': [
            "https://static.wikia.nocookie.net/gensin-impact/images/a/a9/Prototype_Cal._Breguet_Icon.png",
        ],
        'Experimental Field Generator': [
            "https://static.wikia.nocookie.net/gensin-impact/images/8/8d/Experimental_Field_Generator_Icon.png",
            "https://static.wikia.nocookie.net/gensin-impact/images/8/8d/Experimental_Field_Generator_Icon.webp",
        ],
        'Legatus Golem': [
            "https://static.wikia.nocookie.net/gensin-impact/images/7/7e/Legatus_Golem_Icon.png",
            "https://static.wikia.nocookie.net/gensin-impact/images/7/7e/Legatus_Golem_Icon.webp",
        ],
        'Boss Emperor of Fire and Iron': [
            "https://static.wikia.nocookie.net/gensin-impact/images/f/f5/Emperor_of_Fire_and_Iron_Icon.png",
        ],
        'Goldflame Qucusaur Tyrant': [
            "https://static.wikia.nocookie.net/gensin-impact/images/5/5a/Goldflame_Qucusaur_Tyrant_Icon.png",
            "https://static.wikia.nocookie.net/gensin-impact/images/5/5a/Goldflame_Qucusaur_Tyrant_Icon.webp",
            "https://static.wikia.nocookie.net/gensin-impact/images/5/5a/Kongamato_Icon.png",
        ],
        'Gluttonous Yumkasaur Mountain King': [
            "https://static.wikia.nocookie.net/gensin-impact/images/9/95/Gluttonous_Yumkasaur_Mountain_King_Icon.png",
            "https://static.wikia.nocookie.net/gensin-impact/images/9/95/Gluttonous_Yumkasaur_Mountain_King_Icon.webp",
        ],
        'Secret Source Automaton - Configuration Device': [
            "https://static.wikia.nocookie.net/gensin-impact/images/f/f7/Secret_Source_Automaton_Configuration_Device_Icon.png",
        ],
        'Secret Source Automaton: Overseer Device': [
            "https://static.wikia.nocookie.net/gensin-impact/images/d/d9/Secret_Source_Automaton_Overseer_Device_Icon.png",
        ],
        'Super-Heavy Landrover: Mechanized Fortress': [
            "https://static.wikia.nocookie.net/gensin-impact/images/2/23/Super-Heavy_Landrover_Mechanized_Fortress_Icon.png",
        ],
        'Lord of the Hidden Depths: Whisperer of Nightmares': [
            "https://static.wikia.nocookie.net/gensin-impact/images/5/5a/Lord_of_the_Hidden_Depths_Whisperer_of_Nightmares_Icon.png",
        ],
    }
    
    if boss_name in special_cases:
        for url in reversed(special_cases[boss_name]):
            urls.insert(0, url)
    
    return urls

def download_image(url, output_path):
    """Download an image from URL to the specified path."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '')
            if 'image' in content_type and len(response.content) > 100:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return True
        return False
    except Exception:
        return False

def parse_bosses(csv_file):
    """Parse the bosses CSV file and return list of (key, display_name, asset_name) tuples."""
    bosses = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            # Skip region headers (rows starting with '------')
            if not row or row[0].startswith('------'):
                continue
            
            # Row format: key, display_name, asset_name
            if len(row) >= 3:
                key = row[0]
                display_name = row[1]
                asset_name = row[2]
                bosses.append((key, display_name, asset_name))
    
    return bosses

def main():
    """Main function to download all boss portraits."""
    print("=" * 60)
    print("Genshin Impact Boss Portrait Downloader")
    print("=" * 60)
    
    # Ensure target directory exists
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nTarget directory: {TARGET_DIR}")
    
    # Parse bosses from CSV
    bosses = parse_bosses(CSV_FILE)
    print(f"Found {len(bosses)} bosses to download\n")
    
    # Check which files are missing
    missing_bosses = []
    successful = 0
    
    for key, display_name, asset_name in bosses:
        output_path = TARGET_DIR / f"{asset_name}.png"
        
        if output_path.exists() and output_path.stat().st_size > 100:
            successful += 1
        else:
            missing_bosses.append((key, display_name, asset_name))
    
    if not missing_bosses:
        print(f"All {len(bosses)} bosses already downloaded!")
        print(f"\nImages saved to: {TARGET_DIR}")
        return
    
    print(f"Found {len(missing_bosses)} missing bosses to download\n")
    
    # Download only missing bosses
    failed = []
    for i, (key, display_name, asset_name) in enumerate(missing_bosses, 1):
        output_path = TARGET_DIR / f"{asset_name}.png"
        
        print(f"[{i}/{len(missing_bosses)}] {display_name}...", end='', flush=True)
        
        urls = get_all_urls(display_name)
        downloaded = False
        
        for j, url in enumerate(urls):
            if download_image(url, output_path):
                print(" ✓")
                downloaded = True
                successful += 1
                break
            if j < len(urls) - 1:
                time.sleep(0.2)
        
        if not downloaded:
            print(" ✗ Failed")
            failed.append((key, display_name, asset_name))
            if output_path.exists() and output_path.stat().st_size < 100:
                output_path.unlink()
        
        time.sleep(0.3)
    
    # Summary
    print("\n" + "=" * 60)
    print("Download Summary")
    print("=" * 60)
    print(f"Total: {len(bosses)}")
    print(f"Already existed: {successful - len(missing_bosses) + len([f for f in failed if f not in missing_bosses])}")
    print(f"Newly downloaded: {len(missing_bosses) - len(failed)}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print("\nFailed downloads:")
        for key, name, asset in failed:
            print(f"  - {name} ({key})")
    
    print(f"\nImages saved to: {TARGET_DIR}")

if __name__ == "__main__":
    main()
