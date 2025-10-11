# ==========================================
# Genshin Impact Rich Presence GUI v2.6
# Advanced GUI wrapper with comprehensive settings - PyQt5 Version
# ==========================================

import os
import sys
import threading
import time
import json
import subprocess
import tempfile
import shutil
from datetime import datetime

# Third-party imports
try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                 QLabel, QPushButton, QTextEdit, QTabWidget, QFrame, QSplitter,
                                 QProgressBar, QCheckBox, QLineEdit, QComboBox, QSizePolicy,
                                 QGroupBox, QFormLayout, QGridLayout, QMessageBox, QListWidget,
                                 QStatusBar, QMenuBar, QToolBar, QAction, QSystemTrayIcon)
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QRect, QSize, QPoint, QUrl
    from PyQt5.QtGui import QFont, QPixmap, QIcon, QImage, QPalette, QColor, QDesktopServices
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

# Check for tkinter availability (for fallback text mode)
try:
    import tkinter
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

# Typing imports
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum, auto

# Import data types from main module to avoid duplication
import sys
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

from datatypes import ActivityType, Activity, Character, Location

# ==========================================
# Default Configuration
# ==========================================

class Config:
    def __init__(self):
        self.USERNAME = "Player"
        self.MC_AETHER = True
        self.WANDERER_NAME = "Wanderer"
        self.GAME_RESOLUTION = 1080
        self.USE_GPU = True
        self.DISC_APP_ID = "944346292568596500"
        self.ACTIVE_CHARACTER_THRESH = 700
        self.NAME_CONF_THRESH = 0.6
        self.LOC_CONF_THRESH = 0.6
        self.BOSS_CONF_THRESH = 0.6
        self.DOMAIN_CONF_THRESH = 0.6
        self.SLEEP_PER_ITERATION = 0.1
        self.OCR_CHARNAMES_ONE_IN = 30
        self.OCR_LOC_ONE_IN = 10
        self.OCR_BOSS_ONE_IN = 20
        self.OCR_DOMAIN_ONE_IN = 20
        self.PAUSE_STATE_COOLDOWN = 5
        self.INACTIVE_COOLDOWN = 60
        self.ALLOWLIST = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789' -"
        
        # Update coordinates based on resolution
        self.update_coordinates()
    
    def update_coordinates(self):
        """Update screen coordinates based on resolution
        
        This method calculates UI element positions for any resolution that's a multiple of 1080p.
        The coordinates are scaled proportionally based on the height difference from 1080p.
        """
        # Base resolution (1080p)
        BASE_HEIGHT = 1080
        
        scale = self.GAME_RESOLUTION / BASE_HEIGHT
        
        # Define base coordinates for 1080p
        if self.GAME_RESOLUTION == 1080:
            # 1080p coordinates (base)
            self.CHARACTER_NUMBER_COORDINATES = [
                (2484, 356),   # Char 1
                (2484, 481),   # Char 2
                (2484, 610),   # Char 3
                (2484, 735),   # Char 4
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
                (int(2484 * scale), int(610 * scale)),  # Char 3
                (int(2484 * scale), int(735 * scale)),  # Char 4
            ]
            
            # Character name coordinates
            self.CHARACTER_NAME_COORDINATES = [
                (
                    int(2166 * scale),  # x1
                    int(320 * scale),   # y1
                    int(2365 * scale),  # x2
                    int(395 * scale)    # y2
                ),
                (
                    int(2166 * scale),
                    int(445 * scale),
                    int(2365 * scale),
                    int(520 * scale)
                ),
                (
                    int(2166 * scale),
                    int(575 * scale),
                    int(2365 * scale),
                    int(650 * scale)
                ),
                (
                    int(2166 * scale),
                    int(705 * scale),
                    int(2365 * scale),
                    int(780 * scale)
                ),
            ]

            # Other UI element coordinates
            self.BOSS_COORDINATES = (
                int(943 * scale),   # x1
                int(6 * scale),     # y1
                int(1614 * scale),  # x2
                int(66 * scale)     # y2
            )

            self.LOCATION_COORDINATES = (
                int(702 * scale),    # x1
                int(240 * scale),    # y1
                int(1838 * scale),   # x2
                int(345 * scale)     # y2
            )
        
        # Log the current resolution and scale factor
        print(f"Resolution set to: {self.GAME_RESOLUTION}p (Scale factor: {scale:.2f})")
    
    def _get_config_path(self, filename: str = "config.json") -> str:
        """Get the full path to the config file in AppData"""
        appdata = os.getenv('APPDATA')
        config_dir = os.path.join(appdata, 'GenshinImpactRichPresence')
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, filename)
    
    def save_to_file(self, filename: str = "config.json"):
        """Save current configuration to a JSON file in AppData"""
        config_path = self._get_config_path(filename)
        config_dict = {
            key: value for key, value in self.__dict__.items() 
            if not key.startswith('_') and not callable(value) and not key.isupper()
        }
        try:
            with open(config_path, 'w') as f:
                json.dump(config_dict, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def load_from_file(self, filename: str = "config.json"):
        """Load configuration from a JSON file in AppData"""
        config_path = self._get_config_path(filename)
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    config_dict = json.load(f)
                    for key, value in config_dict.items():
                        if hasattr(self, key):
                            setattr(self, key, value)
                self.update_coordinates()
                return True
            except Exception as e:
                print(f"Error loading config: {e}")
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
        self.config.load_from_file()  # This will try to load from AppData

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
        self.dependencies_checked = True  # Assume dependencies are OK since we're not checking

        import multiprocessing
        import subprocess

        # Initialize shared data file path
        import os
        self.shared_data_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gui_shared_data.json')

        # Shared data for RPC thread (updated by monitoring thread)
        self.latest_rpc_data = None

        # Image cache for downloaded images
        self.image_cache = {}

        # Setup UI
        self.setWindowTitle("Genshin Impact Rich Presence v2.6")
        self.setGeometry(100, 100, 900, 700)
        self.setWindowIcon(QIcon("images/ApplicatonIcon.ico"))

        # Set dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2c3e50;
            }
            QTabWidget::pane {
                border: 1px solid #34495e;
                background-color: #34495e;
            }
            QTabBar::tab {
                background-color: #34495e;
                color: #ecf0f1;
                padding: 10px;
                border: 1px solid #34495e;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: #ffffff;
            }
            QLabel {
                color: #ecf0f1;
            }
            QPushButton {
                background-color: #27ae60;
                color: #ffffff;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:pressed {
                background-color: #229954;
            }
            QTextEdit {
                background-color: #34495e;
                color: #ecf0f1;
                border: 1px solid #34495e;
            }
        """)

        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Create sidebar
        self._create_sidebar()
        main_layout.addWidget(self.sidebar_widget, 0)
        main_layout.addLayout(self._create_main_content(), 1)

        # Check dependencies on startup (removed)

        # Start RPC thread - GUI will handle Discord updates using subprocess data
        self._start_rpc_thread()

    def _create_main_content(self):
        """Create the main content area with tabs"""
        main_content_layout = QVBoxLayout()

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #34495e;
                background-color: #34495e;
            }
            QTabBar::tab {
                background-color: #34495e;
                color: #ecf0f1;
                padding: 10px;
                border: 1px solid #34495e;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #3498db;
                color: #ffffff;
            }
            QTabBar::tab:hover {
                background-color: #2980b9;
            }
        """)

        # Create tabs
        self.main_tab = QWidget()
        self.config_tab = QWidget()
        self.about_tab = QWidget()

        self.tab_widget.addTab(self.main_tab, "Main")
        self.tab_widget.addTab(self.config_tab, "Configuration")
        self.tab_widget.addTab(self.about_tab, "About")

        main_content_layout.addWidget(self.tab_widget)

        # Setup tab contents
        self._setup_main_tab()
        self._setup_config_tab()
        self._setup_about_tab()

        return main_content_layout

    # Remove text-based mode code as PyQt5 is available
    # def _run_text_based_mode(self): ... (removed)
    # def _start_text_display(self): ... (removed)

    def _run_non_gui_mode(self):
        """Legacy method - no longer used, subprocess is handled by _start_main_subprocess"""
        pass

    def _create_sidebar(self):
        """Create the sidebar with app controls"""
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setFixedWidth(180)
        self.sidebar_widget.setStyleSheet("""
            QWidget {
                background-color: #34495e;
                border-right: 2px solid #2c3e50;
            }
        """)

        sidebar_layout = QVBoxLayout(self.sidebar_widget)

        # Logo and title
        logo_label = QLabel("Genshin Impact\nRich Presence")
        logo_label.setFont(QFont("Arial", 16, QFont.Bold))
        logo_label.setStyleSheet("color: #ecf0f1; padding: 10px;")
        logo_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(logo_label)

        # Spacer
        sidebar_layout.addStretch()

        # Start/Stop button
        self.start_button = QPushButton("Start Rich Presence")
        self.start_button.setFont(QFont("Arial", 10, QFont.Bold))
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
        self.start_button.clicked.connect(self.toggle_rpc)
        sidebar_layout.addWidget(self.start_button)

        # Status indicator
        self.status_label = QLabel("Status: Stopped")
        self.status_label.setFont(QFont("Arial", 9, QFont.Bold))
        self.status_label.setStyleSheet("color: #e74c3c; padding: 5px; margin: 5px;")
        self.status_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(self.status_label)

        # Current activity
        self.activity_label = QLabel("Activity: Not running")
        self.activity_label.setFont(QFont("Arial", 8))
        self.activity_label.setStyleSheet("color: #bdc3c7; padding: 5px; margin: 5px;")
        self.activity_label.setWordWrap(True)
        self.activity_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(self.activity_label)

        # Spacer
        sidebar_layout.addStretch()

        # Version info
        version_label = QLabel("v2.6")
        version_label.setFont(QFont("Arial", 10))
        version_label.setStyleSheet("color: #7f8c8d; padding: 10px;")
        version_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(version_label)
    
    def _setup_main_tab(self):
        """Setup the main tab with status information"""
        main_layout = QVBoxLayout(self.main_tab)

        # Title
        title_label = QLabel("Genshin Impact Rich Presence")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setStyleSheet("color: #ecf0f1; padding: 10px; margin: 10px;")
        main_layout.addWidget(title_label)

        # Status frame
        status_frame = QFrame()
        status_frame.setFrameStyle(QFrame.Box)
        status_frame.setStyleSheet("""
            QFrame {
                background-color: #34495e;
                border: 1px solid #2c3e50;
                border-radius: 8px;
                margin: 10px;
            }
        """)
        status_layout = QGridLayout(status_frame)

        # Status info with images
        status_items = [
            ("Game Status:", "Not running"),
            ("Current Character:", "None"),
            ("Current Location:", "Unknown"),
            ("Current Activity:", "None"),
            ("Uptime:", "00:00:00")
        ]

        for i, (label, value) in enumerate(status_items):
            # Image placeholder (will be updated dynamically)
            img_label = QLabel("")
            img_label.setFixedSize(32, 32)
            img_label.setStyleSheet("border: 1px solid #2c3e50; background-color: #2c3e50;")
            status_layout.addWidget(img_label, i, 0)

            # Label
            lbl = QLabel(label)
            lbl.setFont(QFont("Arial", 10, QFont.Bold))
            lbl.setStyleSheet("color: #ecf0f1;")
            status_layout.addWidget(lbl, i, 1)

            # Value
            value_label = QLabel(value)
            value_label.setFont(QFont("Arial", 9))
            value_label.setStyleSheet("color: #bdc3c7; padding-left: 10px;")
            status_layout.addWidget(value_label, i, 2)

            # Store references for updating
            setattr(self, f"status_img_{label.lower().replace(' ', '_').replace(':', '')}", img_label)
            setattr(self, f"status_{label.lower().replace(' ', '_').replace(':', '')}", value_label)

        status_layout.setColumnStretch(2, 1)
        main_layout.addWidget(status_frame)

        log_label = QLabel("Activity Log:")
        log_label.setFont(QFont("Arial", 12, QFont.Bold))
        log_label.setStyleSheet("color: #ecf0f1; padding: 5px; margin: 10px 10px 5px 10px;")
        main_layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #34495e;
                color: #ecf0f1;
                border: 1px solid #2c3e50;
                border-radius: 5px;
                padding: 10px;
                margin: 5px 10px 10px 10px;
            }
        """)
        self.log_text.setReadOnly(True)
        main_layout.addWidget(self.log_text)

        main_layout.addStretch()
    
    def _setup_config_tab(self):
        """Setup the configuration tab"""
        config_layout = QVBoxLayout(self.config_tab)

        # Title
        title_label = QLabel("Configuration")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setStyleSheet("color: #ecf0f1; padding: 10px; margin: 10px;")
        config_layout.addWidget(title_label)

        # Create main config frame
        config_frame = QFrame()
        config_frame.setFrameStyle(QFrame.Box)
        config_frame.setStyleSheet("""
            QFrame {
                background-color: #34495e;
                border: 1px solid #2c3e50;
                border-radius: 8px;
                margin: 10px;
            }
        """)
        config_main_layout = QHBoxLayout(config_frame)

        # User settings frame (left side)
        user_frame = QFrame()
        user_frame.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border: 1px solid #34495e;
                border-radius: 5px;
                margin: 5px;
            }
        """)
        user_layout = QVBoxLayout(user_frame)

        user_label = QLabel("User Settings")
        user_label.setFont(QFont("Arial", 14, QFont.Bold))
        user_label.setStyleSheet("color: #ecf0f1; padding: 10px;")
        user_layout.addWidget(user_label)

        # Username
        username_layout = QHBoxLayout()
        username_label = QLabel("Username:")
        username_label.setFont(QFont("Arial", 10))
        username_label.setStyleSheet("color: #ecf0f1; padding: 5px;")
        username_layout.addWidget(username_label)

        self.username_entry = QLineEdit(self.config.USERNAME)
        self.username_entry.setStyleSheet("""
            QLineEdit {
                background-color: #34495e;
                color: #ecf0f1;
                border: 1px solid #2c3e50;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        username_layout.addWidget(self.username_entry)
        user_layout.addLayout(username_layout)

        # Main character selection
        mc_layout = QHBoxLayout()
        mc_label = QLabel("Main Character:")
        mc_label.setFont(QFont("Arial", 10))
        mc_label.setStyleSheet("color: #ecf0f1; padding: 5px;")
        mc_layout.addWidget(mc_label)

        self.mc_combo = QComboBox()
        self.mc_combo.addItems(["Aether (Male)", "Lumine (Female)"])
        self.mc_combo.setCurrentText("Aether (Male)" if self.config.MC_AETHER else "Lumine (Female)")
        self.mc_combo.setStyleSheet("""
            QComboBox {
                background-color: #34495e;
                color: #ecf0f1;
                border: 1px solid #2c3e50;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        mc_layout.addWidget(self.mc_combo)
        user_layout.addLayout(mc_layout)

        # Wanderer name
        wanderer_layout = QHBoxLayout()
        wanderer_label = QLabel("Wanderer Name:")
        wanderer_label.setFont(QFont("Arial", 10))
        wanderer_label.setStyleSheet("color: #ecf0f1; padding: 5px;")
        wanderer_layout.addWidget(wanderer_label)

        self.wanderer_entry = QLineEdit(self.config.WANDERER_NAME)
        self.wanderer_entry.setStyleSheet("""
            QLineEdit {
                background-color: #34495e;
                color: #ecf0f1;
                border: 1px solid #2c3e50;
                border-radius: 3px;
                padding: 5px;
            }
        """)
        wanderer_layout.addWidget(self.wanderer_entry)
        user_layout.addLayout(wanderer_layout)

        config_main_layout.addWidget(user_frame, 1)

        # Performance settings frame (right side)
        perf_frame = QFrame()
        perf_frame.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border: 1px solid #34495e;
                border-radius: 5px;
                margin: 5px;
            }
        """)
        perf_layout = QVBoxLayout(perf_frame)

        perf_label = QLabel("Performance Settings")
        perf_label.setFont(QFont("Arial", 14, QFont.Bold))
        perf_label.setStyleSheet("color: #ecf0f1; padding: 10px;")
        perf_layout.addWidget(perf_label)

        # GPU acceleration toggle
        self.gpu_checkbox = QCheckBox("Enable GPU acceleration for OCR")
        self.gpu_checkbox.setChecked(self.config.USE_GPU)
        self.gpu_checkbox.setFont(QFont("Arial", 10))
        self.gpu_checkbox.setStyleSheet("""
            QCheckBox {
                color: #ecf0f1;
                spacing: 8px;
                padding: 5px;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
            }
            QCheckBox::indicator:checked {
                background-color: #27ae60;
                border: 1px solid #27ae60;
            }
        """)
        perf_layout.addWidget(self.gpu_checkbox)

        perf_layout.addStretch()
        config_main_layout.addWidget(perf_frame, 1)

        config_layout.addWidget(config_frame)

        # Save button
        save_button = QPushButton("Save Settings")
        save_button.setFont(QFont("Arial", 12, QFont.Bold))
        save_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: #ffffff;
                border: none;
                padding: 15px 30px;
                border-radius: 8px;
                margin: 10px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)
        save_button.clicked.connect(self._save_config)
        config_layout.addWidget(save_button)

        config_layout.addStretch()
    
    def _setup_about_tab(self):
        """Setup the about tab"""
        about_layout = QVBoxLayout(self.about_tab)

        # Title
        title_label = QLabel("About Genshin Impact Rich Presence")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setStyleSheet("color: #ecf0f1; padding: 10px; margin: 10px;")
        about_layout.addWidget(title_label)

        # Info text
        info_text = """Genshin Impact Rich Presence v2.6

This application displays your current in-game activity on Discord.

Features:
• Shows your current character and location
• Detects when you're in domains or fighting bosses
• Works with any resolution
• Lightweight and easy to use

Created by ZANdewanai
Rewritten by euwbah

Image assets are intellectual property of HoYoverse
All rights reserved by miHoYo"""

        info_label = QLabel(info_text)
        info_label.setFont(QFont("Arial", 10))
        info_label.setStyleSheet("""
            QLabel {
                color: #ecf0f1;
                padding: 15px;
                margin: 10px;
                background-color: #2c3e50;
                border: 1px solid #34495e;
                border-radius: 8px;
            }
        """)
        info_label.setWordWrap(True)
        about_layout.addWidget(info_label)

        about_layout.addStretch()
    
    def _on_resolution_change(self, value):
        """Handle resolution change in the UI"""
        if value == "Custom":
            # Show custom resolution dialog using PyQt5
            from PyQt5.QtWidgets import QInputDialog
            res_str, ok = QInputDialog.getText(
                self,
                "Custom Resolution",
                "Enter custom resolution height (e.g., 1080):",
                text="1080"
            )
            if ok and res_str:
                try:
                    res = int(res_str)
                    if res > 0:
                        self.config.GAME_RESOLUTION = res
                        # Update UI if we had a resolution selector
                        print(f"Resolution set to: {res}p")
                except (ValueError, TypeError):
                    print("Invalid resolution value")
        else:
            self.config.GAME_RESOLUTION = int(value)

        # Update coordinates based on new resolution
        self.config.update_coordinates()
    
    def _save_config(self):
        """Save configuration from UI to config object"""
        self.config.USERNAME = self.username_entry.text()
        self.config.MC_AETHER = self.mc_combo.currentText().startswith("Aether")
        self.config.WANDERER_NAME = self.wanderer_entry.text()
        self.config.USE_GPU = self.gpu_checkbox.isChecked()

        # Save to file
        if self.config.save_to_file():
            self._log("Configuration saved successfully!")
        else:
            self._log("Error: Could not save configuration. Check permissions.")
            # Try to save to current directory as fallback
            try:
                with open('config.json', 'w') as f:
                    json.dump({
                        'USERNAME': self.config.USERNAME,
                        'MC_AETHER': self.config.MC_AETHER,
                        'WANDERER_NAME': self.config.WANDERER_NAME,
                        'GAME_RESOLUTION': self.config.GAME_RESOLUTION,
                        'USE_GPU': self.config.USE_GPU
                    }, f, indent=4)
                self._log("Configuration saved to current directory instead.")
            except Exception as e:
                self._log(f"Failed to save configuration: {e}")
    
    def _log(self, message: str):
        """Add a message to the log"""
        # Use QTimer to ensure this runs in the main thread
        QTimer.singleShot(0, lambda: self._add_log_message(message))

    def _add_log_message(self, message: str):
        """Add a log message to the text area (called from main thread)"""
        if hasattr(self, 'log_text'):
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
                if hasattr(self, 'latest_rpc_data') and self.latest_rpc_data:
                    current_params = self.latest_rpc_data

                # Update RPC if we have new params and they're different
                if current_params and current_params != previous_update:
                    rpc.update(**current_params)
                    previous_update = current_params
                    self._log(f"🎮 Updated Discord RPC: {current_params.get('details', 'Unknown')}")

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
            activity_type = activity.get('activity_type', 'LOADING')
            activity_data = activity.get('activity_data')
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
            if isinstance(activity_data, dict) and 'location_name' in activity_data:
                return f"Exploring {activity_data['location_name']}"
            elif hasattr(activity_data, 'location_name'):
                return f"Exploring {activity_data.location_name}"
            else:
                return "Exploring"
        elif activity_type == 3:  # DOMAIN
            if isinstance(activity_data, dict) and 'domain_name' in activity_data:
                return f"In Domain: {activity_data['domain_name']}"
            elif hasattr(activity_data, 'domain_name'):
                return f"In Domain: {activity_data.domain_name}"
            else:
                return "In Domain"
        elif activity_type == 7:  # COMMISSION
            return "Completing Commissions"
        elif activity_type == 8:  # WORLD_BOSS
            if isinstance(activity_data, dict) and 'boss_name' in activity_data:
                return f"Fighting {activity_data['boss_name']}"
            elif hasattr(activity_data, 'boss_name'):
                return f"Fighting {activity_data.boss_name}"
            else:
                return "Fighting Boss"
        elif activity_type == 2:  # PAUSED
            return "Game Paused"
        else:
            return "Unknown"

    def _update_activity_display(self, activity: Activity):
        """Update the activity display in the UI using main module state"""
        activity_text = self._get_activity_text(activity)

        # Update activity text in sidebar
        self.activity_label.setText(f"Activity: {activity_text}")

        # Update status display fields using main module state
        if hasattr(main, 'current_active_character') and 1 <= main.current_active_character <= 4:
            char = main.current_characters[main.current_active_character - 1]
            if char is not None:
                # Update character display
                setattr(self, f"status_current_character", QLabel(char.character_display_name))
                # Update image if available
                self._update_status_image("current_character", char.image_key, "Characters")
            else:
                setattr(self, f"status_current_character", QLabel("None"))
        
        if hasattr(main, 'game_start_time') and main.game_start_time:
            uptime_seconds = int(time.time()) - main.game_start_time
            hours, remainder = divmod(uptime_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.status_uptime.setText(uptime_str)
        
        if hasattr(main, 'pause_ocr'):
            self.status_gamestatus.setText("Paused" if main.pause_ocr else "Running")
    
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
            self.status_label.setStyleSheet("color: #2ecc71; padding: 5px; margin: 5px;")
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
                except:
                    pass

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
            self.status_label.setStyleSheet("color: #e74c3c; padding: 5px; margin: 5px;")
            self._log("Rich Presence stopped.")



    def _import_main_module(self):
        """Import and setup the main module with proper path handling"""
        import sys
        import os
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        import main
        return main

    def _start_main_subprocess(self):
        """Start main.py as a subprocess with shared file for data exchange"""
        try:
            import sys
            import os
            
            # Set environment variables for GPU control
            env = os.environ.copy()
            if self.config.USE_GPU:
                env['CUDA_VISIBLE_DEVICES'] = '0'
                env['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512'
                env['TORCH_USE_CUDA_DSA'] = '1'
                env['CUDA_LAUNCH_BLOCKING'] = '0'
            else:
                env['CUDA_VISIBLE_DEVICES'] = ''
                env['TORCH_USE_CUDA_DSA'] = '0'
                env['CUDA_LAUNCH_BLOCKING'] = '0'
            
            # Set environment variable for shared data file
            env['GUI_SHARED_DATA_FILE'] = self.shared_data_file
            
            # Build the command
            script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'main.py')
            command = [sys.executable, script_path]
            
            self._log(f"Starting subprocess: {' '.join(command)}")
            self._log(f"Working directory: {os.path.dirname(os.path.abspath(__file__))}")
            self._log(f"Environment variables set: CUDA_VISIBLE_DEVICES, PYTORCH_CUDA_ALLOC_CONF, GUI_SHARED_DATA_FILE")
            
            # Check if script exists
            if not os.path.exists(script_path):
                self._log(f"Error: Script not found at {script_path}")
                return
            
            # Start main.py as subprocess
            self.main_process = subprocess.Popen(
                command,
                cwd=os.path.dirname(os.path.abspath(__file__)),
                env=env,
                # Don't capture stdout/stderr - let subprocess print directly
                # Communication will happen via shared data file only
            )
            
            self._log(f"Subprocess started with PID: {self.main_process.pid}")
            
            # Start a thread to monitor subprocess output and shared data file
            self._log("🧵 Creating monitoring thread...")
            self.main_thread = threading.Thread(target=self._monitor_main_subprocess, daemon=True)
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
                    self._log(f"🔄 Monitoring loop #{loop_count} - Process alive: {self.main_process.poll() is None}")

                # Check for updates in shared data file
                if os.path.exists(self.shared_data_file):
                    try:
                        with open(self.shared_data_file, 'r') as f:
                            data = json.load(f)
                            if data.get('timestamp', 0) > last_update:
                                last_update = data.get('timestamp', 0)
                                self._log(f"📡 Received data update from subprocess - Activity: {data.get('current_activity', {}).get('activity_type', 'Unknown')}")
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
                                    self._log(f"⏸️ No new data (last update: {last_update})")
                    except (json.JSONDecodeError, FileNotFoundError) as e:
                        # Silently ignore file read errors - file might be being written to
                        if loop_count % 50 == 0:  # Log every 5 seconds
                            self._log(f"⚠️ File read error: {e}")
                        pass
                else:
                    # Debug: file doesn't exist yet
                    if loop_count % 20 == 0:  # Log every 2 seconds
                        self._log("⏳ Shared data file doesn't exist yet")
                    pass

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
    
    def _update_gui_from_data(self, data):
        """Update GUI elements from received data"""
        try:
            self._log(f"🔄 Updating GUI with data: {data.keys() if data else 'None'}")

            # Check if labels exist
            self._log(f"🔍 Checking label existence:")
            self._log(f"  - activity_label: {hasattr(self, 'activity_label')}")
            self._log(f"  - status_current_activity: {hasattr(self, 'status_current_activity')}")
            self._log(f"  - status_current_location: {hasattr(self, 'status_current_location')}")
            self._log(f"  - status_current_character: {hasattr(self, 'status_current_character')}")
            self._log(f"  - status_game_status: {hasattr(self, 'status_game_status')}")
            self._log(f"  - status_uptime: {hasattr(self, 'status_uptime')}")

            if 'current_activity' in data and data['current_activity']:
                activity_data = data['current_activity']
                self._log(f"📊 Activity data: {activity_data}")

                activity_text = self._get_activity_text(activity_data)
                self._log(f"📝 Activity text: '{activity_text}'")

                if hasattr(self, 'activity_label'):
                    self.activity_label.setText(f"Activity: {activity_text}")
                    self._log("✅ Updated activity_label")

                if hasattr(self, 'status_current_activity'):
                    self.status_current_activity.setText(activity_text)
                    self._log("✅ Updated status_current_activity")

                # Handle location display
                activity_type = activity_data.get('activity_type', 'LOADING')
                activity_details = activity_data.get('activity_data')

                if activity_type == 5:  # LOCATION
                    if isinstance(activity_details, dict) and 'location_name' in activity_details:
                        location_name = activity_details['location_name']
                        if hasattr(self, 'status_current_location'):
                            self.status_current_location.setText(location_name)
                            self._log(f"✅ Updated location: {location_name}")
                elif activity_type == 6:  # MAP_LOCATION
                    if isinstance(activity_details, dict) and 'location_name' in activity_details:
                        location_name = activity_details['location_name']
                        if hasattr(self, 'status_current_location'):
                            self.status_current_location.setText(f"Thinking of traveling to {location_name}")
                            self._log(f"✅ Updated map location: {location_name}")
                elif activity_type == 3:  # DOMAIN
                    if isinstance(activity_details, dict) and 'domain_name' in activity_details:
                        if hasattr(self, 'status_current_location'):
                            self.status_current_location.setText(activity_details['domain_name'])
                else:
                    if hasattr(self, 'status_current_location'):
                        self.status_current_location.setText("Unknown")

            if 'current_characters' in data:
                characters = data['current_characters']
                active_char_idx = data.get('current_active_character', 0)
                self._log(f"👥 Characters: {len(characters)} total, active: {active_char_idx}")

                # Update character display for active character
                if active_char_idx and 1 <= active_char_idx <= 4 and characters[active_char_idx - 1]:
                    char = characters[active_char_idx - 1]
                    if isinstance(char, dict):
                        char_name = char.get('character_display_name', 'Unknown')
                        if hasattr(self, 'status_current_character'):
                            self.status_current_character.setText(char_name)
                            self._log(f"🎭 Active character: {char_name}")
                        # Update image if available
                        self._update_status_image("current_character", char.get('image_key'), "Characters")
                    else:
                        if hasattr(self, 'status_current_character'):
                            self.status_current_character.setText("None")
                else:
                    if hasattr(self, 'status_current_character'):
                        self.status_current_character.setText("None")

            if 'game_start_time' in data and data['game_start_time']:
                uptime_seconds = int(time.time() - data['game_start_time'])
                hours, remainder = divmod(uptime_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                if hasattr(self, 'status_uptime'):
                    self.status_uptime.setText(uptime_str)
                    self._log(f"⏰ Updated uptime: {uptime_str}")

            if 'pause_ocr' in data:
                game_status = "Paused" if data['pause_ocr'] else "Running"
                if hasattr(self, 'status_game_status'):
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
            activity_data = data.get('current_activity')
            if not activity_data:
                return None

            # Convert dict back to Activity object
            from datatypes import Activity, ActivityType
            activity_type = ActivityType(activity_data.get('activity_type', 'LOADING'))
            activity_obj = Activity(activity_type, activity_data.get('activity_data'))

            # Get current activity params
            current_params = activity_obj.to_update_params_dict()

            # Add character info if available
            characters = data.get('current_characters', [])
            active_char_idx = data.get('current_active_character', 0)
            if active_char_idx and 1 <= active_char_idx <= 4 and characters[active_char_idx - 1]:
                char = characters[active_char_idx - 1]
                current_params["small_image"] = char.get('image_key')
                current_params["small_text"] = f"Playing as {char.get('character_display_name', 'Unknown')}"

            # Add start time if available
            start_time = data.get('game_start_time')
            if start_time:
                current_params["start"] = start_time

            return current_params

        except Exception as e:
            self._log(f"❌ Error preparing RPC data: {e}")
            return None

    def _ensure_image_cache_dir(self):
        cache_dir = os.path.join(os.getenv('APPDATA'), 'GenshinImpactRichPresence', 'images')
        os.makedirs(cache_dir, exist_ok=True)
        return cache_dir

    def _download_image(self, image_key: str, category: str = "Characters") -> Optional[str]:
        """Download an image from GitHub if not cached"""
        if image_key in self.image_cache:
            return self.image_cache[image_key]

        cache_dir = self._ensure_image_cache_dir()
        image_path = os.path.join(cache_dir, f"{image_key}.png")

        # Check if already cached
        if os.path.exists(image_path):
            self.image_cache[image_key] = image_path
            return image_path

        # Download from GitHub
        try:
            github_url = f"https://raw.githubusercontent.com/ZANdewanai/Genshin-Impact-Rich-Presence/main/Image Assets/{category}/{image_key}.png"
            urllib.request.urlretrieve(github_url, image_path)
            self.image_cache[image_key] = image_path
            return image_path
        except Exception as e:
            # Try alternative URL patterns
            try:
                # Some images might be in different subfolders
                alt_url = f"https://raw.githubusercontent.com/ZANdewanai/Genshin-Impact-Rich-Presence/main/Image Assets/{image_key}.png"
                urllib.request.urlretrieve(alt_url, image_path)
                self.image_cache[image_key] = image_path
                return image_path
            except Exception as e2:
                # Try boss subfolder if category is Bosses
                if category == "Bosses":
                    try:
                        boss_url = f"https://raw.githubusercontent.com/ZANdewanai/Genshin-Impact-Rich-Presence/main/Image Assets/Bosses/World Bosses/{image_key}.png"
                        urllib.request.urlretrieve(boss_url, image_path)
                        self.image_cache[image_key] = image_path
                        return image_path
                    except Exception as e3:
                        pass
                print(f"Failed to download image {image_key}: {e2}")
                return None

    def _update_status_image(self, status_key: str, image_key: str, category: str = "Characters"):
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

                    # Convert PIL image to QPixmap
                    qimage = QImage(pil_image.tobytes(), pil_image.width, pil_image.height, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(qimage)

                    img_label.setPixmap(pixmap.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                    img_label.setText("")
                except Exception as e:
                    print(f"Failed to load image {image_key}: {e}")
                    img_label.setPixmap(QPixmap())
                    img_label.setText("")
            else:
                img_label.setPixmap(QPixmap())
                img_label.setText("")
        else:
            img_label.setPixmap(QPixmap())
            img_label.setText("")

    # Remove unused methods
    # def _monitor_subprocess(self): ... (removed)
    # def change_appearance_mode(self): ... (removed)

    def _update_status_display(self, activity: Activity):
        """Update the status display with images and text using shared data"""
        # Update activity text
        activity_text = self._get_activity_text(activity)

        # Update activity text in sidebar
        self.activity_label.setText(f"Activity: {activity_text}")

        # Update status display fields using shared data (this will be updated by _update_gui_from_data)
        # The actual data comes from the subprocess via shared file
        self.status_current_activity.setText(activity_text)

        # Location and character info will be updated by _update_gui_from_data when shared file is read


    # def change_appearance_mode(self): ... (removed as placeholder)

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

        # Clean up shared data file
        if os.path.exists(self.shared_data_file):
            try:
                os.remove(self.shared_data_file)
                self._log("Shared data file cleaned up")
            except:
                pass

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
