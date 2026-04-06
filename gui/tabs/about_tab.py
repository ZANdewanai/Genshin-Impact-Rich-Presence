from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtGui import QFont


class AboutTab:
    def __init__(self, main_window):
        self.main_window = main_window
        self.widget = QWidget()

        layout = QVBoxLayout(self.widget)

        title_label = QLabel("About Genshin Impact Rich Presence")
        title_label.setObjectName("about_title_label")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title_label)

        info_text = """Genshin Impact Rich Presence v4.0

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
        layout.addWidget(info_label)

        layout.addStretch()

    @property
    def get_widget(self):
        return self.widget
