M3_DARK_STYLESHEET = """
/* Material 3 Dark Theme */

QMainWindow {
    background-color: #1c1b1f;
}

/* Sidebar */
QWidget#sidebar_widget {
    background-color: #141218;
}

/* Tab Widget */
QTabWidget::pane {
    border: none;
    background-color: #1c1b1f;
}

QTabBar::tab {
    background-color: #2b2930;
    color: #938f99;
    padding: 12px 20px;
    border: none;
    border-radius: 8px 8px 0 0;
    margin-right: 4px;
}

QTabBar::tab:selected {
    background-color: #4f378b;
    color: #eaddff;
}

QTabBar::tab:hover:!selected {
    background-color: #49454f;
}

/* Buttons */
QPushButton {
    background-color: #4f378b;
    color: #eaddff;
    border: none;
    padding: 12px 24px;
    border-radius: 20px;
    font-weight: bold;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #6750a4;
}

QPushButton:pressed {
    background-color: #381e72;
}

/* Text Inputs */
QLineEdit {
    background-color: #2b2930;
    color: #e6e1e5;
    border: 1px solid #49454f;
    border-radius: 8px;
    padding: 10px;
    selection-background-color: #4f378b;
}

QLineEdit:focus {
    border: 2px solid #d0bcff;
}

/* ComboBox */
QComboBox {
    background-color: #2b2930;
    color: #e6e1e5;
    border: 1px solid #49454f;
    border-radius: 8px;
    padding: 10px;
}

QComboBox::drop-down {
    border: none;
    width: 30px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #938f99;
}

QComboBox QAbstractItemView {
    background-color: #2b2930;
    color: #e6e1e5;
    border: 1px solid #49454f;
    selection-background-color: #4f378b;
}

/* CheckBox */
QCheckBox {
    color: #e6e1e5;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 2px solid #49454f;
    background-color: transparent;
}

QCheckBox::indicator:checked {
    background-color: #d0bcff;
    border-color: #d0bcff;
}

QCheckBox::indicator:checked::after {
    content: "✓";
    color: #381e72;
    font-weight: bold;
}

/* Labels */
QLabel {
    color: #e6e1e5;
}

/* Frame/Card */
QFrame#status_frame,
QFrame#config_frame,
QFrame#roaster_frame {
    background-color: #2b2930;
    border-radius: 12px;
    border: 1px solid #49454f;
}

/* Text Edit (Log) */
QTextEdit {
    background-color: #2b2930;
    color: #cac4d0;
    border: 1px solid #49454f;
    border-radius: 8px;
    padding: 8px;
    font-family: Consolas, monospace;
    font-size: 11px;
}

/* Scrollbar */
QScrollBar:vertical {
    background-color: #1c1b1f;
    width: 8px;
    border: none;
}

QScrollBar::handle:vertical {
    background-color: #49454f;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #938f99;
}

/* GroupBox titles */
QGroupBox {
    color: #d0bcff;
    font-weight: bold;
    border: none;
    margin-top: 16px;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 0;
    padding: 0 8px;
}
"""


def apply_material3_style(app):
    """Apply Material 3 dark theme to the application"""
    app.setStyleSheet(M3_DARK_STYLESHEET)
