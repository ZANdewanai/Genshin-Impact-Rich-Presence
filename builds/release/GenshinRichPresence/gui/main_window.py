from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QIcon

from .config import Config
from .tabs.main_tab import MainTab
from .tabs.config_tab import ConfigTab
from .tabs.roster_tab import RosterTab
from .tabs.about_tab import AboutTab
from .styles import apply_material3_style


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.config = Config()
        self.config.load_from_file()
        self.config._load_shared_config()

        self.running = False
        self.rpc_running = False
        self.game_start_time = None
        self.main_process = None
        self.main_thread = None
        self.rpc_thread = None
        self.shared_data_file = None
        self.latest_rpc_data = None
        self.log_messages = []

        self.shared_data_file = self._get_shared_data_file()
        self.config.update_coordinates(self.shared_data_file)

        self._init_ui()

    def _get_shared_data_file(self):
        import os

        return os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "gui_shared_data.json"
        )

    def _init_ui(self):
        self.setWindowTitle("Genshin Impact Rich Presence v4.0")
        self.setGeometry(100, 100, 900, 700)

        try:
            self.setWindowIcon(QIcon("images/ApplicatonIcon.ico"))
        except:
            pass

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        main_content_layout = QVBoxLayout(self.central_widget)

        main_content = QWidget()
        main_content_layout_inner = QHBoxLayout(main_content)

        self._create_sidebar()
        main_content_layout_inner.addWidget(self.sidebar_widget, 0)

        self.tab_widget = QTabWidget()
        self.main_tab = MainTab(self)
        self.config_tab = ConfigTab(self)
        self.roster_tab = RosterTab(self)
        self.about_tab = AboutTab(self)

        self.tab_widget.addTab(self.main_tab.widget, "Main")
        self.tab_widget.addTab(self.config_tab.widget, "Configuration")
        self.tab_widget.addTab(self.roster_tab.widget, "Character Roster")
        self.tab_widget.addTab(self.about_tab.widget, "About")

        main_content_layout_inner.addWidget(self.tab_widget, 1)
        main_content_layout_inner.setStretchFactor(self.sidebar_widget, 0)
        main_content_layout_inner.setStretchFactor(self.tab_widget, 1)

        main_content_layout.addWidget(main_content)

    def _create_sidebar(self):
        self.sidebar_widget = QWidget()
        self.sidebar_widget.setObjectName("sidebar_widget")
        self.sidebar_widget.setFixedWidth(200)

        sidebar_layout = QVBoxLayout(self.sidebar_widget)

        logo_label = QLabel("Genshin Impact\nRich Presence")
        logo_label.setFont(QFont("Arial", 16, QFont.Bold))
        logo_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(logo_label)

        sidebar_layout.addStretch()

        self.start_button = QPushButton("Start Rich Presence")
        self.start_button.setObjectName("start_button")
        self.start_button.setFont(QFont("Arial", 10, QFont.Bold))
        self.start_button.clicked.connect(self.toggle_rpc)
        sidebar_layout.addWidget(self.start_button)

        self.status_label = QLabel("Status: Stopped")
        self.status_label.setObjectName("status_label")
        self.status_label.setFont(QFont("Arial", 9, QFont.Bold))
        self.status_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(self.status_label)

        self.activity_label = QLabel("Activity: Not running")
        self.activity_label.setObjectName("activity_label")
        self.activity_label.setFont(QFont("Arial", 8))
        self.activity_label.setWordWrap(True)
        self.activity_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(self.activity_label)

        sidebar_layout.addStretch()

        version_label = QLabel("v4.0")
        version_label.setObjectName("version_label")
        version_label.setFont(QFont("Arial", 10))
        version_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(version_label)

    def toggle_rpc(self):
        if not self.running:
            self._start_rpc()
        else:
            self._stop_rpc()

    def _start_rpc(self):
        self.rpc_running = True
        self.running = True
        self.game_start_time = None

        self.start_button.setText("Stop Rich Presence")
        self.status_label.setText("Status: Running")
        self.status_label.setStyleSheet("color: #2ecc71;")
        self.activity_label.setText("Activity: Starting...")

        self.log("Rich Presence started!")

    def _stop_rpc(self):
        self.running = False
        self.rpc_running = False

        if self.main_process:
            try:
                self.main_process.terminate()
                self.main_process.wait(timeout=5)
            except:
                self.main_process.kill()
            self.main_process = None

        self.start_button.setText("Start Rich Presence")
        self.status_label.setText("Status: Stopped")
        self.status_label.setStyleSheet("color: #e74c3c;")
        self.activity_label.setText("Activity: Not running")

        self.log("Rich Presence stopped.")

    def log(self, message):
        import time

        timestamp = time.strftime("%H:%M:%S")
        self.log_messages.append(f"[{timestamp}] {message}")
        if len(self.log_messages) > 50:
            self.log_messages = self.log_messages[-50:]
        if hasattr(self, "main_tab"):
            self.main_tab.update_log("\n".join(self.log_messages))
