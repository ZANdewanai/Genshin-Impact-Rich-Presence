#!/usr/bin/env python3
"""
Script to download character portraits from Genshin Impact Wiki.
Uses requests to fetch images from the wiki gallery pages.
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

def get_wiki_image_url(character_name):
    """
    Generate the wiki image URL for a character icon.
    Format: https://static.wikia.nocookie.net/gensin-impact/images/[path]/[Character]_Icon.png
    """
    # Replace spaces with underscores for wiki URLs
    wiki_name = character_name.replace(' ', '_')
    
    # Direct image URL format based on the wiki structure
    # The wiki stores images at static.wikia.nocookie.net
    url = f"https://static.wikia.nocookie.net/gensin-impact/images/0/00/{quote(wiki_name)}_Icon.png"
    
    return url

def get_alternative_urls(character_name):
    """Generate alternative URL patterns to try for character icons."""
    wiki_name = character_name.replace(' ', '_')
    
    # Get the last name for characters with full names (e.g., "Kamisato Ayaka" -> "Ayaka")
    parts = character_name.split()
    
    urls = [
        # Standard icon format
        f"https://static.wikia.nocookie.net/gensin-impact/images/0/00/{quote(wiki_name)}_Icon.png",
        f"https://static.wikia.nocookie.net/gensin-impact/images/e/e0/{quote(wiki_name)}_Icon.png",
        f"https://static.wikia.nocookie.net/gensin-impact/images/5/58/{quote(wiki_name)}_Icon.png",
        f"https://static.wikia.nocookie.net/gensin-impact/images/8/80/{quote(wiki_name)}_Icon.png",
        f"https://static.wikia.nocookie.net/gensin-impact/images/1/11/{quote(wiki_name)}_Icon.png",
        # Try just the first name (for names like "Hu Tao", "Yun Jin")
        f"https://static.wikia.nocookie.net/gensin-impact/images/0/00/{quote(parts[0])}_Icon.png",
        # Try card images as fallback
        f"https://static.wikia.nocookie.net/gensin-impact/images/0/00/{quote(wiki_name)}_Card.png",
        f"https://static.wikia.nocookie.net/gensin-impact/images/e/ee/{quote(wiki_name)}_Card.png",
    ]
    
    # Special cases for characters with different naming conventions
    special_cases = {
        'Aether': [
            "https://static.wikia.nocookie.net/gensin-impact/images/5/51/Traveler_Icon.png",
            "https://static.wikia.nocookie.net/gensin-impact/images/5/51/Aether_Icon.png",
        ],
        'Lumine': [
            "https://static.wikia.nocookie.net/gensin-impact/images/5/51/Traveler_Icon.png",
            "https://static.wikia.nocookie.net/gensin-impact/images/5/51/Lumine_Icon.png",
        ],
        'Aloy': [
            "https://static.wikia.nocookie.net/gensin-impact/images/e/e5/Aloy_Icon.png",
        ],
        'Hu Tao': [
            "https://static.wikia.nocookie.net/gensin-impact/images/a/a4/Hu_Tao_Icon.png",
            "https://static.wikia.nocookie.net/gensin-impact/images/a/a4/HuTao_Icon.png",
        ],
        'Yun Jin': [
            "https://static.wikia.nocookie.net/gensin-impact/images/9/93/Yun_Jin_Icon.png",
            "https://static.wikia.nocookie.net/gensin-impact/images/9/93/YunJin_Icon.png",
        ],
        'Yumemizuki Mizuki': [
            "https://static.wikia.nocookie.net/gensin-impact/images/0/00/Yumemizuki_Mizuki_Icon.png",
            "https://static.wikia.nocookie.net/gensin-impact/images/0/00/Mizuki_Icon.png",
        ],
        'Kamisato Ayaka': [
            "https://static.wikia.nocookie.net/gensin-impact/images/f/fd/Kamisato_Ayaka_Icon.png",
            "https://static.wikia.nocookie.net/gensin-impact/images/f/fd/Ayaka_Icon.png",
        ],
        'Kamisato Ayato': [
            "https://static.wikia.nocookie.net/gensin-impact/images/e/e8/Kamisato_Ayato_Icon.png",
            "https://static.wikia.nocookie.net/gensin-impact/images/e/e8/Ayato_Icon.png",
        ],
        'Shikanoin Heizou': [
            "https://static.wikia.nocookie.net/gensin-impact/images/0/00/Shikanoin_Heizou_Icon.png",
            "https://static.wikia.nocookie.net/gensin-impact/images/0/00/Heizou_Icon.png",
        ],
        'Kuki Shinobu': [
            "https://static.wikia.nocookie.net/gensin-impact/images/0/00/Kuki_Shinobu_Icon.png",
            "https://static.wikia.nocookie.net/gensin-impact/images/0/00/Shinobu_Icon.png",
        ],
        'Kaedehara Kazuha': [
            "https://static.wikia.nocookie.net/gensin-impact/images/0/00/Kaedehara_Kazuha_Icon.png",
            "https://static.wikia.nocookie.net/gensin-impact/images/0/00/Kazuha_Icon.png",
        ],
        'Raiden Shogun': [
            "https://static.wikia.nocookie.net/gensin-impact/images/0/00/Raiden_Shogun_Icon.png",
            "https://static.wikia.nocookie.net/gensin-impact/images/0/00/Raiden_Icon.png",
        ],
        'Kujo Sara': [
            "https://static.wikia.nocookie.net/gensin-impact/images/0/00/Kujo_Sara_Icon.png",
            "https://static.wikia.nocookie.net/gensin-impact/images/0/00/Sara_Icon.png",
        ],
        'Arataki Itto': [
            "https://static.wikia.nocookie.net/gensin-impact/images/0/00/Arataki_Itto_Icon.png",
            "https://static.wikia.nocookie.net/gensin-impact/images/0/00/Itto_Icon.png",
        ],
        'Yae Miko': [
            "https://static.wikia.nocookie.net/gensin-impact/images/0/00/Yae_Miko_Icon.png",
            "https://static.wikia.nocookie.net/gensin-impact/images/0/00/Miko_Icon.png",
        ],
        'Sangonomiya Kokomi': [
            "https://static.wikia.nocookie.net/gensin-impact/images/0/00/Sangonomiya_Kokomi_Icon.png",
            "https://static.wikia.nocookie.net/gensin-impact/images/0/00/Kokomi_Icon.png",
        ],
        'Wonderland Manekin': [
            "https://static.wikia.nocookie.net/gensin-impact/images/0/00/Wonderland_Manekin_Icon.png",
        ],
        'Lan Yan': [
            "https://static.wikia.nocookie.net/gensin-impact/images/0/00/Lan_Yan_Icon.png",
            "https://static.wikia.nocookie.net/gensin-impact/images/0/00/LanYan_Icon.png",
        ],
    }
    
    if character_name in special_cases:
        # Insert special case URLs at the beginning
        for url in reversed(special_cases[character_name]):
            urls.insert(0, url)
    
    return urls

def download_image(url, output_path):
    """Download an image from URL to the specified path."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15, allow_redirects=True)
        if response.status_code == 200:
            # Check if content is an image
            content_type = response.headers.get('Content-Type', '')
            if 'image' in content_type:
                # Check content length - must be more than 100 bytes (avoid error pages)
                if len(response.content) > 100:
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
        
        # Skip if already exists and has content
        if output_path.exists() and output_path.stat().st_size > 100:
            print(f"[{i}/{len(characters)}] {display_name}: Already exists")
            successful += 1
            continue
        
        print(f"[{i}/{len(characters)}] Downloading {display_name}...", end='', flush=True)
        
        # Try multiple URL patterns
        urls = get_alternative_urls(display_name)
        downloaded = False
        
        for j, url in enumerate(urls):
            if j > 0:
                print(f"\n  Trying alternative {j}...", end='', flush=True)
            
            if download_image(url, output_path):
                print(" ✓")
                downloaded = True
                successful += 1
                break
            time.sleep(0.3)  # Small delay between attempts
        
        if not downloaded:
            print(" ✗ Failed")
            failed.append((key, display_name))
            # Remove empty file if created
            if output_path.exists() and output_path.stat().st_size < 100:
                output_path.unlink()
        
        # Rate limiting - be nice to the wiki server
        time.sleep(0.5)
    
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
