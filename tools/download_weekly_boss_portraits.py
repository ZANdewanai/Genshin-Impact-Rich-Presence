#!/usr/bin/env python3
"""
Script to download weekly boss (trounce boss) portraits from Genshin Impact Wiki.
Saves them as trounce_boss_[name].png in the bosses folder.
"""
import csv
import hashlib
import time
import requests
from pathlib import Path
from urllib.parse import quote

# Target directory
TARGET_DIR = Path("D:/GitHub/Repos/Genshin-Impact-Rich-Presence/resources/assets/images/bosses")

# CSV file path
CSV_FILE = Path("D:/GitHub/Repos/Genshin-Impact-Rich-Presence/data/domains.csv")

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

def get_all_urls(boss_name, key=None):
    """Generate all possible URLs to try."""
    urls = [
        get_wiki_icon_url(boss_name),
    ]
    
    # For names with spaces, also try without spaces
    if ' ' in boss_name:
        no_space_name = boss_name.replace(' ', '')
        urls.append(get_wiki_icon_url(no_space_name))
    
    # Special cases for weekly bosses with different wiki names
    special_bosses = {
        'scattered ruins': 'Andrius',
        'storming terror': 'Dvalin',
        'earthshaking dragon': 'Azhdaha',
        'the golden shadow': 'Tartaglia',
        'stone stele records': 'Azhdaha',
        'unresolved chess game': 'Tartaglia',
        'guardian of eternity': 'Magatsu Mitake Narukami no Mikoto',
        'duel to the fiery': 'La Signora',
        'lucent altar of the': 'Everlasting Lord of Arcane Wisdom',
        'too were once flawless': "Guardian of Apep's Oasis",
        'shadow of another world': 'All-Devouring Narwhal',
        'the knave': 'The Knave',
        'confrontation of sin': 'Capitano',
        'lord of eroded primal fire': 'Lord of Eroded Primal Fire',
        'the game before the gate': 'The Game Before the Gate',
        'the doctor': 'The Doctor',
    }
    
    # Alternative names to try for some bosses
    alternative_names = {
        'storming terror': ['Stormterror', 'Stormterror Dvalin'],
        'confrontation of sin': ['The Captain', 'Capitano', 'Il Capitano'],
        'the doctor': ['Dottore', 'Il Dottore'],
    }
    
    if key and key in special_bosses:
        boss_name = special_bosses[key]
        urls.insert(0, get_wiki_icon_url(boss_name))
    
    # Add alternative names
    if key and key in alternative_names:
        for alt_name in alternative_names[key]:
            urls.append(get_wiki_icon_url(alt_name))
    
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

def parse_trounce_bosses(csv_file):
    """Parse the domains CSV file and return list of weekly bosses."""
    bosses = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            # Skip empty rows and section headers
            if not row or row[0].startswith('------'):
                continue
            
            # Check if it's a trounce domain entry
            if len(row) >= 4 and row[2] == 'trounce':
                key = row[0]
                display_name = row[1]
                asset_name = row[3]
                # Extract boss name from display name (before the | if present)
                boss_name = display_name.split(' | ')[0] if ' | ' in display_name else display_name
                bosses.append((key, boss_name, asset_name))
    
    return bosses

def main():
    """Main function to download all weekly boss portraits."""
    print("=" * 60)
    print("Genshin Impact Weekly Boss Portrait Downloader")
    print("=" * 60)
    
    # Ensure target directory exists
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nTarget directory: {TARGET_DIR}")
    
    # Parse weekly bosses from CSV
    bosses = parse_trounce_bosses(CSV_FILE)
    print(f"Found {len(bosses)} weekly bosses to download\n")
    
    # Check which files are missing
    missing_bosses = []
    successful = 0
    
    for key, display_name, asset_name in bosses:
        output_path = TARGET_DIR / f"{asset_name}.png"
        
        if output_path.exists() and output_path.stat().st_size > 100:
            print(f"Already exists: {asset_name}.png")
            successful += 1
        else:
            missing_bosses.append((key, display_name, asset_name))
    
    if not missing_bosses:
        print(f"\nAll {len(bosses)} weekly boss portraits already downloaded!")
        print(f"Images saved to: {TARGET_DIR}")
        return
    
    print(f"\nFound {len(missing_bosses)} missing weekly bosses to download\n")
    
    # Download only missing bosses
    failed = []
    for i, (key, display_name, asset_name) in enumerate(missing_bosses, 1):
        output_path = TARGET_DIR / f"{asset_name}.png"
        
        print(f"[{i}/{len(missing_bosses)}] {display_name}...", end='', flush=True)
        
        urls = get_all_urls(display_name, key)
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
            print(f"  - {name} ({key}) -> {asset}.png")
    
    print(f"\nImages saved to: {TARGET_DIR}")

if __name__ == "__main__":
    main()
