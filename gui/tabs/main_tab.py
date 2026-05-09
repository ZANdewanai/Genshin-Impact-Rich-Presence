from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGroupBox,
    QTextEdit,
    QPushButton,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

FONT_FAMILY = "Segoe UI"


class MainTab:
    def __init__(self, main_window):
        self.main_window = main_window
        self.widget = QWidget()
        
        # Store references to value labels for updating
        self.value_labels = {}

        layout = QVBoxLayout(self.widget)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)

        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout(status_group)
        status_layout.setSpacing(12)

        status_header = QHBoxLayout()

        main_window.status_dot = QLabel()
        main_window.status_dot.setFixedSize(14, 14)
        main_window.status_dot.setStyleSheet(
            "background-color: #f44336; border-radius: 7px;"
        )
        status_header.addWidget(main_window.status_dot)

        main_window.status_text = QLabel("Stopped")
        main_window.status_text.setFont(QFont(FONT_FAMILY, 16, QFont.Bold))
        main_window.status_text.setStyleSheet("color: #e0e0e0;")
        status_header.addWidget(main_window.status_text)

        status_header.addStretch()

        main_window.start_button = QPushButton("Start Rich Presence")
        main_window.start_button.setCursor(Qt.PointingHandCursor)
        main_window.start_button.setMinimumWidth(160)
        main_window.start_button.clicked.connect(main_window.toggle_rpc)
        status_header.addWidget(main_window.start_button)

        status_layout.addLayout(status_header)

        layout.addWidget(status_group)

        details_group = QGroupBox("Current Activity")
        details_layout = QVBoxLayout(details_group)
        details_layout.setSpacing(12)

        detail_items = [
            ("Character:", "None", "character"),
            ("Location:", "Unknown", "location"),
            ("Activity:", "None", "activity"),
        ]

        for label_text, value_text, key in detail_items:
            row = QHBoxLayout()
            label = QLabel(label_text)
            label.setFont(QFont(FONT_FAMILY, 11, QFont.Bold))
            label.setStyleSheet("color: #bb86fc;")
            label.setFixedWidth(90)
            row.addWidget(label)
            
            value = QLabel(value_text)
            value.setFont(QFont(FONT_FAMILY, 11))
            value.setStyleSheet("color: #e0e0e0;")
            value.setWordWrap(True)
            self.value_labels[key] = value
            row.addWidget(value, 1)
            
            details_layout.addLayout(row)

        layout.addWidget(details_group)

        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout(log_group)
        log_layout.setContentsMargins(12, 16, 12, 12)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(180)
        log_layout.addWidget(self.log_text)

        layout.addWidget(log_group)
        
        layout.addStretch()

    def update_log(self, text):
        self.log_text.setPlainText(text)
        self.log_text.moveCursor(self.log_text.textCursor().End)

    def update_activity(self, character, location, activity):
        """Update the activity display with current data"""
        self.value_labels["character"].setText(str(character))
        self.value_labels["location"].setText(str(location))
        self.value_labels["activity"].setText(str(activity))
