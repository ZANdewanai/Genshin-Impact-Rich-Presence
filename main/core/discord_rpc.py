"""
Discord Rich Presence management module.

Handles Discord RPC connection, updates, and state management.
"""

import time
import threading
from typing import Optional, Dict, Any
from asyncio import new_event_loop, set_event_loop

import pypresence as discord
from .datatypes import Activity, ActivityType


class DiscordRPCManager:
    """
    Manages Discord Rich Presence connection and updates for Genshin Impact.
    """

    def __init__(self, app_id: str = "944346292568596500"):
        """
        Initialize Discord RPC manager.

        Args:
            app_id: Discord application ID
        """
        self.app_id = app_id
        self.rpc: Optional[discord.Presence] = None
        self.event_loop = new_event_loop()
        self.update_thread: Optional[threading.Thread] = None
        self.running = False

        # Current state
        self.current_activity: Activity = Activity(ActivityType.LOADING, False)
        self.current_characters = [None, None, None, None]
        self.current_active_character = 0
        self.game_start_time: Optional[int] = None

        # Previous update for comparison
        self.previous_update: Optional[Dict[str, Any]] = None

    def start(self):
        """Start the Discord RPC update thread."""
        if self.update_thread is None or not self.update_thread.is_alive():
            self.running = True
            self.update_thread = threading.Thread(
                daemon=True,
                target=self._discord_rpc_loop
            )
            self.update_thread.start()

    def stop(self):
        """Stop the Discord RPC update thread and close connection."""
        self.running = False
        if self.rpc is not None:
            try:
                self.rpc.close()
            except Exception:
                pass  # Ignore errors during shutdown

    def update_activity(self, activity: Activity, characters: list,
                       active_character: int, game_start_time: Optional[int]):
        """
        Update the current activity state.

        Args:
            activity: Current game activity
            characters: Current party characters
            active_character: Currently active character (1-indexed)
            game_start_time: Game start timestamp
        """
        self.current_activity = activity
        self.current_characters = characters
        self.current_active_character = active_character
        self.game_start_time = game_start_time

    def _init_discord_rpc(self):
        """Initialize Discord RPC connection."""
        printed_wait = False
        while self.running:
            try:
                self.rpc = discord.Presence(self.app_id)
                self.rpc.connect()
                print("Connected to Discord Client!")
                return
            except discord.exceptions.DiscordNotFound:
                if not printed_wait:
                    printed_wait = True
                    print("Waiting for discord to start...")
                time.sleep(2.5)
            except Exception as e:
                print("Unknown error while attempting to initialize discord RPC:")
                print(e)
                time.sleep(2.5)

    def _create_update_params(self) -> Dict[str, Any]:
        """Create Discord update parameters from current activity."""
        params = self.current_activity.to_update_params_dict()

        # Add start time based on activity type
        if self.current_activity.activity_type in [
            ActivityType.LOADING,
            ActivityType.COMMISSION,
            ActivityType.LOCATION,
        ]:
            params["start"] = self.game_start_time
        else:
            params["start"] = self.current_activity.start_time

        # Add party information to state field
        party_members = [c.character_display_name for c in self.current_characters
                        if c is not None]
        if party_members:
            party_str = ", ".join(party_members)
            if "state" in params and params["state"]:
                params["state"] += f" | Party: {party_str}"
            else:
                params["state"] = f"Party: {party_str}"

        # Add active character information
        if self.current_active_character != 0:
            c = self.current_characters[self.current_active_character - 1]
            if c is not None:
                params["small_image"] = c.image_key
                params["small_text"] = f"playing {c.character_display_name}"

        return params

    def _discord_rpc_loop(self):
        """Main Discord RPC update loop."""
        set_event_loop(self.event_loop)

        while self.running:
            if self.rpc is None:
                self._init_discord_rpc()

            if not self.running:
                break

            try:
                params = self._create_update_params()

                if self.previous_update != params:
                    self.rpc.update(**params)
                    self.previous_update = params
                    time.sleep(5)  # Rate limit: 5 updates / 20 seconds
                else:
                    time.sleep(1)  # Faster check when no update needed

            except discord.exceptions.InvalidID:
                # Discord closed, reset connection
                self.rpc.close()
                self.rpc = None
                continue
            except Exception as e:
                print("Error updating Discord RPC:")
                print(e)
                time.sleep(1)

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()

    def debug_connection_test(self) -> dict:
        """
        Debug method to test Discord connection.

        Returns:
            Dictionary with connection test results
        """
        print(f"\n{'='*50}")
        print("DISCORD RPC DEBUG - CONNECTION TEST")
        print(f"{'='*50}")

        results = {
            "connection_successful": False,
            "connection_time": 0,
            "error": None
        }

        try:
            print("1. Testing Discord RPC connection...")
            start_time = time.time()

            # Try to initialize connection
            self._init_discord_rpc()

            connection_time = time.time() - start_time
            results["connection_time"] = connection_time

            if self.rpc is not None:
                print(f"   ✅ Connected successfully in {connection_time:.2f}s")
                results["connection_successful"] = True
            else:
                print(f"   ❌ Connection failed after {connection_time:.2f}s")
                results["error"] = "Connection timeout or Discord not running"

        except Exception as e:
            print(f"   ❌ Error during connection: {e}")
            results["error"] = str(e)

        return results

    def debug_activity_update_test(self, test_activities: list = None) -> dict:
        """
        Debug method to test activity updates.

        Args:
            test_activities: List of activities to test (optional)

        Returns:
            Dictionary with update test results
        """
        print(f"\n{'='*50}")
        print("DISCORD RPC DEBUG - ACTIVITY UPDATE TEST")
        print(f"{'='*50}")

        if test_activities is None:
            # Create default test activities
            from datatypes import Location, Boss, Domain, GameMenu
            test_activities = [
                Activity(ActivityType.LOADING, False),
                Activity(ActivityType.LOCATION, Location("Mondstadt", "mondstadt", 0.95)),
                Activity(ActivityType.WORLD_BOSS, Boss("Stormterror", "stormterror", 0.90)),
                Activity(ActivityType.DOMAIN, Domain("Temple of the Wolf", "temple of the wolf", 0.85)),
            ]

        results = {}

        for i, activity in enumerate(test_activities):
            print(f"\n{i+1}. Testing activity: {activity.activity_type.name}")

            try:
                # Update with test data
                test_characters = []  # Empty for simplicity
                test_active_char = 0
                test_start_time = time.time()

                self.update_activity(activity, test_characters, test_active_char, test_start_time)

                # Generate update parameters
                params = self._create_update_params()

                print(f"   Activity type: {activity.activity_type}")
                print(f"   Activity data: {activity.activity_data}")
                print(f"   Update params: {list(params.keys())}")

                # Show key parameters
                if "details" in params:
                    print(f"   Details: '{params['details']}'")
                if "state" in params:
                    print(f"   State: '{params['state']}'")

                results[activity.activity_type.name] = {
                    "success": True,
                    "params": params
                }

                # Brief pause between tests
                time.sleep(1)

            except Exception as e:
                print(f"   ❌ Error: {e}")
                results[activity.activity_type.name] = {
                    "success": False,
                    "error": str(e)
                }

        return results

    def debug_rate_limiting_test(self, test_updates: int = 10) -> dict:
        """
        Debug method to test rate limiting behavior.

        Args:
            test_updates: Number of rapid updates to test

        Returns:
            Dictionary with rate limiting test results
        """
        print(f"\n{'='*50}")
        print(f"DISCORD RPC DEBUG - RATE LIMITING TEST ({test_updates} updates)")
        print(f"{'='*50}")

        results = {
            "updates_sent": 0,
            "updates_skipped": 0,
            "total_time": 0,
            "rate_limiting_works": False
        }

        try:
            # Create a test activity
            from datatypes import Location
            test_activity = Activity(ActivityType.LOCATION, Location("Test Location", "test", 0.8))

            print("1. Testing rapid updates (should be rate limited)...")
            start_time = time.time()

            for i in range(test_updates):
                # Update activity
                self.update_activity(test_activity, [], 0, time.time())

                # Check if update was sent (compare with previous)
                current_params = self._create_update_params()
                was_sent = current_params != self.previous_update

                if was_sent:
                    results["updates_sent"] += 1
                    print(f"   Update {i+1}: ✅ Sent")
                else:
                    results["updates_skipped"] += 1
                    print(f"   Update {i+1}: ⏸️  Skipped (rate limited)")

                # Small delay between updates
                time.sleep(0.5)

            results["total_time"] = time.time() - start_time

            # Analyze results
            success_rate = results["updates_sent"] / test_updates
            print(f"\nRate Limiting Analysis:")
            print(f"   Updates sent: {results['updates_sent']}")
            print(f"   Updates skipped: {results['updates_skipped']}")
            print(f"   Total time: {results['total_time']:.2f}s")
            print(f"   Success rate: {success_rate*100:.1f}%")

            # Rate limiting is working if we didn't send all updates rapidly
            results["rate_limiting_works"] = results["updates_skipped"] > 0

            if results["rate_limiting_works"]:
                print("   ✅ Rate limiting working correctly")
            else:
                print("   ⚠️  Rate limiting may not be working")

        except Exception as e:
            print(f"   ❌ Error during rate limiting test: {e}")
            results["error"] = str(e)

        return results

    def debug_comprehensive_test(self) -> dict:
        """
        Debug method to run comprehensive Discord RPC tests.

        Returns:
            Dictionary with all test results
        """
        print("Starting comprehensive Discord RPC debug test...")

        results = {}

        # Test connection
        results["connection"] = self.debug_connection_test()

        if results["connection"]["connection_successful"]:
            # Test activity updates
            results["activity_updates"] = self.debug_activity_update_test()

            # Test rate limiting
            results["rate_limiting"] = self.debug_rate_limiting_test()

            # Summary
            self._print_rpc_debug_summary(results)
        else:
            print("\n⚠️  Skipping update tests (Discord not connected)")
            print("   Make sure Discord is running to test full functionality")

        return results

    def _print_rpc_debug_summary(self, results: dict):
        """Print a summary of Discord RPC debug results."""
        print(f"\n{'='*50}")
        print("DISCORD RPC DEBUG SUMMARY")
        print(f"{'='*50}")

        # Connection status
        connection = results.get("connection", {})
        if connection.get("connection_successful"):
            print("✅ Discord connection: SUCCESSFUL")
        else:
            print("❌ Discord connection: FAILED")
            print(f"   Error: {connection.get('error', 'Unknown')}")

        # Activity updates
        if "activity_updates" in results:
            activity_results = results["activity_updates"]
            success_count = sum(1 for r in activity_results.values() if r.get("success", False))
            total_activities = len(activity_results)
            print(f"Activity updates: {success_count}/{total_activities} successful")

        # Rate limiting
        if "rate_limiting" in results:
            rate_results = results["rate_limiting"]
            rate_works = rate_results.get("rate_limiting_works", False)
            print(f"Rate limiting: {'✅ Working' if rate_works else '❌ Not working'}")

        # Overall assessment
        print("Overall Assessment:")
        if connection.get("connection_successful"):
            print("✅ Discord RPC ready for production use")
        else:
            print("⚠️  Discord RPC connection issues detected")
            print("⚠️  Install and run Discord to test full functionality")
