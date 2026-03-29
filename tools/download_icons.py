"""
Download icons from Genshin Impact Fandom wiki Category:Icons.
Uses Fandom API to get file list, then downloads using MD5 hash URLs.
Usage: python download_icons.py
"""
import urllib.request
import urllib.parse
import hashlib
import json
import os
import time

API_URL = "https://genshin-impact.fandom.com/api.php"
OUTPUT_DIR = "icons"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


def get_hash_url(filename):
    """Generate wiki image URL using MD5 hash prefix."""
    # Wiki stores files with underscores, not spaces
    wiki_filename = filename.replace(' ', '_')
    md5 = hashlib.md5(wiki_filename.encode('utf-8')).hexdigest()
    first_char = md5[0]
    first_two = md5[:2]
    encoded_name = urllib.parse.quote(wiki_filename)
    return f"https://static.wikia.nocookie.net/gensin-impact/images/{first_char}/{first_two}/{encoded_name}"


def fetch_api(params):
    """Fetch from Fandom API."""
    query = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    url = f"{API_URL}?{query}"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"  API error: {e}")
        return None


def get_category_files(category):
    """Get all files in a category using API."""
    files = []
    continue_param = None

    while True:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": f"Category:{category}",
            "cmtype": "file",
            "cmlimit": 500,
            "format": "json",
            "origin": "*",
        }
        if continue_param:
            params["cmcontinue"] = continue_param

        data = fetch_api(params)
        if not data or "query" not in data:
            break

        for member in data["query"].get("categorymembers", []):
            title = member["title"]
            if title.startswith("File:"):
                files.append(title[5:])

        if "continue" in data and "cmcontinue" in data["continue"]:
            continue_param = data["continue"]["cmcontinue"]
        else:
            break

    return files


def download_file(filename, output_path):
    """Download a single file from wiki."""
    url = get_hash_url(filename)
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read()
            content_type = response.headers.get('Content-Type', '')
            if 'image' not in content_type or len(data) < 100:
                return False
            with open(output_path, "wb") as f:
                f.write(data)
            return True
    except Exception:
        return False


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"Downloading icons from Category:Icons")
    print(f"Output: {os.path.abspath(OUTPUT_DIR)}")
    print("=" * 60)

    print("\nFetching file list from API...")
    files = get_category_files("UI_Icons")
    print(f"Found {len(files)} files")

    image_exts = ('.png', '.jpg', '.jpeg', '.gif', '.webp')
    image_files = [f for f in files if f.lower().endswith(image_exts)]
    print(f"{len(image_files)} are images")
    print("=" * 60)

    successful = 0
    failed = 0

    for i, filename in enumerate(image_files, 1):
        safe_name = filename.replace(' ', '_').replace('/', '_')
        output_path = os.path.join(OUTPUT_DIR, safe_name)

        if os.path.exists(output_path) and os.path.getsize(output_path) > 100:
            print(f"[{i}/{len(image_files)}] {filename}: exists")
            successful += 1
            continue

        print(f"[{i}/{len(image_files)}] {filename}...", end="", flush=True)

        if download_file(filename, output_path):
            size = os.path.getsize(output_path)
            print(f" ✓ ({size:,} bytes)")
            successful += 1
        else:
            print(" ✗ Failed")
            failed += 1

        if i < len(image_files):
            time.sleep(0.3)

    print("\n" + "=" * 60)
    print("Complete! Successful: {}, Failed: {}".format(successful, failed))


if __name__ == "__main__":
    main()
