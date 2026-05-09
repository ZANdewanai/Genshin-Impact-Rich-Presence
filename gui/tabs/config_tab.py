from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGroupBox,
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
        layout.setSpacing(16)

        user_group = QGroupBox("User Settings")
        user_layout = QVBoxLayout(user_group)
        user_layout.setSpacing(12)

        username_row = QHBoxLayout()
        username_label = QLabel("Username:")
        username_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        username_label.setFixedWidth(120)
        username_row.addWidget(username_label)

        self.username_entry = QLineEdit(main_window.config.USERNAME)
        self.username_entry.setFont(QFont("Segoe UI", 10))
        username_row.addWidget(self.username_entry)
        user_layout.addLayout(username_row)

        mc_row = QHBoxLayout()
        mc_label = QLabel("Main Character:")
        mc_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        mc_label.setFixedWidth(120)
        mc_row.addWidget(mc_label)

        self.mc_combo = QComboBox()
        self.mc_combo.setFont(QFont("Segoe UI", 10))
        self.mc_combo.addItems(["Aether (Male)", "Lumine (Female)"])
        self.mc_combo.setCurrentText(
            "Aether (Male)" if main_window.config.MC_AETHER else "Lumine (Female)"
        )
        mc_row.addWidget(self.mc_combo)
        user_layout.addLayout(mc_row)

        wanderer_row = QHBoxLayout()
        wanderer_label = QLabel("Wanderer Name:")
        wanderer_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        wanderer_label.setFixedWidth(120)
        wanderer_row.addWidget(wanderer_label)

        self.wanderer_entry = QLineEdit(main_window.config.WANDERER_NAME)
        self.wanderer_entry.setFont(QFont("Segoe UI", 10))
        wanderer_row.addWidget(self.wanderer_entry)
        user_layout.addLayout(wanderer_row)

        layout.addWidget(user_group)

        perf_group = QGroupBox("Performance")
        perf_layout = QVBoxLayout(perf_group)

        self.gpu_checkbox = QCheckBox("Enable GPU acceleration for OCR")
        self.gpu_checkbox.setFont(QFont("Segoe UI", 10))
        self.gpu_checkbox.setChecked(main_window.config.USE_GPU)
        perf_layout.addWidget(self.gpu_checkbox)

        layout.addWidget(perf_group)

        status_row = QHBoxLayout()
        status_row.addStretch()

        self.config_status_label = QLabel("")
        self.config_status_label.setFont(QFont("Segoe UI", 10))
        self.config_status_label.setVisible(False)
        status_row.addWidget(self.config_status_label)

        save_button = QPushButton("Save Settings")
        save_button.setCursor(Qt.PointingHandCursor)
        save_button.clicked.connect(self._save_config)
        status_row.addWidget(save_button)

        status_row.addStretch()

        layout.addLayout(status_row)

    def _save_config(self):
        self.main_window.config.USERNAME = self.username_entry.text()
        self.main_window.config.MC_AETHER = self.mc_combo.currentText().startswith(
            "Aether"
        )
        self.main_window.config.WANDERER_NAME = self.wanderer_entry.text()
        self.main_window.config.USE_GPU = self.gpu_checkbox.isChecked()

        if self.main_window.config.save_to_file():
            self._show_status("Settings saved successfully!", "#4caf50")
        else:
            self._show_status("Error saving settings", "#f44336")

    def _show_status(self, message, color):
        from PyQt5.QtWidgets import QTimer

        self.config_status_label.setText(message)
        self.config_status_label.setStyleSheet(f"color: {color};")
        self.config_status_label.setVisible(True)
        QTimer.singleShot(2000, lambda: self.config_status_label.setVisible(False))
