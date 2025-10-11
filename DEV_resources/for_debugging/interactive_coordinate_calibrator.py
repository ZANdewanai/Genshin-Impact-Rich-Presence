#!/usr/bin/env python3
"""
Interactive Coordinate Calibrator for Genshin Impact Rich Presence.

Creates an overlay with movable/scalable bounding boxes to precisely define OCR regions.
Uses PyQt5 for GUI (same as main application).
"""

import sys
import os
import json
import time
import threading

# Check for required dependencies
try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                                 QLabel, QPushButton, QTextEdit, QFrame, QSplitter,
                                 QProgressBar, QCheckBox, QLineEdit, QComboBox, QSizePolicy,
                                 QGroupBox, QFormLayout, QGridLayout, QMessageBox, QListWidget,
                                 QStatusBar, QMenuBar, QToolBar, QAction, QColorDialog)
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QRect, QSize, QPoint
    from PyQt5.QtGui import QFont, QPixmap, QIcon, QImage, QPalette, QColor, QPainter, QPen, QBrush
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("❌ PyQt5 not available. Please install with: pip install PyQt5")

try:
    import win32gui
    import win32process
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False
    print("❌ pywin32 not available. Please install with: pip install pywin32")

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("❌ psutil not available. Please install with: pip install psutil")

# Add the main directory to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
dev_resources_dir = os.path.dirname(script_dir)  # DEV_resources
parent_dir = os.path.dirname(dev_resources_dir)  # Main project directory
sys.path.insert(0, parent_dir)
print(f"Script dir: {script_dir}")
print(f"DEV_resources dir: {dev_resources_dir}")
print(f"Parent dir: {parent_dir}")
print(f"CONFIG.py exists: {os.path.exists(os.path.join(parent_dir, 'CONFIG.py'))}")

# Import CONFIG.py directly since there's no core module
try:
    import CONFIG
    print("Successfully imported CONFIG")
except ImportError as e:
    print(f"Failed to import CONFIG: {e}")
    # Try importing as a module from file
    try:
        import importlib.util
        config_path = os.path.join(parent_dir, 'CONFIG.py')
        spec = importlib.util.spec_from_file_location("CONFIG", config_path)
        CONFIG = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(CONFIG)
        print("Successfully loaded CONFIG via importlib")
    except Exception as e2:
        print(f"Failed to load CONFIG via importlib: {e2}")
        sys.exit(1)

# Import all variables from CONFIG
GAME_RESOLUTION = CONFIG.GAME_RESOLUTION

class BoundingBoxWidget(QWidget):
    """A PyQt5 widget representing a movable/scalable bounding box overlay."""

    def __init__(self, name, x1, y1, x2, y2, color="red", parent=None):
        super().__init__(parent)
        self.name = name
        self.color = QColor(color)
        self.selected = False
        self.dragging = False
        self.resize_handle = -1
        self.drag_start_pos = QPoint()

        # Set up the widget
        self.setGeometry(x1, y1, x2 - x1, y2 - y1)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        # Make it semi-transparent
        self.setWindowOpacity(0.8)

    def paintEvent(self, event):
        """Draw the bounding box."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw rectangle
        pen = QPen(self.color, 2 if not self.selected else 4)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 50)))  # Semi-transparent fill

        rect = self.rect().adjusted(1, 1, -1, -1)
        painter.drawRect(rect)

        # Draw label
        font = QFont("Arial", 10, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QPen(self.color))
        painter.drawText(5, 15, self.name)

        # Draw resize handles if selected
        if self.selected:
            handle_size = 6
            painter.setPen(QPen(Qt.white, 1))
            painter.setBrush(QBrush(self.color))

            # Corner handles
            corners = [
                QPoint(0, 0),
                QPoint(self.width(), 0),
                QPoint(self.width(), self.height()),
                QPoint(0, self.height())
            ]

            for corner in corners:
                handle_rect = QRect(
                    corner.x() - handle_size//2,
                    corner.y() - handle_size//2,
                    handle_size, handle_size
                )
                painter.drawRect(handle_rect)

    def mousePressEvent(self, event):
        """Handle mouse press for dragging or resizing."""
        if event.button() == Qt.LeftButton:
            # Check if clicking on a resize handle
            handle_size = 6
            corners = [
                QPoint(0, 0),
                QPoint(self.width(), 0),
                QPoint(self.width(), self.height()),
                QPoint(0, self.height())
            ]

            for i, corner in enumerate(corners):
                handle_rect = QRect(
                    corner.x() - handle_size//2,
                    corner.y() - handle_size//2,
                    handle_size, handle_size
                )
                if handle_rect.contains(event.pos()):
                    self.resize_handle = i
                    self.selected = True
                    self.update()
                    return

            # Start dragging
            self.dragging = True
            self.selected = True
            self.drag_start_pos = event.globalPos() - self.pos()
            self.update()

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging or resizing."""
        if self.dragging:
            # Move the widget
            new_pos = event.globalPos() - self.drag_start_pos
            self.move(new_pos)
        elif self.resize_handle >= 0:
            # Resize the widget
            new_geom = self.geometry()

            if self.resize_handle == 0:  # Top-left
                new_geom.setTopLeft(event.globalPos())
            elif self.resize_handle == 1:  # Top-right
                new_geom.setTopRight(event.globalPos())
            elif self.resize_handle == 2:  # Bottom-right
                new_geom.setBottomRight(event.globalPos())
            elif self.resize_handle == 3:  # Bottom-left
                new_geom.setBottomLeft(event.globalPos())

            # Ensure minimum size
            if new_geom.width() < 20:
                if self.resize_handle in [0, 3]:
                    new_geom.setLeft(new_geom.right() - 20)
                else:
                    new_geom.setRight(new_geom.left() + 20)

            if new_geom.height() < 20:
                if self.resize_handle in [0, 1]:
                    new_geom.setTop(new_geom.bottom() - 20)
                else:
                    new_geom.setBottom(new_geom.top() + 20)

            self.setGeometry(new_geom)

    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.resize_handle = -1

    def get_coords(self):
        """Get current bounding box coordinates."""
        geom = self.geometry()
        return (geom.left(), geom.top(), geom.right(), geom.bottom())

