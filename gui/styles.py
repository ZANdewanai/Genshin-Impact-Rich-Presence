M3_DARK_STYLESHEET = """
QMainWindow {
    background-color: #1e1e20;
}

QTabWidget::pane {
    border: none;
    background-color: #1e1e20;
}

QTabBar::tab {
    background-color: #2b2930;
    color: #938f99;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background-color: #4f378b;
    color: #eaddff;
}

QTabBar::tab:hover:!selected {
    background-color: #49454f;
}

QPushButton {
    background-color: #4f378b;
    color: #eaddff;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #6750a4;
}

QPushButton:pressed {
    background-color: #381e72;
}

QLineEdit {
    background-color: #2b2930;
    color: #e6e1e5;
    border: 1px solid #49454f;
    border-radius: 4px;
    padding: 6px;
}

QLineEdit:focus {
    border: 2px solid #d0bcff;
}

QComboBox {
    background-color: #2b2930;
    color: #e6e1e5;
    border: 1px solid #49454f;
    border-radius: 4px;
    padding: 6px;
}

QComboBox::drop-down {
    border: none;
}

QCheckBox {
    color: #e6e1e5;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #938f99;
    border-radius: 3px;
}

QCheckBox::indicator:checked {
    background-color: #d0bcff;
    border-color: #d0bcff;
}

QLabel {
    color: #e6e1e5;
}

QGroupBox {
    color: #d0bcff;
    border: 1px solid #49454f;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}

QTextEdit {
    background-color: #2b2930;
    color: #e6e1e5;
    border: 1px solid #49454f;
    border-radius: 4px;
    font-family: Consolas, monospace;
    font-size: 11px;
}
"""

M3_LIGHT_STYLESHEET = """
QMainWindow {
    background-color: #fffbfe;
}

QTabWidget::pane {
    border: none;
    background-color: #fffbfe;
}

QTabBar::tab {
    background-color: #e7e0ec;
    color: #49454f;
    padding: 10px 20px;
    margin-right: 2px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background-color: #6750a4;
    color: #ffffff;
}

QTabBar::tab:hover:!selected {
    background-color: #ccc2dc;
}

QPushButton {
    background-color: #6750a4;
    color: #ffffff;
    border: none;
    padding: 10px 20px;
    border-radius: 4px;
    font-weight: bold;
}

QPushButton:hover {
    background-color: #7f67be;
}

QPushButton:pressed {
    background-color: #4f378b;
}

QLineEdit {
    background-color: #e7e0ec;
    color: #1c1b1f;
    border: 1px solid #79747e;
    border-radius: 4px;
    padding: 6px;
}

QLineEdit:focus {
    border: 2px solid #6750a4;
}

QComboBox {
    background-color: #e7e0ec;
    color: #1c1b1f;
    border: 1px solid #79747e;
    border-radius: 4px;
    padding: 6px;
}

QCheckBox {
    color: #1c1b1f;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 2px solid #79747e;
    border-radius: 3px;
}

QCheckBox::indicator:checked {
    background-color: #6750a4;
    border-color: #6750a4;
}

QLabel {
    color: #1c1b1f;
}

QGroupBox {
    color: #6750a4;
    border: 1px solid #cac4d0;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 10px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 5px;
}

QTextEdit {
    background-color: #e7e0ec;
    color: #1c1b1f;
    border: 1px solid #cac4d0;
    border-radius: 4px;
    font-family: Consolas, monospace;
    font-size: 11px;
}
"""


def apply_material3_style(app):
    """Apply Material 3 dark theme to the application"""
    app.setStyleSheet(M3_DARK_STYLESHEET)
