#!/usr/bin/env python3
"""
Interactive Coordinate Calibrator for Genshin Impact Rich Presence.

Creates an overlay with movable/scalable bounding boxes to precisely define OCR regions.
Uses PyQt5 for GUI with grid snapping and paired character box movement.
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
                                 QStatusBar, QMenuBar, QToolBar, QAction, QColorDialog, QSpinBox)
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QRect, QSize, QPoint, QEvent
    from PyQt5.QtGui import QFont, QPixmap, QIcon, QImage, QPalette, QColor, QPainter, QPen, QBrush
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("❌ PyQt5 not available. Please install with: pip install PyQt5")

# Add parent directory to path (tools/ -> root)
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)  # Main project directory
sys.path.insert(0, parent_dir)

# Import CONFIG.py with core/ module structure
import CONFIG

# Import all variables from CONFIG
GAME_RESOLUTION = CONFIG.GAME_RESOLUTION

# Import base coordinates for calibrator (use 1440p base directly)
from CONFIG import BASE_NAMES_4P_COORD, BASE_NUMBER_4P_COORD, BASE_ACTIVITY_COORD, BASE_BOSS_COORD, BASE_DOMAIN_COORD, BASE_PARTY_SETUP_COORD, BASE_LOCATION_COORD, BASE_MAP_LOC_COORD

# Force 1440p for calibrator
GAME_RESOLUTION = 1440

class GridOverlay(QWidget):
    """Grid overlay widget for visual grid reference."""

    def __init__(self, parent=None, grid_size=20, show_grid=True):
        super().__init__(parent)
        self.grid_size = grid_size
        self.show_grid = show_grid
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.3)
        self.setAttribute(Qt.WA_OpaquePaintEvent, False)

    def paintEvent(self, event):
        if not self.show_grid:
            return

        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)

            # Get screen dimensions
            screen = QApplication.primaryScreen().geometry()
            width, height = screen.width(), screen.height()

            # Draw grid lines with increased opacity for better visibility
            pen = QPen(QColor(255, 255, 255, 150), 1)
            painter.setPen(pen)

            # Calculate step size to limit number of lines for performance
            max_lines = 500  # Maximum lines to prevent performance issues
            x_step = self.grid_size
            if width // x_step > max_lines:
                x_step = max(1, width // max_lines)

            y_step = self.grid_size
            if height // y_step > max_lines:
                y_step = max(1, height // max_lines)

            # Vertical lines
            for x in range(0, width, x_step):
                painter.drawLine(x, 0, x, height)

            # Horizontal lines
            for y in range(0, height, y_step):
                painter.drawLine(0, y, width, y)

        except Exception as e:
            print(f"Grid overlay paint error: {e}")

class BoundingBoxWidget(QWidget):
    """A PyQt5 widget representing a movable/scalable bounding box overlay with grid snapping."""

    def __init__(self, name, x1, y1, x2, y2, color="red", parent=None, grid_size=10, enable_snap=True):
        super().__init__(parent)
        self.name = name
        self.color = QColor(color)
        self.selected = False
        self.dragging = False
        self.resize_handle = -1
        self.drag_start_pos = QPoint()
        self.grid_size = grid_size
        self.enable_snap = enable_snap

        # Store the actual content bounds (inner box)
        self.content_x1 = x1
        self.content_y1 = y1
        self.content_x2 = x2
        self.content_y2 = y2

        # Set up the widget with extra space for coordinate labels
        # Expand by 50px left and right, 20px top and bottom for labels
        outer_x1 = x1 - 50
        outer_y1 = y1 - 20
        outer_x2 = x2 + 50
        outer_y2 = y2 + 20
        self.setGeometry(outer_x1, outer_y1, outer_x2 - outer_x1, outer_y2 - outer_y1)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        # Make it semi-transparent
        self.setWindowOpacity(0.8)

    def snap_to_grid_point(self, pos):
        """Snap position to grid."""
        if not self.enable_snap:
            return pos

        x = round(pos.x() / self.grid_size) * self.grid_size
        y = round(pos.y() / self.grid_size) * self.grid_size
        return QPoint(x, y)

    def paintEvent(self, event):
        """Draw the bounding box."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Calculate content box position within expanded widget
        content_rect = QRect(
            self.content_x1 - self.x(),
            self.content_y1 - self.y(),
            self.content_x2 - self.content_x1,
            self.content_y2 - self.content_y1
        )

        # Draw the actual content rectangle
        pen = QPen(self.color, 2 if not self.selected else 4)
        painter.setPen(pen)
        painter.setBrush(QBrush(QColor(0, 0, 0, 50)))  # Semi-transparent fill
        painter.drawRect(content_rect.adjusted(1, 1, -1, -1))

        # Draw label above the box
        font = QFont("Arial", 10, QFont.Bold)
        painter.setFont(font)
        painter.setPen(QPen(self.color))
        painter.drawText(content_rect.left(), content_rect.top() - 20, self.name)

        # Draw coordinates at corners (outside the content box, inside expanded widget)
        coords = (self.content_x1, self.content_y1, self.content_x2, self.content_y2)
        coord_font = QFont("Arial", 8, QFont.Bold)
        painter.setFont(coord_font)
        painter.setPen(QPen(QColor(255, 255, 0)))  # Yellow text

        # Top-left coordinates (top-left area of expanded widget)
        painter.drawText(2, 15, f"({coords[0]},{coords[1]})")
        # Bottom-right coordinates (bottom-right area of expanded widget)
        br_text = f"({coords[2]},{coords[3]})"
        painter.drawText(self.width() - 75, self.height() - 5, br_text)

        # Draw resize handles if selected (on the content box corners)
        if self.selected:
            handle_size = 12
            painter.setPen(QPen(Qt.white, 1))
            painter.setBrush(QBrush(self.color))

            corners = [
                QPoint(content_rect.left(), content_rect.top()),
                QPoint(content_rect.right(), content_rect.top()),
                QPoint(content_rect.right(), content_rect.bottom()),
                QPoint(content_rect.left(), content_rect.bottom())
            ]

            for corner in corners:
                handle_rect = QRect(
                    corner.x() - handle_size//2,
                    corner.y() - handle_size//2,
                    handle_size, handle_size
                )
                painter.drawRect(handle_rect)

    def mousePressEvent(self, event):
        """Handle mouse press for dragging or resizing with multi-selection support."""
        if event.button() == Qt.LeftButton:
            parent = self.parent().parent()  # Get the main window
            shift_pressed = event.modifiers() & Qt.ShiftModifier
            alt_pressed = event.modifiers() & Qt.AltModifier

            if shift_pressed:
                # Multi-selection: add to selection
                if self not in parent.selected_boxes:
                    parent.selected_boxes.add(self)
                    self.selected = True
                    self.update()
            elif alt_pressed:
                # Deselect: remove from selection
                if self in parent.selected_boxes:
                    parent.selected_boxes.remove(self)
                    self.selected = False
                    self.update()
            else:
                # Single selection or drag existing selection
                if self not in parent.selected_boxes:
                    # Clear others and select this if not already selected
                    parent.selected_boxes.clear()
                    parent.selected_boxes.add(self)
                    self.selected = True
                    # Deselect others
                    for box in parent.boxes:
                        if box != self:
                            box.selected = False
                else:
                    # Already in selection, keep the group selected
                    self.selected = True

                self.update()

            # Check if clicking on a resize handle (only for single selection or if this box is selected)
            if self.selected:
                handle_size = 12
                # Use content box corners for resize handles
                content_rect = QRect(
                    self.content_x1 - self.x(),
                    self.content_y1 - self.y(),
                    self.content_x2 - self.content_x1,
                    self.content_y2 - self.content_y1
                )
                corners = [
                    QPoint(content_rect.left(), content_rect.top()),
                    QPoint(content_rect.right(), content_rect.top()),
                    QPoint(content_rect.right(), content_rect.bottom()),
                    QPoint(content_rect.left(), content_rect.bottom())
                ]

                for i, corner in enumerate(corners):
                    handle_rect = QRect(
                        corner.x() - handle_size//2,
                        corner.y() - handle_size//2,
                        handle_size, handle_size
                    )
                    if handle_rect.contains(event.pos()):
                        self.resize_handle = i
                        return

            # Start dragging if not resizing
            self.dragging = True
            self.drag_start_pos = event.globalPos() - self.pos()

    def mouseMoveEvent(self, event):
        """Handle mouse move for dragging or resizing with grid snapping."""
        if self.dragging:
            # Calculate the movement delta
            current_pos = event.globalPos() - self.drag_start_pos
            snapped_pos = self.snap_to_grid_point(current_pos)

            # Calculate how much we've moved since last update
            prev_pos = self.pos()
            delta_x = snapped_pos.x() - prev_pos.x()
            delta_y = snapped_pos.y() - prev_pos.y()

            # Update content coordinates BEFORE moving widget
            self.content_x1 += delta_x
            self.content_y1 += delta_y
            self.content_x2 += delta_x
            self.content_y2 += delta_y

            # Move this widget
            self.move(snapped_pos)

            # If this box is in the multi-selection, move all selected boxes
            parent = self.parent().parent()  # Get the main window
            if self in parent.selected_boxes:
                for selected_box in parent.selected_boxes:
                    if selected_box != self:
                        # Update content coordinates for selected box
                        selected_box.content_x1 += delta_x
                        selected_box.content_y1 += delta_y
                        selected_box.content_x2 += delta_x
                        selected_box.content_y2 += delta_y
                        selected_current_pos = selected_box.pos()
                        selected_new_pos = selected_current_pos + QPoint(delta_x, delta_y)
                        selected_box.move(self.snap_to_grid_point(selected_new_pos))
                        selected_box.update()  # Ensure visual update
            else:
                # Move all similar bounding boxes by the same delta (legacy behavior)
                self.move_similar_boxes(delta_x, delta_y)

        elif self.resize_handle >= 0:
            # Resize the widget with grid snapping
            new_geom = self.geometry()

            if self.resize_handle == 0:  # Top-left
                new_pos = self.snap_to_grid_point(event.globalPos())
                new_geom.setTopLeft(new_pos)
            elif self.resize_handle == 1:  # Top-right
                new_pos = self.snap_to_grid_point(event.globalPos())
                new_geom.setTopRight(new_pos)
            elif self.resize_handle == 2:  # Bottom-right
                new_pos = self.snap_to_grid_point(event.globalPos())
                new_geom.setBottomRight(new_pos)
            elif self.resize_handle == 3:  # Bottom-left
                new_pos = self.snap_to_grid_point(event.globalPos())
                new_geom.setBottomLeft(new_pos)

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
            # Update content coordinates based on new geometry
            self.content_x1 = new_geom.left()
            self.content_y1 = new_geom.top()
            self.content_x2 = new_geom.right()
            self.content_y2 = new_geom.bottom()

    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if event.button() == Qt.LeftButton:
            self.dragging = False
            self.resize_handle = -1

            # Save state after movement or resizing
            parent = self.parent().parent()
            if hasattr(parent, 'save_box_state'):
                parent.save_box_state()

    def get_coords(self):
        """Get current bounding box coordinates (content area, not expanded widget)."""
        return (self.content_x1, self.content_y1, self.content_x2, self.content_y2)

    def mirror_dimensions_to_similar_boxes(self, new_geom):
        """Mirror dimensions to all similar boxes (same type: name or number)."""
        if not hasattr(self.parent(), 'boxes'):
            return

        parent = self.parent()
        current_width = new_geom.width()
        current_height = new_geom.height()

        # Find all similar boxes (same type)
        similar_boxes = []
        if "Name" in self.name:
            # Find all character name boxes
            for box in parent.boxes:
                if "Name" in box.name and box != self:
                    similar_boxes.append(box)
        elif "Number" in self.name:
            # Find all character number boxes
            for box in parent.boxes:
                if "Number" in box.name and box != self:
                    similar_boxes.append(box)

        # Apply the same dimensions to all similar boxes
        for similar_box in similar_boxes:
            # Calculate the center of the similar box
            current_geom = similar_box.geometry()
            center_x = current_geom.left() + current_geom.width() // 2
            center_y = current_geom.top() + current_geom.height() // 2

            # Create new geometry with same dimensions but centered at same point
            new_left = center_x - current_width // 2
            new_top = center_y - current_height // 2

            similar_box.setGeometry(new_left, new_top, current_width, current_height)

    def move_similar_boxes(self, delta_x, delta_y):
        """Move all similar bounding boxes by the same delta."""
        if not hasattr(self.parent(), 'boxes'):
            return

        parent = self.parent()
        # Find all similar boxes (same type)
        similar_boxes = []
        if "Name" in self.name:
            # Find all character name boxes
            for box in parent.boxes:
                if "Name" in box.name and box != self:
                    similar_boxes.append(box)
        elif "Number" in self.name:
            # Find all character number boxes
            for box in parent.boxes:
                if "Number" in box.name and box != self:
                    similar_boxes.append(box)

        # Move all similar boxes by the same delta
        for similar_box in similar_boxes:
            # Update content coordinates
            similar_box.content_x1 += delta_x
            similar_box.content_y1 += delta_y
            similar_box.content_x2 += delta_x
            similar_box.content_y2 += delta_y
            current_pos = similar_box.pos()
            new_pos = current_pos + QPoint(delta_x, delta_y)
            similar_box.move(self.snap_to_grid_point(new_pos))
            similar_box.update()  # Ensure visual update



