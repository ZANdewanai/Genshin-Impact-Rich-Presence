#!/usr/bin/env python3
"""
Script to download character portraits from Genshin Impact Wiki.
Uses requests to fetch images with proper headers to avoid being blocked.
"""
import csv
import os
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

def get_wiki_portrait_url(character_name):
    """
    Generate the wiki portrait URL for a character.
    The wiki uses specific naming conventions for images.
    """
    # Clean up the character name for URL
    # Replace spaces with underscores and capitalize each word
    wiki_name = character_name.replace(' ', '_')
    
    # Wiki portrait URL format
    # Try the newer format first (icon/portrait)
    url = f"https://static.wikia.nocookie.net/gensin-impact/images/0/0a/Character_{quote(wiki_name)}_Thumb.png"
    
    return url

def get_alternative_urls(character_name):
    """Generate alternative URL patterns to try."""
    wiki_name = character_name.replace(' ', '_')
    base_name = character_name.split()[-1] if ' ' in character_name else character_name
    
    urls = [
        # Various wiki naming patterns
        f"https://static.wikia.nocookie.net/gensin-impact/images/0/0a/Character_{quote(wiki_name)}_Thumb.png",
        f"https://static.wikia.nocookie.net/gensin-impact/images/e/e1/Character_{quote(wiki_name)}_Portrait.png",
        f"https://static.wikia.nocookie.net/gensin-impact/images/0/00/Character_{quote(wiki_name)}_Card.jpg",
        f"https://static.wikia.nocookie.net/gensin-impact/images/0/00/{quote(wiki_name)}_Card.jpg",
        # Try with just the last name (for full names like "Kamisato Ayaka")
        f"https://static.wikia.nocookie.net/gensin-impact/images/0/0a/Character_{quote(base_name)}_Thumb.png",
        f"https://static.wikia.nocookie.net/gensin-impact/images/e/e1/Character_{quote(base_name)}_Portrait.png",
        # Item icon format (for Aloy and others)
        f"https://static.wikia.nocookie.net/gensin-impact/images/0/0a/{quote(wiki_name)}_Thumb.png",
        # Card art
        f"https://static.wikia.nocookie.net/gensin-impact/images/0/0a/{quote(wiki_name)}_Card.png",
    ]
    
    # Special cases
    special_cases = {
        'aether': "https://static.wikia.nocookie.net/gensin-impact/images/8/89/Character_Traveler_Thumb.png",
        'lumine': "https://static.wikia.nocookie.net/gensin-impact/images/8/89/Character_Traveler_Thumb.png",
        'aloy': "https://static.wikia.nocookie.net/gensin-impact/images/e/e5/Character_Aloy_Thumb.png",
        'wonderland manekin': "https://static.wikia.nocookie.net/gensin-impact/images/0/0a/Character_Wonderland_Manekin_Thumb.png",
    }
    
    if character_name.lower() in special_cases:
        urls.insert(0, special_cases[character_name.lower()])
    
    return urls

def download_image(url, output_path):
    """Download an image from URL to the specified path."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)
        if response.status_code == 200:
            # Check if content is an image
            content_type = response.headers.get('Content-Type', '')
            if 'image' in content_type:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                return True
        return False
    except Exception as e:
        print(f"  Error downloading {url}: {e}")
        return False

def parse_characters(csv_file):
    """Parse the characters CSV file and return list of (key, display_name) tuples."""
    characters = []
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            # Skip region headers (rows starting with '------')
            if not row or row[0].startswith('------'):
                continue
            
            # Row format: key, asset_name, display_name
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
    
    # Ensure target directory exists
    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\nTarget directory: {TARGET_DIR}")
    
    # Parse characters from CSV
    characters = parse_characters(CSV_FILE)
    print(f"Found {len(characters)} characters to download\n")
    
    # Track statistics
    successful = 0
    failed = []
    
    # Download each character portrait
    for i, (key, display_name) in enumerate(characters, 1):
        # Sanitize filename
        safe_name = re.sub(r'[^\w\-. ]', '_', display_name)
        output_path = TARGET_DIR / f"{safe_name}.png"
        
        # Skip if already exists
        if output_path.exists():
            print(f"[{i}/{len(characters)}] {display_name}: Already exists")
            successful += 1
            continue
        
        print(f"[{i}/{len(characters)}] Downloading {display_name}...", end='')
        
        # Try multiple URL patterns
        urls = get_alternative_urls(display_name)
        downloaded = False
        
        for url in urls:
            if download_image(url, output_path):
                print(" ✓")
                downloaded = True
                successful += 1
                break
            time.sleep(0.5)  # Small delay between attempts
        
        if not downloaded:
            print(" ✗ Failed")
            failed.append((key, display_name))
        
        # Rate limiting - be nice to the wiki server
        time.sleep(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("Download Summary")
    print("=" * 60)
    print(f"Total: {len(characters)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print("\nFailed downloads:")
        for key, name in failed:
            print(f"  - {name} ({key})")
    
    print(f"\nImages saved to: {TARGET_DIR}")

if __name__ == "__main__":
    main()
