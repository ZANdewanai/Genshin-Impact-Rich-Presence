# ==========================================
# Genshin Impact Rich Presence GUI v3.0 INDEV
# Advanced GUI wrapper with comprehensive settings - PyQt5 Version
# ==========================================

import os
import sys
import threading
import time
import json
import subprocess
from pathlib import Path

# Third-party imports
try:
    from PyQt5.QtWidgets import (
        QApplication,
        QMainWindow,
        QWidget,
        QVBoxLayout,
        QHBoxLayout,
        QLabel,
        QPushButton,
        QTextEdit,
        QTabWidget,
        QFrame,
        QSplitter,
        QProgressBar,
        QCheckBox,
        QLineEdit,
        QComboBox,
        QSizePolicy,
        QGroupBox,
        QFormLayout,
        QGridLayout,
        QMessageBox,
        QListWidget,
        QStatusBar,
        QMenuBar,
        QToolBar,
        QAction,
        QSystemTrayIcon,
    )
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QRect, QSize, QPoint, QUrl
    from PyQt5.QtGui import (
        QFont,
        QPixmap,
        QIcon,
        QImage,
        QPalette,
        QColor,
        QDesktopServices,
    )

    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("Warning: PyQt5 not available. GUI features will be disabled.")

try:
    import numpy as np
    import psutil
    import pypresence as discord
    import win32gui
    import win32con
    import win32process
    from PIL import Image, ImageGrab
    import urllib.request

    DEPENDENCIES_OK = True
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Please install required packages:")
    print("pip install numpy psutil pypresence pywin32 pillow")
    DEPENDENCIES_OK = False

# Typing imports
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum, auto

# Import data types from main module to avoid duplication
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from core.datatypes import ActivityType, Activity, Character, Location

# ==========================================
# Default Configuration
# ==========================================


