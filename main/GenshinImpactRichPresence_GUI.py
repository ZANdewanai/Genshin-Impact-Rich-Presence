# ==========================================
# Genshin Impact Rich Presence GUI v2.6
# Advanced GUI wrapper with comprehensive settings
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
import customtkinter
import tkinter as tk
from tkinter import messagebox, filedialog
import numpy as np
import psutil
import pypresence as discord
import win32gui
import win32con
import win32process
from PIL import Image, ImageGrab
import urllib.request

# Typing imports
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum, auto

# ==========================================
# Data Types and Enums
# ==========================================

class ActivityType(Enum):
    LOADING = auto()
    LOCATION = auto()
    DOMAIN = auto()
    COMMISSION = auto()
    BOSS = auto()
    IDLE = auto()
    PAUSED = auto()

@dataclass
class Character:
    character_name: str
    character_display_name: str
    image_key: str

@dataclass
class Location:
    location_name: str
    search_str: str

@dataclass
class Activity:
    activity_type: ActivityType
    activity_data: Any
    start_time: Optional[int] = None
    
    def __post_init__(self):
        if self.start_time is None:
            self.start_time = int(time.time())
    
    def is_idle(self) -> bool:
        return self.activity_type in [ActivityType.IDLE, ActivityType.PAUSED]
    
    def to_update_params_dict(self) -> dict:
        params = {
            "details": "Genshin Impact",
            "state": "In Game",
            "large_image": "gi_icon",
            "large_text": "Genshin Impact",
            "start": self.start_time,
        }
        
        if self.activity_type == ActivityType.LOADING:
            params["state"] = "Loading..."
        elif self.activity_type == ActivityType.LOCATION:
            params["state"] = f"Exploring {self.activity_data.location_name}"
        elif self.activity_type == ActivityType.DOMAIN:
            params["state"] = f"In Domain: {self.activity_data}"
        elif self.activity_type == ActivityType.COMMISSION:
            params["state"] = "Completing Commissions"
        elif self.activity_type == ActivityType.BOSS:
            params["state"] = f"Fighting {self.activity_data}"
        elif self.activity_type == ActivityType.PAUSED:
            params["state"] = "Game Paused"
        
        return params

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
        
        # Calculate scale factor based on height ratio
        scale = self.GAME_RESOLUTION / BASE_HEIGHT
        
        # Define base coordinates for 1080p
        if self.GAME_RESOLUTION == 1080:
            # 1080p coordinates (base)
            self.NUMBER_4P_COORD = [
                (2484, 356),   # Char 1
                (2484, 481),   # Char 2
                (2484, 610),   # Char 3
                (2484, 735),   # Char 4
            ]
            
            self.NAMES_4P_COORD = [
                (2166, 320, 2365, 395),  # Char 1
                (2166, 445, 2365, 520),  # Char 2
                (2166, 575, 2365, 650),  # Char 3
                (2166, 705, 2365, 780),  # Char 4
            ]
            
            self.BOSS_COORD = (943, 6, 1614, 66)
            self.LOCATION_COORD = (702, 240, 1838, 345)
            
        else:
            # For other resolutions, scale from 1080p coordinates
            # Character number coordinates (for active character detection)
            self.NUMBER_4P_COORD = [
                (int(2484 * scale), int(356 * scale)),  # Char 1
                (int(2484 * scale), int(481 * scale)),  # Char 2
                (int(2484 * scale), int(610 * scale)),  # Char 3
                (int(2484 * scale), int(735 * scale)),  # Char 4
            ]
            
            # Character name coordinates
            self.NAMES_4P_COORD = [
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
            self.BOSS_COORD = (
                int(943 * scale),   # x1
                int(6 * scale),     # y1
                int(1614 * scale),  # x2
                int(66 * scale)     # y2
            )
            
            self.LOCATION_COORD = (
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

class GenshinRichPresenceApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        
        # Initialize configuration
        self.config = Config()
        self.config.load_from_file()  # This will try to load from AppData

        # Initialize app state
        self.running = False
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
        self.ocr_thread = None
        self.main_process = None  # Process for main.py

        # Initialize image cache
        self.image_cache = {}
        self._ensure_image_cache_dir()
        
        # Setup UI
        self.title("Genshin Impact Rich Presence v2.6")
        self.geometry("900x700")
        
        # Set appearance
        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("blue")
        
        # Configure grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # Create sidebar
        self._create_sidebar()
        
        # Create tabs
        self.tabview = customtkinter.CTkTabview(self)
        self.tabview.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        # Add tabs
        self.tab_main = self.tabview.add("Main")
        self.tab_config = self.tabview.add("Configuration")
        self.tab_about = self.tabview.add("About")
        
        # Setup tab contents
        self._setup_main_tab()
        self._setup_config_tab()
        self._setup_about_tab()
        
        # Start with main tab selected
        self.tabview.set("Main")
        
        # Start RPC thread
        self._start_rpc_thread()
    
    def _create_sidebar(self):
        """Create the sidebar with app controls"""
        # Sidebar frame
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        
        # Logo and title
        self.logo_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            text="Genshin Impact\nRich Presence",
            font=customtkinter.CTkFont(size=20, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))



        # Start/Stop button
        self.start_button = customtkinter.CTkButton(
            self.sidebar_frame,
            text="Start Rich Presence",
            command=self.toggle_rpc,
            fg_color=("#2ecc71", "#27ae60"),
            hover_color=("#27ae60", "#229954"),
            font=customtkinter.CTkFont(weight="bold")
        )
        self.start_button.grid(row=2, column=0, padx=20, pady=10)
        
        # Status indicator
        self.status_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            text="Status: Stopped",
            text_color=("#e74c3c", "#c0392b"),
            font=customtkinter.CTkFont(weight="bold")
        )
        self.status_label.grid(row=3, column=0, padx=20, pady=5)

        # Current activity
        self.activity_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            text="Activity: Not running",
            wraplength=120,
            justify="center"
        )
        self.activity_label.grid(row=4, column=0, padx=20, pady=5)
        
        # Appearance mode
        self.appearance_mode_label = customtkinter.CTkLabel(
            self.sidebar_frame, 
            text="Appearance Mode:",
            anchor="w"
        )
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        
        self.appearance_mode_menu = customtkinter.CTkOptionMenu(
            self.sidebar_frame,
            values=["Light", "Dark", "System"],
            command=self.change_appearance_mode
        )
        self.appearance_mode_menu.grid(row=6, column=0, padx=20, pady=(0, 10))
        
        # Version info
        self.version_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            text="v2.6",
            text_color=("gray60", "gray40")
        )
        self.version_label.grid(row=7, column=0, padx=20, pady=10)
    
    def _setup_main_tab(self):
        """Setup the main tab with status information"""
        # Main tab configuration
        self.tab_main.grid_columnconfigure(0, weight=1)
        self.tab_main.grid_rowconfigure(1, weight=1)

        # Title
        title_label = customtkinter.CTkLabel(
            self.tab_main,
            text="Genshin Impact Rich Presence",
            font=customtkinter.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")

        # Status frame
        status_frame = customtkinter.CTkFrame(self.tab_main)
        status_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        status_frame.grid_columnconfigure(1, weight=1)

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
            img_label = customtkinter.CTkLabel(status_frame, text="", width=32, height=32)
            img_label.grid(row=i, column=0, padx=(10, 5), pady=5, sticky="w")

            # Label
            lbl = customtkinter.CTkLabel(
                status_frame,
                text=label,
                font=customtkinter.CTkFont(weight="bold")
            )
            lbl.grid(row=i, column=1, padx=(0, 5), pady=5, sticky="w")

            # Value
            value_var = customtkinter.StringVar(value=value)
            value_lbl = customtkinter.CTkLabel(
                status_frame,
                textvariable=value_var,
                anchor="w"
            )
            value_lbl.grid(row=i, column=2, padx=(0, 10), pady=5, sticky="ew")

            # Store references for updating
            setattr(self, f"status_img_{label.lower().replace(' ', '_').replace(':', '')}", img_label)
            setattr(self, f"status_{label.lower().replace(' ', '_').replace(':', '')}", value_var)

        # Log area
        log_label = customtkinter.CTkLabel(
            self.tab_main,
            text="Activity Log:",
            font=customtkinter.CTkFont(weight="bold")
        )
        log_label.grid(row=2, column=0, padx=20, pady=(20, 5), sticky="w")

        self.log_text = customtkinter.CTkTextbox(
            self.tab_main,
            height=150,
            state="disabled"
        )
        self.log_text.grid(row=3, column=0, padx=20, pady=(0, 20), sticky="nsew")
    
    def _setup_config_tab(self):
        """Setup the configuration tab"""
        # Configuration tab setup
        self.tab_config.grid_columnconfigure(1, weight=1)
        
        # Title
        title_label = customtkinter.CTkLabel(
            self.tab_config,
            text="Configuration",
            font=customtkinter.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, padx=20, pady=10, sticky="w")
        
        # User settings frame
        user_frame = customtkinter.CTkFrame(self.tab_config)
        user_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        # Game settings frame
        game_frame = customtkinter.CTkFrame(self.tab_config)
        game_frame.grid(row=1, column=1, padx=20, pady=10, sticky="nsew")
        
        # Performance settings frame
        perf_frame = customtkinter.CTkFrame(self.tab_config)
        perf_frame.grid(row=2, column=0, columnspan=2, padx=20, pady=10, sticky="nsew")
        
        # User settings
        user_label = customtkinter.CTkLabel(
            user_frame,
            text="User Settings",
            font=customtkinter.CTkFont(weight="bold")
        )
        user_label.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")
        
        # Username
        customtkinter.CTkLabel(user_frame, text="Username:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.username_var = customtkinter.StringVar(value=self.config.USERNAME)
        customtkinter.CTkEntry(user_frame, textvariable=self.username_var).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # Main character
        customtkinter.CTkLabel(user_frame, text="Main Character:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.mc_aether_var = customtkinter.BooleanVar(value=self.config.MC_AETHER)
        customtkinter.CTkOptionMenu(
            user_frame,
            values=["Aether (Male)", "Lumine (Female)"],
            variable=customtkinter.StringVar(value="Aether (Male)" if self.config.MC_AETHER else "Lumine (Female)"),
            command=lambda x: self.mc_aether_var.set(x.startswith("Aether"))
        ).grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        
        # Wanderer name
        customtkinter.CTkLabel(user_frame, text="Wanderer Name:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.wanderer_name_var = customtkinter.StringVar(value=self.config.WANDERER_NAME)
        customtkinter.CTkEntry(user_frame, textvariable=self.wanderer_name_var).grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        
        # Game settings
        game_label = customtkinter.CTkLabel(
            game_frame,
            text="Game Settings",
            font=customtkinter.CTkFont(weight="bold")
        )
        game_label.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")
        
        # Performance settings
        perf_label = customtkinter.CTkLabel(
            perf_frame,
            text="Performance Settings",
            font=customtkinter.CTkFont(weight="bold")
        )
        perf_label.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")
        
        # Save button
        save_btn = customtkinter.CTkButton(
            self.tab_config,
            text="Save Settings",
            command=self._save_config,
            fg_color=("#2ecc71", "#27ae60"),
            hover_color=("#27ae60", "#229954")
        )
        save_btn.grid(row=3, column=0, columnspan=2, pady=20)
    
    def _setup_about_tab(self):
        """Setup the about tab"""
        # About tab setup
        self.tab_about.grid_columnconfigure(0, weight=1)
        self.tab_about.grid_rowconfigure(1, weight=1)
        
        # Title
        title_label = customtkinter.CTkLabel(
            self.tab_about,
            text="About Genshin Impact Rich Presence",
            font=customtkinter.CTkFont(size=20, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        # Info text
        info_text = """Genshin Impact Rich Presence v2.6

This application displays your current in-game activity on Discord.

Features:
- Shows your current character and location
- Detects when you're in domains or fighting bosses
- Works with any resolution
- Lightweight and easy to use

Created by ZANdewanai
Rewritten by euwbah

Image assets are intellectual property of HoYoverse
All rights reserved by miHoYo"""
        
        info_label = customtkinter.CTkLabel(
            self.tab_about,
            text=info_text,
            justify="left"
        )
        info_label.grid(row=1, column=0, padx=20, pady=10, sticky="nw")
    
    def _on_resolution_change(self, value):
        """Handle resolution change in the UI"""
        if value == "Custom":
            # Show custom resolution dialog
            dialog = customtkinter.CTkInputDialog(
                text="Enter custom resolution height (e.g., 1080):",
                title="Custom Resolution"
            )
            try:
                res = int(dialog.get_input())
                if res > 0:
                    self.config.GAME_RESOLUTION = res
                    self.resolution_var.set(str(res))
            except (ValueError, TypeError):
                self.resolution_var.set("1080")
        else:
            self.config.GAME_RESOLUTION = int(value)
        
        # Update coordinates based on new resolution
        self.config.update_coordinates()
    
    def _save_config(self):
        """Save configuration from UI to config object"""
        self.config.USERNAME = self.username_var.get()
        self.config.MC_AETHER = self.mc_aether_var.get()
        self.config.WANDERER_NAME = self.wanderer_name_var.get()
        self.config.USE_GPU = self.use_gpu_var.get()
        
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
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{time.strftime('%H:%M:%S')}] {message}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
    
    def _start_rpc_thread(self):
        """Start the Discord RPC thread"""
        self.rpc_thread = threading.Thread(target=self._rpc_loop, daemon=True)
        self.rpc_thread.start()
    
    def _rpc_loop(self):
        """Main RPC update loop"""
        rpc = None
        
        def init_discord_rpc():
            nonlocal rpc
            while True:
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
        
        while True:
            if rpc is None:
                init_discord_rpc()
            
            try:
                # Get current activity params
                params = self.current_activity.to_update_params_dict()
                
                # Add character info if available
                if hasattr(self, 'current_active_character') and 1 <= self.current_active_character <= 4:
                    char = self.current_characters[self.current_active_character - 1]
                    if char is not None:
                        params["small_image"] = char.image_key
                        params["small_text"] = f"Playing as {char.character_display_name}"
                
                # Update RPC if params changed
                if params != previous_update:
                    rpc.update(**params)
                    previous_update = params
                    
                    # Update UI
                    self.after(0, self._update_status_display, self.current_activity)
                
                time.sleep(1)  # Rate limit to 1 update per second
                
            except discord.exceptions.InvalidID:
                # Discord closed, need to reconnect
                rpc = None
                continue
            except Exception as e:
                self._log(f"Error updating RPC: {e}")
                time.sleep(5)
    
    def _update_activity_display(self, activity: Activity):
        """Update the activity display in the UI"""
        activity_text = "Unknown"
        
        if activity.activity_type == ActivityType.LOADING:
            activity_text = "Loading..."
        elif activity.activity_type == ActivityType.LOCATION:
            activity_text = f"Exploring {activity.activity_data.location_name}"
        elif activity.activity_type == ActivityType.DOMAIN:
            activity_text = f"In Domain: {activity.activity_data}"
        elif activity.activity_type == ActivityType.COMMISSION:
            activity_text = "Completing Commissions"
        elif activity.activity_type == ActivityType.BOSS:
            activity_text = f"Fighting {activity.activity_data}"
        elif activity.activity_type == ActivityType.PAUSED:
            activity_text = "Game Paused"
        
        self.activity_label.configure(text=f"Activity: {activity_text}")
    
    def toggle_rpc(self):
        """Toggle the Rich Presence on/off"""
        if not self.running:
            try:
                # Always run main.py as subprocess - more reliable than inline OCR
                # Get the current working directory and look for main.py there
                current_dir = os.getcwd()
                main_script = os.path.join(current_dir, "main.py")

                if not os.path.exists(main_script):
                    # Try to find main.py in the same directory as this script
                    script_dir = os.path.dirname(os.path.abspath(__file__))
                    main_script = os.path.join(script_dir, "main.py")

                if os.path.exists(main_script):
                    self.main_process = subprocess.Popen(
                        [sys.executable, main_script],
                        cwd=current_dir,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True
                    )
                    # Start a thread to monitor the subprocess output
                    import threading
                    self.monitor_thread = threading.Thread(target=self._monitor_subprocess, daemon=True)
                    self.monitor_thread.start()
                else:
                    self._log(f"ERROR: main.py not found! Searched in: {main_script}")
                    return

                self.running = True
                self.start_button.configure(
                    text="Stop Rich Presence",
                    fg_color=("#e74c3c", "#c0392b"),
                    hover_color=("#c0392b", "#a93226")
                )
                self.status_label.configure(
                    text="Status: Running",
                    text_color=("#2ecc71", "#27ae60")
                )
                self._log("Rich Presence started!")
            except Exception as e:
                self._log(f"Failed to start Rich Presence: {e}")
        else:
            # Stop the thread/process
            self.running = False
            if self.main_process:
                try:
                    self.main_process.terminate()
                    self.main_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.main_process.kill()
                self.main_process = None

            self.start_button.configure(
                text="Start Rich Presence",
                fg_color=("#2ecc71", "#27ae60"),
                hover_color=("#27ae60", "#229954")
            )
            self.status_label.configure(
                text="Status: Stopped",
                text_color=("#e74c3c", "#c0392b")
            )
            self._log("Rich Presence stopped.")

    def _run_main_inline(self):
        """Run the main OCR logic inline (for bundled exe)"""
        try:
            # Import main module functions
            import main
            # Run the main loop (modified to work inline)
            main.loop_count = 0
            main.current_characters = [None, None, None, None]
            main.current_active_character = 0
            main.game_start_time = None
            main.pause_ocr = False

            # Initialize OCR
            print("Initializing OCR.")
            print("OCR started.")
            print("_______________________________________________________________")

            # Main loop (simplified version)
            while self.running:
                try:
                    # Check if Genshin is running
                    print(f"[DEBUG] Checking Genshin window: class='UnityWndClass', name='Genshin Impact'")
                    if not main.ps_helper.check_process_window_open("UnityWndClass", "Genshin Impact"):
                        if main.current_activity.activity_type != main.ActivityType.IDLE:
                            main.current_activity = main.Activity(main.ActivityType.IDLE, False)
                            self.after(0, self._log, "Genshin Impact not detected. Waiting for game to start...")
                        time.sleep(5)
                        continue

                    # Run OCR detection (simplified)
                    main.loop_count += 1

                    # Character detection
                    if main.loop_count % main.OCR_CHARNAMES_ONE_IN == 0:
                        try:
                            charname_cap = [
                                main.np.array(main.ImageGrab.grab(bbox=main.NAMES_4P_COORD[i])) for i in range(4)
                            ]

                            char_results = [
                                [((0,0,0,0), pytesseract.image_to_string(img, config=f'--psm 6 -c tessedit_char_whitelist={main.ALLOWLIST}'), 1.0)] for img in charname_cap
                            ]

                            for character_index, result in enumerate(char_results):
                                if len(result) > 0:
                                    text = " ".join([word.strip() for word in [r[1] for r in result]])
                                    avg_conf = sum([r[2] for r in result]) / len(result)

                                    if text.strip():
                                        self.after(0, self._log, f"[DEBUG] Char {character_index + 1} OCR: '{text}' (conf: {avg_conf:.2f})")

                                    if avg_conf > main.NAME_CONF_THRESH:
                                        char = main.DATA.search_character(text)
                                        if char != None and (
                                            main.current_characters[character_index] == None
                                            or char != main.current_characters[character_index]
                                        ):
                                            main.current_characters[character_index] = char
                                            self.after(0, self._log, f"Detected character {character_index + 1}: {char.character_display_name}")
                                            # Update GUI
                                            self.after(0, self._update_status_display, main.current_activity)
                        except Exception as e:
                            self.after(0, self._log, f"OCR Error: {e}")

                    # Active character detection
                    try:
                        charnumber_cap = [
                            main.ImageGrab.grab(bbox=(main.NUMBER_4P_COORD[i][0], main.NUMBER_4P_COORD[i][1], main.NUMBER_4P_COORD[i][0] + 1, main.NUMBER_4P_COORD[i][1] + 1)).getpixel((0, 0))
                            for i in range(4)
                        ]
                        charnumber_brightness = [sum(rgb) for rgb in charnumber_cap]
                        active_character = [idx for idx, bri in enumerate(charnumber_brightness) if bri < main.ACTIVE_CHARACTER_THRESH]

                        if len(active_character) == 1 and active_character[0] + 1 != main.current_active_character:
                            main.current_active_character = active_character[0] + 1
                            if main.current_characters[main.current_active_character - 1] != None:
                                char_name = main.current_characters[main.current_active_character - 1].character_display_name
                                self.after(0, self._log, f'Switched active character to "{char_name}"')
                                self.after(0, self._update_status_display, main.current_activity)
                    except Exception as e:
                        pass

                    time.sleep(main.SLEEP_PER_ITERATION)

                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.after(0, self._log, f"Main loop error: {e}")
                    time.sleep(2)

        except Exception as e:
            self.after(0, self._log, f"Failed to run OCR inline: {e}")
            self.running = False
    
    def _get_genshin_window_size(self) -> Optional[Tuple[int, int]]:
        """Get the size of the Genshin Impact window"""
        try:
            def callback(hwnd, window_list):
                if win32gui.IsWindowVisible(hwnd):
                    window_text = win32gui.GetWindowText(hwnd)
                    if 'Genshin Impact' in window_text or 'YuanShen' in window_text:
                        rect = win32gui.GetWindowRect(hwnd)
                        width = rect[2] - rect[0]
                        height = rect[3] - rect[1]
                        # Only return if we have a reasonable window size
                        if width > 100 and height > 100:
                            window_list.append((width, height))
            
            windows = []
            win32gui.EnumWindows(callback, windows)
            
            if windows:
                # Return the first window found (should be the main game window)
                return windows[0]
            return None
        except Exception as e:
            self.after(0, self._log, f"Error detecting window size: {e}")
            return None
    
    def _is_genshin_running(self) -> bool:
        """Check if Genshin Impact is currently running"""
        try:
            # First try to get window size (which also checks if the process is running)
            if self._get_genshin_window_size() is not None:
                return True
                
            # Fallback to process check if window check fails
            for proc in psutil.process_iter(['pid', 'name']):
                if 'GenshinImpact' in proc.info.get('name', '') or 'YuanShen' in proc.info.get('name', ''):
                    return True
            return False
        except Exception as e:
            self.after(0, self._log, f"Error checking if Genshin is running: {e}")
            return False
    
    def _start_ocr_thread(self):
        """Start the OCR thread with GPU acceleration"""
        try:
            if self.ocr_thread is None or not self.ocr_thread.is_alive():
                self._log("Initializing OCR with GPU acceleration...")
                # Initialize with specific model path and GPU
                # OCR initialized
                self.ocr_thread = threading.Thread(target=self._ocr_loop, daemon=True)
                self.ocr_thread.start()
        except Exception as e:
            error_msg = f"Error initializing OCR: {str(e)}"
            self.after(0, self._log, error_msg)
            self.after(0, self._log, "Please ensure you have an NVIDIA GPU with CUDA installed.")
            self.running = False
    
    def _ocr_loop(self):
        """Main OCR loop for detecting game state"""
        self._log("OCR thread started. Make sure Genshin Impact is running in the background.")
        
        loop_count = 0
        last_activity = None
        last_active_character = 0
        consecutive_failures = 0
        last_resolution_check = 0
        detected_resolution = None
        
        while self.running:
            try:
                # Check if Genshin Impact is running and get its resolution
                window_size = self._get_genshin_window_size()
                if window_size is None:
                    if not isinstance(self.current_activity.activity_type, ActivityType) or self.current_activity.activity_type != ActivityType.IDLE:
                        self.current_activity = Activity(ActivityType.IDLE, False)
                        self._log("Genshin Impact not detected. Waiting for game to start...")
                    time.sleep(5)
                    continue
                
                # Auto-detect and update resolution if needed
                current_time = time.time()
                if current_time - last_resolution_check > 10:  # Check every 10 seconds
                    last_resolution_check = current_time
                    width, height = window_size
                    
                    # Only update if resolution changed significantly
                    if detected_resolution != (width, height):
                        detected_resolution = (width, height)
                        self.config.GAME_RESOLUTION = height  # Use height as the base for scaling
                        self.config.update_coordinates()
                        self._log(f"Auto-detected game resolution: {width}x{height}")
                        self._log(f"Using scale factor: {height/1080:.2f} (based on {height}p)")
                
                # Check if we need to update resolution (once every 60 seconds)
                current_time = time.time()
                if current_time - last_resolution_check > 60:  # Check every minute
                    last_resolution_check = current_time
                    _, height = window_size
                    # Only update if resolution changed significantly
                    if abs(height - self.config.GAME_RESOLUTION) > 10:  # 10px threshold
                        self.config.GAME_RESOLUTION = height
                        self.config.update_coordinates()
                        self._log(f"Detected game resolution: {window_size[0]}x{window_size[1]} (using height: {height}p)")
                        self._log(f"Updated coordinates with scale factor: {height/1080:.2f}")
                
                # Reset failure counter if we successfully detect the game
                consecutive_failures = 0
                
                # Get current timestamp for activity timing
                current_time = int(time.time())
                
                # Check if we should scan for character names (every OCR_CHARNAMES_ONE_IN loops)
                scan_characters = (loop_count % self.config.OCR_CHARNAMES_ONE_IN == 0)
                
                # Check if we should scan for location (every OCR_LOC_ONE_IN loops)
                scan_location = (loop_count % self.config.OCR_LOC_ONE_IN == 0)
                
                # Check if we should scan for boss/domain (every OCR_BOSS_ONE_IN loops)
                scan_boss = (loop_count % self.config.OCR_BOSS_ONE_IN == 0)
                
                # Detect active character
                active_char_idx = self._detect_active_character()
                if active_char_idx is not None and active_char_idx != last_active_character:
                    last_active_character = active_char_idx
                    self.current_active_character = active_char_idx
                    self._log(f"Active character changed to position {active_char_idx + 1}")
                
                # Scan character names if needed
                if scan_characters:
                    self._scan_character_names()
                
                # Scan location if needed
                location_text = None
                if scan_location:
                    location_text = self._scan_location()
                    if location_text:
                        self._log(f"Detected location: {location_text}")
                        self.current_activity = Activity(ActivityType.LOCATION, location_text, current_time)
                
                # Scan for boss/domain if needed
                if scan_boss:
                    boss_text = self._scan_boss_domain()
                    if boss_text:
                        self._log(f"Detected boss/domain: {boss_text}")
                        if "domain" in boss_text.lower():
                            self.current_activity = Activity(ActivityType.DOMAIN, boss_text, current_time)
                        else:
                            self.current_activity = Activity(ActivityType.BOSS, boss_text, current_time)
                
                # Update loop counter
                loop_count += 1
                time.sleep(self.config.SLEEP_PER_ITERATION)
                
            except Exception as e:
                consecutive_failures += 1
                error_msg = f"OCR Error (attempt {consecutive_failures}): {str(e)}"
                self.after(0, self._log, error_msg)
                
                if consecutive_failures > 5:  # If we fail too many times, set to idle
                    self.current_activity = Activity(ActivityType.IDLE, False)
                    self.after(0, self._log, "Multiple OCR failures. Setting status to idle.")
                
                time.sleep(2)  # Wait before retrying
    
    def install_dependencies(self):
        """Install dependencies by running install.py"""
        self._log("Starting dependency installation...")
        try:
            # Run install.py as subprocess
            result = subprocess.run(
                [sys.executable, "install.py"],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            # Log stdout
            if result.stdout:
                for line in result.stdout.splitlines():
                    self._log(f"INSTALL: {line}")
            
            # Log stderr
            if result.stderr:
                for line in result.stderr.splitlines():
                    self._log(f"INSTALL ERROR: {line}")
            
            if result.returncode == 0:
                self._log("Dependencies installed successfully!")
            else:
                self._log(f"Installation failed with return code {result.returncode}")
                
        except Exception as e:
            self._log(f"Error during installation: {e}")

    def _ensure_image_cache_dir(self):
        """Ensure the image cache directory exists"""
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
                print(f"Failed to download image {image_key}: {e2}")
                return None

    def _update_status_image(self, status_key: str, image_key: str, category: str = "Characters"):
        """Update the image for a status item"""
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
                    ctk_image = customtkinter.CTkImage(pil_image, size=(32, 32))
                    img_label.configure(image=ctk_image, text="")
                    img_label.image = ctk_image  # Keep reference
                except Exception as e:
                    print(f"Failed to load image {image_key}: {e}")
                    img_label.configure(image="", text="")
            else:
                img_label.configure(image="", text="")
        else:
            img_label.configure(image="", text="")

    def _monitor_subprocess(self):
        """Monitor the subprocess output and log it to the GUI"""
        if self.main_process and self.main_process.stdout:
            try:
                for line in iter(self.main_process.stdout.readline, ''):
                    if line.strip():
                        # Log the output to the GUI
                        self.after(0, self._log, f"OCR: {line.strip()}")
            except Exception as e:
                self.after(0, self._log, f"Error monitoring subprocess: {e}")

    def _update_status_display(self, activity: Activity):
        """Update the status display with images and text"""
        # Update activity text
        activity_text = "Unknown"
        if activity.activity_type == ActivityType.LOADING:
            activity_text = "Loading..."
        elif activity.activity_type == ActivityType.LOCATION:
            activity_text = f"Exploring {activity.activity_data.location_name}"
        elif activity.activity_type == ActivityType.DOMAIN:
            activity_text = f"In Domain: {activity.activity_data}"
        elif activity.activity_type == ActivityType.COMMISSION:
            activity_text = "Completing Commissions"
        elif activity.activity_type == ActivityType.BOSS:
            activity_text = f"Fighting {activity.activity_data}"
        elif activity.activity_type == ActivityType.PAUSED:
            activity_text = "Game Paused"
        elif activity.activity_type == ActivityType.IDLE:
            activity_text = "Game not detected"

        self.activity_label.configure(text=f"Activity: {activity_text}")

        # Update character image and text
        if hasattr(self, 'current_active_character') and 1 <= self.current_active_character <= 4:
            char = self.current_characters[self.current_active_character - 1]
            if char is not None:
                self.status_current_character.set(char.character_display_name)
                self._update_status_image("current_character", char.image_key, "Characters")
            else:
                self.status_current_character.set("None")
                self._update_status_image("current_character", None)
        else:
            self.status_current_character.set("None")
            self._update_status_image("current_character", None)

        # Update location text (no image for locations currently)
        if activity.activity_type == ActivityType.LOCATION:
            self.status_current_location.set(activity.activity_data.location_name)
        else:
            self.status_current_location.set("Unknown")

        # Update activity text
        self.status_current_activity.set(activity_text)

        # Update uptime
        if hasattr(self, 'game_start_time') and self.game_start_time:
            uptime_seconds = int(time.time()) - self.game_start_time
            hours, remainder = divmod(uptime_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            uptime_str = "00:00:00"
        self.status_uptime.set(uptime_str)

    def change_appearance_mode(self, new_appearance_mode: str):
        """Change UI appearance mode"""
        customtkinter.set_appearance_mode(new_appearance_mode.lower())

    def on_closing(self):
        """Handle window closing"""
        self.running = False
        self.destroy()

if __name__ == "__main__":
    app = GenshinRichPresenceApp()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()
