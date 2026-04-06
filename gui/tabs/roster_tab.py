from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QLineEdit,
    QPushButton,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
import json
import os


class RosterTab:
    def __init__(self, main_window):
        self.main_window = main_window
        self.widget = QWidget()

        layout = QVBoxLayout(self.widget)

        title_label = QLabel("Character Roster")
        title_label.setObjectName("roaster_title_label")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title_label)

        roaster_frame = QFrame()
        roaster_frame.setObjectName("roaster_frame")
        roaster_frame.setFrameStyle(QFrame.Box)
        roaster_main_layout = QVBoxLayout(roaster_frame)

        character_images = self._load_character_images()

        self.char_image_entries = {}

        instructions = QLabel(
            "Configure custom image keys for Genshin characters.\n"
            "Use this for alternate skins, Fatui versions, or other variants."
        )
        instructions.setObjectName("instructions")
        instructions.setFont(QFont("Arial", 9))
        instructions.setWordWrap(True)
        roaster_main_layout.addWidget(instructions)

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
            roaster_main_layout.addLayout(char_layout)

        roaster_main_layout.addStretch()

        add_char_btn = QPushButton("Add Character")
        add_char_btn.setObjectName("add_char_btn")
        add_char_btn.setFont(QFont("Arial", 8))
        add_char_btn.clicked.connect(self._add_character_entry)
        roaster_main_layout.addWidget(add_char_btn)

        layout.addWidget(roaster_frame)

        self.roster_status_label = QLabel("")
        self.roster_status_label.setObjectName("roaster_status_label")
        self.roster_status_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.roster_status_label.setAlignment(Qt.AlignCenter)
        self.roster_status_label.setVisible(False)
        layout.addWidget(self.roster_status_label)

        save_button = QPushButton("Save Character Settings")
        save_button.setObjectName("roaster_save_button")
        save_button.setFont(QFont("Arial", 12, QFont.Bold))
        save_button.clicked.connect(self._save_roster_config)
        layout.addWidget(save_button)

        layout.addStretch()

    def _load_character_images(self):
        try:
            shared_config_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..",
                "..",
                "shared_config.json",
            )
            if os.path.exists(shared_config_path):
                with open(shared_config_path, "r") as f:
                    shared_config = json.load(f)
                    return shared_config.get("CHARACTER_IMAGES", {})
        except:
            pass
        return {}

    def _add_character_entry(self):
        self.roster_status_label.setText("Feature coming soon")
        self.roster_status_label.setStyleSheet("color: #f39c12;")
        self.roster_status_label.setVisible(True)

    def _save_roster_config(self):
        from PyQt5.QtCore import Qt

        character_images = {}
        for char_name, entry in self.char_image_entries.items():
            image_key = entry.text().strip()
            if image_key:
                character_images[char_name] = image_key

        shared_config_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "..", "shared_config.json"
        )
        try:
            config_dict = {
                "USERNAME": self.main_window.config.USERNAME,
                "MC_AETHER": self.main_window.config.MC_AETHER,
                "WANDERER_NAME": self.main_window.config.WANDERER_NAME,
                "GAME_RESOLUTION": self.main_window.config.GAME_RESOLUTION,
                "USE_GPU": self.main_window.config.USE_GPU,
            }
            if character_images:
                config_dict["CHARACTER_IMAGES"] = character_images

            with open(shared_config_path, "w") as f:
                json.dump(config_dict, f, indent=4)

            self.roster_status_label.setText("Character settings saved!")
            self.roster_status_label.setStyleSheet("color: #2ecc71;")
            self.roster_status_label.setVisible(True)
        except Exception as e:
            self.roster_status_label.setText(f"Error: {str(e)}")
            self.roster_status_label.setStyleSheet("color: #e74c3c;")
            self.roster_status_label.setVisible(True)

        QTimer.singleShot(3000, lambda: self.roster_status_label.setVisible(False))

    @property
    def get_widget(self):
        return self.widget
