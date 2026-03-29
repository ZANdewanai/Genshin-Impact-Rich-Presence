#!/usr/bin/env python3
"""
Script to download missing asset images from Genshin Impact Wiki.
Compares CSV image keys against existing files and downloads missing ones.
"""
import csv
import hashlib
import os
import re
import time
import requests
from pathlib import Path
from urllib.parse import quote

# Base paths
BASE_DIR = Path(__file__).parent.parent
IMAGES_DIR = BASE_DIR / "resources/assets/images"
DATA_DIR = BASE_DIR / "data"

# User agent to avoid being blocked
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}


def get_hash_prefix(filename):
    """Generate the hash prefix for a wiki image URL."""
    md5 = hashlib.md5(filename.encode('utf-8')).hexdigest()
    return md5[0], md5[:2]


def get_wiki_menu_icon_url(name):
    """Generate wiki URL for menu/UI icons with comprehensive naming patterns."""
    wiki_name = name.replace(' ', '_')
    # Also try with spaces as some wiki files use spaces
    spaced_name = name.replace('_', ' ')
    
    # Comprehensive patterns for UI icons on Genshin wiki
    patterns = [
        # Primary patterns
        f"Icon_{wiki_name}.png",
        f"UI_{wiki_name}.png",
        f"Item_{wiki_name}.png",
        # With Menu suffix
        f"Icon_{wiki_name}_Menu.png",
        f"UI_{wiki_name}_Menu.png",
        # Icon suffix
        f"{wiki_name}_Icon.png",
        # Category-specific patterns
        f"Icon_Inventory_{wiki_name}.png",
        f"Icon_Archive_{wiki_name}.png",
        f"Icon_Menu_{wiki_name}.png",
        f"Icon_Quest_{wiki_name}.png",
        f"Icon_Commission_{wiki_name}.png",
        f"Icon_Cooking_{wiki_name}.png",
        f"Icon_Forge_{wiki_name}.png",
        f"Icon_Craft_{wiki_name}.png",
        f"Icon_Shop_{wiki_name}.png",
        f"Icon_Friends_{wiki_name}.png",
        f"Icon_Settings_{wiki_name}.png",
        f"Icon_Wish_{wiki_name}.png",
        f"Icon_Battle_Pass_{wiki_name}.png",
        f"Icon_Achievements_{wiki_name}.png",
        f"Icon_Dressing_Room_{wiki_name}.png",
        f"Icon_Co-Op_{wiki_name}.png",
        f"Icon_Mailbox_{wiki_name}.png",
        # Alternative naming (spaces instead of underscores)
        f"Icon_{spaced_name}.png",
        f"UI_{spaced_name}.png",
        # With hyphens
        f"Icon_{wiki_name.replace('_', '-')}.png",
        # Lowercase variations
        f"icon_{wiki_name.lower()}.png",
        f"ui_{wiki_name.lower()}.png",
    ]
    
    urls = []
    for pattern in patterns:
        first_char, first_two = get_hash_prefix(pattern)
        url = f"https://static.wikia.nocookie.net/gensin-impact/images/{first_char}/{first_two}/{quote(pattern)}"
        urls.append(url)
    
    return urls


def get_wiki_character_url(character_name):
    """Generate character icon URL."""
    urls = []
    wiki_name = character_name.replace(' ', '_')
    
    # Try different naming patterns
    patterns = [
        f"{wiki_name}_Icon.png",
        f"Character_{wiki_name}_Icon.png",
        f"{wiki_name}_Card.png",
        f"Character_{wiki_name}_Card.png",
    ]
    
    # Special cases
    if character_name in ['Aether', 'Lumine']:
        urls.insert(0, "https://static.wikia.nocookie.net/gensin-impact/images/5/51/Traveler_Icon.png")
    if character_name == 'Kujo Sara':
        urls.insert(0, "https://static.wikia.nocookie.net/gensin-impact/images/d/df/Kujou_Sara_Icon.png")
    
    for pattern in patterns:
        first_char, first_two = get_hash_prefix(pattern)
        url = f"https://static.wikia.nocookie.net/gensin-impact/images/{first_char}/{first_two}/{quote(pattern)}"
        urls.append(url)
    
    return urls


