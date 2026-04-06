from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QFrame, QTextEdit
from PyQt5.QtGui import QFont


class MainTab:
    def __init__(self, main_window):
        self.main_window = main_window
        self.widget = QWidget()

        layout = QVBoxLayout(self.widget)

        title_label = QLabel("Genshin Impact Rich Presence")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title_label)

        status_frame = QFrame()
        status_frame.setObjectName("status_frame")
        status_frame.setFrameStyle(QFrame.Box)
        status_layout = QGridLayout(status_frame)

        status_items = [
            ("Game Status:", "Not running"),
            ("Current Character:", "None"),
            ("Current Location:", "Unknown"),
            ("Current Activity:", "None"),
            ("Uptime:", "00:00:00"),
        ]

        for i, (label, value) in enumerate(status_items):
            img_label = QLabel("")
            img_label.setFixedSize(32, 32)
            img_label.setObjectName(
                f"status_img_{label.lower().replace(' ', '_').replace(':', '')}"
            )
            status_layout.addWidget(img_label, i, 0)

            lbl = QLabel(label)
            lbl.setFont(QFont("Arial", 10, QFont.Bold))
            status_layout.addWidget(lbl, i, 1)

            value_label = QLabel(value)
            value_label.setFont(QFont("Arial", 9))
            value_label.setObjectName(
                f"status_{label.lower().replace(' ', '_').replace(':', '')}"
            )
            status_layout.addWidget(value_label, i, 2)

            setattr(
                self,
                f"status_img_{label.lower().replace(' ', '_').replace(':', '')}",
                img_label,
            )
            setattr(
                self,
                f"status_{label.lower().replace(' ', '_').replace(':', '')}",
                value_label,
            )

        status_layout.setColumnStretch(2, 1)
        layout.addWidget(status_frame)

        log_label = QLabel("Activity Log:")
        log_label.setObjectName("log_label")
        log_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setObjectName("log_text")
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        layout.addStretch()

    def update_log(self, text):
        self.log_text.setPlainText(text)

    def update_status(self, key, value):
        attr = f"status_{key}"
        if hasattr(self, attr):
            getattr(self, attr).setText(value)

    @property
    def get_widget(self):
        return self.widget
