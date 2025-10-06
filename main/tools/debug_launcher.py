"""
Debug Launcher for Genshin Impact Rich Presence.

This script enables debug mode and runs comprehensive debugging tests
for all components of the application.
"""

import os
import sys
import time

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from game_monitor import GameMonitor
from ocr_engine import OCREngine
from game_state_detector import GameStateDetector
from discord_rpc import DiscordRPCManager
from datatypes import Data


def run_debug_tests():
    """Run comprehensive debug tests for all components."""
    print("🔧 GENSHIN IMPACT RICH PRESENCE - DEBUG MODE")
    print("=" * 60)

    # Initialize data
    print("📊 Initializing game data...")
    data = Data()

    # Create debug configuration
    debug_config = {
        'DEBUG_MODE': True,
        'DEBUG_SAVE_IMAGES': True,
        'DEBUG_IMAGES_DIRECTORY': './debug_comprehensive',
        'SLEEP_PER_ITERATION': 0.1,
        'INACTIVE_COOLDOWN': 5,
        'PAUSE_STATE_COOLDOWN': 3,
        'OCR_CHARNAMES_ONE_IN': 1,
        'OCR_BOSS_ONE_IN': 1,
        'OCR_LOC_ONE_IN': 1,
    }

    print("✅ Debug configuration loaded")

    # Test OCR Engine
    print("\n🖼️  TESTING OCR ENGINE...")
    print("-" * 40)

    ocr_engine = OCREngine(
        debug_mode=True,
        debug_save_images=True,
        debug_images_directory="./debug_ocr_comprehensive"
    )

    # Test OCR regions capture
    test_regions = {
        "character_1": (100, 100, 200, 150),  # Example coordinates
        "location": (300, 200, 400, 250),
        "boss": (500, 300, 600, 350),
    }

    try:
        ocr_results = ocr_engine.debug_capture_all_regions(test_regions)
        print("   ✅ OCR Engine test completed")
    except Exception as e:
        print(f"   ❌ OCR Engine test failed: {e}")

    # Test Game State Detector
    print("\n🎯 TESTING GAME STATE DETECTOR...")
    print("-" * 40)

    game_detector = GameStateDetector(data, ocr_engine, debug_config)

    try:
        detection_results = game_detector.debug_all_detection_methods()
        print("   ✅ Game State Detector test completed")
    except Exception as e:
        print(f"   ❌ Game State Detector test failed: {e}")

    # Test Discord RPC (if Discord is running)
    print("\n🎮 TESTING DISCORD RPC...")
    print("-" * 40)

    discord_rpc = DiscordRPCManager()

    try:
        rpc_results = discord_rpc.debug_connection_test()
        if rpc_results.get("connection_successful", False):
            print("   ✅ Discord RPC test completed")
        else:
            print("   ⚠️  Discord RPC test skipped (Discord not running)")
    except Exception as e:
        print(f"   ❌ Discord RPC test failed: {e}")

    # Test Game Monitor
    print("\n🎮 TESTING GAME MONITOR...")
    print("-" * 40)

    game_monitor = GameMonitor(data, debug_config)

    try:
        monitor_results = game_monitor.debug_component_integration()
        print("   ✅ Game Monitor test completed")
    except Exception as e:
        print(f"   ❌ Game Monitor test failed: {e}")

    # Summary
    print("\n" + "=" * 60)
    print("🎉 DEBUG TESTING COMPLETED")
    print("=" * 60)

    print("\nDebug Reports Generated:")
    print("  📁 ./debug_ocr_comprehensive/     - OCR engine debug images")
    print("  📁 ./debug_comprehensive/         - General debug images")
    print("  📁 ./debug_game_state_detector/   - Game state detection images")
    print("  📁 ./debug_game_monitor/          - Game monitor debug images")

    print("\nTo disable debug mode, set DEBUG_MODE = False in CONFIG.py")
    print("Debug output will only appear when DEBUG_MODE = True")


def main():
    """Main function to run debug tests."""
    print("Starting Genshin Impact Rich Presence Debug Tests...")

    try:
        run_debug_tests()

        print("\n✅ Debug testing completed successfully!")
        return 0

    except KeyboardInterrupt:
        print("\n\n⚠️  Debug testing interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Debug testing failed with error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
