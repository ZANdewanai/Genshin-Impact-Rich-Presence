import ctypes
import numpy as np
from typing import Optional, Tuple, Union, List

class CaptureUtils:
    def __init__(self, debug_mode: bool = False):
        self.debug_mode = debug_mode

    def capture_game_region(self, region_bbox: Union[Tuple, List],
                           game_window_rect: Optional[Tuple] = None) -> Optional[np.ndarray]:
        """
        Capture a region of the screen relative to the game window.

        Args:
            region_bbox: A tuple of (left, top, right, bottom) relative to the game window,
                        or (x, y) for a single point
            game_window_rect: Game window rectangle, will be detected if not provided

        Returns:
            numpy.ndarray: The captured image as a numpy array, or None if capture failed
        """
        try:
            # Ensure region_bbox is a tuple or list
            if not isinstance(region_bbox, (tuple, list)):
                if self.debug_mode:
                    print(f"[DEBUG] Invalid region_bbox type: {type(region_bbox)}")
                return None

            # Handle single point (x,y) by creating a small region around it
            if len(region_bbox) == 2:
                x, y = map(int, region_bbox)
                region_bbox = (x, y, x + 1, y + 1)

            # Ensure we have exactly 4 coordinates
            if len(region_bbox) != 4:
                if self.debug_mode:
                    print(f"[DEBUG] Invalid region_bbox length: {len(region_bbox)}")
                return None

            # Get the game window position and size if not provided
            if game_window_rect is None:
                game_window_rect = self._get_game_window_rect()
                if not game_window_rect or len(game_window_rect) < 4:
                    if self.debug_mode:
                        print("[DEBUG] Could not get valid game window rect")
                    return None

            try:
                # Convert coordinates to integers and calculate absolute screen coordinates
                left = int(game_window_rect[0]) + int(region_bbox[0])
                top = int(game_window_rect[1]) + int(region_bbox[1])
                right = int(game_window_rect[0]) + int(region_bbox[2])
                bottom = int(game_window_rect[1]) + int(region_bbox[3])
            except (ValueError, TypeError) as e:
                if self.debug_mode:
                    print(f"[DEBUG] Error converting coordinates: {e}")
                return None

            # Get screen size
            user32 = ctypes.windll.user32
            screen_width = user32.GetSystemMetrics(0)
            screen_height = user32.GetSystemMetrics(1)

            # Ensure coordinates are within screen bounds
            left = max(0, min(int(left), screen_width - 1))
            top = max(0, min(int(top), screen_height - 1))
            right = max(left + 1, min(int(right), screen_width))
            bottom = max(top + 1, min(int(bottom), screen_height))

            if left >= right or top >= bottom:
                if self.debug_mode:
                    print(f"[DEBUG] Invalid region coordinates after adjustment: {left}, {top}, {right}, {bottom}")
                return None

            # Ensure minimum size of 1x1
            width = right - left
            height = bottom - top
            if width < 1 or height < 1:
                if self.debug_mode:
                    print(f"[DEBUG] Region too small: {width}x{height}")
                return None

            # Check if the game window is focused before capturing
            if not self._is_game_focused():
                if self.debug_mode:
                    print("[DEBUG] Game window not focused, skipping capture")
                return None

            # Capture the region
            bbox = (left, top, right, bottom)
            return self._capture_screen_region(bbox)

        except Exception as e:
            if self.debug_mode:
                error_msg = str(e)
                print(f"[DEBUG] Error in capture_game_region: {error_msg}")
            return None

    def _get_game_window_rect(self) -> Optional[Tuple]:
        """Get the position and size of the Genshin Impact game window."""
        try:
            import win32gui
            import win32con

            result = [None]

            def callback(hwnd, _):
                if win32gui.IsWindowVisible(hwnd):
                    window_text = win32gui.GetWindowText(hwnd)
                    if "Genshin Impact" in window_text:
                        rect = win32gui.GetWindowRect(hwnd)
                        # Check if window is minimized
                        if win32gui.IsIconic(hwnd):
                            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                        result[0] = rect
                        return False  # Stop enumeration
                return True  # Continue enumeration

            win32gui.EnumWindows(callback, None)
            return result[0]

        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] Error getting game window rect: {e}")
            return None

    def _is_game_focused(self) -> bool:
        """Check if the Genshin Impact game window is currently focused."""
        try:
            from window_utils import is_genshin_window_focused
            return is_genshin_window_focused(self.debug_mode)
        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] Error checking window focus: {e}")
            return False

    def _capture_screen_region(self, bbox: Tuple) -> Optional[np.ndarray]:
        """Capture a screen region using Windows API."""
        try:
            hwnd = ctypes.windll.user32.GetDesktopWindow()
            hdc = ctypes.windll.user32.GetDC(hwnd)
            mfcDC = ctypes.windll.gdi32.CreateCompatibleDC(hdc)
            saveDC = ctypes.windll.gdi32.SaveDC(mfcDC)

            left, top, right, bottom = bbox
            width = right - left
            height = bottom - top

            # Create a bitmap
            saveBitMap = ctypes.windll.gdi32.CreateCompatibleBitmap(hdc, width, height)
            ctypes.windll.gdi32.SelectObject(mfcDC, saveBitMap)

            # Copy the screen to the bitmap
            ctypes.windll.gdi32.BitBlt(mfcDC, 0, 0, width, height,
                                     hdc, left, top, 0x00CC0020)  # SRCCOPY

            # Convert to PIL Image
            bmpinfo = {
                'size': (width, height),
                'width': width,
                'height': height,
                'bits': 32,
                'planes': 1,
                'compression': 0,
                'size_image': width * height * 4
            }

            # Create a buffer for the bitmap data
            bmpstr = ctypes.create_string_buffer(width * height * 4)
            ctypes.windll.gdi32.GetBitmapBits(saveBitMap, len(bmpstr), bmpstr)

            # Clean up
            ctypes.windll.gdi32.RestoreDC(mfcDC, saveDC)
            ctypes.windll.gdi32.DeleteObject(saveBitMap)
            ctypes.windll.gdi32.DeleteDC(mfcDC)
            ctypes.windll.user32.ReleaseDC(hwnd, hdc)

            # Convert to numpy array
            img = np.frombuffer(bmpstr, dtype=np.uint8)
            img = img.reshape((height, width, 4))  # RGBA
            return img[..., :3]  # Convert RGBA to RGB

        except Exception as e:
            if self.debug_mode:
                print(f"[DEBUG] Error in _capture_screen_region: {e}")
            return None
