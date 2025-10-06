"""
Process helper functions.

For detecting if a window is visible.
"""

import time
import pywintypes
import win32.win32gui as win32gui
import win32.win32process as win32process
import win32.lib.win32con as win32con
import psutil
import ctypes

EnumWindows = ctypes.windll.user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(
    ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)
)
GetWindowText = ctypes.windll.user32.GetWindowTextW
GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
IsWindowVisible = ctypes.windll.user32.IsWindowVisible


def _getProcessIDByName(process_name: str):
    pids = []

    for proc in psutil.process_iter():
        if process_name.lower() in proc.name().lower():
            pids.append(proc.pid)

    return pids


def _get_hwnds_for_pid(pid):
    def callback(hwnd, hwnds):
        # if win32gui.IsWindowVisible(hwnd) and win32gui.IsWindowEnabled(hwnd):
        _, found_pid = win32process.GetWindowThreadProcessId(hwnd)

        if found_pid == pid:
            hwnds.append(hwnd)
        return True

    hwnds = []
    win32gui.EnumWindows(callback, hwnds)
    return hwnds


_hwnd_cache = {}


def check_process_window_open(window_class=None, window_caption=None):
    """
    Returns `True` if a window with the given `window_class` and
    `window_caption` (window name) is visible. 
    
    If either class/name is `None`, the window handle search will match based 
    on the other provided value.
    """
    if window_caption in _hwnd_cache:
        hwnd = _hwnd_cache[window_caption]
    else:
        hwnd = win32gui.FindWindow(window_class, window_caption)
        if hwnd != 0: # don't cache invalid handles
            _hwnd_cache[window_caption] = hwnd

    try:
        _, showCmd, *_ = win32gui.GetWindowPlacement(hwnd)
        # print(f'hwnd: {hwnd}, visible: {IsWindowVisible(hwnd)}, showCmd: {showCmd}')
    except pywintypes.error:
        # Possible Invalid Window Handle error.
        # Genshin may be closed. Return False & invalidate cache.
        _hwnd_cache.pop(window_caption, None)
        return False

    if (
        hwnd != 0
        and IsWindowVisible(hwnd)
        and showCmd in [win32con.SW_SHOWMAXIMIZED, win32con.SW_SHOWNORMAL]
    ):
        return True

    return False