class CoordinateCalibrator(QMainWindow):
    """Main calibration tool with overlay using PyQt5."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Genshin Impact OCR Coordinate Calibrator")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.9)

        # Get screen geometry
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create overlay widget for bounding boxes
        self.overlay_widget = QWidget(self)
        self.overlay_widget.setGeometry(screen)
        self.overlay_widget.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.overlay_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.overlay_widget.setWindowOpacity(0.8)

        # Create control panel
        self.create_control_panel()
        layout.addWidget(self.control_panel)

        # Bounding boxes storage
        self.boxes = []
        self.selected_box = None

        # Use coordinates from CONFIG.py directly (already scaled)
        self.ocr_regions = []

        # Add character name regions
        for i, coords in enumerate(CONFIG.NAMES_4P_COORD):
            self.ocr_regions.append({
                "name": f"Character {i+1} Name",
                "coords": coords,
                "color": ["red", "blue", "green", "orange"][i]
            })

        # Add character number regions (individual small boxes)
        for i, coords in enumerate(CONFIG.NUMBER_4P_COORD):
            self.ocr_regions.append({
                "name": f"Character {i+1} Number",
                "coords": coords,
                "color": "purple"
            })

        # Add single coordinate regions
        self.ocr_regions.extend([
            {"name": "Location Text", "coords": CONFIG.LOCATION_COORD, "color": "cyan"},
            {"name": "Boss Name", "coords": CONFIG.BOSS_COORD, "color": "magenta"},
            {"name": "Domain Name", "coords": CONFIG.DOMAIN_COORD, "color": "yellow"},
            {"name": "Map Location", "coords": CONFIG.MAP_LOC_COORD, "color": "orange"},
            {"name": "Activity Region", "coords": CONFIG.ACTIVITY_COORD, "color": "lime"},
            {"name": "Game Menu", "coords": CONFIG.PARTY_SETUP_COORD, "color": "brown"},
        ])

        # Load existing coordinates and create bounding boxes
        self.load_coordinates()

        # Show overlay
        self.overlay_widget.show()

    def create_control_panel(self):
        """Create the control panel using PyQt5."""
        self.control_panel = QWidget()
        self.control_panel.setFixedHeight(120)
        self.control_panel.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                border-top: 2px solid #34495e;
            }
            QLabel {
                color: #ecf0f1;
            }
            QPushButton {
                background-color: #27ae60;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
        """)

        layout = QVBoxLayout(self.control_panel)

        # Instructions
        instructions = QLabel("🎯 Click and drag boxes to position them | 🖱️ Drag corners to resize | 🎨 Right-click to change colors")
        instructions.setFont(QFont("Arial", 9))
        layout.addWidget(instructions)

        # Controls
        controls_layout = QHBoxLayout()

        # Left side controls
        left_controls = QWidget()
        left_layout = QHBoxLayout(left_controls)

        copy_btn = QPushButton("📋 Copy Coordinates")
        copy_btn.clicked.connect(self.copy_coordinates)
        left_layout.addWidget(copy_btn)

        save_btn = QPushButton("💾 Save to File")
        save_btn.clicked.connect(self.save_coordinates)
        left_layout.addWidget(save_btn)

        reset_btn = QPushButton("🔄 Reset All")
        reset_btn.clicked.connect(self.reset_boxes)
        left_layout.addWidget(reset_btn)

        controls_layout.addWidget(left_controls)

        # Center spacer
        controls_layout.addStretch()

        # Right side controls
        right_controls = QWidget()
        right_layout = QHBoxLayout(right_controls)

        close_btn = QPushButton("❌ Close")
        close_btn.clicked.connect(self.close)
        right_layout.addWidget(close_btn)

        controls_layout.addWidget(right_controls)

        layout.addLayout(controls_layout)

        # Status bar
        self.status_label = QLabel("Ready - Click and drag boxes to position them")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #34495e;
                color: #ecf0f1;
                padding: 5px;
                border: 1px solid #2c3e50;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.status_label)

    def start_screenshot_thread(self):
        """Start background thread for continuous screenshots."""
        self.running = True
        self.screenshot_thread = threading.Thread(target=self.screenshot_loop, daemon=True)
        self.screenshot_thread.start()

    def screenshot_loop(self):
        """Continuously capture and display game screenshots."""
        while self.running:
            try:
                # This would need to be implemented to capture the game window
                # For now, we'll use a placeholder background
                time.sleep(0.1)  # Update 10 times per second
            except Exception as e:
                print(f"Screenshot error: {e}")
                time.sleep(1)

    def load_coordinates(self):
        """Load existing coordinates and create bounding boxes."""
        for region_info in self.ocr_regions:
            name = region_info["name"]
            coords = region_info["coords"]
            color = region_info["color"]

            try:
                if isinstance(coords, (list, tuple)) and len(coords) == 4:
                    # Single bounding box (x1, y1, x2, y2)
                    x1, y1, x2, y2 = coords
                    box = BoundingBoxWidget(name, x1, y1, x2, y2, color, self.overlay_widget)
                    box.show()
                    self.boxes.append(box)
                elif isinstance(coords, (list, tuple)) and len(coords) == 2:
                    # Single coordinate point (x, y) - create small box around it
                    x, y = coords
                    box = BoundingBoxWidget(name, x-15, y-15, x+15, y+15, color, self.overlay_widget)
                    box.show()
                    self.boxes.append(box)
                else:
                    print(f"Warning: Unknown coordinate format for {name}: {coords} (type: {type(coords)})")
                    continue

            except Exception as e:
                print(f"Error loading coordinates for {name}: {e} (coords: {coords})")
                continue

        self.status_label.setText(f"Loaded {len(self.boxes)} bounding boxes (Resolution: {GAME_RESOLUTION}p)")

    def reset_boxes(self):
        """Reset all boxes to default positions."""
        # Hide and delete all existing boxes
        for box in self.boxes:
            box.hide()
            box.deleteLater()

        self.boxes.clear()
        self.load_coordinates()
        self.status_label.setText("Reset all boxes to default positions")

    def copy_coordinates(self):
        """Copy current coordinates to clipboard."""
        coords_dict = {}

        for i, box in enumerate(self.boxes):
            coords = box.get_coords()
            if len(coords) == 4:
                coords_dict[box.name] = (int(coords[0]), int(coords[1]),
                                        int(coords[2]), int(coords[3]))

        # Format as Python code
        output = "# Updated OCR Coordinates\n\n"

        # Group by type
        char_names = {}
        char_numbers = {}
        char_number_points = {}  # Store original 2-tuple points for character numbers
        others = {}

        for name, coords in coords_dict.items():
            if name.startswith('Character') and 'Name' in name:
                # Extract character number from name like "Character 1 Name" -> 1
                char_num = int(name.split()[1])
                char_names[char_num] = coords
            elif name.startswith('Character') and 'Number' in name:
                # Extract character number from name like "Character 1 Number" -> 1
                char_num = int(name.split()[1])
                # Store the center point as 2-tuple for export
                center_x = (coords[0] + coords[2]) // 2
                center_y = (coords[1] + coords[3]) // 2
                char_number_points[char_num] = (center_x, center_y)
            else:
                others[name] = coords

        # Sort by character number and output
        if char_names:
            output += "NAMES_4P_COORD = [\n"
            for i in sorted(char_names.keys()):
                output += f"    {char_names[i]},  # Character {i}\n"
            output += "]\n\n"

        if char_number_points:
            output += "NUMBER_4P_COORD = [\n"
            for i in sorted(char_number_points.keys()):
                output += f"    {char_number_points[i]},  # Char {i}\n"
            output += "]\n\n"

        # Handle other regions with proper naming
        for name, coords in sorted(others.items()):
            if "Location Text" in name:
                output += f"LOCATION_COORD = {coords}\n"
            elif "Boss Name" in name:
                output += f"BOSS_COORD = {coords}\n"
            elif "Domain Name" in name:
                output += f"DOMAIN_COORD = {coords}\n"
            elif "Map Location" in name:
                output += f"MAP_LOC_COORD = {coords}\n"
            elif "Game Menu" in name:
                output += f"PARTY_SETUP_COORD = {coords}\n"
            elif "Activity Region" in name:
                output += f"ACTIVITY_COORD = {coords}\n"
            else:
                output += f"{name.upper().replace(' ', '_')}_COORD = {coords}\n"

        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(output)

        self.status_label.setText(f"Copied {len(coords_dict)} coordinate sets to clipboard")

        # Show message box
        QMessageBox.information(self, "Coordinates Copied",
                              f"Copied coordinates for {len(coords_dict)} regions to clipboard.\n\nPaste into CONFIG.py")

    def save_coordinates(self):
        """Save coordinates to a file."""
        coords_dict = {}

        for box in self.boxes:
            coords = box.get_coords()
            if len(coords) == 4:
                coords_dict[box.name] = (int(coords[0]), int(coords[1]),
                                        int(coords[2]), int(coords[3]))

        filename = "calibrated_coordinates.json"
        try:
            with open(filename, 'w') as f:
                json.dump(coords_dict, f, indent=2)
            self.status_label.setText(f"Saved coordinates to {filename}")
        except Exception as e:
            self.status_label.setText(f"Error saving coordinates: {e}")

    def on_right_click(self, event):
        """Handle right-click for color selection."""
        # Find clicked box
        clicked_box = None
        for box in self.boxes.values():
            if self.canvas.bbox(box.rect):
                x1, y1, x2, y2 = self.canvas.bbox(box.rect)
                if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                    clicked_box = box
                    break

        if clicked_box:
            # Show color picker
            color = colorchooser.askcolor(title=f"Choose color for {clicked_box.name}")
            if color[1]:
                clicked_box.set_color(color[1])
                self.status_var.set(f"Changed {clicked_box.name} color to {color[1]}")

    def on_key_press(self, event):
        """Handle keyboard shortcuts."""
        if event.keysym == 'Escape':
            self.quit()
        elif event.keysym == 'Delete' and self.selected_box:
            self.delete_selected_box()
        elif event.keysym == 'c':
            self.copy_coordinates()
        elif event.keysym == 's':
            self.save_coordinates()
        # Grid shortcuts
        elif event.keysym == 'g':
            self.toggle_grid()
        elif event.keysym == 'G':
            self.toggle_snap()
        elif event.keysym == '1':
            self.set_grid_size(10)
        elif event.keysym == '2':
            self.set_grid_size(20)
        elif event.keysym == '3':
            self.set_grid_size(50)
        elif event.keysym == '4':
            self.set_grid_size(100)

    def on_canvas_resize(self, event):
        """Handle canvas resize events."""
        # Redraw grid when canvas is resized
        self.draw_grid()

    def delete_selected_box(self):
        """Delete the currently selected box."""
        if self.selected_box:
            box = self.boxes[self.selected_box]
            self.canvas.delete(box.rect)
            self.canvas.delete(box.label)
            for handle in box.handles:
                self.canvas.delete(handle)
            del self.boxes[self.selected_box]
            self.selected_box = None

    def quit(self):
        """Quit the application."""
        self.running = False
        if self.screenshot_thread:
            self.screenshot_thread.join(timeout=1.0)
        self.root.quit()
        self.root.destroy()

