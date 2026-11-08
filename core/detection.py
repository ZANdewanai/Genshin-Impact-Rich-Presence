"""Coordinate resolution monitoring.

Checks for Genshin window resolution changes and updates coordinates.
"""

import time

from core import ps_helper
from core import state as state_module


# Resolution check interval (seconds)
RESOLUTION_CHECK_INTERVAL = 60

# Resolution change threshold
RESOLUTION_CHANGE_THRESHOLD = 10


def update_coordinates_if_needed():
    """
    Checks if Genshin window resolution has changed and updates coordinates accordingly.
    Called both for initialization and for continuous monitoring.
    """
    # Lazy import to avoid circular import with CONFIG
    from CONFIG import get_dynamic_coordinates

    try:
        current_time = time.time()

        # Check if we need to monitor for resolution changes
        if (
            state_module.current_resolution is not None
            and (current_time - state_module._last_resolution_check) >= RESOLUTION_CHECK_INTERVAL
        ):
            state_module._last_resolution_check = current_time

            # Get current window size
            window_rect = ps_helper.get_genshin_window_rect()
            if window_rect:
                current_window_size = (
                    window_rect[2] - window_rect[0],
                    window_rect[3] - window_rect[1],
                )  # width, height

                # Check if resolution changed significantly
                if (
                    abs(current_window_size[1] - state_module.current_resolution[1])
                    > RESOLUTION_CHANGE_THRESHOLD
                ):
                    if state_module.DEBUG_MODE:
                        print(
                            f"Detected resolution change: {state_module.current_resolution[0]}x{state_module.current_resolution[1]} -> {current_window_size[0]}x{current_window_size[1]}"
                        )

                    # Force re-detection of coordinates
                    state_module.current_resolution = None
            else:
                state_module.current_resolution = None

        # Initialize or re-initialize coordinates if needed
        if state_module.current_resolution is None:
            new_coordinates, new_resolution = get_dynamic_coordinates()

            # Only update if we actually got new coordinates
            if new_coordinates and new_resolution:
                state_module.current_resolution = new_resolution
                state_module.current_coordinates = new_coordinates

                resolution_log = f"{'Updated' if state_module._last_resolution_check > 0 else 'Initialized'} coordinates for resolution: {new_resolution[0]}x{new_resolution[1]}"
                if resolution_log != state_module._last_coordinate_log:
                    print(resolution_log)
                    state_module._last_coordinate_log = resolution_log

                return True

    except (OSError, RuntimeError, ValueError) as e:
        if state_module.DEBUG_MODE:
            print(
                f"Error {'updating' if state_module.current_resolution else 'initializing'} coordinates: {e}"
            )

    return False