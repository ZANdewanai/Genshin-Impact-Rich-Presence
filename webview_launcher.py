import os
import threading
import sys

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

DIST_INDEX = os.path.join(script_dir, "gui", "dist", "index.html")
if not os.path.exists(DIST_INDEX):
    print(f"Error: built UI not found at {DIST_INDEX}")
    print("Build it with:  cd gui && pnpm install && pnpm build")
    sys.exit(1)

api = Api()
window = webview.create_window(
    "Genshin Impact Rich Presence",
    DIST_INDEX,
    js_api=api,
    width=1060,
    height=900,
    min_size=(900, 620),
    background_color="#08091a",
)


def _fit_window(_=None):
    """Resize the window so the whole panel fits with no scrolling."""
    try:
        size = window.evaluate_js(
            """
            (() => { const el = document.body.children[0].children[0].children[0];
            if (!el) return [0, 0];
            const r = el.getBoundingClientRect();
            return [Math.ceil(r.width), Math.ceil(r.height)]; })()
            """
        )
        if size and size[0] and size[1]:
            # +40 = outer p-5 padding on both sides, +72 vertical safety margin
            window.resize(max(900, size[0] + 40), max(620, size[1] + 72))
    except Exception as e:
        print(f"fit failed: {e}")


window.events.loaded += _fit_window
# Re-fit once web fonts have finished loading (layout shifts after first paint),
# so the window always matches the true content height.
for _delay in (0.8, 2.0, 3.5):
    threading.Timer(_delay, _fit_window).start()

try:
    webview.start(gui="edgechromium")
finally:
    api.shutdown()
