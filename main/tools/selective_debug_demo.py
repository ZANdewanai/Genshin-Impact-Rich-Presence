"""
Selective OCR Debugging Examples

This script demonstrates how to use the selective debugging methods
to debug specific OCR components individually.
"""

import os
import sys

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ocr_engine import OCREngine
from game_state_detector import GameStateDetector
from datatypes import Data


def demo_selective_debugging():
    """Demonstrate selective debugging of OCR components."""
    print("🎯 SELECTIVE OCR DEBUGGING DEMO")
    print("=" * 50)

    # Initialize components
    data = Data()
    ocr_engine = OCREngine(debug_mode=True, debug_save_images=True)
    detector = GameStateDetector(data, ocr_engine, {})

    print("✅ Components initialized")

    # Example 1: Debug a specific capture region
    print("\n" + "=" * 50)
    print("📸 EXAMPLE 1: Debug Specific Capture Region")
    print("=" * 50)

    # Define a test region (you would use your actual coordinates)
    test_region = {
        "character_name": (100, 200, 300, 250)  # Example coordinates
    }

    print("Testing character name region...")
    results = ocr_engine.debug_capture_comparison(test_region)

    if results:
        for region_name, result in results.items():
            if result.get("success"):
                best = result.get("best_result", {})
                print(f"✅ {region_name}: '{best.get('cleaned_text', '')}' (PSM {best.get('psm')})")

    # Example 2: Debug a specific detection method
    print("\n" + "=" * 50)
    print("🔍 EXAMPLE 2: Debug Specific Detection Method")
    print("=" * 50)

    print("Testing location detection specifically...")
    location_results = detector.debug_specific_detection("location")

    if location_results.get("success"):
        print(f"✅ Location detected: {location_results.get('location', 'N/A')}")
    else:
        print(f"❌ Location detection failed: {location_results.get('error', 'Unknown')}")

    # Example 3: Compare multiple detection methods
    print("\n" + "=" * 50)
    print("⚖️ EXAMPLE 3: Compare Multiple Detection Methods")
    print("=" * 50)

    print("Comparing character and location detection...")
    comparison_results = detector.debug_detection_comparison(["character", "location"])

    if comparison_results:
        for method, result in comparison_results.items():
            if result.get("success"):
                print(f"✅ {method}: Working")
            else:
                print(f"❌ {method}: Failed - {result.get('error', 'Unknown')}")

    print("\n" + "=" * 50)
    print("💡 SELECTIVE DEBUGGING TIPS")
    print("=" * 50)
    print("• Use debug_specific_region() to test individual capture areas")
    print("• Use debug_specific_detection() to test individual detection methods")
    print("• Use debug_capture_comparison() to compare multiple regions")
    print("• Use debug_detection_comparison() to compare multiple detection types")
    print("• All methods only run when DEBUG_MODE = True")
    print("• Debug images are saved to ./debug_* directories")


if __name__ == "__main__":
    demo_selective_debugging()
