import os
import sys
import json
import subprocess
import time
import threading

from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QFrame,
    QGroupBox,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QPalette, QColor

from .config import Config
from .tabs.main_tab import MainTab
from .tabs.config_tab import ConfigTab
from .tabs.about_tab import AboutTab

# Constants
FONT_FAMILY = "Segoe UI"


class MainWindow(QMainWindow):
    # Signal for thread-safe logging
    log_signal = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()

        self.config = Config()
        self.config.load_from_file()
        self.config._load_shared_config()

        self.running = False
        self.rpc_process = None
        self.log_messages = []
        self.current_character = "None"
        self.current_location = "Unknown"
        self.current_activity = "None"

        self.shared_data_file = self._get_shared_data_file()
        self.config.update_coordinates(self.shared_data_file)

        # Timer for polling status updates
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._poll_status)
        
        # Connect log signal for thread-safe logging
        self.log_signal.connect(self._do_log)

        self._init_ui()
        self._apply_modern_style()

    def _get_shared_data_file(self):
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "gui_shared_data.json"
        )

    def _get_main_py_path(self):
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "main.py"
        )

    def _get_python_exe(self):
        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..",
            "python3.13.11_embedded",
            "python.exe"
        )

    def _init_ui(self):
        self.setWindowTitle("Genshin Impact Rich Presence")
        self.resize(850, 600)
        self.setMinimumSize(700, 500)

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(20)

        # Header with title and version
        header_layout = QHBoxLayout()
        
        header = QLabel("Genshin Impact Rich Presence")
        header.setObjectName("appTitle")
        header.setFont(QFont(FONT_FAMILY, 24, QFont.Bold))
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        version = QLabel("v4.0")
        version.setObjectName("version")
        version.setFont(QFont(FONT_FAMILY, 12))
        header_layout.addWidget(version)
        
        main_layout.addLayout(header_layout)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("mainTabs")
        self.tab_widget.setFont(QFont(FONT_FAMILY, 10))

        self.main_tab = MainTab(self)
        self.config_tab = ConfigTab(self)
        self.about_tab = AboutTab(self)

        self.tab_widget.addTab(self.main_tab.widget, " Status ")
        self.tab_widget.addTab(self.config_tab.widget, " Settings ")
        self.tab_widget.addTab(self.about_tab.widget, " About ")

        main_layout.addWidget(self.tab_widget)

    def _apply_modern_style(self):
        """Apply modern dark theme styling"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
            
            #centralWidget {
                background-color: #121212;
            }
            
            #appTitle {
                color: #bb86fc;
                background-color: transparent;
            }
            
            #version {
                color: #9e9e9e;
                padding: 4px 12px;
                background-color: #1e1e1e;
                border-radius: 12px;
            }
            
            #mainTabs::pane {
                border: none;
                background-color: #1e1e1e;
                border-radius: 12px;
            }
            
            QLabel {
                color: #e0e0e0;
                background-color: transparent;
            }
            
            QTabBar::tab {
                background-color: transparent;
                color: #9e9e9e;
                padding: 12px 24px;
                border: none;
                border-bottom: 2px solid transparent;
                font-weight: 500;
            }
            
            QTabBar::tab:selected {
                color: #bb86fc;
                border-bottom: 2px solid #bb86fc;
            }
            
            QTabBar::tab:hover:!selected {
                color: #e0e0e0;
            }
            
            QGroupBox {
                background-color: #1e1e1e;
                border: 1px solid #2c2c2c;
                border-radius: 12px;
                margin-top: 12px;
                padding-top: 16px;
                font-weight: 600;
                color: #bb86fc;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px;
            }
            
            QPushButton {
                background-color: #bb86fc;
                color: #121212;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
            }
            
            QPushButton:hover {
                background-color: #c995fd;
            }
            
            QPushButton:pressed {
                background-color: #9f55e0;
            }
            
            QPushButton:disabled {
                background-color: #3d3d3d;
                color: #757575;
            }
            
            QLineEdit {
                background-color: #2c2c2c;
                color: #e0e0e0;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 8px 12px;
            }
            
            QLineEdit:focus {
                border: 2px solid #bb86fc;
            }
            
            QComboBox {
                background-color: #2c2c2c;
                color: #e0e0e0;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 8px 12px;
            }
            
            QCheckBox {
                color: #e0e0e0;
                spacing: 8px;
            }
            
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
                border: 2px solid #757575;
                border-radius: 4px;
            }
            
            QCheckBox::indicator:checked {
                background-color: #bb86fc;
                border-color: #bb86fc;
            }
            
            QTextEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #2c2c2c;
                border-radius: 8px;
                padding: 12px;
                font-family: "Consolas", "Monaco", monospace;
                font-size: 12px;
            }
            
            QLabel {
                color: #e0e0e0;
            }
            
            QScrollArea {
                border: none;
            }
        """)

    def toggle_rpc(self):
        if not self.running:
            self._start_rpc()
        else:
            self._stop_rpc()

    def _start_rpc(self):
        """Launch the rich presence process"""
        try:
            # Save current config to shared config file
            self._save_shared_config()
            
            # Get paths
            python_exe = self._get_python_exe()
            main_py = self._get_main_py_path()
            
            # Check if python exists
            if not os.path.exists(python_exe):
                self.log(f"ERROR: Python not found at {python_exe}")
                return
            
            # Check if main.py exists
            if not os.path.exists(main_py):
                self.log(f"ERROR: main.py not found at {main_py}")
                return
            
            # Prepare environment
            env = os.environ.copy()
            if self.config.USE_GPU:
                env["CUDA_VISIBLE_DEVICES"] = "0"
            else:
                env["CUDA_VISIBLE_DEVICES"] = ""
            
            # Launch the RPC process with output capture for GUI
            self.rpc_process = subprocess.Popen(
                [python_exe, main_py],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=env,
                cwd=os.path.dirname(main_py),
                encoding='utf-8',
                errors='replace'
            )
            
            self.running = True
            self.start_button.setText("Stop Rich Presence")
            self.status_dot.setStyleSheet("background-color: #4caf50; border-radius: 6px;")
            self.status_text.setText("Running")
            
            self.log("Rich Presence started!")
            
            # Start polling for updates
            self.status_timer.start(1000)  # Poll every second
            
            # Start reading output threads
            import threading
            threading.Thread(target=self._read_stdout, daemon=True).start()
            threading.Thread(target=self._read_stderr, daemon=True).start()
            
        except Exception as e:
            self.log(f"ERROR starting RPC: {e}")
            self._stop_rpc()

    def _stop_rpc(self):
        """Stop the rich presence process"""
        self.running = False
        self.status_timer.stop()
        
        if self.rpc_process:
            try:
                self.rpc_process.terminate()
                self.rpc_process.wait(timeout=3)
            except (OSError, subprocess.TimeoutExpired):
                try:
                    self.rpc_process.kill()
                except OSError:
                    pass
            self.rpc_process = None
        
        self.start_button.setText("Start Rich Presence")
        self.status_dot.setStyleSheet("background-color: #f44336; border-radius: 6px;")
        self.status_text.setText("Stopped")
        self.current_activity = "None"
        self._update_activity_display()
        
        self.log("Rich Presence stopped.")

    def _read_stdout(self):
        """Read stdout from RPC process in separate thread"""
        try:
            if self.rpc_process and self.rpc_process.stdout:
                for line in iter(self.rpc_process.stdout.readline, ''):
                    if line:
                        self.log_signal.emit(line.rstrip())
                    if not self.running:
                        break
        except (IOError, OSError) as err:
            self.log_signal.emit(f"[stdout error: {err}]")

    def _read_stderr(self):
        """Read stderr from RPC process in separate thread"""
        try:
            if self.rpc_process and self.rpc_process.stderr:
                for line in iter(self.rpc_process.stderr.readline, ''):
                    if line:
                        self.log_signal.emit(f"[ERROR] {line.rstrip()}")
                    if not self.running:
                        break
        except (IOError, OSError) as err:
            self.log_signal.emit(f"[stderr error: {err}]")

    def _poll_status(self):
        """Poll shared data file for status updates"""
        if not self.running:
            return
        
        try:
            if os.path.exists(self.shared_data_file):
                with open(self.shared_data_file, "r") as f:
                    data = json.load(f)
                
                # Update display with latest data
                char = data.get("active_characters", ["None"])[0] if data.get("active_characters") else "None"
                loc = data.get("location", "Unknown")
                activity = data.get("activity", "None")
                
                if char != self.current_character or loc != self.current_location or activity != self.current_activity:
                    self.current_character = char
                    self.current_location = loc
                    self.current_activity = activity
                    self._update_activity_display()
                    
        except Exception as e:
            pass
        
        # Check if process is still alive
        if self.rpc_process and self.rpc_process.poll() is not None:
            self.log("RPC process ended unexpectedly")
            self._stop_rpc()

    def _update_activity_display(self):
        """Update the activity display in the main tab"""
        if hasattr(self.main_tab, 'update_activity'):
            self.main_tab.update_activity(
                self.current_character,
                self.current_location,
                self.current_activity
            )

    def _save_shared_config(self):
        """Save config to shared file for main.py to read"""
        shared_config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "shared_config.json"
        )
        try:
            config_dict = {
                "USERNAME": self.config.USERNAME,
                "MC_AETHER": self.config.MC_AETHER,
                "WANDERER_NAME": self.config.WANDERER_NAME,
                "GAME_RESOLUTION": self.config.GAME_RESOLUTION,
                "USE_GPU": self.config.USE_GPU,
            }
            with open(shared_config_path, "w") as f:
                json.dump(config_dict, f, indent=4)
        except Exception as e:
            self.log(f"Warning: Could not save shared config: {e}")

    def log(self, message):
        """Add a log message - can be called from any thread"""
        # Emit signal for thread-safe GUI update
        self.log_signal.emit(message)
    
    def _do_log(self, message):
        """Actually update the GUI log (runs on main thread)"""
        timestamp = time.strftime("%H:%M:%S")
        self.log_messages.append(f"[{timestamp}] {message}")
        if len(self.log_messages) > 100:
            self.log_messages = self.log_messages[-100:]
        if hasattr(self, "main_tab"):
            self.main_tab.update_log("\n".join(self.log_messages))

    def closeEvent(self, event):
        """Handle window close"""
        if self.running:
            self._stop_rpc()
        event.accept()
