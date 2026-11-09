import os
import sys
import http.server
import socketserver
import threading
import time
import functools

# When launched with pythonw.exe (silent mode) there is no console and
# sys.stdout/sys.stderr are None - every print() would crash. Route them
# to the null device so the script behaves identically in both modes.
if sys.stdout is None or sys.stderr is None:
    _devnull = open(os.devnull, "w")
    if sys.stdout is None:
        sys.stdout = _devnull
    if sys.stderr is None:
        sys.stderr = _devnull


def _single_instance_guard(name: str):
    """Windows named mutex - returns a handle, or None if already running.

    Two GUI instances would spawn competing engines writing the same
    gui_shared_data.json / Discord presence, so refuse the second launch.
    """
    if sys.platform != "win32":
        return True  # non-Windows: no guard
    import ctypes
    kernel32 = ctypes.windll.kernel32
    handle = kernel32.CreateMutexW(None, False, name)
    if not handle:
        return None
    if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        kernel32.CloseHandle(handle)
        return None
    return handle  # keep referenced for process lifetime


_INSTANCE_MUTEX = _single_instance_guard("GenshinImpactRichPresence_GUI")
if _INSTANCE_MUTEX is None:
    print("Another instance is already running - exiting.")
    sys.exit(0)

# Frozen (PyInstaller exe): __file__ points inside the bundle's temp
# extraction dir - base everything on the exe's own folder instead.
if getattr(sys, "frozen", False):
    script_dir = os.path.dirname(os.path.abspath(sys.executable))
else:
    script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

print("Starting Web GUI (pywebview) version...")
try:
    import webview

    from gui.api import Api
except ImportError as e:
    print(f"Error: pywebview not installed. {e}")
    print("Install with: pip install pywebview")
    sys.exit(1)

DIST_DIR = os.path.join(script_dir, "gui", "dist")
if not os.path.exists(DIST_DIR):
    print(f"Error: built UI directory not found at {DIST_DIR}")
    print("Build it with:  cd gui && pnpm install && pnpm build")
    sys.exit(1)


# Serve the built files over a local HTTP server. Binding port 0 lets the OS
# pick a free port atomically (no check-then-bind race), and `directory=`
# avoids os.chdir() inside the server thread.
Handler = functools.partial(
    http.server.SimpleHTTPRequestHandler, directory=DIST_DIR
)


class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


httpd = ReusableTCPServer(("127.0.0.1", 0), Handler)
PORT = httpd.server_address[1]


def start_http_server():
    print(f"Serving built UI at http://localhost:{PORT}")
    httpd.serve_forever()

# Start the server in a separate thread
server_thread = threading.Thread(target=start_http_server, daemon=True)
server_thread.start()

# Give the server a moment to start
time.sleep(0.5)

# Construct the URL to load
ui_url = f"http://localhost:{PORT}/index.html"
print(f"Loading UI from: {ui_url}")

api = Api()
ASPECT = 16 / 9  # 16:9 — the UI is designed for this ratio
window = webview.create_window(
    "Genshin Impact Rich Presence",
    ui_url,
    js_api=api,
    width=1280,
    height=720,
    min_size=(960, 540),
    background_color="#08091a",
)
print("Window created successfully")


def _enforce_aspect(*_):
    """Lock the window to a 16:9 ratio so the 16:9 UI never looks stretched or tall."""
    try:
        w = window.width
        h = window.height
        target_h = round(w / ASPECT)
        if target_h != h:
            window.resize(w, target_h)
    except Exception as e:
        print(f"aspect lock failed: {e}")


window.events.loaded += _enforce_aspect
# Keep the ratio locked even if the user resizes the window.
window.events.resized += _enforce_aspect
# Re-apply once web fonts have finished loading (layout can shift after first paint).
for _delay in (0.8, 2.0, 3.5):
    threading.Timer(_delay, _enforce_aspect).start()

try:
    webview.start(gui="edgechromium")
finally:
    api.shutdown()