class CoordinateCalibrator(QMainWindow):
    """Main calibration tool with overlay using PyQt5 with grid snapping and paired character boxes."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Genshin Impact OCR Coordinate Calibrator - Grid Mode")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.9)

        # Get screen geometry
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create overlay widget for bounding boxes (full screen)
        self.overlay_widget = QWidget(self)
        self.overlay_widget.setGeometry(screen)
        self.overlay_widget.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.overlay_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.overlay_widget.setWindowOpacity(0.8)

        # Create grid overlay (full screen)
        self.grid_overlay = GridOverlay(self.overlay_widget, grid_size=20, show_grid=True)
        self.grid_overlay.setGeometry(screen)
        self.grid_overlay.show()
        self.grid_overlay.lower()  # Send grid to the back

        # Create control panel as overlay at bottom
        self.create_control_panel()

        # Create control panel as overlay at bottom (taller for better button access)
        control_height = 200
        self.control_panel.setParent(self.overlay_widget)
        self.control_panel.setGeometry(0, screen.height() - control_height, screen.width(), control_height)
        self.control_panel.show()
        self.control_panel.raise_()  # Ensure it's on top

        # Bounding boxes storage
        self.boxes = []
        self.selected_box = None
        self.selected_boxes = set()  # For multi-selection
        self.grid_size = 20
        self.snap_to_grid = True

        # Grid size history for undo/redo
        self.grid_history = [20]  # Start with default
        self.history_index = 0
        self.max_history = 50

        # Bounding box positions history for undo/redo
        self.box_history = []
        self.box_history_index = 0
        self.save_box_state()  # Save initial state

        # Use coordinates from CONFIG.py directly (already scaled)
        self.ocr_regions = []

        # Add character name regions
        for i, coords in enumerate(BASE_NAMES_4P_COORD):
            self.ocr_regions.append({
                "name": f"Character {i+1} Name",
                "coords": coords,
                "color": ["red", "blue", "green", "orange"][i]
            })

        # Add character number regions (individual small boxes)
        for i, coords in enumerate(BASE_NUMBER_4P_COORD):
            self.ocr_regions.append({
                "name": f"Character {i+1} Number",
                "coords": coords,
                "color": "purple"
            })

        # Add single coordinate regions
        self.ocr_regions.extend([
            {"name": "Location Text", "coords": BASE_LOCATION_COORD, "color": "cyan"},
            {"name": "Boss Name", "coords": BASE_BOSS_COORD, "color": "magenta"},
            {"name": "Domain Name", "coords": BASE_DOMAIN_COORD, "color": "yellow"},
            {"name": "Map Location", "coords": BASE_MAP_LOC_COORD, "color": "orange"},
            {"name": "Activity Region", "coords": BASE_ACTIVITY_COORD, "color": "lime"},
            {"name": "Game Menu", "coords": BASE_PARTY_SETUP_COORD, "color": "brown"},
        ])

        # Load existing coordinates and create bounding boxes
        self.load_coordinates()

        # Show overlay
        self.overlay_widget.show()

    def create_control_panel(self):
        """Create the control panel using PyQt5."""
        self.control_panel = QWidget()
        self.control_panel.setFixedHeight(200)
        self.control_panel.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)  # Make it a top-level tool window
        # Removed WA_TranslucentBackground to fix background rendering
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
                padding: 12px 20px;
                border-radius: 6px;
                margin: 4px;
                min-height: 35px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2ecc71;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
        """)

        layout = QVBoxLayout(self.control_panel)

        # Instructions
        instructions = QLabel("🎯 Shift+Click to add to group | Alt+Click to remove | Click selected box to drag group | 🖱️ Drag corners to resize | 🎨 Right-click to change colors")
        instructions.setFont(QFont("Arial", 9))
        layout.addWidget(instructions)

        # Top row controls
        top_controls_layout = QHBoxLayout()
        top_controls_layout.setSpacing(10)  # Add spacing between sections

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

        top_controls_layout.addWidget(left_controls)

        # Center spacer
        top_controls_layout.addStretch()

        # Right side controls
        right_controls = QWidget()
        right_layout = QHBoxLayout(right_controls)

        close_btn = QPushButton("❌ Close")
        close_btn.clicked.connect(self.close)
        right_layout.addWidget(close_btn)

        top_controls_layout.addWidget(right_controls)

        layout.addLayout(top_controls_layout)

        # Bottom row - Grid controls
        grid_controls_layout = QHBoxLayout()
        grid_controls_layout.setSpacing(8)  # Add spacing between grid controls

        # Grid size controls
        grid_size_label = QLabel("Grid Size:")
        grid_controls_layout.addWidget(grid_size_label)

        grid_size_5_btn = QPushButton("5px")
        grid_size_5_btn.clicked.connect(lambda: self.set_grid_size(5))
        grid_controls_layout.addWidget(grid_size_5_btn)

        grid_size_10_btn = QPushButton("10px")
        grid_size_10_btn.clicked.connect(lambda: self.set_grid_size(10))
        grid_controls_layout.addWidget(grid_size_10_btn)

        grid_size_20_btn = QPushButton("20px")
        grid_size_20_btn.clicked.connect(lambda: self.set_grid_size(20))
        grid_controls_layout.addWidget(grid_size_20_btn)

        # Grid visibility toggle
        self.grid_visible_btn = QPushButton("Hide Grid")
        self.grid_visible_btn.clicked.connect(self.toggle_grid)
        grid_controls_layout.addWidget(self.grid_visible_btn)

        # Grid snapping toggle
        self.snap_btn = QPushButton("Disable Snap")
        self.snap_btn.clicked.connect(self.toggle_snap)
        grid_controls_layout.addWidget(self.snap_btn)

        # Undo/Redo buttons
        undo_btn = QPushButton("↶ Undo Positions")
        undo_btn.clicked.connect(self.undo_box_positions)
        grid_controls_layout.addWidget(undo_btn)

        redo_btn = QPushButton("↷ Redo Positions")
        redo_btn.clicked.connect(self.redo_box_positions)
        grid_controls_layout.addWidget(redo_btn)

        layout.addLayout(grid_controls_layout)

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
        """Load existing coordinates and create bounding boxes with paired character boxes."""
        # First pass: Create all boxes
        temp_boxes = {}

        for region_info in self.ocr_regions:
            name = region_info["name"]
            coords = region_info["coords"]
            color = region_info["color"]

            try:
                if isinstance(coords, (list, tuple)) and len(coords) == 4:
                    # Single bounding box (x1, y1, x2, y2)
                    x1, y1, x2, y2 = coords
                    box = BoundingBoxWidget(name, x1, y1, x2, y2, color, self.overlay_widget,
                                          grid_size=self.grid_size, enable_snap=self.snap_to_grid)
                    temp_boxes[name] = box
                elif isinstance(coords, (list, tuple)) and len(coords) == 2:
                    # Single coordinate point (x, y) - create small box around it
                    x, y = coords
                    box = BoundingBoxWidget(name, x-15, y-15, x+15, y+15, color, self.overlay_widget,
                                          grid_size=self.grid_size, enable_snap=self.snap_to_grid)
                    temp_boxes[name] = box
                else:
                    print(f"Warning: Unknown coordinate format for {name}: {coords} (type: {type(coords)})")
                    continue

            except Exception as e:
                print(f"Error loading coordinates for {name}: {e} (coords: {coords})")
                continue

        # Second pass: Set up paired relationships for character name/number boxes
        for name, box in temp_boxes.items():
            if "Character" in name and "Name" in name:
                # Extract character number
                char_num = int(name.split()[1])
                number_name = f"Character {char_num} Number"

                if number_name in temp_boxes:
                    # Pair the name box with its corresponding number box
                    box.paired_box = temp_boxes[number_name]
                    temp_boxes[number_name].paired_box = box

                    print(f"✅ Paired {name} with {number_name}")

        # Add all boxes to the main list and show them
        for name, box in temp_boxes.items():
            self.boxes.append(box)
            box.show()

        self.status_label.setText(f"Loaded {len(self.boxes)} bounding boxes (Resolution: {GAME_RESOLUTION}p) - Grid: {self.grid_size}px")

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
        # Read directly from box content coordinates (what's shown on screen)
        char_names = {}
        char_number_points = {}  # Store 2-tuple center points for character numbers
        others = {}

        for box in self.boxes:
            name = box.name
            # Get content coordinates directly (what's displayed on screen)
            x1, y1, x2, y2 = box.content_x1, box.content_y1, box.content_x2, box.content_y2
            
            if name.startswith('Character') and 'Name' in name:
                # Extract character number from name like "Character 1 Name" -> 1
                char_num = int(name.split()[1])
                char_names[char_num] = (x1, y1, x2, y2)
            elif name.startswith('Character') and 'Number' in name:
                # Extract character number from name like "Character 1 Number" -> 1
                char_num = int(name.split()[1])
                # For number boxes, the center point is the actual coordinate
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                char_number_points[char_num] = (center_x, center_y)
            else:
                # Other regions use full bbox
                if "Location Text" in name:
                    others["LOCATION_COORD"] = (x1, y1, x2, y2)
                elif "Boss Name" in name:
                    others["BOSS_COORD"] = (x1, y1, x2, y2)
                elif "Domain Name" in name:
                    others["DOMAIN_COORD"] = (x1, y1, x2, y2)
                elif "Map Location" in name:
                    others["MAP_LOC_COORD"] = (x1, y1, x2, y2)
                elif "Game Menu" in name:
                    others["PARTY_SETUP_COORD"] = (x1, y1, x2, y2)
                elif "Activity Region" in name:
                    others["ACTIVITY_COORD"] = (x1, y1, x2, y2)

        # Format as Python code
        output = "# Updated OCR Coordinates\n\n"

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

        # Handle other regions
        for coord_name in sorted(others.keys()):
            output += f"{coord_name} = {others[coord_name]}\n"

        # Copy to clipboard
        clipboard = QApplication.clipboard()
        clipboard.setText(output)

        total_coords = len(char_names) + len(char_number_points) + len(others)
        self.status_label.setText(f"Copied {total_coords} coordinate sets to clipboard")

        # Show message box
        QMessageBox.information(self, "Coordinates Copied",
                              f"Copied coordinates for {total_coords} regions to clipboard.\n\nPaste into CONFIG.py")

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

    def toggle_grid(self):
        """Toggle grid visibility."""
        self.grid_overlay.show_grid = not self.grid_overlay.show_grid
        self.grid_overlay.update()
        grid_status = "ON" if self.grid_overlay.show_grid else "OFF"
        self.status_label.setText(f"Grid {grid_status} - Grid size: {self.grid_size}px")

    def toggle_snap(self):
        """Toggle grid snapping."""
        self.snap_to_grid = not self.snap_to_grid
        snap_status = "ON" if self.snap_to_grid else "OFF"

        # Update all boxes with new snap setting
        for box in self.boxes:
            box.enable_snap = self.snap_to_grid

        self.status_label.setText(f"Grid snap {snap_status} - Grid size: {self.grid_size}px")

    def set_grid_size(self, size):
        """Set grid size and update all boxes, with history tracking."""
        if size != self.grid_size:
            # Save current state to history if not at end
            if self.history_index < len(self.grid_history) - 1:
                self.grid_history = self.grid_history[:self.history_index + 1]
            self.grid_history.append(size)
            # Limit history to max steps
            if len(self.grid_history) > self.max_history:
                self.grid_history.pop(0)
            self.history_index = len(self.grid_history) - 1

        self.grid_size = size
        self.grid_overlay.grid_size = size
        self.grid_overlay.update()

        # Update all boxes with new grid size
        for box in self.boxes:
            box.grid_size = size

        self.status_label.setText(f"Grid size: {self.grid_size}px - Snap: {'ON' if self.snap_to_grid else 'OFF'}")

    def save_box_state(self):
        """Save current bounding box positions to history."""
        positions = {}
        for box in self.boxes:
            positions[box.name] = box.get_coords()

        if self.box_history_index < len(self.box_history) - 1:
            self.box_history = self.box_history[:self.box_history_index + 1]
        self.box_history.append(positions)
        if len(self.box_history) > self.max_history:
            self.box_history.pop(0)
        self.box_history_index = len(self.box_history) - 1

    def undo_box_positions(self):
        """Undo to previous bounding box positions."""
        if self.box_history_index > 0:
            self.box_history_index -= 1
            positions = self.box_history[self.box_history_index]
            for box in self.boxes:
                if box.name in positions:
                    x1, y1, x2, y2 = positions[box.name]
                    box.setGeometry(x1, y1, x2 - x1, y2 - y1)
                    box.update()  # Ensure visual update
            self.status_label.setText("Undid box positions")
        else:
            self.status_label.setText("No more undo steps")

    def redo_box_positions(self):
        """Redo to next bounding box positions."""
        if self.box_history_index < len(self.box_history) - 1:
            self.box_history_index += 1
            positions = self.box_history[self.box_history_index]
            for box in self.boxes:
                if box.name in positions:
                    x1, y1, x2, y2 = positions[box.name]
                    box.setGeometry(x1, y1, x2 - x1, y2 - y1)
                    box.update()  # Ensure visual update
            self.status_label.setText("Redid box positions")
        else:
            self.status_label.setText("No more redo steps")

    def closeEvent(self, event):
        """Handle window close event."""
        # Clean up all boxes
        for box in self.boxes:
            box.hide()
            box.deleteLater()
        event.accept()

