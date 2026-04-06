#!/usr/bin/env python3
import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

try:
    from PyQt5.QtWidgets import QApplication

    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("Error: PyQt5 is required. Install with: pip install PyQt5")
    sys.exit(1)

from gui.main_window import MainWindow
from gui.styles import apply_material3_style


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Genshin Impact Rich Presence")

    apply_material3_style(app)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
