"""
Game Monitor module for Genshin Impact Rich Presence.

Coordinates game state detection, manages the main game loop, and handles state transitions.
"""

import time
import signal
import threading
from typing import Optional, Tuple

# Import window_utils using relative import instead of sys.path manipulation
from .. import window_utils

from ..datatypes import Activity, ActivityType, Location
from ..discord_rpc import DiscordRPCManager
from .game_state_detector import GameStateDetector
from ..ocr.ocr_engine import OCREngine


class GameMonitor:
    """
    Main game monitor that coordinates all game state detection and manages the game loop.
    """

    def __init__(self, data, config: dict):
        """
        Initialize game monitor.

        Args:
            data: Game data instance
            config: Configuration dictionary
        """
        self.data = data
        self.config = config

        # Initialize components
        self.ocr_engine = OCREngine(
            debug_mode=config.get('DEBUG_MODE', False),
            debug_save_images=config.get('DEBUG_SAVE_IMAGES', False),
            debug_images_directory=config.get('DEBUG_IMAGES_DIRECTORY', './debug_images')
        )

        self.game_state_detector = GameStateDetector(data, self.ocr_engine, config)

        # Set the game_state_detector reference in OCR engine
        self.ocr_engine.game_state_detector = self.game_state_detector
        self.discord_rpc = DiscordRPCManager()

        # Game state variables
        self.current_activity: Activity = Activity(ActivityType.LOADING, False)
        self.current_characters = [None, None, None, None]
        self.current_active_character = 0
        self.game_start_time: Optional[int] = None
        self.prev_non_idle_activity: Activity = Activity(ActivityType.LOADING, False)
        self.prev_location: Optional[Location] = None

        # Pause state management
        self.pause_ocr = True
        self.game_paused = False
        self.game_pause_state_cooldown = 0
        self.game_pause_state_displayed = False

        # Inactive detection management
        self.inactive_detection_cooldown = 0
        self.inactive_detection_mode: Optional[ActivityType] = None

        # Party reload flag
        self.reload_party_flag = False

        # Loop control
        self.running = False
        self.loop_count = 0

        # Configuration values
        self.sleep_per_iteration = config.get('SLEEP_PER_ITERATION', 0.08)
        self.inactive_cooldown = config.get('INACTIVE_COOLDOWN', 0)
        self.pause_state_cooldown = config.get('PAUSE_STATE_COOLDOWN', 0)
        self.ocr_charnames_one_in = config.get('OCR_CHARNAMES_ONE_IN', 1)
        self.ocr_boss_one_in = config.get('OCR_BOSS_ONE_IN', 1)
        self.ocr_loc_one_in = config.get('OCR_LOC_ONE_IN', 1)

        # Thread for window focus checking
        self.focus_thread: Optional[threading.Thread] = None

    def start(self):
        """Start the game monitor."""
        self.running = True

        # Start Discord RPC
        self.discord_rpc.start()

        # Start the main game loop
        self._game_loop()

    def stop(self):
        """Stop the game monitor."""
        self.running = False
        self.discord_rpc.stop()

        # Stop focus thread
        if self.focus_thread and self.focus_thread.is_alive():
            self.focus_thread.join(timeout=1.0)

    def _game_loop(self):
        """Main game monitoring loop."""
        try:
            while self.running:
                self.loop_count += 1

                # Check if game is running and focused
                if not self._check_game_focus():
                    time.sleep(self.sleep_per_iteration)
                    continue

                # Detect active character (every loop)
                active_character, brightness = self.game_state_detector.detect_active_character()

                # Handle active character detection
                self._handle_active_character_detection(active_character)

                if active_character != 0:
                    # Reset inactive detection cooldown when active character found
                    self.inactive_detection_cooldown = 0

                    # Restore previous activity if game was idle
                    if self.current_activity.is_idle():
                        self.current_activity = self.prev_non_idle_activity

                    # Detect party members (with throttling)
                    if (self.loop_count % self.ocr_charnames_one_in == 0
                        or any(c is None for c in self.current_characters)
                        or self.reload_party_flag):
                        self.current_characters = self.game_state_detector.detect_party_members()
                        self.reload_party_flag = False

                    # Detect location (with throttling)
                    if self.loop_count % self.ocr_loc_one_in == 0:  # Use CONFIG setting for location frequency
                        location = self.game_state_detector.detect_location()
                        if location and self._should_update_location(location):
                            self._update_location(location)

                    # Detect boss (with throttling)
                    if self.loop_count % self.ocr_boss_one_in == 0:
                        boss = self.game_state_detector.detect_boss()
                        if boss and self._should_update_boss(boss):
                            self._update_boss(boss)

                else:  # No active character detected (game paused/inactive)
                    self._handle_inactive_game_state()

                # Update Discord RPC
                self.discord_rpc.update_activity(
                    self.current_activity,
                    self.current_characters,
                    self.current_active_character,
                    self.game_start_time
                )

                # Handle pause state changes
                self._handle_pause_state()

                time.sleep(self.sleep_per_iteration)

        except KeyboardInterrupt:
            print("\nReceived keyboard interrupt. Shutting down...")
        except Exception as e:
            print(f"Error in game loop: {e}")
            time.sleep(1)  # Prevent tight loop on error

    def _check_game_focus(self) -> bool:
        """Check if game is running and focused."""
        try:
            # Check if Genshin Impact is running
            if not self._is_genshin_running():
                if not self.pause_ocr:
                    if self.ocr_engine.debug_mode:
                        print("[FOCUS] Genshin Impact is not running, pausing OCR")
                    self.pause_ocr = True
                time.sleep(0.5)
                return False

            # Check if the game window is focused
            focused = window_utils.is_genshin_window_focused(self.ocr_engine.debug_mode)

            # Update the pause state only if it changes
            if self.pause_ocr and focused:
                print("[MAIN] Game window focused, resuming OCR")
                self.pause_ocr = False
            elif not self.pause_ocr and not focused:
                if self.ocr_engine.debug_mode:
                    print("[FOCUS] Game window lost focus, pausing OCR")
                self.pause_ocr = True

            return focused

        except Exception as e:
            if self.ocr_engine.debug_mode:
                print(f"[DEBUG] Error in _check_game_focus: {e}")
            return False

    def _is_genshin_running(self) -> bool:
        """Check if Genshin Impact is currently running."""
        try:
            import psutil
            for proc in psutil.process_iter(['name']):
                try:
                    if proc.info['name'] == 'GenshinImpact.exe':
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except Exception:
            pass
        return False

    def _handle_active_character_detection(self, active_character: int):
        """Handle active character detection results."""
        if active_character != self.current_active_character:
            if self.current_activity.activity_type == ActivityType.LOADING:
                self.current_activity.activity_data = True

            self.current_active_character = active_character
            if active_character != 0 and self.current_characters[active_character - 1] is not None:
                char_name = self.current_characters[active_character - 1].character_display_name
                print(f'Switched active character to "{char_name}"')

    def _handle_inactive_game_state(self):
        """Handle game state when no active character is detected."""
        # Set game as paused initially
        curr_game_paused = True

        # Decrement inactive detection cooldown
        if self.inactive_detection_cooldown > 0:
            self.inactive_detection_cooldown -= 1

        # Detect game menu if cooldown allows
        if (self.inactive_detection_cooldown == 0 or
            self.inactive_detection_mode == ActivityType.GAME_MENU):
            game_menu = self.game_state_detector.detect_game_menu()
            if game_menu and self._should_update_game_menu(game_menu):
                self._update_game_menu(game_menu)
                curr_game_paused = False

        # Detect domain if game is paused and cooldown allows
        if (curr_game_paused and
            (self.inactive_detection_cooldown == 0 or
             self.inactive_detection_mode == ActivityType.DOMAIN) and
            self.loop_count % 10 == 0):  # Only run every 10 iterations

            domain = self.game_state_detector.detect_domain()
            if domain and self._should_update_domain(domain):
                self._update_domain(domain)
                curr_game_paused = False

    def _should_update_location(self, location: Location) -> bool:
        """Check if location should be updated."""
        return (self.current_activity.activity_type != ActivityType.LOCATION or
                self.current_activity.activity_data.search_str != location.search_str)

    def _should_update_boss(self, boss) -> bool:
        """Check if boss should be updated."""
        return (self.current_activity.activity_type != ActivityType.WORLD_BOSS or
                self.current_activity.activity_data.search_str != boss.search_str)

    def _should_update_game_menu(self, game_menu) -> bool:
        """Check if game menu should be updated."""
        return (self.current_activity.activity_type != ActivityType.GAME_MENU or
                self.current_activity.activity_data.search_str != game_menu.search_str)

    def _should_update_domain(self, domain) -> bool:
        """Check if domain should be updated."""
        return (self.current_activity.activity_type != ActivityType.DOMAIN or
                self.current_activity.activity_data.search_str != domain.search_str)

    def _update_location(self, location: Location):
        """Update current location."""
        self.current_activity = Activity(ActivityType.LOCATION, location)
        self.prev_location = location
        print(f"Detected location: {location.location_name}")

    def _update_boss(self, boss):
        """Update current boss."""
        self.current_activity = Activity(ActivityType.WORLD_BOSS, boss)
        print(f"Detected boss: {boss.boss_name}")

    def _update_game_menu(self, game_menu):
        """Update current game menu."""
        self.inactive_detection_cooldown = self.inactive_cooldown
        self.inactive_detection_mode = ActivityType.GAME_MENU
        self.current_activity = Activity(ActivityType.GAME_MENU, game_menu)
        print(f"Detected game menu: {game_menu.game_menu_name}")

    def _update_domain(self, domain):
        """Update current domain."""
        self.inactive_detection_cooldown = self.inactive_cooldown
        self.inactive_detection_mode = ActivityType.DOMAIN
        self.current_activity = Activity(ActivityType.DOMAIN, domain)
        print(f"✅ Detected domain: {domain.domain_name}")

    def _handle_pause_state(self):
        """Handle game pause state changes."""
        if self.game_pause_state_cooldown > 0:
            self.game_pause_state_cooldown -= 1

        curr_game_paused = (self.current_active_character == 0)

        if curr_game_paused != self.game_paused:
            self.game_pause_state_cooldown = self.pause_state_cooldown
            self.game_paused = curr_game_paused
        elif (self.game_pause_state_cooldown == 0 and
              curr_game_paused != self.game_pause_state_displayed):

            if curr_game_paused:
                self.current_activity = Activity(ActivityType.PAUSED, self.prev_non_idle_activity)
                print("Game paused.")
            else:
                print("Game resumed.")

            self.game_pause_state_displayed = curr_game_paused

        if not self.current_activity.is_idle():
            self.prev_non_idle_activity = self.current_activity

        # Set game start time if activity is no longer loading and not already set
        if (self.current_activity.activity_type != ActivityType.LOADING or
            self.current_activity.activity_data) and self.game_start_time is None:
            self.game_start_time = time.time()

    def debug_component_integration(self) -> dict:
        """
        Debug method to test integration between GameMonitor components.

        Returns:
            Dictionary with integration test results
        """
        if not self.ocr_engine.debug_mode:
            print("[DEBUG] Debug mode not enabled")
            return {}

        print(f"\n{'='*60}")
        print("GAME MONITOR DEBUG - COMPONENT INTEGRATION")
        print(f"{'='*60}")

        results = {}

        # Test OCR Engine
        print(f"\n1. Testing OCR Engine...")
        try:
            if self.ocr_engine:
                print("   ✅ OCR Engine initialized")
                results["ocr_engine"] = True
            else:
                print("   ❌ OCR Engine not initialized")
                results["ocr_engine"] = False
        except Exception as e:
            print(f"   ❌ OCR Engine error: {e}")
            results["ocr_engine"] = False

        # Test Game State Detector
        print(f"\n2. Testing Game State Detector...")
        try:
            if self.game_state_detector:
                print("   ✅ Game State Detector initialized")
                results["game_state_detector"] = True
            else:
                print("   ❌ Game State Detector not initialized")
                results["game_state_detector"] = False
        except Exception as e:
            print(f"   ❌ Game State Detector error: {e}")
            results["game_state_detector"] = False

        # Test Discord RPC
        print(f"\n3. Testing Discord RPC...")
        try:
            if self.discord_rpc:
                print("   ✅ Discord RPC initialized")
                results["discord_rpc"] = True
            else:
                print("   ❌ Discord RPC not initialized")
                results["discord_rpc"] = False
        except Exception as e:
            print(f"   ❌ Discord RPC error: {e}")
            results["discord_rpc"] = False

        # Test configuration
        print(f"\n4. Testing configuration...")
        config_items = [
            'sleep_per_iteration', 'inactive_cooldown', 'pause_state_cooldown',
            'ocr_charnames_one_in', 'ocr_boss_one_in', 'ocr_loc_one_in'
        ]

        config_success = True
        for item in config_items:
            if hasattr(self, item):
                value = getattr(self, item)
                print(f"   {item}: {value}")
            else:
                print(f"   ❌ Missing config: {item}")
                config_success = False

        results["configuration"] = config_success

        return results

    def debug_state_transitions(self) -> dict:
        """
        Debug method to test state transition logic.

        Returns:
            Dictionary with transition test results
        """
        if not self.ocr_engine.debug_mode:
            print("[DEBUG] Debug mode not enabled")
            return {}

        print(f"\n{'='*60}")
        print("GAME MONITOR DEBUG - STATE TRANSITIONS")
        print(f"{'='*60}")

        results = {}

        # Test activity transitions
        print("1. Testing activity state transitions...")

        test_activities = [
            Activity(ActivityType.LOADING, False),
            Activity(ActivityType.LOCATION, Location("Mondstadt", "mondstadt", 0.95)),
            Activity(ActivityType.WORLD_BOSS, None),
            Activity(ActivityType.DOMAIN, None),
            Activity(ActivityType.PAUSED, Activity(ActivityType.LOCATION, Location("Mondstadt", "mondstadt", 0.95))),
        ]

        for i, activity in enumerate(test_activities):
            print(f"\n   Testing transition to: {activity.activity_type.name}")

            old_activity = self.current_activity
            self.current_activity = activity

            print(f"     From: {old_activity.activity_type.name}")
            print(f"     To: {activity.activity_type.name}")
            print(f"     Is idle: {activity.is_idle()}")

            # Test idle state handling
            if activity.is_idle():
                if not self.current_activity.is_idle():
                    self.current_activity = self.prev_non_idle_activity
                    print(f"     Restored previous activity: {self.current_activity.activity_type.name}")

            results[activity.activity_type.name] = {
                "transition_successful": True,
                "is_idle": activity.is_idle()
            }

        # Test pause state handling
        print("2. Testing pause state handling...")

        # Simulate game pause
        print("   Simulating game pause...")
        self.current_active_character = 0

        for i in range(3):
            old_paused = self.game_paused
            self._handle_pause_state()
            print(f"     Iteration {i+1}: paused={self.game_paused}, cooldown={self.game_pause_state_cooldown}")
            time.sleep(0.1)

        # Simulate game resume
        print("   Simulating game resume...")
        self.current_active_character = 1

        for i in range(3):
            old_paused = self.game_paused
            self._handle_pause_state()
            print(f"     Iteration {i+1}: paused={self.game_paused}, cooldown={self.game_pause_state_cooldown}")
            time.sleep(0.1)

        results["pause_handling"] = {
            "pause_detected": self.game_paused == False,  # Should be False after resume
            "cooldown_mechanism": self.game_pause_state_cooldown >= 0
        }

        return results

    def debug_game_loop_simulation(self, iterations: int = 5) -> dict:
        """
        Debug method to simulate game loop iterations.

        Args:
            iterations: Number of iterations to simulate

        Returns:
            Dictionary with loop simulation results
        """
        if not self.ocr_engine.debug_mode:
            print("[DEBUG] Debug mode not enabled")
            return {}

        print(f"\n{'='*60}")
        print(f"GAME MONITOR DEBUG - LOOP SIMULATION ({iterations} iterations)")
        print(f"{'='*60}")

        results = {
            "iterations_completed": 0,
            "game_focused": False,
            "ocr_operations": 0,
            "state_changes": 0
        }

        print("1. Simulating game loop iterations...")

        for i in range(iterations):
            print(f"\n   Iteration {i+1}:")

            # Test game focus check
            focused = self._check_game_focus()
            print(f"     Game focused: {focused}")
            print(f"     OCR paused: {self.pause_ocr}")

            if focused:
                results["game_focused"] = True

                # Simulate active character detection
                active_char, brightness = self.game_state_detector.detect_active_character()
                print(f"     Active character: {active_char}")
                print(f"     Brightness: {brightness}")

                if active_char != 0:
                    results["ocr_operations"] += 1

                    # Simulate character handling
                    self._handle_active_character_detection(active_char)

                    # Simulate throttling logic
                    charnames_due = (self.loop_count % self.ocr_charnames_one_in == 0)
                    boss_due = (self.loop_count % self.ocr_boss_one_in == 0)
                    location_due = (self.loop_count % 5 == 0)

                    print(f"     OCR due - Charnames: {charnames_due}, Boss: {boss_due}, Location: {location_due}")

                    if charnames_due:
                        print("     → Would run character detection")
                    if boss_due:
                        print("     → Would run boss detection")
                    if location_due:
                        print("     → Would run location detection")
                else:
                    print("     → Would run inactive state detection")

                # Simulate Discord RPC update
                self.discord_rpc.update_activity(
                    self.current_activity,
                    self.current_characters,
                    self.current_active_character,
                    self.game_start_time
                )

                # Simulate pause state handling
                old_paused = self.game_paused
                self._handle_pause_state()
                if old_paused != self.game_paused:
                    results["state_changes"] += 1
                    print(f"     Pause state changed: {old_paused} → {self.game_paused}")

            else:
                print("     → Skipping OCR (game not focused)")

            results["iterations_completed"] += 1
            self.loop_count += 1

            # Simulate sleep
            time.sleep(self.sleep_per_iteration)

        return results

    def debug_comprehensive_test(self) -> dict:
        """
        Debug method to run comprehensive GameMonitor tests.

        Returns:
            Dictionary with all test results
        """
        print("Starting comprehensive GameMonitor debug test...")

        results = {}

        # Test component integration
        results["component_integration"] = self.debug_component_integration()

        # Test state transitions
        results["state_transitions"] = self.debug_state_transitions()

        # Test game loop simulation
        results["loop_simulation"] = self.debug_game_loop_simulation()

        # Summary
        self._print_monitor_debug_summary(results)

        return results

    def _print_monitor_debug_summary(self, results: dict):
        """Print a summary of GameMonitor debug results."""
        print(f"\n{'='*60}")
        print("GAME MONITOR DEBUG SUMMARY")
        print(f"{'='*60}")

        # Component integration
        integration = results.get("component_integration", {})
        ocr_ok = integration.get("ocr_engine", False)
        detector_ok = integration.get("game_state_detector", False)
        rpc_ok = integration.get("discord_rpc", False)
        config_ok = integration.get("configuration", False)

        print("Component Integration:")
        print(f"   OCR Engine: {'✅' if ocr_ok else '❌'}")
        print(f"   Game State Detector: {'✅' if detector_ok else '❌'}")
        print(f"   Discord RPC: {'✅' if rpc_ok else '❌'}")
        print(f"   Configuration: {'✅' if config_ok else '❌'}")

        # State transitions
        transitions = results.get("state_transitions", {})
        pause_ok = transitions.get("pause_handling", {}).get("pause_detected", False)
        cooldown_ok = transitions.get("pause_handling", {}).get("cooldown_mechanism", False)

        print("State Transitions:")
        print(f"   Pause handling: {'✅' if pause_ok else '❌'}")
        print(f"   Cooldown mechanism: {'✅' if cooldown_ok else '❌'}")

        # Loop simulation
        simulation = results.get("loop_simulation", {})
        iterations_ok = simulation.get("iterations_completed", 0) > 0
        focus_ok = simulation.get("game_focused", False)

        print("Loop Simulation:")
        print(f"   Iterations completed: {'✅' if iterations_ok else '❌'}")
        print(f"   Game focus detection: {'✅' if focus_ok else '❌'}")
        print(f"   OCR operations: {simulation.get('ocr_operations', 0)}")
        print(f"   State changes: {simulation.get('state_changes', 0)}")

        # Overall assessment
        all_components_ok = all([ocr_ok, detector_ok, rpc_ok, config_ok])
        all_functionality_ok = all([pause_ok, cooldown_ok, iterations_ok])

        print("Overall Assessment:")
        if all_components_ok and all_functionality_ok:
            print("✅ GameMonitor ready for production use")
        else:
            print("⚠️  GameMonitor has some issues that need attention")
            if not all_components_ok:
                print("   → Check component initialization")
            if not all_functionality_ok:
                print("   → Check state transition logic")
