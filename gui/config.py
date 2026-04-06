import os
import json


class Config:
    CONFIG_FILENAME = "gui_config.json"

    def __init__(self):
        self.USERNAME = "Player"
        self.MC_AETHER = True
        self.WANDERER_NAME = "Wanderer"
        self.GAME_RESOLUTION = 1080
        self.USE_GPU = True
        self.DISC_APP_ID = "944346292568596500"
        self.ACTIVE_CHARACTER_THRESH = 720
        self.NAME_CONF_THRESH = 0.6
        self.LOC_CONF_THRESH = 0.5
        self.BOSS_CONF_THRESH = 0.5
        self.DOMAIN_CONF_THRESH = 0.5
        self.SLEEP_PER_ITERATION = 0.14
        self.OCR_CHARNAMES_ONE_IN = 10
        self.OCR_LOC_ONE_IN = 5
        self.OCR_BOSS_ONE_IN = 30
        self.OCR_DOMAIN_ONE_IN = 30
        self.PAUSE_STATE_COOLDOWN = 2
        self.INACTIVE_COOLDOWN = 5
        self.ALLOWLIST = (
            "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789' -"
        )

    def update_coordinates(self, shared_data_file=None):
        adapted_coords = None

        if shared_data_file and os.path.exists(shared_data_file):
            try:
                with open(shared_data_file, "r") as f:
                    shared_data = json.load(f)
                if "adapted_coordinates" in shared_data:
                    adapted_coords = shared_data["adapted_coordinates"]
            except Exception as e:
                print(f"Error loading shared data file: {e}")

        BASE_HEIGHT = 1080
        scale = self.GAME_RESOLUTION / BASE_HEIGHT

        if adapted_coords:
            self.CHARACTER_NAME_COORDINATES = adapted_coords["ADAPTED_NAMES_4P_COORD"]
            self.CHARACTER_NUMBER_COORDINATES = adapted_coords[
                "ADAPTED_NUMBER_4P_COORD"
            ]

            if self.GAME_RESOLUTION == 1080:
                self.BOSS_COORDINATES = (943, 6, 1614, 66)
                self.LOCATION_COORDINATES = (702, 240, 1838, 345)
            else:
                self.BOSS_COORDINATES = (
                    int(943 * scale),
                    int(6 * scale),
                    int(1614 * scale),
                    int(66 * scale),
                )
                self.LOCATION_COORDINATES = (
                    int(702 * scale),
                    int(240 * scale),
                    int(1838 * scale),
                    int(345 * scale),
                )
        else:
            if self.GAME_RESOLUTION == 1080:
                self.CHARACTER_NUMBER_COORDINATES = [
                    (2484, 356),
                    (2484, 481),
                    (2484, 610),
                    (2484, 735),
                ]
                self.CHARACTER_NAME_COORDINATES = [
                    (2166, 320, 2365, 395),
                    (2166, 445, 2365, 520),
                    (2166, 575, 2365, 650),
                    (2166, 705, 2365, 780),
                ]
                self.BOSS_COORDINATES = (943, 6, 1614, 66)
                self.LOCATION_COORDINATES = (702, 240, 1838, 345)
            else:
                self.CHARACTER_NUMBER_COORDINATES = [
                    (int(2484 * scale), int(356 * scale)),
                    (int(2484 * scale), int(481 * scale)),
                    (int(2484 * scale), int(610 * scale)),
                    (int(2484 * scale), int(735 * scale)),
                ]
                self.CHARACTER_NAME_COORDINATES = [
                    (
                        int(2166 * scale),
                        int(320 * scale),
                        int(2365 * scale),
                        int(395 * scale),
                    ),
                    (
                        int(2166 * scale),
                        int(445 * scale),
                        int(2365 * scale),
                        int(520 * scale),
                    ),
                    (
                        int(2166 * scale),
                        int(575 * scale),
                        int(2365 * scale),
                        int(650 * scale),
                    ),
                    (
                        int(2166 * scale),
                        int(705 * scale),
                        int(2365 * scale),
                        int(780 * scale),
                    ),
                ]
                self.BOSS_COORDINATES = (
                    int(943 * scale),
                    int(6 * scale),
                    int(1614 * scale),
                    int(66 * scale),
                )
                self.LOCATION_COORDINATES = (
                    int(702 * scale),
                    int(240 * scale),
                    int(1838 * scale),
                    int(345 * scale),
                )

    def _get_config_path(self, filename: str = None) -> str:
        if filename is None:
            filename = self.CONFIG_FILENAME
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", filename)

    def save_to_file(self, filename: str = None):
        if filename is None:
            filename = self.CONFIG_FILENAME
        config_path = self._get_config_path(filename)
        config_dict = {
            key: value
            for key, value in self.__dict__.items()
            if not key.startswith("_") and not callable(value) and not key.isupper()
        }
        try:
            with open(config_path, "w") as f:
                json.dump(config_dict, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    def load_from_file(self, filename: str = None):
        if filename is None:
            filename = self.CONFIG_FILENAME
        config_path = self._get_config_path(filename)
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config_dict = json.load(f)
                    for key, value in config_dict.items():
                        if hasattr(self, key):
                            setattr(self, key, value)
                self.update_coordinates()
                return True
            except Exception as e:
                print(f"Error loading config: {e}")
        return False

    def _load_shared_config(self):
        shared_config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "shared_config.json"
        )
        if os.path.exists(shared_config_path):
            try:
                with open(shared_config_path, "r") as f:
                    shared_config = json.load(f)
                    for key in [
                        "USERNAME",
                        "MC_AETHER",
                        "WANDERER_NAME",
                        "GAME_RESOLUTION",
                        "USE_GPU",
                    ]:
                        if key in shared_config:
                            setattr(self, key, shared_config[key])
                return True
            except Exception as e:
                print(f"Error loading shared config: {e}")
        return False
