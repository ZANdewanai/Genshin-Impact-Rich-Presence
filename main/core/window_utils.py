"""
Window and focus utilities for Genshin Impact.
This module provides cross-module access to window focus state.
"""
import time
import win32gui
import win32process
import psutil
from typing import Optional, Tuple, Any

# Global state to track focus
_last_focus_state = False
_last_print_time = 0

def is_genshin_window_focused(debug_mode: bool = False) -> bool:
    """
    Check if the Genshin Impact game window is currently focused.
    
    Args:
        debug_mode: Whether to print debug information
        
    Returns:
        bool: True if Genshin Impact window is focused, False otherwise
    """
    global _last_focus_state, _last_print_time
    
    try:
        # First check if Genshin Impact process is running
        if not _is_genshin_process_running():
            if debug_mode and (_last_focus_state or time.time() - _last_print_time > 5):
                print("[FOCUS] Genshin Impact process is not running")
                _last_print_time = time.time()
            _last_focus_state = False
            return False
            
        # Get the handle of the active window
        active_window = win32gui.GetForegroundWindow()
        if not active_window:
            if debug_mode and (_last_focus_state or time.time() - _last_print_time > 5):
                print("[FOCUS] No active window found")
                _last_print_time = time.time()
            _last_focus_state = False
            return False
            
        # Check if window is minimized or not visible
        if win32gui.IsIconic(active_window) or not win32gui.IsWindowVisible(active_window):
            if debug_mode and (_last_focus_state or time.time() - _last_print_time > 5):
                print("[FOCUS] Game window is minimized or not visible")
                _last_print_time = time.time()
            _last_focus_state = False
            return False
            
        # Get the window class and title of the active window
        window_class = win32gui.GetClassName(active_window)
        window_title = win32gui.GetWindowText(active_window)
        
        # Check for Genshin Impact window by title and class first (faster than process check)
        is_genshin = ("Genshin Impact" in window_title and 
                     'UnityWndClass' in window_class)
        
        # If not found, try by process name
        if not is_genshin:
            try:
                _, process_id = win32process.GetWindowThreadProcessId(active_window)
                process = psutil.Process(process_id)
                process_name = process.name().lower()
                
                # Check for various possible process names
                is_genshin = ("genshinimpact" in process_name or 
                             "genshin impact" in process_name or
                             "yuan" in process_name or  # Sometimes appears as 'YuanShen.exe'
                             any(p.name().lower() == 'genshinimpact.exe' 
                                 for p in process.parents()))  # Check parent processes
                
            except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
                pass
        
        # Debug output only on focus change or every 10 seconds
        if debug_mode:
            current_time = time.time()
            
            # Only print on state change or every 10 seconds if still focused
            if (is_genshin != _last_focus_state or 
                (is_genshin and current_time - _last_print_time > 10)):
                
                status = "FOCUSED" if is_genshin else "LOST FOCUS"
                debug_info = [
                    f"[FOCUS] Game window {status}",
                    f"[FOCUS] Window Title: {window_title}",
                    f"[FOCUS] Window Class: {window_class}",
                ]
                
                try:
                    _, pid = win32process.GetWindowThreadProcessId(active_window)
                    debug_info.append(f"[FOCUS] Process ID: {pid}")
                    
                    p = psutil.Process(pid)
                    debug_info.append(f"[FOCUS] Process Name: {p.name()}")
                    if p.parent():
                        debug_info.append(f"[FOCUS] Parent Process: {p.parent().name()}")
                except Exception as e:
                    if debug_mode and current_time - _last_print_time > 60:
                        debug_info.append(f"[FOCUS] Could not get process info: {e}")
                
                print("\n".join(debug_info))
                _last_print_time = current_time
        
        _last_focus_state = is_genshin
        return is_genshin
            
    except Exception as e:
        current_time = time.time()
        if debug_mode and current_time - _last_print_time > 60:
            print(f"[FOCUS] Error checking window focus: {e}")
            _last_print_time = current_time
        return False


def _is_genshin_process_running() -> bool:
    """
    Check if the Genshin Impact process is currently running.
    
    Returns:
        bool: True if Genshin Impact process is running, False otherwise
    """
    try:
        # Use a more efficient method to check for the process
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] == 'GenshinImpact.exe':
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception:
                continue
        return False
    except Exception:
        return False
