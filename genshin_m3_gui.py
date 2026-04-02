# ==========================================
# Genshin Impact Rich Presence GUI v4.0
# Material 3 UI using Slint
# ==========================================

import os
import sys
import threading
import time
import json

try:
    import psutil
    import pypresence as discord

    DEPENDENCIES_OK = True
except ImportError as e:
    print(f"Missing dependencies: {e}")
    DEPENDENCIES_OK = False

from slint import load_file, callback

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from core.datatypes import ActivityType, Activity


class Config:
    CONFIG_FILENAME = "gui_config.json"

    def __init__(self):
        self.USERNAME = "Player"
        self.MC_AETHER = True
        self.WANDERER_NAME = "Wanderer"
        self.GAME_RESOLUTION = 1080
        self.USE_GPU = True
        self.DISC_APP_ID = "944346292568596500"

    def load_from_file(self, filename=None):
        if filename is None:
            filename = self.CONFIG_FILENAME
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config_dict = json.load(f)
                    for key, value in config_dict.items():
                        if hasattr(self, key):
                            setattr(self, key, value)
                return True
            except Exception as e:
                print(f"Error loading config: {e}")
        return False


class GenshinM3Window:
    def __init__(self):
        self.config = Config()
        self.config.load_from_file()

        self.running = False
        self.rpc_running = False
        self.current_activity = Activity(ActivityType.LOADING, False)
        self.current_characters = [None, None, None, None]
        self.game_start_time = None
        self.rpc = None
        self.log_messages = []

        self._create_ui()

    def _log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_messages.append(f"[{timestamp}] {message}")
        if len(self.log_messages) > 30:
            self.log_messages = self.log_messages[-30:]

        if hasattr(self, "window"):
            self.window.log_text = "\n".join(self.log_messages)

    def _create_ui(self):
        self._log("Loading Material 3 UI...")

        try:
            components = load_file("genshin_m3_app.slint")
            self.window = components.GenshinM3App()

            self.window.set_game_status("Ready")
            self.window.set_current_character("None")
            self.window.set_current_location("Unknown")
            self.window.set_uptime("00:00:00")
            self.window.set_rpc_running(False)
            self.window.set_log_text("Ready to start...")

            self.window.start_rpc = self._start_rpc_handler
            self.window.stop_rpc = self._stop_rpc_handler

            self._log("Material 3 UI loaded!")
            self.window.run()

        except Exception as e:
            print(f"Error creating UI: {e}")
            import traceback

            traceback.print_exc()
            self._log(f"Error: {e}")

    def _start_rpc_handler(self):
        if self.running:
            return

        self.running = True
        self.game_start_time = time.time()

        self.window.set_rpc_running(True)
        self.window.set_game_status("Running")
        self._log("Rich Presence started!")

        self.rpc_thread = threading.Thread(target=self._rpc_loop, daemon=True)
        self.rpc_thread.start()

    def _stop_rpc_handler(self):
        self.running = False

        self.window.set_rpc_running(False)
        self.window.set_game_status("Stopped")
        self._log("Rich Presence stopped!")

        if self.rpc:
            try:
                self.rpc.close()
            except:
                pass

    def _rpc_loop(self):
        try:
            self.rpc = discord.Presence(self.config.DISC_APP_ID)
            self.rpc.connect()
            self._log("Connected to Discord!")
        except Exception as e:
            self._log(f"Discord error: {e}")
            self._stop_rpc_handler()
            return

        while self.running:
            try:
                state = (
                    self.current_activity.name if self.current_activity else "Loading"
                )

                character_names = [
                    c.name if c else "" for c in self.current_characters[:3]
                ]
                details = f"Party: {' | '.join([n for n in character_names if n]) or 'No characters'}"

                self.rpc.update(
                    state=state,
                    details=details,
                    large_image="menu_paimon",
                    large_text="Genshin Impact",
                    start_timestamp=self.game_start_time,
                )

                uptime = int(time.time() - self.game_start_time)
                hours, minutes, seconds = (
                    uptime // 3600,
                    (uptime % 3600) // 60,
                    uptime % 60,
                )
                self.window.set_uptime(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

                time.sleep(15)

            except Exception as e:
                self._log(f"RPC error: {e}")
                break

        try:
            if self.rpc:
                self.rpc.close()
        except:
            pass


def main():
    app = GenshinM3Window()


if __name__ == "__main__":
    main()
