#!/usr/bin/env python3
"""
Interactive Coordinate Calibrator for Genshin Impact Rich Presence.

Creates an overlay with movable/scalable bounding boxes to precisely define OCR regions.
"""

import sys
import os
import json
import time
import threading

# Check for required dependencies
try:
    import tkinter as tk
    from tkinter import ttk, colorchooser, messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    print("❌ tkinter not available. Please install with: pip install tk")
    print("   On Ubuntu/Debian: sudo apt-get install python3-tk")
    print("   On Windows: tkinter is usually included with Python")

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
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import CONFIG.py directly since there's no core module
import CONFIG

# Import all variables from CONFIG
GAME_RESOLUTION = CONFIG.GAME_RESOLUTION

class BoundingBox:
    """Represents a movable/scalable bounding box."""

    def __init__(self, canvas, x1, y1, x2, y2, name, color="red", calibrator=None):
        self.canvas = canvas
        self.name = name
        self.color = color
        self.calibrator = calibrator  # Reference to the main calibrator

        # Create rectangle
        self.rect = canvas.create_rectangle(x1, y1, x2, y2,
                                          outline=color, width=2, tags=name)

        # Create label
        self.label = canvas.create_text((x1 + x2) // 2, y1 - 15,
                                       text=name, fill=color, font=('Arial', 10, 'bold'))

        # Create resize handles (larger for easier clicking)
        self.handles = []
        self.handle_size = 5  # Increased from 3 to 5 for better visibility
        for i, (px, py) in enumerate([(x1, y1), (x2, y1), (x2, y2), (x1, y2)]):
            handle = canvas.create_rectangle(px-self.handle_size, py-self.handle_size, px+self.handle_size, py+self.handle_size,
                                           fill=color, outline='white', width=2)
            self.handles.append(handle)

        self.selected = False
        self.drag_data = {"x": 0, "y": 0}
        self.resize_handle = None

        # Bind events
        canvas.tag_bind(name, "<ButtonPress-1>", self.on_press)
        canvas.tag_bind(name, "<ButtonRelease-1>", self.on_release)
        canvas.tag_bind(name, "<B1-Motion>", self.on_drag)

        for handle in self.handles:
            canvas.tag_bind(handle, "<ButtonPress-1>", self.on_handle_press)
            canvas.tag_bind(handle, "<ButtonRelease-1>", self.on_handle_release)
            canvas.tag_bind(handle, "<B1-Motion>", self.on_handle_drag)

    def on_press(self, event):
        """Handle box selection."""
        self.selected = True
        self.canvas.itemconfig(self.rect, outline='yellow', width=3)
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def on_release(self, event):
        """Handle box release."""
        self.selected = False
        self.canvas.itemconfig(self.rect, outline=self.color, width=2)

    def on_drag(self, event):
        """Handle box dragging."""
        if not self.selected:
            return

        # Calculate delta
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]

        # Apply snap-to-grid if enabled
        if self.calibrator and hasattr(self.calibrator, 'snap_to_grid') and self.calibrator.snap_to_grid.get():
            # Snap the movement delta to grid
            grid_size = self.calibrator.grid_size
            dx = round(dx / grid_size) * grid_size
            dy = round(dy / grid_size) * grid_size

            # Snap the final position to grid
            rect_coords = self.canvas.coords(self.rect)
            new_x = rect_coords[0] + dx
            new_y = rect_coords[1] + dy
            new_x = round(new_x / grid_size) * grid_size
            new_y = round(new_y / grid_size) * grid_size

            # Calculate snapped delta
            dx = new_x - rect_coords[0]
            dy = new_y - rect_coords[1]

        # Move rectangle
        self.canvas.move(self.rect, dx, dy)
        self.canvas.move(self.label, dx, dy)

        # Move handles
        for handle in self.handles:
            self.canvas.move(handle, dx, dy)

        # Update drag data
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y

    def on_handle_press(self, event):
        """Handle resize handle press."""
        # Find which handle was pressed with larger tolerance area
        tolerance = 8  # Increased tolerance for easier clicking

        for i, handle in enumerate(self.handles):
            hx1, hy1, hx2, hy2 = self.canvas.bbox(handle)
            # Expand the hit area by tolerance amount
            hx1 -= tolerance
            hy1 -= tolerance
            hx2 += tolerance
            hy2 += tolerance

            if hx1 <= event.x <= hx2 and hy1 <= event.y <= hy2:
                self.resize_handle = i
                break

    def on_handle_release(self, event):
        """Handle resize handle release."""
        self.resize_handle = None

    def on_handle_drag(self, event):
        """Handle resize handle dragging."""
        if self.resize_handle is None:
            return

        # Get current rectangle coordinates
        x1, y1, x2, y2 = self.canvas.coords(self.rect)

        # Update based on which handle is being dragged
        if self.resize_handle == 0:  # Top-left
            x1, y1 = event.x, event.y
        elif self.resize_handle == 1:  # Top-right
            x2, y1 = event.x, event.y
        elif self.resize_handle == 2:  # Bottom-right
            x2, y2 = event.x, event.y
        elif self.resize_handle == 3:  # Bottom-left
            x1, y2 = event.x, event.y

        # Apply snap-to-grid if enabled
        if self.calibrator and hasattr(self.calibrator, 'snap_to_grid') and self.calibrator.snap_to_grid.get():
            grid_size = self.calibrator.grid_size
            x1 = round(x1 / grid_size) * grid_size
            y1 = round(y1 / grid_size) * grid_size
            x2 = round(x2 / grid_size) * grid_size
            y2 = round(y2 / grid_size) * grid_size

        # Ensure minimum size
        if x2 - x1 < 10:
            if self.resize_handle in [0, 3]:
                x1 = x2 - 10
            else:
                x2 = x1 + 10

        if y2 - y1 < 10:
            if self.resize_handle in [0, 1]:
                y1 = y2 - 10
            else:
                y2 = y1 + 10

        # Update rectangle
        self.canvas.coords(self.rect, x1, y1, x2, y2)

        # Update label position
        self.canvas.coords(self.label, (x1 + x2) // 2, y1 - 15)

        # Update handles positions (don't reassign the handle IDs)
        self.canvas.coords(self.handles[0], x1-self.handle_size, y1-self.handle_size, x1+self.handle_size, y1+self.handle_size)
        self.canvas.coords(self.handles[1], x2-self.handle_size, y1-self.handle_size, x2+self.handle_size, y1+self.handle_size)
        self.canvas.coords(self.handles[2], x2-self.handle_size, y2-self.handle_size, x2+self.handle_size, y2+self.handle_size)
        self.canvas.coords(self.handles[3], x1-self.handle_size, y2-self.handle_size, x1+self.handle_size, y2+self.handle_size)

    def get_coords(self):
        """Get current bounding box coordinates."""
        return self.canvas.coords(self.rect)

    def set_color(self, color):
        """Change box color."""
        self.color = color
        self.canvas.itemconfig(self.rect, outline=color)
        self.canvas.itemconfig(self.label, fill=color)
        for handle in self.handles:
            self.canvas.itemconfig(handle, fill=color)

class CoordinateCalibrator:
    """Main calibration tool with overlay."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Genshin Impact OCR Coordinate Calibrator")
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.8)  # Semi-transparent

        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create canvas for overlay
        self.canvas = tk.Canvas(self.main_frame, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Create control panel
        self.create_control_panel()

        # Bounding boxes storage
        self.boxes = {}
        self.selected_box = None

        # Grid system
        self.grid_size = 20  # Default grid size
        self.grid_enabled = tk.BooleanVar(value=True)
        self.snap_to_grid = tk.BooleanVar(value=True)
        self.grid_lines = []  # Store grid line IDs

        # Use coordinates from CONFIG.py directly (already scaled)
        self.ocr_regions = {}

        # Add character name regions
        for i, coords in enumerate(CONFIG.NAMES_4P_COORD):
            self.ocr_regions[f"character_{i+1}"] = {
                "name": f"Character {i+1} Name",
                "coords": coords,
                "color": ["red", "blue", "green", "orange"][i]
            }

        # Add character number regions (individual small boxes)
        for i, coords in enumerate(CONFIG.NUMBER_4P_COORD):
            self.ocr_regions[f"character_number_{i+1}"] = {
                "name": f"Character {i+1} Number",
                "coords": coords,
                "color": "purple"
            }

        # Add single coordinate regions
        self.ocr_regions.update({
            "location": {"name": "Location Text", "coords": CONFIG.LOCATION_COORD, "color": "cyan"},
            "boss": {"name": "Boss Name", "coords": CONFIG.BOSS_COORD, "color": "magenta"},
            "domain": {"name": "Domain Name", "coords": CONFIG.DOMAIN_COORD, "color": "yellow"},
            "map_location": {"name": "Map Location", "coords": CONFIG.MAP_LOC_COORD, "color": "orange"},
            "activity": {"name": "Activity Region", "coords": CONFIG.ACTIVITY_COORD, "color": "lime"},
            "game_menu": {"name": "Game Menu", "coords": CONFIG.PARTY_SETUP_COORD, "color": "brown"},
        })

        # Bind events
        self.canvas.bind("<Button-3>", self.on_right_click)  # Right-click menu
        self.canvas.bind("<Key>", self.on_key_press)
        self.canvas.bind("<Configure>", self.on_canvas_resize)  # Handle canvas resize
        self.canvas.focus_set()

        # Start background screenshot thread
        self.screenshot_thread = None
        self.running = False
        self.start_screenshot_thread()

        # Load existing coordinates
        self.load_coordinates()

        # Draw initial grid
        self.draw_grid()

    def draw_grid(self):
        """Draw grid lines on the canvas."""
        # Clear existing grid lines
        for line_id in self.grid_lines:
            self.canvas.delete(line_id)
        self.grid_lines.clear()

        if not self.grid_enabled.get():
            return

        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1:  # Canvas not yet drawn
            return

        # Draw vertical lines
        for x in range(0, canvas_width, self.grid_size):
            line_id = self.canvas.create_line(x, 0, x, canvas_height,
                                           fill='#333333', width=1, dash=(2, 2))
            self.grid_lines.append(line_id)

        # Draw horizontal lines
        for y in range(0, canvas_height, self.grid_size):
            line_id = self.canvas.create_line(0, y, canvas_width, y,
                                           fill='#333333', width=1, dash=(2, 2))
            self.grid_lines.append(line_id)

    def snap_to_grid(self, value):
        """Snap a value to the nearest grid point."""
        if not self.snap_to_grid.get():
            return value
        return round(value / self.grid_size) * self.grid_size

    def toggle_grid(self):
        """Toggle grid visibility."""
        self.grid_enabled.set(not self.grid_enabled.get())
        self.draw_grid()
        status = "ON" if self.grid_enabled.get() else "OFF"
        self.status_var.set(f"Grid {status} - Grid Size: {self.grid_size}px")

    def toggle_snap(self):
        """Toggle snap-to-grid functionality."""
        self.snap_to_grid.set(not self.snap_to_grid.get())
        status = "ON" if self.snap_to_grid.get() else "OFF"
        self.status_var.set(f"Snap-to-Grid {status}")

    def set_grid_size(self, size):
        """Set grid size."""
        self.grid_size = size
        self.draw_grid()
        self.status_var.set(f"Grid Size: {self.grid_size}px - Grid: {'ON' if self.grid_enabled.get() else 'OFF'}")

    def create_control_panel(self):
        """Create the control panel."""
        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        # Instructions
        instructions = ttk.Label(control_frame,
                                text="🎯 Click and drag boxes to position them | 🖱️ Drag corners to resize | 🎨 Right-click to change colors | ⌘ Grid: G=Toggle | S=Snap | 1-4=Size",
                                font=('Arial', 9))
        instructions.pack(pady=5)

        # Controls
        controls_frame = ttk.Frame(control_frame)
        controls_frame.pack(fill=tk.X)

        # Left side controls
        left_controls = ttk.Frame(controls_frame)
        left_controls.pack(side=tk.LEFT)

        ttk.Button(left_controls, text="📋 Copy Coordinates",
                  command=self.copy_coordinates).pack(side=tk.LEFT, padx=5)
        ttk.Button(left_controls, text="💾 Save to File",
                  command=self.save_coordinates).pack(side=tk.LEFT, padx=5)
        ttk.Button(left_controls, text="🔄 Reset All",
                  command=self.reset_boxes).pack(side=tk.LEFT, padx=5)

        # Grid controls (center)
        grid_controls = ttk.Frame(controls_frame)
        grid_controls.pack(side=tk.LEFT, expand=True)

        # Grid size options
        grid_size_frame = ttk.Frame(grid_controls)
        grid_size_frame.pack(side=tk.TOP, pady=2)

        ttk.Label(grid_size_frame, text="Grid Size:").pack(side=tk.LEFT)
        for size in [10, 20, 50, 100]:
            ttk.Button(grid_size_frame, text=f"{size}px",
                      command=lambda s=size: self.set_grid_size(s),
                      width=6).pack(side=tk.LEFT, padx=2)

        # Grid toggle controls
        grid_toggle_frame = ttk.Frame(grid_controls)
        grid_toggle_frame.pack(side=tk.TOP, pady=2)

        ttk.Button(grid_toggle_frame, text="👁 Grid",
                  command=self.toggle_grid).pack(side=tk.LEFT, padx=2)
        ttk.Button(grid_toggle_frame, text="🔗 Snap",
                  command=self.toggle_snap).pack(side=tk.LEFT, padx=2)

        # Right side controls
        right_controls = ttk.Frame(controls_frame)
        right_controls.pack(side=tk.RIGHT)

        ttk.Button(right_controls, text="❌ Close",
                  command=self.quit).pack(side=tk.RIGHT, padx=5)

        # Status bar
        self.status_var = tk.StringVar(value="Ready - Click and drag boxes to position them")
        status_bar = ttk.Label(control_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=2)

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
        for region_key, region_info in self.ocr_regions.items():
            name = region_info["name"]
            coords = region_info["coords"]
            color = region_info["color"]

            try:
                if isinstance(coords, (list, tuple)) and len(coords) == 4:
                    # Single bounding box (x1, y1, x2, y2)
                    x1, y1, x2, y2 = coords
                    box = BoundingBox(self.canvas, x1, y1, x2, y2, region_key, color, self)
                    self.boxes[region_key] = box
                elif isinstance(coords, (list, tuple)) and len(coords) == 2:
                    # Single coordinate point (x, y) - create small box around it
                    x, y = coords
                    box = BoundingBox(self.canvas, x-15, y-15, x+15, y+15, region_key, color, self)
                    self.boxes[region_key] = box
                elif isinstance(coords, list) and len(coords) > 0 and isinstance(coords[0], (list, tuple)):
                    # Multiple bounding boxes or coordinate points
                    for i, coord_set in enumerate(coords):
                        if len(coord_set) == 4:
                            # Bounding box (x1, y1, x2, y2)
                            x1, y1, x2, y2 = coord_set
                            box_name = f"{region_key}_{i}"
                            box = BoundingBox(self.canvas, x1, y1, x2, y2, box_name, color, self)
                            self.boxes[box_name] = box
                        elif len(coord_set) == 2:
                            # Coordinate point (x, y) - create small box around it
                            x, y = coord_set
                            box_name = f"{region_key}_{i}"
                            box = BoundingBox(self.canvas, x-15, y-15, x+15, y+15, box_name, color, self)
                            self.boxes[box_name] = box
                else:
                    print(f"Warning: Unknown coordinate format for {region_key}: {coords} (type: {type(coords)})")
                    continue

            except Exception as e:
                print(f"Error loading coordinates for {region_key}: {e} (coords: {coords})")
                continue

        self.status_var.set(f"Loaded {len(self.boxes)} bounding boxes (Resolution: {GAME_RESOLUTION}p)")

    def reset_boxes(self):
        """Reset all boxes to default positions."""
        for box in self.boxes.values():
            self.canvas.delete(box.rect)
            self.canvas.delete(box.label)
            for handle in box.handles:
                self.canvas.delete(handle)

        self.boxes.clear()
        self.load_coordinates()
        self.status_var.set("Reset all boxes to default positions")

    def copy_coordinates(self):
        """Copy current coordinates to clipboard."""
        coords_dict = {}

        for region_key, box in self.boxes.items():
            coords = box.get_coords()
            if len(coords) == 4:
                coords_dict[region_key] = (int(coords[0]), int(coords[1]),
                                          int(coords[2]), int(coords[3]))

        # Format as Python code
        output = "# Updated OCR Coordinates\n\n"

        # Group by type
        char_names = {}
        char_numbers = {}
        char_number_points = {}  # Store original 2-tuple points for character numbers
        others = {}

        for name, coords in coords_dict.items():
            if name.startswith('character_') and not name.startswith('character_number_'):
                # Extract character number from name like "character_1" -> 1
                char_num = name.split('_')[1]
                char_names[int(char_num)] = coords
            elif name.startswith('character_number_'):
                # Extract character number from name like "character_number_1" -> 1
                char_num = name.split('_')[2]
                char_numbers[int(char_num)] = coords
                # Also store the center point as 2-tuple for export
                center_x = (coords[0] + coords[2]) // 2
                center_y = (coords[1] + coords[3]) // 2
                char_number_points[int(char_num)] = (center_x, center_y)
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
            if name == "location":
                output += f"LOCATION_COORD = {coords}\n"
            elif name == "boss":
                output += f"BOSS_COORD = {coords}\n"
            elif name == "domain":
                output += f"DOMAIN_COORD = {coords}\n"
            elif name == "map_location":
                output += f"MAP_LOC_COORD = {coords}\n"
            elif name == "game_menu":
                output += f"PARTY_SETUP_COORD = {coords}\n"
            else:
                output += f"{name.upper()}_COORD = {coords}\n"

        # Copy to clipboard
        self.root.clipboard_clear()
        self.root.clipboard_append(output)

        self.status_var.set(f"Copied {len(coords_dict)} coordinate sets to clipboard")

        # Show preview
        messagebox.showinfo("Coordinates Copied",
                          f"Copied coordinates for {len(coords_dict)} regions to clipboard.\n\nPaste into CONFIG.py")

    def save_coordinates(self):
        """Save coordinates to a file."""
        coords_dict = {}

        for region_key, box in self.boxes.items():
            coords = box.get_coords()
            if len(coords) == 4:
                coords_dict[region_key] = (int(coords[0]), int(coords[1]),
                                          int(coords[2]), int(coords[3]))

        filename = "calibrated_coordinates.json"
        with open(filename, 'w') as f:
            json.dump(coords_dict, f, indent=2)

        self.status_var.set(f"Saved coordinates to {filename}")

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
    if not TKINTER_AVAILABLE:
        print("❌ Cannot start calibrator: tkinter is not available")
        print("💡 Install tkinter:")
        print("   pip install tk")
        print("   On Ubuntu/Debian: sudo apt-get install python3-tk")
        return

    if not PSUTIL_AVAILABLE:
        print("❌ Cannot start calibrator: psutil is not available")
        print("💡 Install psutil:")
        print("   pip install psutil")
        return

    print("📋 Instructions:")
    print("   🎯 Click and drag boxes to move them")
    print("   🖱️  Drag corners to resize boxes")
    print("   🎨 Right-click boxes to change colors")
    print("   📋 Press 'C' to copy coordinates")
    print("   💾 Press 'S' to save to file")
    print("   🗑️  Press 'Delete' to remove selected box")
    print("   ❌ Press 'Escape' to exit")
    print("   👁  Press 'G' to toggle grid visibility")
    print("   🔗 Press 'Shift+G' to toggle snap-to-grid")
    print("   📏 Press '1-4' to change grid size (10px, 20px, 50px, 100px)")
    print()
    print("🚀 Starting calibrator...")

    try:
        print(f"📺 Detected screen resolution: {GAME_RESOLUTION}p")
        print(f"📏 Coordinates scaled from 1080p base to {GAME_RESOLUTION}p")
        print()

        calibrator = CoordinateCalibrator()
        print("✅ Calibrator started successfully")
        print("🎯 Position the overlay over your Genshin Impact window")
        print("📦 Adjust the bounding boxes to match your OCR regions")
        print()

        calibrator.root.mainloop()

    except Exception as e:
        print(f"❌ Error starting calibrator: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
