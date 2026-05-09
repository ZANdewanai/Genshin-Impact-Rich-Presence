from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QSizePolicy
from PyQt5.QtGui import QFont


class AboutTab:
    def __init__(self, main_window):
        self.main_window = main_window
        self.widget = QWidget()

        layout = QVBoxLayout(self.widget)
        layout.setSpacing(16)

        info_group = QGroupBox("About")
        info_layout = QVBoxLayout(info_group)
        info_layout.setSpacing(12)

        title = QLabel("Genshin Impact Rich Presence")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        info_layout.addWidget(title)

        version = QLabel("Version 4.0")
        version.setFont(QFont("Segoe UI", 10))
        info_layout.addWidget(version)

        info_layout.addWidget(self._create_separator())

        desc = QLabel(
            "This application displays your current in-game activity on Discord.\n\n"
            "Features:\n"
            "• Shows your current character and location\n"
            "• Detects when you're in domains or fighting bosses\n"
            "• Works with any resolution\n"
            "• Lightweight and easy to use"
        )
        desc.setFont(QFont("Segoe UI", 10))
        desc.setWordWrap(True)
        info_layout.addWidget(desc)

        info_layout.addWidget(self._create_separator())

        credits = QLabel("Credits:")
        credits.setFont(QFont("Segoe UI", 10, QFont.Bold))
        info_layout.addWidget(credits)

        credit_text = QLabel(
            "Created by ZANdewanai\n"
            "Rewritten by euwbah\n"
            "Rewritten again by ZANdewanai\n\n"
            "Game assets are intellectual property of HoYoverse"
        )
        credit_text.setFont(QFont("Segoe UI", 10))
        info_layout.addWidget(credit_text)

        layout.addWidget(info_group)

        layout.addStretch()

    def _create_separator(self):
        sep = QLabel()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #49454f;")
        return sep
