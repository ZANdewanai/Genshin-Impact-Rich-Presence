#!/usr/bin/env python3
"""
Create placeholder images for missing assets.
"""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
IMAGES_DIR = BASE_DIR / "resources/assets/images"

def create_placeholder(width, height, text, color=(100, 100, 100), text_color=(255, 255, 255)):
    """Create a simple placeholder image with text."""
    img = Image.new('RGB', (width, height), color)
    draw = ImageDraw.Draw(img)
    
    # Try to use a default font, fallback to basic text if not available
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except:
        font = ImageFont.load_default()
    
    # Calculate text position (centered)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    draw.text((x, y), text, fill=text_color, font=font)
    return img

def create_domain_placeholders():
    """Create placeholder images for missing domain assets."""
    missing_domains = [
        ("domains/forgery", "domain_forgery_snezhnaya", "Scars of Cursed\nObsession", (150, 50, 50)),
        ("domains/blessing", "domain_blessing_snezhnaya", "Inverted Glacier", (50, 100, 150)),
        ("domains/mastery", "domain_mastery_snezhnaya", "Relics of Fallen\nGrace", (50, 150, 50)),
    ]
    
    for subdir, filename, text, color in missing_domains:
        output_dir = IMAGES_DIR / subdir
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{filename}.png"
        
        if not output_path.exists():
            img = create_placeholder(256, 256, text, color)
            img.save(output_path)
            print(f"Created: {output_path}")
        else:
            print(f"Already exists: {output_path}")

def create_boss_placeholders():
    """Create placeholder images for missing boss assets."""
    missing_bosses = [
        ("domains/trounce", "trounce_boss_ronova", "Ronova", (150, 50, 150)),
    ]
    
    for subdir, filename, text, color in missing_bosses:
        output_dir = IMAGES_DIR / subdir
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{filename}.png"
        
        if not output_path.exists():
            img = create_placeholder(256, 256, text, color)
            img.save(output_path)
            print(f"Created: {output_path}")
        else:
            print(f"Already exists: {output_path}")

def create_location_placeholders():
    """Create placeholder images for missing location emblems."""
    missing_locations = [
        ("locations", "emblem_snezhnaya", "Snezhnaya", (100, 150, 200)),
    ]
    
    for subdir, filename, text, color in missing_locations:
        output_dir = IMAGES_DIR / subdir
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{filename}.png"
        
        if not output_path.exists():
            img = create_placeholder(256, 256, text, color)
            img.save(output_path)
            print(f"Created: {output_path}")
        else:
            print(f"Already exists: {output_path}")

if __name__ == "__main__":
    print("Creating placeholder images...")
    create_domain_placeholders()
    create_boss_placeholders()
    create_location_placeholders()
    print("Done!")
