"""
Overlay system for visualizing OCR regions in Genshin Impact.

This module provides a transparent overlay that displays OCR detection regions
for debugging and development purposes.
"""
import tkinter as tk
import threading
import time
import sys
import ctypes
from typing import Optional, Dict, Any, Tuple, List

import sys
import os
import importlib.util

# Load CONFIG.py as a script
config_path = os.path.join(os.path.dirname(__file__), '../../CONFIG.py')
exec(open(config_path).read())

# Load window_utils module dynamically
window_utils_path = os.path.join(os.path.dirname(__file__), '../window_utils.py')
spec = importlib.util.spec_from_file_location("window_utils", window_utils_path)
window_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(window_utils)

import tkinter as tk
import threading
import time
import sys
import ctypes
from typing import Optional, Dict, Any, Tuple, List

# Import our utility functions and constants
from .overlay_utils import (
    OverlayConfig, load_config_from_module,
    WINDOW_STYLES, DEFAULT_UPDATE_INTERVAL_MS, DEFAULT_ERROR_RETRY_DELAY_MS
)

class OCRDebuggerOverlay:
    """
    A debugging overlay that visualizes OCR detection regions in Genshin Impact.
    
    This overlay creates a transparent window that shows the areas being scanned
    for game information, making it easier to debug OCR detection issues.
    """

    def __init__(self):
        """Initialize the overlay with default values."""
        # Initialize attributes with default values first
        self.overlay_window: Optional[tk.Tk] = None
        self.canvas: Optional[tk.Canvas] = None
        self.update_thread: Optional[threading.Thread] = None
        self.running: bool = False
        self._last_bring_to_front: float = 0.0
        self.regions: Dict[str, Tuple[List, str]] = {}
        self.labels: Dict[str, str] = {}
        self._drawn_text_y_positions = []
        
        # Initialize debug mode early to ensure it's always available
        self.debug_mode = False
        
        # Set default colors that can be overridden by config
        self.border_color = 'yellow'
        self.text_color = 'white'
        self.background_color = 'black'
        self.border_width = 2
        self.opacity = 0.8
        
        # Load configuration from CONFIG module
        self.config = self._load_config()
        
        # Apply config values if available
        if hasattr(self.config, 'debug_mode'):
            self.debug_mode = self.config.debug_mode
        if hasattr(self.config, 'border_color'):
            self.border_color = self.config.border_color
        if hasattr(self.config, 'text_color'):
            self.text_color = self.config.text_color
        if hasattr(self.config, 'background_color'):
            self.background_color = self.config.background_color
        if hasattr(self.config, 'border_width'):
            self.border_width = self.config.border_width
        if hasattr(self.config, 'opacity'):
            self.opacity = self.config.opacity

    def _load_config(self) -> OverlayConfig:
        """
        Load configuration from the CONFIG module.
        
        Returns:
            OverlayConfig: The loaded configuration
        """
        try:
            # Import the entire config module to avoid circular imports
            import CONFIG
            
            # Load basic configuration
            config = load_config_from_module(CONFIG)
            
            # Load coordinates with safe fallbacks
            coords = {}
            for name in [
                'NUMBER_4P_COORD', 'NAMES_4P_COORD', 'BOSS_COORD',
                'LOCATION_COORD', 'DOMAIN_COORD', 'GAME_MENU_COORD',
                'MAP_LOC_COORD'
            ]:
                coords[name] = getattr(CONFIG, name, [])
            
            # Store regions with validation
            self.regions = {
                "character_numbers": (coords['NUMBER_4P_COORD'], "character_numbers"),
                "character_names": (coords['NAMES_4P_COORD'], "character_names"),
                "boss": ([coords['BOSS_COORD']] if coords['BOSS_COORD'] else [], "boss"),
                "location": ([coords['LOCATION_COORD']] if coords['LOCATION_COORD'] else [], "location"),
                "domain": ([coords['DOMAIN_COORD']] if coords['DOMAIN_COORD'] else [], "domain"),
                "game_menu": ([coords['GAME_MENU_COORD']] if coords['GAME_MENU_COORD'] else [], "game_menu"),
                "map_location": ([coords['MAP_LOC_COORD']] if coords['MAP_LOC_COORD'] else [], "map_location")
            }
            
            # Store labels with safe fallback
            self.labels = OCR_REGION_LABELS
            if not hasattr(self.labels, 'get'):
                self.labels = {}
            
            if config.debug_mode:
                print("[DEBUG] Overlay configuration loaded successfully")
                print(f"[DEBUG] Overlay enabled: {config.enabled}")
                print(f"[DEBUG] Border color: {config.border_color}")
                print(f"[DEBUG] Text color: {config.text_color}")
                print(f"[DEBUG] Border width: {config.border_width}")
                print(f"[DEBUG] Opacity: {config.opacity}")
            
            return config
            
        except Exception as e:
            print(f"[ERROR] Error loading overlay configuration: {e}")
            if hasattr(self, 'debug_mode') and self.debug_mode:
                import traceback
                traceback.print_exc()
            return OverlayConfig()  # Return default config on error

    def start(self) -> bool:
        """
        Start the overlay in the main thread.
        
        Returns:
            bool: True if the overlay started successfully, False otherwise
        """
        try:
            if self.running:
                if self.debug_mode:
                    print("[DEBUG] Overlay is already running")
                return True
                
            self.running = True
            
            # Check if game is running and focused before creating window
            if not self._is_game_running() or not self._is_game_focused():
                if self.debug_mode:
                    print("[DEBUG] Game not running or not focused, deferring overlay creation")
                # Start a monitoring thread that will create the overlay when game is ready
                self._start_monitoring_thread()
                return True
            
            # Create the overlay window in the main thread
            self._create_overlay()
            
            # Start the update loop using Tkinter's after method instead of a separate thread
            if hasattr(self, 'overlay_window') and self.overlay_window:
                self._schedule_next_update()
                # Start Tkinter event processing
                self.overlay_window.after(10, self._process_tkinter_events)
            
            if self.debug_mode:
                print("[DEBUG] Overlay started in main thread")
                
            return True
                
        except Exception as e:
            print(f"[ERROR] Failed to start overlay: {e}")
            self.running = False
            if self.debug_mode:
                import traceback
                traceback.print_exc()
            return False
            
    def _update_overlay_loop(self):
        """
        Main update loop for the overlay.
        This method is called repeatedly to keep the Tkinter event loop running.
        """
        if not hasattr(self, 'overlay_window') or not self.overlay_window or not self.running:
            return
            
        try:
            # Process any pending Tkinter events
            self.overlay_window.update_idletasks()
            self.overlay_window.update()
            
            # Update the overlay content
            self._update_overlay()
            
            # Schedule the next update
            self._schedule_next_update()
            
            # Schedule the next update if still running
            if self.running and self.overlay_window:
                self.overlay_window.after(10, self._process_tkinter_events)
                
        except Exception as e:
            error_msg = str(e).lower()
            if "application has been destroyed" not in error_msg:
                print(f"[ERROR] Tkinter update error: {e}")
                if self.config.debug_mode:
                    import traceback

    def stop(self):
        """Stop the overlay and close the window."""
        self.running = False
        
        # Try to stop the Tkinter main loop
        if hasattr(self, 'overlay_window') and self.overlay_window:
            try:
                # Schedule window destruction in the Tkinter thread
                self.overlay_window.after(0, self.overlay_window.quit)
                self.overlay_window.after(0, self.overlay_window.destroy)

                # If we're in the main thread, update to process the destroy command
                if threading.current_thread() is threading.main_thread():
                    self.overlay_window.update()

            finally:
                self.overlay_window = None
        
    def _process_tkinter_events(self):
        """
        Process pending Tkinter events to keep the window responsive.
        This replaces the need for a separate mainloop thread.
        """
        if not hasattr(self, 'overlay_window') or not self.overlay_window or not self.running:
            return
            
        try:
            # Process any pending events
            self.overlay_window.update_idletasks()
            
            # Schedule the next update
            if self.running and self.overlay_window:
                self.overlay_window.after(10, self._process_tkinter_events)
                
        except Exception as e:
            error_msg = str(e).lower()
            if "application has been destroyed" not in error_msg:
                print(f"[ERROR] Tkinter event processing error: {e}")
                if self.config.debug_mode:
                    import traceback
                    traceback.print_exc()

    def _update_overlay_loop(self) -> None:
        """
        Main update loop for the overlay.
        
        This method is called repeatedly to update the overlay content and handle window management.
        """
        try:
            if not self.running or not self.overlay_window:
                return
                
            # Update the overlay content
            self._update_overlay()
            
            # Only try to bring to front every 5 seconds to reduce overhead
            current_time = time.time()
            
            if current_time - self._last_bring_to_front >= 5.0:  # Reduced frequency
                try:
                    # Only update window state if it still exists
                    if hasattr(self, 'overlay_window') and self.overlay_window:
                        self.overlay_window.after(0, self._safe_bring_to_front)
                    self._last_bring_to_front = current_time
                except Exception as e:
                    if self.config.debug_mode:
                        print(f"[DEBUG] Error in update loop: {e}")
                        import traceback
                        traceback.print_exc()
        except Exception as e:
            if self.config.debug_mode:
                print(f"[DEBUG] Critical error in update loop: {e}")
                import traceback
                traceback.print_exc()
    def _schedule_next_update(self, delay_ms: int = 100) -> None:
        """
        Schedule the next overlay update.
        
        Args:
            delay_ms: Delay in milliseconds before the next update
        """
        try:
            if hasattr(self, 'overlay_window') and self.overlay_window and self.running:
                self.overlay_window.after(delay_ms, self._update_overlay_loop)
        except Exception as e:
            error_str = str(e).lower()
            
            # Handle specific window-related errors
            if any(msg in error_str for msg in ["invalid command name", "application has been destroyed"]):
                if self.config.debug_mode:
                    print("[DEBUG] Window was closed, stopping overlay updates")
                return
                
            print(f"[ERROR] Overlay update error: {e}")
            
            if self.config.debug_mode:
                import traceback
                traceback.print_exc()
                
            # Try to recover with a longer delay
            if self.running and hasattr(self, 'overlay_window') and self.overlay_window:
                self.overlay_window.after(
                    self.config.error_retry_delay_ms,
                    self._update_overlay_loop
                )

            # Try to recover with a longer delay
            if self.running and hasattr(self, 'overlay_window') and self.overlay_window:
                self.overlay_window.after(
                    self.config.error_retry_delay_ms,
                    self._update_overlay_loop
                )

    def _make_click_through(self, hwnd: int) -> None:
        """
        Make the window click-through using Windows API.
        
        Args:
            hwnd: The window handle to modify
        """
        try:
            # Define constants
            GWL_EXSTYLE = -20
            WS_EX_LAYERED = 0x00080000
            WS_EX_TRANSPARENT = 0x00000020
            WS_EX_TOOLWINDOW = 0x00000080
            WS_EX_NOACTIVATE = 0x08000000
            
            # Get current window style
            current_style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            
            # Set new style with click-through and no-activate flags
            new_style = (current_style | 
                        WS_EX_LAYERED | 
                        WS_EX_TOOLWINDOW | 
                        WS_EX_NOACTIVATE)
            
            # Apply the new style
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)
            
            # Apply static click-through (always transparent to avoid focus issues)
            ctypes.windll.user32.SetWindowLongW(
                hwnd, 
                GWL_EXSTYLE, 
                ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE) | 
                WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
            )
            
            if self.debug_mode:
                print("[DEBUG] Set static click-through mode")
                
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] Could not set click-through: {e}")
            # Fall back to a simpler approach if the dynamic method fails
            try:
                ctypes.windll.user32.SetWindowLongW(
                    hwnd, 
                    GWL_EXSTYLE, 
                    ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE) | 
                    WS_EX_LAYERED | WS_EX_TRANSPARENT | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
                )
                if self.debug_mode:
                    print("[DEBUG] Fallback: Set static click-through mode")
            except:
                pass
    
    def _configure_window_properties(self, window_handle: int) -> None:
        """
        Configure window properties to make it a transparent overlay.
        
{{ ... }}
        Args:
            window_handle: The handle to the window to configure
        """
        try:
            # Call _make_click_through to handle the window styles
            self._make_click_through(window_handle)
            
            # Set up the window to stay on top and not steal focus
            ctypes.windll.user32.SetWindowPos(
                window_handle, 
                -1,  # HWND_TOPMOST
                0, 0, 0, 0,
                0x0001 | 0x0002  # SWP_NOSIZE | SWP_NOMOVE
            )
            
            if self.debug_mode:
                print("[DEBUG] Set window to stay on top")
                
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] Could not configure window properties: {e}")
                
    def _create_overlay(self):
        """Create the overlay window and canvas with proper error handling."""
        try:
            if self.debug_mode:
                print("[DEBUG] Creating overlay window...")
                print(f"[DEBUG] Using colors - border: {self.config.border_color}, text: {self.config.text_color}")
            
            # Create main window
            self.overlay_window = tk.Tk()
            self.overlay_window.title("Genshin Impact OCR Overlay")
            
            # Set a default background color that will be made transparent
            bg_color = 'white'  # Using white as the transparent color
            
            try:
                # Configure window
                self.overlay_window.config(bg=self.config.background_color)
                
                # Set window properties
                self.overlay_window.attributes("-alpha", self.config.opacity)
                self.overlay_window.attributes("-topmost", True)
                self.overlay_window.attributes("-fullscreen", True)
                self.overlay_window.attributes("-transparentcolor", self.config.background_color)
                
                # Remove window decorations
                self.overlay_window.overrideredirect(True)
                
                # Get screen dimensions
                screen_width = self.overlay_window.winfo_screenwidth()
                screen_height = self.overlay_window.winfo_screenheight()
                
                # Create canvas with transparent background
                self.canvas = tk.Canvas(
                    self.overlay_window, 
                    width=screen_width,
                    height=screen_height,
                    bg=self.config.background_color,
                    highlightthickness=0,
                    bd=0  # No border
                )
                self.canvas.pack(fill=tk.BOTH, expand=True)
                
                # Make the canvas background transparent
                self.overlay_window.wm_attributes("-transparentcolor", bg_color)
                
                # Make window click-through
                try:
                    # Get the window handle
                    hwnd = ctypes.windll.user32.GetParent(self.overlay_window.winfo_id())
                    
                    # Configure initial window properties
                    self._configure_window_properties(hwnd)
                    
                    # Set up a timer to periodically update the window state
                    def update_window_state():
                        try:
                            if hasattr(self, 'overlay_window') and self.overlay_window:
                                # Keep window on top
                                ctypes.windll.user32.SetWindowPos(
                                    hwnd, -1,  # HWND_TOPMOST
                                    0, 0, 0, 0,
                                    0x0001 | 0x0002  # SWP_NOSIZE | SWP_NOMOVE
                                )
                                # Schedule next update
                                self.overlay_window.after(1000, update_window_state)
                        except Exception as e:
                            if self.debug_mode:
                                print(f"[DEBUG] Error in window state update: {e}")
                    
                    # Start the window state update loop
                    if hasattr(self, 'overlay_window') and self.overlay_window:
                        self.overlay_window.after(1000, update_window_state)
                        
                    if self.debug_mode:
                        print("[DEBUG] Window properties and click-through configured")
                        
                except Exception as e:
                    if self.debug_mode:
                        print(f"[DEBUG] Could not set click-through: {e}")
                
                # Bind escape key to close overlay
                self.overlay_window.bind("<Escape>", lambda e: self.stop())
                
                if self.debug_mode:
                    print("[DEBUG] Overlay window created successfully")
                    print(f"[DEBUG] Screen size: {screen_width}x{screen_height}")
                
                # Force update to ensure window is properly rendered
                self.overlay_window.update_idletasks()
                self.overlay_window.lift()

                # Don't start a separate mainloop thread - the overlay should be managed from the main thread
                # The main thread will handle updates through the _update_overlay_loop method
                
            except Exception as e:
                print(f"[ERROR] Error configuring overlay window: {e}")
                if self.debug_mode:
                    import traceback
                    traceback.print_exc()
                raise
                
        except Exception as e:
            error_msg = f"[ERROR] Failed to create overlay: {e}"
            print(error_msg)
            if self.debug_mode:
                import traceback
                traceback.print_exc()
                
            # Clean up if window was partially created
            if hasattr(self, 'overlay_window') and self.overlay_window:
                try:
                    self.overlay_window.destroy()
                except:
                    pass
                self.overlay_window = None
            
            # Disable overlay to prevent repeated errors
            self.enabled = False
            print("[INFO] Overlay has been disabled due to errors")
            raise

    def _start_monitoring_thread(self):
        """Start a background thread to monitor game state and create overlay when ready."""
        if hasattr(self, '_monitoring_thread') and self._monitoring_thread.is_alive():
            return
            
        self._monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()
        
    def _monitoring_loop(self):
        """Background loop to monitor game state and create overlay when ready."""
        while self.running:
            try:
                if self._is_game_running() and self._is_game_focused():
                    # Game is ready, create overlay in main thread
                    self.overlay_window.after(0, self._create_overlay)
                    break
                time.sleep(1)  # Check every second
            except Exception as e:
                if self.debug_mode:
                    print(f"[DEBUG] Error in monitoring loop: {e}")
                break

    def _is_game_focused(self):
        """Check if the game window is focused."""
        try:
            return window_utils.is_genshin_window_focused(self.debug_mode)
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] Error checking game focus: {e}")
            return False

    def _is_game_running(self):
        """Check if the game process is running."""
        try:
            return window_utils._is_genshin_process_running()
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] Error checking game running: {e}")
            return False

    def _update_overlay(self):
        """Update the overlay with current OCR regions."""
        if not self.overlay_window or not self.canvas:
            return

        try:
            # Check if game is running first
            if not self._is_game_running():
                # Hide the window when game is not running
                if self.overlay_window:
                    self.overlay_window.withdraw()
                return

            # Check if game is focused before updating
            if not self._is_game_focused():
                # Hide the window when game is not focused
                if self.overlay_window:
                    self.overlay_window.withdraw()
                return

            # Show window if it was hidden
            if self.overlay_window and not self.overlay_window.winfo_viewable():
                self.overlay_window.deiconify()
                self.overlay_window.lift()

            # Draw regions (add debug output)
            if self.debug_mode:
                print(f"[DEBUG] Updating overlay regions")

            # Clear previous drawings and reset text position tracking
            self.canvas.delete("all")
            if hasattr(self, '_drawn_text_y_positions'):
                self._drawn_text_y_positions = []
            
            # Track which regions we've already drawn to prevent duplicates
            drawn_regions = set()
            
            # Draw all regions
            for region_name, (coords_list, label_key) in self.regions.items():
                if not coords_list or region_name in drawn_regions:
                    continue
                    
                # Only draw each unique region once
                self._draw_region(region_name, coords_list, label_key)
                drawn_regions.add(region_name)
                
        except Exception as e:
            if self.debug_mode and hasattr(self, 'debug_mode'):
                print(f"[ERROR] Failed to update overlay: {e}")
                
    def _draw_region(self, region_name, coords_list, label_key):
        """Draw border and label for a specific OCR region with proper error handling."""
        if not coords_list or not hasattr(self, 'canvas') or not self.canvas:
            if self.debug_mode and not coords_list:
                print(f"[DEBUG] No coordinates provided for region: {region_name}")
            return

        try:
            # Get label with fallback
            label = self.labels.get(label_key, region_name)
            
            # Ensure colors are valid strings
            border_color = str(self.border_color) if self.border_color else 'yellow'
            # Use light cyan for better visibility against white text
            text_color = '#00FFFF'  # Always use light cyan for better visibility
            if self.debug_mode:
                print(f"[DEBUG] Using text color: {text_color} (self.text_color was: {self.text_color})")
            
            # Ensure border width is valid
            try:
                border_width = max(1, min(10, int(self.border_width)))
            except (ValueError, TypeError):
                border_width = 2
            
            # Process all coordinates in the list
            for i, coords in enumerate(coords_list):
                if not coords or len(coords) != 4:
                    if self.debug_mode:
                        print(f"[DEBUG] Invalid coordinates for {region_name} {i+1}: {coords}")
                    continue
                
                try:
                    left, top, right, bottom = map(int, coords)
                    
                    # Draw border with error handling
                    try:
                        self.canvas.create_rectangle(
                            left, top, right, bottom,
                            outline=border_color,
                            width=border_width,
                            fill="",
                            tags=(f"{region_name}_{i}", "border")
                        )
                    except tk.TclError as e:
                        if "color" in str(e).lower():
                            # Fallback to default color if specified color is invalid
                            self.canvas.create_rectangle(
                                left, top, right, bottom,
                                outline='yellow',
                                width=border_width,
                                fill="",
                                tags=(f"{region_name}_{i}", "border")
                            )
                            if self.debug_mode:
                                print(f"[DEBUG] Used fallback color for {region_name} {i+1} border")
                        else:
                            raise
                    
                    # Calculate text position with dynamic vertical spacing
                    text_x = left + (right - left) // 2
                    
                    # Start with desired position above the region
                    desired_y = max(20, top - 20)
                    
                    # Find first available y position that doesn't overlap with existing text
                    min_spacing = 30  # Minimum spacing between text labels
                    
                    # Initialize text_y with desired position
                    text_y = desired_y
                    
                    # Check for overlap with existing text positions
                    if hasattr(self, '_drawn_text_y_positions') and self._drawn_text_y_positions:
                        # Sort existing y positions
                        sorted_y = sorted(self._drawn_text_y_positions)
                        
                        # Find the first non-overlapping position
                        for y in sorted_y:
                            if abs(y - text_y) < min_spacing:
                                text_y = y + min_spacing
                    
                    # Add this position to the list of used positions
                    if not hasattr(self, '_drawn_text_y_positions'):
                        self._drawn_text_y_positions = []
                    self._drawn_text_y_positions.append(text_y)
                    
                    # Create a unique label for each character (e.g., "character_names_1", "character_names_2", etc.)
                    char_label = f"{label} {i+1}" if region_name == "character_names" else label
                    
                    # Draw label text with error handling
                    try:
                        self.canvas.create_text(
                            text_x, text_y,
                            text=char_label.upper(),  # Make text uppercase for better visibility
                            fill=text_color,
                            font=("Arial", 14, "bold"),  # Increased font size to 14 (40% larger than 10)
                            anchor="s",
                            tags=(f"{region_name}_{i}", "label")
                        )
                    except tk.TclError as e:
                        if "color" in str(e).lower():
                            # Fallback to light cyan text color if specified color is invalid
                            self.canvas.create_text(
                                text_x, text_y,
                                text=char_label.upper(),
                                fill='#00FFFF',  # Light cyan
                                font=("Arial", 14, "bold"),
                                anchor="s",
                                tags=(f"{region_name}_{i}", "label")
                            )
                            if self.debug_mode:
                                print(f"[DEBUG] Used fallback color for {region_name} {i+1} text")
                
                except (ValueError, TypeError) as e:
                    if self.debug_mode:
                        print(f"[DEBUG] Invalid coordinate values for {region_name}: {coords} - {e}")
                    continue
                except Exception as e:
                    if self.debug_mode:
                        print(f"[DEBUG] Error drawing {region_name}: {e}")
                    continue
                    
        except Exception as e:
            if self.debug_mode:
                print(f"[ERROR] Failed to draw region {region_name}: {e}")
                import traceback
                traceback.print_exc()

# Global overlay instance
overlay = OCRDebuggerOverlay()
