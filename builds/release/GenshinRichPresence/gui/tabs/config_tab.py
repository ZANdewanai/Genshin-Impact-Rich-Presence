from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QPushButton,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont


class ConfigTab:
    def __init__(self, main_window):
        self.main_window = main_window
        self.widget = QWidget()

        layout = QVBoxLayout(self.widget)

        title_label = QLabel("Configuration")
        title_label.setObjectName("config_title_label")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title_label)

        config_frame = QFrame()
        config_frame.setObjectName("config_frame")
        config_frame.setFrameStyle(QFrame.Box)
        config_main_layout = QHBoxLayout(config_frame)

        user_frame = QFrame()
        user_frame.setObjectName("user_frame")
        user_layout = QVBoxLayout(user_frame)

        user_label = QLabel("User Settings")
        user_label.setObjectName("user_label")
        user_label.setFont(QFont("Arial", 14, QFont.Bold))
        user_layout.addWidget(user_label)

        username_layout = QHBoxLayout()
        username_label = QLabel("Username:")
        username_label.setObjectName("username_label")
        username_label.setFont(QFont("Arial", 10))
        username_layout.addWidget(username_label)

        self.username_entry = QLineEdit(main_window.config.USERNAME)
        self.username_entry.setObjectName("username_entry")
        username_layout.addWidget(self.username_entry)
        user_layout.addLayout(username_layout)

        mc_layout = QHBoxLayout()
        mc_label = QLabel("Main Character:")
        mc_label.setObjectName("mc_label")
        mc_label.setFont(QFont("Arial", 10))
        mc_layout.addWidget(mc_label)

        self.mc_combo = QComboBox()
        self.mc_combo.setObjectName("mc_combo")
        self.mc_combo.addItems(["Aether (Male)", "Lumine (Female)"])
        self.mc_combo.setCurrentText(
            "Aether (Male)" if main_window.config.MC_AETHER else "Lumine (Female)"
        )
        mc_layout.addWidget(self.mc_combo)
        user_layout.addLayout(mc_layout)

        wanderer_layout = QHBoxLayout()
        wanderer_label = QLabel("Wanderer Name:")
        wanderer_label.setObjectName("wanderer_label")
        wanderer_label.setFont(QFont("Arial", 10))
        wanderer_layout.addWidget(wanderer_label)

        self.wanderer_entry = QLineEdit(main_window.config.WANDERER_NAME)
        self.wanderer_entry.setObjectName("wanderer_entry")
        wanderer_layout.addWidget(self.wanderer_entry)
        user_layout.addLayout(wanderer_layout)

        config_main_layout.addWidget(user_frame, 1)

        perf_frame = QFrame()
        perf_frame.setObjectName("perf_frame")
        perf_layout = QVBoxLayout(perf_frame)

        perf_label = QLabel("Performance Settings")
        perf_label.setObjectName("perf_label")
        perf_label.setFont(QFont("Arial", 14, QFont.Bold))
        perf_layout.addWidget(perf_label)

        self.gpu_checkbox = QCheckBox("Enable GPU acceleration for OCR")
        self.gpu_checkbox.setObjectName("gpu_checkbox")
        self.gpu_checkbox.setChecked(main_window.config.USE_GPU)
        self.gpu_checkbox.setFont(QFont("Arial", 10))
        perf_layout.addWidget(self.gpu_checkbox)

        perf_layout.addStretch()
        config_main_layout.addWidget(perf_frame, 1)

        layout.addWidget(config_frame)

        self.config_status_label = QLabel("")
        self.config_status_label.setObjectName("config_status_label")
        self.config_status_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.config_status_label.setAlignment(Qt.AlignCenter)
        self.config_status_label.setVisible(False)
        layout.addWidget(self.config_status_label)

        save_button = QPushButton("Save Settings")
        save_button.setObjectName("config_save_button")
        save_button.setFont(QFont("Arial", 12, QFont.Bold))
        save_button.clicked.connect(self._save_config)
        layout.addWidget(save_button)

        layout.addStretch()

    def _save_config(self):
        self.main_window.config.USERNAME = self.username_entry.text()
        self.main_window.config.MC_AETHER = self.mc_combo.currentText().startswith(
            "Aether"
        )
        self.main_window.config.WANDERER_NAME = self.wanderer_entry.text()
        self.main_window.config.USE_GPU = self.gpu_checkbox.isChecked()

        if self.main_window.config.save_to_file():
            self._show_status("Settings saved successfully!", "#2ecc71")
        else:
            self._show_status("Error saving settings", "#e74c3c")

    def _show_status(self, message, color):
        self.config_status_label.setText(message)
        self.config_status_label.setStyleSheet(f"color: {color}; padding: 5px;")
        self.config_status_label.setVisible(True)
        QTimer.singleShot(3000, lambda: self.config_status_label.setVisible(False))

    @property
    def get_widget(self):
        return self.widget