class Config:
    """Configuration class for the GUI"""

    CONFIG_FILENAME = "gui_config.json"  # Self-contained config file

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

        # Update coordinates based on resolution - defer until GUI is initialized
        # self.update_coordinates()  # Moved to after shared_data_file is set

    def update_coordinates(self, shared_data_file=None):
        """Update screen coordinates based on resolution or use adapted coordinates from main.py

        This method first tries to load adapted coordinates from gui_shared_data.json.
        If no adapted coordinates are found, it falls back to calculating coordinates based on resolution.
        """
        # Try to load adapted coordinates from shared data file first
        adapted_coords = None

        if shared_data_file and os.path.exists(shared_data_file):
            try:
                with open(shared_data_file, "r") as f:
                    shared_data = json.load(f)

                # Check if adapted coordinates are available
                if "adapted_coordinates" in shared_data:
                    adapted_coords = shared_data["adapted_coordinates"]
                    if (
                        "ADAPTED_NAMES_4P_COORD" in adapted_coords
                        and "ADAPTED_NUMBER_4P_COORD" in adapted_coords
                    ):
                        print(f"📍 Using adapted coordinates from shared data file")
                    else:
                        print(
                            f"📍 No adapted coordinates found in shared data file, using calculated coordinates"
                        )
                else:
                    print(
                        f"📍 No adapted coordinates section in shared data file, using calculated coordinates"
                    )
            except Exception as e:
                print(
                    f"📍 Error loading shared data file: {e}, using calculated coordinates"
                )

        # Base resolution (1080p)
        BASE_HEIGHT = 1080
        scale = self.GAME_RESOLUTION / BASE_HEIGHT

        if adapted_coords:
            # Use adapted coordinates from main.py
            self.CHARACTER_NAME_COORDINATES = adapted_coords["ADAPTED_NAMES_4P_COORD"]
            self.CHARACTER_NUMBER_COORDINATES = adapted_coords[
                "ADAPTED_NUMBER_4P_COORD"
            ]

            # For other coordinates, still use calculated values since they're not adapted
            # Define base coordinates for 1080p
            if self.GAME_RESOLUTION == 1080:
                self.BOSS_COORDINATES = (943, 6, 1614, 66)
                self.LOCATION_COORDINATES = (702, 240, 1838, 345)
            else:
                # Scale other coordinates for different resolutions
                self.BOSS_COORDINATES = (
                    int(943 * scale),  # x1
                    int(6 * scale),  # y1
                    int(1614 * scale),  # x2
                    int(66 * scale),  # y2
                )
                self.LOCATION_COORDINATES = (
                    int(702 * scale),  # x1
                    int(240 * scale),  # y1
                    int(1838 * scale),  # x2
                    int(345 * scale),  # y2
                )
        else:
            # Use original calculated coordinates
            # Define base coordinates for 1080p
            if self.GAME_RESOLUTION == 1080:
                # 1080p coordinates (base)
                self.CHARACTER_NUMBER_COORDINATES = [
                    (2484, 356),  # Char 1
                    (2484, 481),  # Char 2
                    (2484, 610),  # Char 3
                    (2484, 735),  # Char 4
                ]

                self.CHARACTER_NAME_COORDINATES = [
                    (2166, 320, 2365, 395),  # Char 1
                    (2166, 445, 2365, 520),  # Char 2
                    (2166, 575, 2365, 650),  # Char 3
                    (2166, 705, 2365, 780),  # Char 4
                ]

                self.BOSS_COORDINATES = (943, 6, 1614, 66)
                self.LOCATION_COORDINATES = (702, 240, 1838, 345)

            else:
                # For other resolutions, scale from 1080p coordinates
                # Character number coordinates (for active character detection)
                self.CHARACTER_NUMBER_COORDINATES = [
                    (int(2484 * scale), int(356 * scale)),  # Char 1
                    (int(2484 * scale), int(481 * scale)),  # Char 2
                    (int(2484 * scale), int(610 * scale)),  # Char 3
                    (int(2484 * scale), int(735 * scale)),  # Char 4
                ]

                # Character name coordinates
                self.CHARACTER_NAME_COORDINATES = [
                    (
                        int(2166 * scale),  # x1
                        int(320 * scale),  # y1
                        int(2365 * scale),  # x2
                        int(395 * scale),  # y2
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

                # Other UI element coordinates
                self.BOSS_COORDINATES = (
                    int(943 * scale),  # x1
                    int(6 * scale),  # y1
                    int(1614 * scale),  # x2
                    int(66 * scale),  # y2
                )

                self.LOCATION_COORDINATES = (
                    int(702 * scale),  # x1
                    int(240 * scale),  # y1
                    int(1838 * scale),  # x2
                    int(345 * scale),  # y2
                )

        # Log the current resolution and scale factor
        print(f"Resolution set to: {self.GAME_RESOLUTION}p (Scale factor: {scale:.2f})")

        # Log coordinate source
        if adapted_coords:
            print("📍 Using ADAPTED coordinates from main.py:")
            print(f"   Character names: {self.CHARACTER_NAME_COORDINATES}")
            print(f"   Character numbers: {self.CHARACTER_NUMBER_COORDINATES}")
        else:
            print("📍 Using CALCULATED coordinates based on resolution")

    def _get_config_path(self, filename: str = None) -> str:
        """Get the full path to the config file in the project directory"""
        if filename is None:
            filename = self.CONFIG_FILENAME
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

    def save_to_file(self, filename: str = None):
        """Save current configuration to a JSON file in the project directory"""
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
        """Load configuration from a JSON file in the project directory"""
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
        """Load configuration from current directory shared_config.json (used by main.py)"""
        shared_config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "shared_config.json"
        )
        if os.path.exists(shared_config_path):
            try:
                with open(shared_config_path, "r") as f:
                    shared_config = json.load(f)
                    # Update config with shared config values (these take precedence)
                    for key in [
                        "USERNAME",
                        "MC_AETHER",
                        "WANDERER_NAME",
                        "GAME_RESOLUTION",
                        "USE_GPU",
                    ]:
                        if key in shared_config:
                            setattr(self, key, shared_config[key])
                            print(
                                f"Loaded {key} from shared config: {shared_config[key]}"
                            )
                return True
            except Exception as e:
                print(f"Error loading shared config: {e}")
        return False


# ==========================================
# Main Application
# ==========================================


class GenshinRichPresenceApp(QMainWindow):
    def __init__(self):
        if not PYQT_AVAILABLE:
            print("Running in text-based mode due to missing PyQt5.")
            self._run_text_based_mode()
            return

        super().__init__()

        # Initialize configuration
        self.config = Config()
        self.config.load_from_file()  # Now loads from project directory gui_config.json
        self.config._load_shared_config()  # Load from current directory shared_config.json

        # Initialize app state
        self.running = False
        self.rpc_running = False  # Flag to control RPC thread
        self.current_activity = Activity(ActivityType.LOADING, False)
        self.current_active_character = 0
        self.current_characters = [None, None, None, None]
        self.prev_non_idle_activity = Activity(ActivityType.LOADING, False)
        self.prev_location = None
        self.game_start_time = None
        self.reader = None
        self.rpc = None
        self.rpc_thread = None
        self.ocr_thread = None  # Initialize ocr_thread as None
        self.main_process = None  # Process for main.py
        self.log_file_path = "rich_presence.log"  # Log file for main.py output
        self.last_log_position = 0  # Track where we last read in the log file
        self.dependencies_checked = (
            True  # Assume dependencies are OK since we're not checking
        )

        # Initialize shared data file path
        self.shared_data_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "gui_shared_data.json"
        )

        # Shared data for RPC thread (updated by monitoring thread)
        self.latest_rpc_data = None

        # Image cache for downloaded images
        self.image_cache = {}

        # Start a timer to periodically check for coordinate updates
        self.coordinate_update_timer = QTimer()
        self.coordinate_update_timer.timeout.connect(self._check_for_coordinate_updates)
        self.coordinate_update_timer.start(5000)  # Check every 5 seconds

        # Now that shared_data_file is set, update coordinates
        self.config.update_coordinates(self.shared_data_file)

        # Create tab widgets first
        self.main_tab = QWidget()
        self.config_tab = QWidget()
        self.roster_tab = QWidget()
        self.about_tab = QWidget()

        # Create tab widget
        self.tab_widget = QTabWidget()

        # Setup UI
        self.setWindowTitle("Genshin Impact Rich Presence v3.0 INDEV")
        self.setGeometry(100, 100, 900, 700)
        self.setWindowIcon(QIcon("images/ApplicatonIcon.ico"))

        # Create main layout and central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_content_layout = QVBoxLayout(self.central_widget)

        # Load external stylesheet
        self._load_stylesheet()
        # Create main content area with sidebar and tab widget
        main_content = QWidget()
        main_content_layout_inner = QHBoxLayout(main_content)

        # Create sidebar
        self._create_sidebar()

        # Add sidebar and tab widget to main layout
        main_content_layout_inner.addWidget(self.sidebar_widget, 0)
        main_content_layout_inner.addWidget(self.tab_widget, 1)

        # Add stretch to push everything to the top
        main_content_layout_inner.setStretchFactor(self.sidebar_widget, 0)
        main_content_layout_inner.setStretchFactor(self.tab_widget, 1)

        main_content_layout.addWidget(main_content)

        # Setup tab contents and add tabs to tab widget
        self._setup_main_tab()
        self._setup_config_tab()
        self._setup_roster_tab()
        self._setup_about_tab()

        # Add tabs to tab widget
        self.tab_widget.addTab(self.main_tab, "Main")
        self.tab_widget.addTab(self.config_tab, "Configuration")
        self.tab_widget.addTab(self.roster_tab, "Character Roster")
        self.tab_widget.addTab(self.about_tab, "About")

    # Remove text-based mode code as PyQt5 is available
    # def _run_text_based_mode(self): ... (removed)
    # def _start_text_display(self): ... (removed)

    def _load_stylesheet(self):
        """Load external stylesheet file"""
        try:
            stylesheet_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "resources", "styles.qss"
            )
            if os.path.exists(stylesheet_path):
                with open(stylesheet_path, "r") as f:
                    stylesheet = f.read()
                self.setStyleSheet(stylesheet)
                self._log("✅ External stylesheet loaded successfully")
            else:
                self._log("⚠️ Stylesheet file not found, using default styling")
        except Exception as e:
            self._log(f"❌ Error loading stylesheet: {e}")

    def _run_non_gui_mode(self):
        """Legacy method - no longer used, subprocess is handled by _start_main_subprocess"""
        pass

    def _create_sidebar(self):
        """Create the sidebar with app controls"""
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setObjectName("sidebar_widget")
        self.sidebar_widget.setFixedWidth(200)

        sidebar_layout = QVBoxLayout(self.sidebar_widget)

        # Logo and title
        logo_label = QLabel("Genshin Impact\nRich Presence")
        logo_label.setFont(QFont("Arial", 16, QFont.Bold))
        logo_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(logo_label)

        # Spacer
        sidebar_layout.addStretch()

        # Start/Stop button
        self.start_button = QPushButton("Start Rich Presence")
        self.start_button.setObjectName("start_button")
        self.start_button.setFont(QFont("Arial", 10, QFont.Bold))
        self.start_button.clicked.connect(self.toggle_rpc)
        sidebar_layout.addWidget(self.start_button)

        # Status indicator
        self.status_label = QLabel("Status: Stopped")
        self.status_label.setObjectName("status_label")
        self.status_label.setFont(QFont("Arial", 9, QFont.Bold))
        self.status_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(self.status_label)

        # Current activity
        self.activity_label = QLabel("Activity: Not running")
        self.activity_label.setObjectName("activity_label")
        self.activity_label.setFont(QFont("Arial", 8))
        self.activity_label.setWordWrap(True)
        self.activity_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(self.activity_label)

        # Spacer
        sidebar_layout.addStretch()

        # Version info
        version_label = QLabel("v2.6")
        version_label.setObjectName("version_label")
        version_label.setFont(QFont("Arial", 10))
        version_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(version_label)

    def _setup_main_tab(self):
        """Setup the main tab with status information"""
        main_layout = QVBoxLayout(self.main_tab)

        # Title
        title_label = QLabel("Genshin Impact Rich Presence")
        title_label.setObjectName("main_tab")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        main_layout.addWidget(title_label)

        # Status frame
        status_frame = QFrame()
        status_frame.setObjectName("status_frame")
        status_frame.setFrameStyle(QFrame.Box)
        status_layout = QGridLayout(status_frame)

        # Status info with images
        status_items = [
            ("Game Status:", "Not running"),
            ("Current Character:", "None"),
            ("Current Location:", "Unknown"),
            ("Current Activity:", "None"),
            ("Uptime:", "00:00:00"),
        ]

        for i, (label, value) in enumerate(status_items):
            # Image placeholder (will be updated dynamically)
            img_label = QLabel("")
            img_label.setFixedSize(32, 32)
            img_label.setObjectName(
                f"status_img_{label.lower().replace(' ', '_').replace(':', '')}"
            )
            status_layout.addWidget(img_label, i, 0)

            # Label
            lbl = QLabel(label)
            lbl.setFont(QFont("Arial", 10, QFont.Bold))
            status_layout.addWidget(lbl, i, 1)

            # Value
            value_label = QLabel(value)
            value_label.setFont(QFont("Arial", 9))
            value_label.setObjectName(
                f"status_{label.lower().replace(' ', '_').replace(':', '')}"
            )
            status_layout.addWidget(value_label, i, 2)

            # Store references for updating
            setattr(
                self,
                f"status_img_{label.lower().replace(' ', '_').replace(':', '')}",
                img_label,
            )
            setattr(
                self,
                f"status_{label.lower().replace(' ', '_').replace(':', '')}",
                value_label,
            )

        status_layout.setColumnStretch(2, 1)
        main_layout.addWidget(status_frame)

        log_label = QLabel("Activity Log:")
        log_label.setObjectName("log_label")
        log_label.setFont(QFont("Arial", 12, QFont.Bold))
        main_layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setObjectName("log_text")
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        main_layout.addWidget(self.log_text)

        main_layout.addStretch()

    def _setup_config_tab(self):
        """Setup the configuration tab"""
        config_layout = QVBoxLayout(self.config_tab)

        # Title
        title_label = QLabel("Configuration")
        title_label.setObjectName("config_title_label")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        config_layout.addWidget(title_label)

        # Create main config frame
        config_frame = QFrame()
        config_frame.setObjectName("config_frame")
        config_frame.setFrameStyle(QFrame.Box)
        config_main_layout = QHBoxLayout(config_frame)

        # User settings frame (left side)
        user_frame = QFrame()
        user_frame.setObjectName("user_frame")
        user_layout = QVBoxLayout(user_frame)

        user_label = QLabel("User Settings")
        user_label.setObjectName("user_label")
        user_label.setFont(QFont("Arial", 14, QFont.Bold))
        user_layout.addWidget(user_label)

        # Username
        username_layout = QHBoxLayout()
        username_label = QLabel("Username:")
        username_label.setObjectName("username_label")
        username_label.setFont(QFont("Arial", 10))
        username_layout.addWidget(username_label)

        self.username_entry = QLineEdit(self.config.USERNAME)
        self.username_entry.setObjectName("username_entry")
        username_layout.addWidget(self.username_entry)
        user_layout.addLayout(username_layout)

        # Main character selection
        mc_layout = QHBoxLayout()
        mc_label = QLabel("Main Character:")
        mc_label.setObjectName("mc_label")
        mc_label.setFont(QFont("Arial", 10))
        mc_layout.addWidget(mc_label)

        self.mc_combo = QComboBox()
        self.mc_combo.setObjectName("mc_combo")
        self.mc_combo.addItems(["Aether (Male)", "Lumine (Female)"])
        self.mc_combo.setCurrentText(
            "Aether (Male)" if self.config.MC_AETHER else "Lumine (Female)"
        )
        mc_layout.addWidget(self.mc_combo)
        user_layout.addLayout(mc_layout)

        # Wanderer name
        wanderer_layout = QHBoxLayout()
        wanderer_label = QLabel("Wanderer Name:")
        wanderer_label.setObjectName("wanderer_label")
        wanderer_label.setFont(QFont("Arial", 10))
        wanderer_layout.addWidget(wanderer_label)

        self.wanderer_entry = QLineEdit(self.config.WANDERER_NAME)
        self.wanderer_entry.setObjectName("wanderer_entry")
        wanderer_layout.addWidget(self.wanderer_entry)
        user_layout.addLayout(wanderer_layout)

        config_main_layout.addWidget(user_frame, 1)

        # Performance settings frame (right side)
        perf_frame = QFrame()
        perf_frame.setObjectName("perf_frame")
        perf_layout = QVBoxLayout(perf_frame)

        perf_label = QLabel("Performance Settings")
        perf_label.setObjectName("perf_label")
        perf_label.setFont(QFont("Arial", 14, QFont.Bold))
        perf_layout.addWidget(perf_label)

        # GPU acceleration toggle
        self.gpu_checkbox = QCheckBox("Enable GPU acceleration for OCR")
        self.gpu_checkbox.setObjectName("gpu_checkbox")
        self.gpu_checkbox.setChecked(self.config.USE_GPU)
        self.gpu_checkbox.setFont(QFont("Arial", 10))
        perf_layout.addWidget(self.gpu_checkbox)

        perf_layout.addStretch()
        config_main_layout.addWidget(perf_frame, 1)

        config_layout.addWidget(config_frame)

        # Status label for save feedback
        self.config_status_label = QLabel("")
        self.config_status_label.setObjectName("config_status_label")
        self.config_status_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.config_status_label.setAlignment(Qt.AlignCenter)
        self.config_status_label.setVisible(False)
        config_layout.addWidget(self.config_status_label)

        # Save button
        save_button = QPushButton("Save Settings")
        save_button.setObjectName("config_save_button")
        save_button.setFont(QFont("Arial", 12, QFont.Bold))
        save_button.clicked.connect(self._save_config)
        config_layout.addWidget(save_button)

        config_layout.addStretch()

    def _setup_roster_tab(self):
        """Setup the roster tab for character image management"""
        roaster_layout = QVBoxLayout(self.roster_tab)

        # Title
        title_label = QLabel("Character Roster")
        title_label.setObjectName("roaster_title_label")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        roaster_layout.addWidget(title_label)

        # Create main roaster frame
        roaster_frame = QFrame()
        roaster_frame.setObjectName("roaster_frame")
        roaster_frame.setFrameStyle(QFrame.Box)
        roaster_main_layout = QVBoxLayout(roaster_frame)

        # Load current character images from shared config
        character_images = {}
        try:
            shared_config_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "shared_config.json"
            )
            if os.path.exists(shared_config_path):
                with open(shared_config_path, "r") as f:
                    shared_config = json.load(f)
                    character_images = shared_config.get("CHARACTER_IMAGES", {})
        except Exception as e:
            # Non-critical error - config file might not exist yet, use defaults
            self._log(f"⚠️ Could not load character images from config: {e}")

        # Character image mapping widget
        self.character_images_widget = QWidget()
        self.character_images_widget.setObjectName("character_images_widget")
        char_images_layout = QVBoxLayout(self.character_images_widget)

        # Instructions
        instructions = QLabel(
            "Configure custom image keys for Genshin characters.\nUse this for alternate skins, Fatui versions, or other variants.\nTraveler gender is configured in 'Main Character' above."
        )
        instructions.setObjectName("instructions")
        instructions.setFont(QFont("Arial", 9))
        instructions.setWordWrap(True)
        char_images_layout.addWidget(instructions)

        # Character image entries
        self.char_image_entries = {}

        # Common characters that users might want to customize
        # These are actual characters from the Genshin roster that can have variants
        common_characters = ["Aether", "Lumine", "Wanderer", "Diluc", "Kaeya", "Amber"]

        for char_name in common_characters:
            char_layout = QHBoxLayout()

            char_label = QLabel(f"{char_name}:")
            char_label.setObjectName("char_label")
            char_label.setFont(QFont("Arial", 9))
            char_layout.addWidget(char_label)

            char_entry = QLineEdit(character_images.get(char_name, ""))
            char_entry.setPlaceholderText("e.g., char_traveler_fatui")
            char_layout.addWidget(char_entry)

            self.char_image_entries[char_name] = char_entry
            char_images_layout.addLayout(char_layout)

        # Add stretch and button to add more characters
        char_images_layout.addStretch()

        add_char_btn = QPushButton("Add Character")
        add_char_btn.setObjectName("add_char_btn")
        add_char_btn.setFont(QFont("Arial", 8))
        add_char_btn.clicked.connect(self._add_character_image_entry)
        char_images_layout.addWidget(add_char_btn)

        roaster_main_layout.addWidget(self.character_images_widget)

        roaster_layout.addWidget(roaster_frame)

        # Status label for save feedback
        self.roster_status_label = QLabel("")
        self.roster_status_label.setObjectName("roaster_status_label")
        self.roster_status_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.roster_status_label.setAlignment(Qt.AlignCenter)
        self.roster_status_label.setVisible(False)
        roaster_layout.addWidget(self.roster_status_label)

        # Save button
        save_button = QPushButton("Save Character Settings")
        save_button.setObjectName("roaster_save_button")
        save_button.setFont(QFont("Arial", 12, QFont.Bold))
        save_button.clicked.connect(self._save_roster_config)
        roaster_layout.addWidget(save_button)

        roaster_layout.addStretch()

    def _setup_about_tab(self):
        """Setup the about tab"""
        about_layout = QVBoxLayout(self.about_tab)

        # Title
        title_label = QLabel("About Genshin Impact Rich Presence")
        title_label.setObjectName("about_title_label")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        about_layout.addWidget(title_label)

        # Info text
        info_text = """Genshin Impact Rich Presence v3.0 INDEV

This application displays your current in-game activity on Discord.

Features:
• Shows your current character and location
• Detects when you're in domains or fighting bosses
• Works with any resolution
• Lightweight and easy to use

Created by ZANdewanai
Rewritten by euwbah
then Rewritten again by ZANdewanai

Image assets are intellectual property of HoYoverse
All rights reserved by miHoYo"""

        info_label = QLabel(info_text)
        info_label.setObjectName("info_label")
        info_label.setFont(QFont("Arial", 10))
        info_label.setWordWrap(True)
        about_layout.addWidget(info_label)

        about_layout.addStretch()

    def _save_config(self):
        """Save configuration from UI to config object"""
        self.config.USERNAME = self.username_entry.text()
        self.config.MC_AETHER = self.mc_combo.currentText().startswith("Aether")
        self.config.WANDERER_NAME = self.wanderer_entry.text()
        self.config.USE_GPU = self.gpu_checkbox.isChecked()

        # Collect character image mappings
        character_images = {}
        for char_name, entry in self.char_image_entries.items():
            image_key = entry.text().strip()
            if image_key:  # Only include non-empty entries
                character_images[char_name] = image_key

        # Show saving status
        self._show_config_status("💾 Saving settings...", "#f39c12", True)

        # Save to file
        if self.config.save_to_file():
            self._show_config_status("✅ Settings saved successfully!", "#2ecc71", True)
            self._log("Configuration saved successfully!")
        else:
            self._show_config_status(
                "❌ Error: Could not save configuration. Check permissions.",
                "#e74c3c",
                True,
            )
            self._log("Error: Could not save configuration. Check permissions.")
            # Try to save to current directory as fallback
            try:
                with open("config.json", "w") as f:
                    json.dump(
                        {
                            "USERNAME": self.config.USERNAME,
                            "MC_AETHER": self.config.MC_AETHER,
                            "WANDERER_NAME": self.config.WANDERER_NAME,
                            "GAME_RESOLUTION": self.config.GAME_RESOLUTION,
                            "USE_GPU": self.config.USE_GPU,
                        },
                        f,
                        indent=4,
                    )
                self._show_config_status(
                    "✅ Settings saved to current directory!", "#2ecc71", True
                )
                self._log("Configuration saved to current directory instead.")
            except Exception as e:
                self._show_config_status(
                    f"❌ Failed to save: {str(e)}", "#e74c3c", True
                )
                self._log(f"Failed to save configuration: {e}")

        # Also save to shared config file for subprocess
        shared_config_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "shared_config.json"
        )
        try:
            config_dict = {
                "USERNAME": self.config.USERNAME,
                "MC_AETHER": self.config.MC_AETHER,
                "WANDERER_NAME": self.config.WANDERER_NAME,
                "GAME_RESOLUTION": self.config.GAME_RESOLUTION,
                "USE_GPU": self.config.USE_GPU,
            }

            # Add character images if any
            if character_images:
                config_dict["CHARACTER_IMAGES"] = character_images

            with open(shared_config_file, "w") as f:
                json.dump(config_dict, f, indent=4)
            self._log("Shared config updated for subprocess.")
        except Exception as e:
            self._show_config_status(
                f"⚠️ Warning: Could not update shared config: {str(e)}", "#f39c12", True
            )
            self._log(f"Failed to update shared config: {e}")

    def _show_config_status(self, message: str, color: str, temporary: bool = True):
        """Show a temporary status message in the configuration tab"""
        if hasattr(self, "config_status_label"):
            self.config_status_label.setText(message)
            self.config_status_label.setStyleSheet(f"""
                QLabel {{
                    color: {color};
                    padding: 5px;
                    margin: 5px 10px;
                    background-color: rgba({color[1:]}, 0.1);
                    border: 1px solid {color};
                    border-radius: 3px;
                }}
            """)
            self.config_status_label.setVisible(True)

            if temporary:
                # Hide the message after 3 seconds
                QTimer.singleShot(3000, lambda: self._hide_config_status())

    def _hide_config_status(self):
        """Hide the configuration status label"""
        if hasattr(self, "config_status_label"):
            self.config_status_label.setVisible(False)

    def _log(self, message: str):
        """Add a message to the log"""
        # Use QTimer to ensure this runs in the main thread
        QTimer.singleShot(0, lambda: self._add_log_message(message))

    def _add_log_message(self, message: str):
        """Add a log message to the text area (called from main thread)"""
        if hasattr(self, "log_text"):
            self.log_text.append(f"[{time.strftime('%H:%M:%S')}] {message}")
            # Scroll to bottom
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.End)
            self.log_text.setTextCursor(cursor)

    def _start_rpc_thread(self):
        """Start the Discord RPC thread"""
        self.rpc_thread = threading.Thread(target=self._rpc_loop, daemon=True)
        self.rpc_thread.start()

    def _rpc_loop(self):
        """Main RPC update loop - gets data from monitoring thread via shared variables"""
        rpc = None

        def init_discord_rpc():
            nonlocal rpc
            while self.rpc_running:
                try:
                    rpc = discord.Presence(self.config.DISC_APP_ID)
                    rpc.connect()
                    self._log("Connected to Discord!")
                    break
                except discord.exceptions.DiscordNotFound:
                    self._log("Waiting for Discord to start...")
                    time.sleep(5)
                except Exception as e:
                    self._log(f"Error connecting to Discord: {e}")
                    time.sleep(5)

        previous_update = None

        while self.rpc_running:
            if rpc is None:
                init_discord_rpc()

            try:
                # Get latest data from shared variables (updated by monitoring thread)
                current_params = None
                if hasattr(self, "latest_rpc_data") and self.latest_rpc_data:
                    current_params = self.latest_rpc_data
                    self._log(
                        f"🔄 RPC thread got data: {current_params.get('details', 'Unknown')}"
                    )

                # Update RPC if we have new params and they're different
                if current_params and current_params != previous_update:
                    rpc.update(**current_params)
                    previous_update = current_params
                    self._log(
                        f"🎮 Updated Discord RPC: {current_params.get('details', 'Unknown')}"
                    )

                time.sleep(1)  # Rate limit to 1 update per second

            except discord.exceptions.InvalidID:
                # Discord closed, need to reconnect
                rpc = None
                continue
            except Exception as e:
                self._log(f"Error updating RPC: {e}")
                time.sleep(5)

    def _get_activity_text(self, activity) -> str:
        """Convert activity type to display text"""
        # Handle both Activity objects and dict data from shared file
        if isinstance(activity, dict):
            activity_type = activity.get("activity_type", "LOADING")
            activity_data = activity.get("activity_data")
        else:
            activity_type = activity.activity_type
            activity_data = activity.activity_data

        # Convert string activity type to enum if needed
        if isinstance(activity_type, str):
            try:
                activity_type = ActivityType(activity_type)
            except ValueError:
                activity_type = ActivityType.LOADING

        if activity_type == 1:  # LOADING
            return "Loading..."
        elif activity_type == 5:  # LOCATION
            if isinstance(activity_data, dict) and "location_name" in activity_data:
                return f"Exploring {activity_data['location_name']}"
            elif hasattr(activity_data, "location_name"):
                return f"Exploring {activity_data.location_name}"
            else:
                return "Exploring"
        elif activity_type == 3:  # DOMAIN
            if isinstance(activity_data, dict) and "domain_name" in activity_data:
                return f"In Domain: {activity_data['domain_name']}"
            elif hasattr(activity_data, "domain_name"):
                return f"In Domain: {activity_data.domain_name}"
            else:
                return "In Domain"
        elif activity_type == 7:  # COMMISSION
            return "Completing Commissions"
        elif activity_type == 8:  # WORLD_BOSS
            if isinstance(activity_data, dict) and "boss_name" in activity_data:
                return f"Fighting {activity_data['boss_name']}"
            elif hasattr(activity_data, "boss_name"):
                return f"Fighting {activity_data.boss_name}"
            else:
                return "Fighting Boss"
        elif activity_type == 2:  # PAUSED
            return "Game Paused"
        else:
            return "Unknown"

    def toggle_rpc(self):
        """Toggle the Rich Presence on/off"""
        if not self.running:
            # Start Rich Presence
            self.rpc_running = True  # Enable RPC thread
            self._start_main_subprocess()
            self.running = True
            self.start_button.setText("Stop Rich Presence")
            self.start_button.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: #ffffff;
                    border: none;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 5px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            self.status_label.setText("Status: Running")
            self.status_label.setStyleSheet(
                "color: #2ecc71; padding: 5px; margin: 5px;"
            )
            self._log("Rich Presence started!")
        else:
            # Stop Rich Presence
            self.running = False
            self.rpc_running = False  # Disable RPC thread

            if self.main_process:
                self.main_process.terminate()
                try:
                    self.main_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.main_process.kill()
                self.main_process = None

            if self.main_thread and self.main_thread.is_alive():
                self.main_thread.join(timeout=5)
            self.main_thread = None

            # Wait for RPC thread to finish
            if self.rpc_thread and self.rpc_thread.is_alive():
                self.rpc_thread.join(timeout=5)
            self.rpc_thread = None

            # Clean up shared data file
            if os.path.exists(self.shared_data_file):
                try:
                    os.remove(self.shared_data_file)
                except Exception as e:
                    self._log(f"⚠️ Failed to remove shared data file: {e}")

            self.start_button.setText("Start Rich Presence")
            self.start_button.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60;
                    color: #ffffff;
                    border: none;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 5px;
                }
                QPushButton:hover {
                    background-color: #2ecc71;
                }
                QPushButton:pressed {
                    background-color: #229954;
                }
            """)
            self.status_label.setText("Status: Stopped")
            self.status_label.setStyleSheet(
                "color: #e74c3c; padding: 5px; margin: 5px;"
            )
            self._log("Rich Presence stopped.")

    def _import_main_module(self):
        """Import and setup the main module with proper path handling"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        import main

        return main

    def _start_main_subprocess(self):
        """Start main.py as a subprocess with shared file for data exchange"""
        try:
            # Set environment variables for GPU control
            env = os.environ.copy()
            if self.config.USE_GPU:
                env["CUDA_VISIBLE_DEVICES"] = "0"
                env["PYTORCH_CUDA_ALLOC_CONF"] = "max_split_size_mb:512"
                env["TORCH_USE_CUDA_DSA"] = "1"
                env["CUDA_LAUNCH_BLOCKING"] = "0"
            else:
                env["CUDA_VISIBLE_DEVICES"] = ""
                env["TORCH_USE_CUDA_DSA"] = "0"
                env["CUDA_LAUNCH_BLOCKING"] = "0"

            # Set environment variable for shared data file
            env["GUI_SHARED_DATA_FILE"] = self.shared_data_file

            # Build the command
            script_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "main.py"
            )
            # Use embedded Python explicitly - ALWAYS
            embedded_python = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "python3.13.11_embedded",
                "python.exe",
            )

            if not os.path.exists(embedded_python):
                self._log(f"❌ Embedded Python not found at: {embedded_python}")
                self._log("❌ Cannot start - embedded Python is required")
                return

            self._log(f"✅ Using embedded Python: {embedded_python}")

            command = [embedded_python, script_path]

            self._log(f"Starting subprocess: {' '.join(command)}")
            self._log(
                f"Working directory: {os.path.dirname(os.path.abspath(__file__))}"
            )
            self._log(
                f"Environment variables set: CUDA_VISIBLE_DEVICES, PYTORCH_CUDA_ALLOC_CONF, GUI_SHARED_DATA_FILE"
            )

            # Check if script exists
            if not os.path.exists(script_path):
                self._log(f"Error: Script not found at {script_path}")
                return

            # Start main.py as subprocess - capture stderr for error display
            self.main_process = subprocess.Popen(
                command,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True,
            )

            # Start thread to capture stderr output
            stderr_thread = threading.Thread(
                target=self._capture_subprocess_output,
                args=(self.main_process.stderr,),
                daemon=True,
            )
            stderr_thread.start()

            self._log(f"Subprocess started with PID: {self.main_process.pid}")

            # Start a thread to monitor subprocess output and shared data file
            self._log("🧵 Creating monitoring thread...")
            self.main_thread = threading.Thread(
                target=self._monitor_main_subprocess, daemon=True
            )
            self.main_thread.start()
            self._log(f"🧵 Monitoring thread started: {self.main_thread.is_alive()}")

        except Exception as e:
            self._log(f"Failed to start main subprocess: {e}")
            self.running = False

    def _monitor_main_subprocess(self):
        """Monitor subprocess and read shared data file for GUI updates"""
        self._log("🔍 Starting subprocess monitoring thread")
        try:
            last_update = 0
            loop_count = 0
            while self.main_process and self.main_process.poll() is None:
                loop_count += 1
                if loop_count % 50 == 0:  # Log every 5 seconds
                    self._log(
                        f"🔄 Monitoring loop #{loop_count} - Process alive: {self.main_process.poll() is None}"
                    )

                # Check for updates in shared data file
                if os.path.exists(self.shared_data_file):
                    try:
                        with open(self.shared_data_file, "r") as f:
                            data = json.load(f)
                            if data.get("timestamp", 0) > last_update:
                                last_update = data.get("timestamp", 0)
                                self._log(
                                    f"📡 Received data update from subprocess - Activity: {data.get('current_activity', {}).get('activity_type', 'Unknown')}"
                                )
                                self._log(f"📊 Full data received: {data}")

                                # Update GUI
                                self._update_gui_from_data(data)
                                self._log("✅ GUI update method called")

                                # Prepare RPC data for RPC thread
                                rpc_data = self._prepare_rpc_data(data)
                                if rpc_data:
                                    self.latest_rpc_data = rpc_data
                                    self._log("✅ RPC data prepared for RPC thread")
                            else:
                                if loop_count % 100 == 0:  # Log every 10 seconds
                                    self._log(
                                        f"⏸️ No new data (last update: {last_update})"
                                    )
                    except (json.JSONDecodeError, FileNotFoundError) as e:
                        # File might be being written to - log occasionally but don't spam
                        if loop_count % 50 == 0:  # Log every 5 seconds
                            self._log(f"⚠️ File read error: {e}")
                else:
                    # Debug: file doesn't exist yet
                    if loop_count % 20 == 0:  # Log every 2 seconds
                        self._log("⏳ Shared data file doesn't exist yet")

                time.sleep(0.1)

            # If we exit the loop, check the return code
            if self.main_process:
                return_code = self.main_process.poll()
                self._log(f"Subprocess exited with return code: {return_code}")
                # Don't set self.running = False here - let the toggle logic handle it
        except Exception as e:
            self._log(f"Error monitoring subprocess: {e}")
            import traceback

            self._log(f"Error traceback: {traceback.format_exc()}")
            # Don't set self.running = False here - let the toggle logic handle it

    def _capture_subprocess_output(self, pipe):
        """Capture subprocess stderr output and display in GUI log"""
        try:
            for line in iter(pipe.readline, ""):
                if line:
                    line = line.strip()
                    if line:
                        self._log(f"[Subprocess] {line}")
        except Exception as e:
            self._log(f"Error capturing subprocess output: {e}")
        finally:
            pipe.close()

    def _update_gui_from_data(self, data):
        """Update GUI elements from received data"""
        try:
            self._log(f"🔄 Updating GUI with data: {data.keys() if data else 'None'}")

            # Check if labels exist
            self._log(f"🔍 Checking label existence:")
            self._log(f"  - activity_label: {hasattr(self, 'activity_label')}")
            self._log(
                f"  - status_current_activity: {hasattr(self, 'status_current_activity')}"
            )
            self._log(
                f"  - status_current_location: {hasattr(self, 'status_current_location')}"
            )
            self._log(
                f"  - status_current_character: {hasattr(self, 'status_current_character')}"
            )
            self._log(f"  - status_game_status: {hasattr(self, 'status_game_status')}")
            self._log(f"  - status_uptime: {hasattr(self, 'status_uptime')}")

            if "current_activity" in data and data["current_activity"]:
                activity_data = data["current_activity"]
                self._log(f"📊 Activity data: {activity_data}")

                activity_text = self._get_activity_text(activity_data)
                self._log(f"📝 Activity text: '{activity_text}'")

                if hasattr(self, "activity_label"):
                    self.activity_label.setText(f"Activity: {activity_text}")
                    self._log("✅ Updated activity_label")

                if hasattr(self, "status_current_activity"):
                    self.status_current_activity.setText(activity_text)
                    self._log("✅ Updated status_current_activity")

                # Handle location display
                activity_type = activity_data.get("activity_type", "LOADING")
                activity_details = activity_data.get("activity_data")

                if activity_type == 5:  # LOCATION
                    if (
                        isinstance(activity_details, dict)
                        and "location_name" in activity_details
                    ):
                        # Format location with subregion and region information
                        location_parts = []
                        if activity_details.get("location_name"):
                            location_parts.append(activity_details["location_name"])
                        if activity_details.get("subarea"):
                            location_parts.append(activity_details["subarea"])
                        if activity_details.get("country"):
                            location_parts.append(activity_details["country"])

                        full_location_name = (
                            ", ".join(location_parts)
                            if location_parts
                            else activity_details["location_name"]
                        )
                        if hasattr(self, "status_current_location"):
                            self.status_current_location.setText(full_location_name)
                            self._log(f"✅ Updated location: {full_location_name}")
                elif activity_type == 6:  # MAP_LOCATION
                    if (
                        isinstance(activity_details, dict)
                        and "location_name" in activity_details
                    ):
                        # Format location with subregion and region information
                        location_parts = []
                        if activity_details.get("location_name"):
                            location_parts.append(activity_details["location_name"])
                        if activity_details.get("subarea"):
                            location_parts.append(activity_details["subarea"])
                        if activity_details.get("country"):
                            location_parts.append(activity_details["country"])

                        full_location_name = (
                            ", ".join(location_parts)
                            if location_parts
                            else activity_details["location_name"]
                        )
                        if hasattr(self, "status_current_location"):
                            self.status_current_location.setText(
                                f"Thinking of traveling to {full_location_name}"
                            )
                            self._log(f"✅ Updated map location: {full_location_name}")
                elif activity_type == 3:  # DOMAIN
                    if (
                        isinstance(activity_details, dict)
                        and "domain_name" in activity_details
                    ):
                        if hasattr(self, "status_current_location"):
                            self.status_current_location.setText(
                                activity_details["domain_name"]
                            )
                else:
                    if hasattr(self, "status_current_location"):
                        self.status_current_location.setText("Unknown")

            if "current_characters" in data:
                characters = data["current_characters"]
                active_char_idx = data.get("current_active_character", 0)
                self._log(
                    f"👥 Characters: {len(characters)} total, active: {active_char_idx}"
                )

                # Update character display for active character
                if (
                    active_char_idx
                    and 1 <= active_char_idx <= 4
                    and characters[active_char_idx - 1]
                ):
                    char = characters[active_char_idx - 1]
                    if isinstance(char, dict):
                        char_name = char.get("character_display_name", "Unknown")
                        if hasattr(self, "status_current_character"):
                            self.status_current_character.setText(char_name)
                            self._log(f"🎭 Active character: {char_name}")
                        # Update image if available
                        self._update_status_image(
                            "current_character", char.get("image_key"), "Characters"
                        )
                    else:
                        if hasattr(self, "status_current_character"):
                            self.status_current_character.setText("None")
                else:
                    if hasattr(self, "status_current_character"):
                        self.status_current_character.setText("None")

            if "game_start_time" in data and data["game_start_time"]:
                uptime_seconds = int(time.time() - data["game_start_time"])
                hours, remainder = divmod(uptime_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                if hasattr(self, "status_uptime"):
                    self.status_uptime.setText(uptime_str)
                    self._log(f"⏰ Updated uptime: {uptime_str}")

            if "pause_ocr" in data:
                game_status = "Paused" if data["pause_ocr"] else "Running"
                if hasattr(self, "status_game_status"):
                    self.status_game_status.setText(game_status)
                    self._log(f"🎮 Game status: {game_status}")

        except Exception as e:
            self._log(f"❌ Error updating GUI from data: {e}")
            import traceback

            self._log(f"❌ Traceback: {traceback.format_exc()}")

    def _prepare_rpc_data(self, data):
        """Prepare RPC data from shared data for the RPC thread"""
        try:
            # Extract activity data from shared file
            activity_data = data.get("current_activity")
            if not activity_data:
                return None

            # Convert dict back to Activity object
            from core.datatypes import Activity, ActivityType

            activity_type = ActivityType(activity_data.get("activity_type", "LOADING"))
            activity_obj = Activity(activity_type, activity_data.get("activity_data"))

            # Get current activity params
            current_params = activity_obj.to_update_params_dict()

            # Add character info if available
            characters = data.get("current_characters", [])
            active_char_idx = data.get("current_active_character", 0)
            if (
                active_char_idx
                and 1 <= active_char_idx <= 4
                and characters[active_char_idx - 1]
            ):
                char = characters[active_char_idx - 1]
                current_params["small_image"] = char.get("image_key")
                current_params["small_text"] = (
                    f"Playing as {char.get('character_display_name', 'Unknown')}"
                )

            # Add start time if available
            start_time = data.get("game_start_time")
            if start_time:
                current_params["start"] = start_time

            return current_params

        except Exception as e:
            self._log(f"❌ Error preparing RPC data: {e}")
            return None

    def _check_for_coordinate_updates(self):
        """Check for updated coordinates from shared data file and update if necessary"""
        if os.path.exists(self.shared_data_file):
            try:
                with open(self.shared_data_file, "r") as f:
                    shared_data = json.load(f)

                # Check if adapted coordinates are available and different from current
                if "adapted_coordinates" in shared_data:
                    adapted_coords = shared_data["adapted_coordinates"]

                    if (
                        "ADAPTED_NAMES_4P_COORD" in adapted_coords
                        and "ADAPTED_NUMBER_4P_COORD" in adapted_coords
                    ):
                        new_name_coords = adapted_coords["ADAPTED_NAMES_4P_COORD"]
                        new_number_coords = adapted_coords["ADAPTED_NUMBER_4P_COORD"]

                        # Check if coordinates have changed
                        coords_changed = (
                            new_name_coords != self.config.CHARACTER_NAME_COORDINATES
                            or new_number_coords
                            != self.config.CHARACTER_NUMBER_COORDINATES
                        )

                        if coords_changed:
                            print("🔄 Updated GUI coordinates from shared data file")
                            self.config.CHARACTER_NAME_COORDINATES = new_name_coords
                            self.config.CHARACTER_NUMBER_COORDINATES = new_number_coords
                            self._log("📍 GUI coordinates updated from adaptive system")

            except Exception as e:
                # Silently handle file read errors
                pass

    def _ensure_image_cache_dir(self):
        cache_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "cache", "image_cache"
        )
        os.makedirs(cache_dir, exist_ok=True)
        return cache_dir

    def _try_boss_subfolders(
        self, image_key: str, cache_dir: str, image_path: str
    ) -> Optional[str]:
        """Try downloading from boss subfolders"""
        subfolders = [
            "hypostasis",
            "regisvine",
            "animal",
            "mechanical_construct",
            "elemental",
            "person_and_mechanical",
        ]
        for subfolder in subfolders:
            try:
                boss_url = f"https://raw.githubusercontent.com/ZANdewanai/Genshin-Impact-Rich-Presence/main/resources/assets/images/bosses/{subfolder}/{image_key}.png"
                urllib.request.urlretrieve(boss_url, image_path)
                return image_path
            except Exception:
                continue
        return None

    def _download_image(
        self, image_key: str, category: str = "Characters"
    ) -> Optional[str]:
        """Download an image from GitHub if not cached"""
        if image_key in self.image_cache:
            return self.image_cache[image_key]

        cache_dir = self._ensure_image_cache_dir()
        image_path = os.path.join(cache_dir, f"{image_key}.png")

        # Check if already cached
        if os.path.exists(image_path):
            self.image_cache[image_key] = image_path
            return image_path

        # Map category to correct folder name
        folder_map = {"Characters": "characters", "Bosses": "bosses"}
        folder = folder_map.get(category, category.lower())

        # Download from GitHub with correct folder
        try:
            github_url = f"https://raw.githubusercontent.com/ZANdewanai/Genshin-Impact-Rich-Presence/main/resources/assets/images/{folder}/{image_key}.png"
            urllib.request.urlretrieve(github_url, image_path)
            self.image_cache[image_key] = image_path
            return image_path
        except Exception as e:
            # Try alternative URL patterns
            try:
                # Try without folder for characters
                alt_url = f"https://raw.githubusercontent.com/ZANdewanai/Genshin-Impact-Rich-Presence/main/resources/assets/images/{image_key}.png"
                urllib.request.urlretrieve(alt_url, image_path)
                self.image_cache[image_key] = image_path
                return image_path
            except Exception as e2:
                # For bosses, try specific subfolders
                if category == "Bosses":
                    boss_path = self._try_boss_subfolders(
                        image_key, cache_dir, image_path
                    )
                    if boss_path:
                        self.image_cache[image_key] = boss_path
                        return boss_path
                print(f"Failed to download image {image_key}: {e2}")
                return None

    def _update_status_image(
        self, status_key: str, image_key: str, category: str = "Characters"
    ):
        """Update the image for a status item"""
        from PyQt5.QtGui import QPixmap, QImage

        img_label = getattr(self, f"status_img_{status_key}", None)
        if not img_label:
            return

        if image_key and image_key != "None":
            image_path = self._download_image(image_key, category)
            if image_path:
                try:
                    # Load and resize image for UI
                    pil_image = Image.open(image_path)
                    pil_image = pil_image.resize((32, 32), Image.Resampling.LANCZOS)

                    # Determine format based on image mode
                    if pil_image.mode in ("RGBA", "LA") or (
                        pil_image.mode == "P" and "transparency" in pil_image.info
                    ):
                        pil_image = pil_image.convert("RGBA")
                        qimage_format = QImage.Format_RGBA8888
                    else:
                        pil_image = pil_image.convert("RGB")
                        qimage_format = QImage.Format_RGB888

                    # Convert PIL image to QPixmap
                    qimage = QImage(
                        pil_image.tobytes(),
                        pil_image.width,
                        pil_image.height,
                        qimage_format,
                    )
                    pixmap = QPixmap.fromImage(qimage)

                    img_label.setPixmap(
                        pixmap.scaled(
                            32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation
                        )
                    )
                    img_label.setText("")
                except Exception as e:
                    print(f"Failed to load image {image_key}: {e}")
                    img_label.setPixmap(QPixmap())
                    img_label.setText("❌")
            else:
                img_label.setPixmap(QPixmap())
                img_label.setText("❌")
        else:
            img_label.setPixmap(QPixmap())
            img_label.setText("")

    def _add_character_image_entry(self):
        """Add a new character image entry field"""
        from PyQt5.QtWidgets import QInputDialog, QLineEdit, QMessageBox

        char_name, ok = QInputDialog.getText(
            self, "Add Character", "Enter character name:", QLineEdit.Normal, ""
        )

        if ok and char_name.strip():
            char_name = char_name.strip()

            # Check if already exists
            if char_name in self.char_image_entries:
                QMessageBox.warning(
                    self, "Duplicate", f"Character '{char_name}' already exists!"
                )
                return

            # Create new entry
            char_layout = QHBoxLayout()

            char_label = QLabel(f"{char_name}:")
            char_label.setObjectName("char_label")
            char_label.setFont(QFont("Arial", 9))
            char_layout.addWidget(char_label)

            char_entry = QLineEdit()
            char_entry.setPlaceholderText("e.g., char_traveler_fatui")
            char_entry.setStyleSheet("""
                QLineEdit {
                    background-color: #34495e;
                    color: #ecf0f1;
                    border: 1px solid #2c3e50;
                    border-radius: 3px;
                    padding: 3px;
                }
            """)
            char_layout.addWidget(char_entry)

            remove_btn = QPushButton("✕")
            remove_btn.setFont(QFont("Arial", 8))
            remove_btn.setStyleSheet("""
                QPushButton {
                    background-color: #e74c3c;
                    color: #ffffff;
                    border: none;
                    padding: 2px 8px;
                    border-radius: 3px;
                    margin: 0px;
                    min-width: 25px;
                    max-width: 25px;
                }
                QPushButton:hover {
                    background-color: #c0392b;
                }
            """)
            remove_btn.clicked.connect(
                lambda: self._remove_character_image_entry(char_layout, char_name)
            )
            char_layout.addWidget(remove_btn)

            # Insert before the "Add Character" button
            char_images_layout = self.character_images_widget.layout()
            add_btn_index = char_images_layout.count() - 1  # Button is last item
            char_images_layout.insertLayout(add_btn_index, char_layout)

            self.char_image_entries[char_name] = char_entry

            self._log(f"Added character image entry for: {char_name}")

    def _remove_character_image_entry(self, layout, char_name):
        """Remove a character image entry"""
        # Remove from layout
        char_images_layout = self.character_images_widget.layout()
        char_images_layout.removeItem(layout)

        # Clean up widgets
        while layout.count() > 0:
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        layout.deleteLater()

        # Remove from dictionary
        if char_name in self.char_image_entries:
            del self.char_image_entries[char_name]

        self._log(f"Removed character image entry for: {char_name}")

    def _save_roster_config(self):
        """Save character image configuration from roster tab"""
        # Collect character image mappings
        character_images = {}
        for char_name, entry in self.char_image_entries.items():
            image_key = entry.text().strip()
            if image_key:  # Only include non-empty entries
                character_images[char_name] = image_key

        # Show saving status
        self.roster_status_label.setText("💾 Saving character settings...")
        self.roster_status_label.setStyleSheet("""
            QLabel {
                color: #f39c12;
                padding: 5px;
                margin: 5px 10px;
                background-color: rgba(243, 156, 18, 0.1);
                border: 1px solid #f39c12;
                border-radius: 3px;
            }
        """)
        self.roster_status_label.setVisible(True)

        # Save to shared config file for subprocess
        shared_config_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "shared_config.json"
        )
        try:
            # Load existing config
            if os.path.exists(shared_config_file):
                with open(shared_config_file, "r") as f:
                    config_dict = json.load(f)
            else:
                config_dict = {}

            # Update character images
            config_dict["CHARACTER_IMAGES"] = character_images

            # Save updated config
            with open(shared_config_file, "w") as f:
                json.dump(config_dict, f, indent=4)

            # Show success
            self.roster_status_label.setText("✅ Character settings saved!")
            self.roster_status_label.setStyleSheet("""
                QLabel {
                    color: #2ecc71;
                    padding: 5px;
                    margin: 5px 10px;
                    background-color: rgba(46, 204, 113, 0.1);
                    border: 1px solid #2ecc71;
                    border-radius: 3px;
                }
            """)
            self._log("Character image settings saved successfully!")

            # Hide after 3 seconds
            QTimer.singleShot(3000, lambda: self.roster_status_label.setVisible(False))

        except Exception as e:
            self.roster_status_label.setText(f"❌ Error: {str(e)}")
            self.roster_status_label.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    padding: 5px;
                    margin: 5px 10px;
                    background-color: rgba(231, 76, 60, 0.1);
                    border: 1px solid #e74c3c;
                    border-radius: 3px;
                }
            """)
            self._log(f"Failed to save character settings: {e}")

            # Hide after 5 seconds for errors
            QTimer.singleShot(5000, lambda: self.roster_status_label.setVisible(False))

    def closeEvent(self, event):
        """Handle window closing"""
        self._log("🛑 Application closing - cleaning up processes...")
        self.running = False
        self.rpc_running = False  # Stop RPC thread

        if self.main_process:
            self._log("Terminating main subprocess...")
            self.main_process.terminate()
            try:
                self.main_process.wait(timeout=5)
                self._log("Main subprocess terminated gracefully")
            except subprocess.TimeoutExpired:
                self._log("Force killing main subprocess...")
                self.main_process.kill()
            self.main_process = None

        if self.main_thread and self.main_thread.is_alive():
            self._log("Waiting for main monitoring thread...")
            self.main_thread.join(timeout=5)
        self.main_thread = None

        # Wait for RPC thread to finish
        if self.rpc_thread and self.rpc_thread.is_alive():
            self._log("Waiting for RPC thread...")
            self.rpc_thread.join(timeout=5)
        self.rpc_thread = None

        # Stop coordinate update timer
        if hasattr(self, "coordinate_update_timer"):
            self.coordinate_update_timer.stop()

        self._log("✅ Application cleanup complete")
        event.accept()


if __name__ == "__main__":
    # Check if we have the required dependencies for GUI mode
    if not DEPENDENCIES_OK:
        print("Cannot start application - missing dependencies.")
        print("Please install required packages and try again.")
        sys.exit(1)

    try:
        app = QApplication(sys.argv)
        window = GenshinRichPresenceApp()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error starting application: {e}")
        print("Make sure all dependencies are installed.")
        sys.exit(1)
