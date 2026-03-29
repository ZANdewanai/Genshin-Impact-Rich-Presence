"""
Debug script to check what URLs are being extracted from the category page.
"""
import urllib.request
import urllib.parse
import html.parser
import os
import time
import re

CATEGORY_URL = "https://genshin-impact.fandom.com/wiki/Category:Icons"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


class DebugLinkExtractor(html.parser.HTMLParser):
    """Extract ALL image URLs from HTML for debugging."""

    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag == "img":
            src = attrs_dict.get("data-src") or attrs_dict.get("src")
            if src:
                self.urls.append(("img", src, attrs_dict.get("alt", "no alt")))
        elif tag == "a":
            href = attrs_dict.get("href")
            if href and (".png" in href or ".jpg" in href or "File:" in href):
                self.urls.append(("a", href, attrs_dict.get("title", "no title")))


def fetch_page(url):
    """Fetch page."""
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode("utf-8")
    except Exception as e:
        print(f"Failed: {e}")
        return None


def main():
    print("Fetching page...")
    html = fetch_page(CATEGORY_URL)
    if not html:
        print("Failed to fetch")
        return

    # Save HTML to debug file
    with open("debug_category.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("Saved HTML to debug_category.html")

    # Extract URLs
    extractor = DebugLinkExtractor()
    extractor.feed(html)

    print(f"\nFound {len(extractor.urls)} potential URLs:")
    print("=" * 80)

    for tag_type, url, alt in extractor.urls[:50]:  # Show first 50
        print(f"[{tag_type}] alt={alt[:40]:<40} url={url[:80]}")

    # Also look for category gallery specific patterns
    print("\n" + "=" * 80)
    print("Looking for category gallery patterns...")

    # Look for category-page__member patterns
    member_links = re.findall(r'class="category-page__member-[^"]*"[^>]*href="([^"]+)"', html)
    print(f"\nFound {len(member_links)} category-page__member links:")
    for link in member_links[:20]:
        print(f"  {link}")


if __name__ == "__main__":
    main()
