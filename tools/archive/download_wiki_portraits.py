#!/usr/bin/env python3
"""
Script to download character portraits from Genshin Impact Wiki.
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
TARGET_DIR = Path("D:/GitHub/Repos/Genshin-Impact-Rich-Presence/resources/assets/images/Downloaded-characters")

# CSV file path
CSV_FILE = Path("D:/GitHub/Repos/Genshin-Impact-Rich-Presence/data/characters.csv")

# User agent to avoid being blocked
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def get_hash_prefix(filename):
    """Generate the hash prefix for a wiki image URL."""
    md5 = hashlib.md5(filename.encode('utf-8')).hexdigest()
    return md5[0], md5[:2]

def get_wiki_icon_url(character_name):
    """
    Generate the correct wiki icon URL using MD5 hash.
    Format: https://static.wikia.nocookie.net/gensin-impact/images/[first_char]/[first_two_chars]/[CharacterName]_Icon.png
    """
    # Replace spaces with underscores for wiki URLs
    wiki_name = character_name.replace(' ', '_')
    filename = f"{wiki_name}_Icon.png"
    
    # Get hash prefixes
    first_char, first_two = get_hash_prefix(filename)
    
    # Construct URL
    url = f"https://static.wikia.nocookie.net/gensin-impact/images/{first_char}/{first_two}/{quote(filename)}"
    
    return url

def get_wiki_card_url(character_name):
    """Generate the wiki card URL as fallback."""
    wiki_name = character_name.replace(' ', '_')
    filename = f"{wiki_name}_Card.png"
    
    first_char, first_two = get_hash_prefix(filename)
    
    return f"https://static.wikia.nocookie.net/gensin-impact/images/{first_char}/{first_two}/{quote(filename)}"

def get_wiki_character_icon_url(character_name):
    """Generate character icon URL (Character_ prefix)."""
    wiki_name = character_name.replace(' ', '_')
    filename = f"Character_{wiki_name}_Icon.png"
    
    first_char, first_two = get_hash_prefix(filename)
    
    return f"https://static.wikia.nocookie.net/gensin-impact/images/{first_char}/{first_two}/{quote(filename)}"

def get_all_urls(character_name):
    """Generate all possible URLs to try."""
    urls = [
        get_wiki_icon_url(character_name),
        get_wiki_character_icon_url(character_name),
        get_wiki_card_url(character_name),
    ]
    
    # For names with spaces, also try without spaces
    if ' ' in character_name:
        no_space_name = character_name.replace(' ', '')
        urls.append(get_wiki_icon_url(no_space_name))
        urls.append(get_wiki_character_icon_url(no_space_name))
    
    # For names with full names (e.g., "Kamisato Ayaka"), also try just the last name
    parts = character_name.split()
    if len(parts) > 1:
        last_name = parts[-1]
        urls.append(get_wiki_icon_url(last_name))
        urls.append(get_wiki_character_icon_url(last_name))
    
    # Special case for Traveler
    if character_name in ['Aether', 'Lumine']:
        urls.insert(0, "https://static.wikia.nocookie.net/gensin-impact/images/5/51/Traveler_Icon.png")
    
    # Special case for Kujo Sara - also known as "Kujou Sara" or just "Sara"
    if character_name == 'Kujo Sara':
        urls.insert(0, "https://static.wikia.nocookie.net/gensin-impact/images/d/df/Kujou_Sara_Icon.png")
    
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
    except Exception as e:
        return False

def parse_characters(csv_file):
    """Parse the characters CSV file and return list of (key, display_name) tuples."""
    characters = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or row[0].startswith('------'):
                continue
            if len(row) >= 3:
                key = row[0]
                display_name = row[2]
                characters.append((key, display_name))
    
    return characters

def main():
    """Main function to download all character portraits."""
    print("=" * 60)
    print("Genshin Impact Character Portrait Downloader")
    print("=" * 60)
    
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nTarget directory: {TARGET_DIR}")
    
    characters = parse_characters(CSV_FILE)
    print(f"Found {len(characters)} characters to download\n")
    
    successful = 0
    # Check which files are missing
    missing_characters = []
    for key, display_name in characters:
        safe_name = re.sub(r'[^\w\-. ]', '_', display_name)
        output_path = TARGET_DIR / f"{safe_name}.png"
        
        if output_path.exists() and output_path.stat().st_size > 100:
            successful += 1
        else:
            missing_characters.append((key, display_name))
    
    if not missing_characters:
        print(f"All {len(characters)} characters already downloaded!")
        print(f"\nImages saved to: {TARGET_DIR}")
        return
    
    print(f"Found {len(missing_characters)} missing characters to download\n")
    
    # Download only missing characters
    failed = []
    for i, (key, display_name) in enumerate(missing_characters, 1):
        safe_name = re.sub(r'[^\w\-. ]', '_', display_name)
        output_path = TARGET_DIR / f"{safe_name}.png"
        
        if output_path.exists() and output_path.stat().st_size > 100:
            print(f"[{i}/{len(missing_characters)}] {display_name}: Already exists")
            successful += 1
            continue
        
        print(f"[{i}/{len(missing_characters)}] {display_name}...", end='', flush=True)
        
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
            failed.append((key, display_name))
            if output_path.exists() and output_path.stat().st_size < 100:
                output_path.unlink()
        
        time.sleep(0.3)
    
    print("\n" + "=" * 60)
    print("Download Summary")
    print("=" * 60)
    print(f"Total: {len(characters)}")
    print(f"Already existed: {successful}")
    print(f"Newly downloaded: {successful - (successful - len(missing_characters) + len(failed))}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print("\nFailed downloads:")
        for key, name in failed:
            print(f"  - {name} ({key})")
    
    print(f"\nImages saved to: {TARGET_DIR}")

if __name__ == "__main__":
    main()