def main():
    """Main function."""
    print("🎯 Genshin Impact OCR Coordinate Calibrator")
    print("=" * 50)

    # Check dependencies
    if not PYQT_AVAILABLE:
        print("❌ Cannot start calibrator: PyQt5 is not available")
        print("💡 Install PyQt5:")
        print("   pip install PyQt5")
        return

    if not PSUTIL_AVAILABLE:
        print("❌ Cannot start calibrator: psutil is not available")
        print("💡 Install psutil:")
        print("   pip install psutil")
        return

    print("📋 Instructions:")
    print("   🎯 Click and drag boxes to move them")
    print("   🖱️  Drag corners to resize boxes")
    print("   📋 Click 'Copy Coordinates' to copy to clipboard")
    print("   💾 Click 'Save to File' to save coordinates")
    print("   🔄 Click 'Reset All' to reset to defaults")
    print("   ❌ Click 'Close' to exit")
    print()
    print("🚀 Starting calibrator...")

    try:
        print(f"📺 Detected screen resolution: {GAME_RESOLUTION}p")
        print(f"📏 Coordinates scaled from 1080p base to {GAME_RESOLUTION}p")
        print()

        app = QApplication(sys.argv)
        calibrator = CoordinateCalibrator()
        calibrator.show()

        print("✅ Calibrator started successfully")
        print("🎯 Position the overlay over your Genshin Impact window")
        print("📦 Adjust the bounding boxes to match your OCR regions")
        print()

        sys.exit(app.exec_())

    except Exception as e:
        print(f"❌ Error starting calibrator: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