def get_wiki_boss_url(boss_name):
    """Generate boss icon URL."""
    wiki_name = boss_name.replace(' ', '_')
    patterns = [
        f"{wiki_name}_Icon.png",
        f"{wiki_name}_Portrait.png",
    ]
    urls = []
    for pattern in patterns:
        first_char, first_two = get_hash_prefix(pattern)
        url = f"https://static.wikia.nocookie.net/gensin-impact/images/{first_char}/{first_two}/{quote(pattern)}"
        urls.append(url)
    return urls


def get_wiki_domain_url(domain_name):
    """Generate domain icon URL."""
    wiki_name = domain_name.replace(' ', '_')
    patterns = [
        f"{wiki_name}_Icon.png",
        f"Domain_{wiki_name}.png",
    ]
    urls = []
    for pattern in patterns:
        first_char, first_two = get_hash_prefix(pattern)
        url = f"https://static.wikia.nocookie.net/gensin-impact/images/{first_char}/{first_two}/{quote(pattern)}"
        urls.append(url)
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


def find_existing_file(image_key):
    """Check if an image file exists for the given key."""
    # Map key prefix to subfolder
    subfolder = ""
    if image_key.startswith('char_'):
        subfolder = "characters"
    elif image_key.startswith('boss_'):
        subfolder = "bosses"
    elif image_key.startswith('domain_'):
        # Check domain subfolders
        for domain_type in ['forgery', 'blessing', 'mastery', 'trounce']:
            if f'_{domain_type}_' in image_key or image_key.endswith(f'_{domain_type}'):
                subfolder = f"domains/{domain_type}"
                break
        if not subfolder:
            subfolder = "domains"
    elif image_key.startswith('emblem_'):
        subfolder = "locations"
    elif image_key.startswith('area_'):
        subfolder = "areas"
    elif image_key.startswith('menu_'):
        subfolder = "ui/menus"
    elif image_key.startswith('ui_'):
        subfolder = "ui/ui"
    elif image_key.startswith('tree_'):
        subfolder = "content/tree"
    elif image_key.startswith('fountain_'):
        subfolder = "content/fountain"
    elif image_key.startswith('spiral_abyss'):
        subfolder = "content/abyss"
    elif image_key.startswith('tablet_'):
        subfolder = "content"
    else:
        return None
    
    # Check for file with .png or .jpg extension (both underscore and space naming)
    folder = IMAGES_DIR / subfolder
    # Try original key name (with underscores)
    for ext in ['.png', '.jpg']:
        file_path = folder / f"{image_key}{ext}"
        if file_path.exists() and file_path.stat().st_size > 100:
            return file_path
    # Try with spaces instead of underscores
    spaced_key = image_key.replace('_', ' ')
    for ext in ['.png', '.jpg']:
        file_path = folder / f"{spaced_key}{ext}"
        if file_path.exists() and file_path.stat().st_size > 100:
            return file_path
    return None


def parse_csv_for_images(csv_file, image_col, name_col=None):
    """Parse CSV and return list of (image_key, display_name) tuples."""
    items = []
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if not row or row[0].startswith('------'):
                    continue
                if len(row) > image_col:
                    image_key = row[image_col]
                    name = row[name_col] if name_col is not None and len(row) > name_col else image_key
                    items.append((image_key, name))
    except Exception as e:
        print(f"Error reading {csv_file}: {e}")
    
    return items


def get_all_csv_image_keys():
    """Get all image keys from all CSV files."""
    all_images = {
        'characters': [],
        'bosses': [],
        'domains': [],
        'locations': [],
        'gamemenus': [],
    }
    
    # Characters: search_str, image_key, display_name
    all_images['characters'] = parse_csv_for_images(
        DATA_DIR / "characters.csv", image_col=1, name_col=2
    )
    
    # Bosses: search_str, boss_name, image_key
    all_images['bosses'] = parse_csv_for_images(
        DATA_DIR / "bosses.csv", image_col=2, name_col=1
    )
    
    # Domains: search_str, domain_name, domain_type, image_key
    all_images['domains'] = parse_csv_for_images(
        DATA_DIR / "domains.csv", image_col=3, name_col=1
    )
    
    # Locations: search_str, location_name, subarea, country, image_key
    all_images['locations'] = parse_csv_for_images(
        DATA_DIR / "locations.csv", image_col=4, name_col=1
    )
    
    # Gamemenus: search_str, gamemenu_name, gamemenu_type, image_key
    all_images['gamemenus'] = parse_csv_for_images(
        DATA_DIR / "gamemenus.csv", image_col=3, name_col=1
    )
    
    return all_images


