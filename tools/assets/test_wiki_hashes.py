#!/usr/bin/env python3
"""Test wiki URL hash generation."""
import hashlib
import requests

def get_hash_prefix(filename):
    md5 = hashlib.md5(filename.encode('utf-8')).hexdigest()
    return md5[0], md5[:2]

# Test files
test_files = [
    'Icon_Cooking.png',
    'Icon_Forge.png',
    'Icon_Craft.png',
    'Icon_Archive.png',
    'Icon_Camera.png',
    'Aether_Icon.png',
    'Character_Aether_Icon.png',
]

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

print("Testing wiki URL generation:")
print("=" * 60)

for filename in test_files:
    first_char, first_two = get_hash_prefix(filename)
    url = f'https://static.wikia.nocookie.net/gensin-impact/images/{first_char}/{first_two}/{filename}'
    
    print(f"\n{filename}:")
    print(f"  Hash prefix: {first_char}/{first_two}")
    print(f"  URL: {url}")
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        print(f"  Status: {resp.status_code}")
        if resp.status_code == 200:
            content_type = resp.headers.get('Content-Type', 'unknown')
            print(f"  Content-Type: {content_type}")
            print(f"  Size: {len(resp.content)} bytes")
            if 'image' in content_type and len(resp.content) > 1000:
                print(f"  ✓ VALID IMAGE")
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 60)