def main():
    """Main function."""
    print("🎯 Genshin Impact OCR Coordinate Calibrator - Grid Mode")
    print("=" * 60)
    print("✨ Features: Grid snapping, Paired character box movement")
    print()

    # Check dependencies
    if not PYQT_AVAILABLE:
        print("❌ Cannot start calibrator: PyQt5 is not available")
        print("💡 Install PyQt5:")
        print("   pip install PyQt5")
        return

    print("📋 Instructions:")
    print("   🎯 Shift+Click to add to group | Alt+Click to remove | Click selected box to drag group | Resize with corners")
    print("   👥 Character name/number boxes move together | Global snapping for similar boxes")
    print("   📋 Click 'Copy Coordinates' to copy to clipboard")
    print("   💾 Click 'Save to File' to save coordinates")
    print("   🔄 Click 'Reset All' to reset to defaults")
    print("   ❌ Click 'Close' to exit")
    print()
    print("🎨 Controls:")
    print("   Grid size buttons: 5px, 10px, 20px")
    print("   Undo/Redo: ↶ Undo Positions, ↷ Redo Positions (up to 50 steps)")
    print("   Use buttons to toggle grid visibility and snapping")
    print()
    print("🚀 Starting calibrator...")

    try:
        print(f"📺 Detected screen resolution: {GAME_RESOLUTION}p")
        print(f"📏 Coordinates scaled from 1440p base to {GAME_RESOLUTION}p")
        print()

        app = QApplication(sys.argv)
        calibrator = CoordinateCalibrator()
        calibrator.show()

        print("✅ Calibrator started successfully")
        print("🎯 Position the overlay over your Genshin Impact window")
        print("📦 Adjust the bounding boxes to match your OCR regions")
        print("💡 Tip: Move character name boxes and their number boxes will follow!")
        print()

        sys.exit(app.exec_())

    except Exception as e:
        print(f"❌ Error starting calibrator: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