def download_missing_assets():
    """Main function to find and download missing assets."""
    print("=" * 70)
    print("Genshin Impact Missing Asset Downloader")
    print("=" * 70)
    print(f"\nImages directory: {IMAGES_DIR}")
    
    all_images = get_all_csv_image_keys()
    
    # Find missing images
    missing = []
    found = 0
    processed_keys = set()  # Track already-processed image keys
    
    for category, items in all_images.items():
        for image_key, name in items:
            # Skip icon_* keys (no corresponding files)
            if image_key.startswith('icon_'):
                continue
            
            # Skip duplicate image keys (multiple CSV entries sharing same image)
            if image_key in processed_keys:
                continue
            processed_keys.add(image_key)
            
            existing = find_existing_file(image_key)
            if existing:
                found += 1
            else:
                missing.append((category, image_key, name))
    
    print(f"\nFound {found} existing images")
    print(f"Missing {len(missing)} images")
    
    if not missing:
        print("\n✓ All images are already present!")
        return
    
    print(f"\nDownloading {len(missing)} missing images...\n")
    
    successful = 0
    failed = []
    
    for i, (category, image_key, name) in enumerate(missing, 1):
        # Determine output path
        subfolder = ""
        if image_key.startswith('char_'):
            subfolder = "characters"
        elif image_key.startswith('boss_'):
            subfolder = "bosses"
        elif image_key.startswith('domain_'):
            for domain_type in ['forgery', 'blessing', 'mastery', 'trounce']:
                if f'_{domain_type}_' in image_key or image_key.endswith(f'_{domain_type}'):
                    subfolder = f"domains/{domain_type}"
                    break
            if not subfolder:
                subfolder = "domains"
        elif image_key.startswith('emblem_'):
            subfolder = "locations"
        elif image_key.startswith('area_'):
            subfolder = "areas"
        elif image_key.startswith('menu_'):
            subfolder = "ui/menus"
        elif image_key.startswith('ui_'):
            subfolder = "ui/ui"
        elif image_key.startswith('tree_'):
            subfolder = "content/tree"
        elif image_key.startswith('fountain_'):
            subfolder = "content/fountain"
        elif image_key.startswith('spiral_abyss'):
            subfolder = "content/abyss"
        elif image_key.startswith('tablet_'):
            subfolder = "content"
        
        if not subfolder:
            continue
        
        output_dir = IMAGES_DIR / subfolder
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{image_key}.png"
        
        print(f"[{i}/{len(missing)}] {category}: {name} ({image_key})...", end='', flush=True)
        
        # Get appropriate URLs based on category
        urls = []
        if category == 'characters':
            urls = get_wiki_character_url(name)
        elif category == 'bosses':
            urls = get_wiki_boss_url(name)
        elif category == 'domains':
            urls = get_wiki_domain_url(name)
        elif category == 'gamemenus':
            # Use menu icon URL patterns for gamemenu items
            urls = get_wiki_menu_icon_url(name)
        else:
            # Try generic icon URL
            urls = get_wiki_menu_icon_url(name)
        
        downloaded = False
        for j, url in enumerate(urls):
            if download_image(url, output_path):
                print(" ✓")
                successful += 1
                downloaded = True
                break
            if j < len(urls) - 1:
                time.sleep(0.2)
        
        if not downloaded:
            print(" ✗ Failed")
            failed.append((category, image_key, name))
            # Clean up partial file
            if output_path.exists() and output_path.stat().st_size < 100:
                output_path.unlink()
        
        time.sleep(0.3)
    
    print("\n" + "=" * 70)
    print("Download Summary")
    print("=" * 70)
    print(f"Total missing: {len(missing)}")
    print(f"Successfully downloaded: {successful}")
    print(f"Failed: {len(failed)}")
    
    if failed:
        print("\nFailed downloads:")
        for category, image_key, name in failed:
            print(f"  - [{category}] {name} ({image_key})")


if __name__ == "__main__":
    download_missing_assets()
