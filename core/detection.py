"""Coordinate resolution monitoring.

Legacy detection loop removed — sensor architecture (CharSensor /
LocationSensor / MenuSensor + coordinator) is the only supported path now.
This module only keeps the resolution-change watcher and its globals.
"""

import time

from core import ps_helper, state as state_module

from CONFIG import (
    get_dynamic_coordinates,
)

# Resolution check interval (seconds)
RESOLUTION_CHECK_INTERVAL = 60

# Resolution change threshold
RESOLUTION_CHANGE_THRESHOLD = 10

# Coordinate globals updated by update_coordinates_if_needed().
NUMBER_4P_COORD = None
NAMES_4P_COORD = None
BOSS_COORD = None
LOCATION_COORD = None
MAP_LOC_COORD = None
ACTIVITY_COORD = None
DOMAIN_COORD = None
PARTY_SETUP_COORD = None


def update_coordinates_if_needed():
    """
    Checks if Genshin window resolution has changed and updates coordinates accordingly.
    Called both for initialization and for continuous monitoring.
    """
    global NUMBER_4P_COORD, NAMES_4P_COORD, BOSS_COORD, LOCATION_COORD
    global MAP_LOC_COORD, ACTIVITY_COORD, DOMAIN_COORD, PARTY_SETUP_COORD

    try:
        current_time = time.time()

        # Check if we need to monitor for resolution changes (every RESOLUTION_CHECK_INTERVAL seconds)
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
                    state_module.current_resolution = (
                        None  # Reset to trigger re-initialization below
                    )
            else:
                state_module.current_resolution = None

        # Initialize or re-initialize coordinates if needed
        if state_module.current_resolution is None:
            new_coordinates, new_resolution = get_dynamic_coordinates()

            # Only update if we actually got new coordinates
            if new_coordinates and new_resolution:
                state_module.current_resolution = new_resolution
                state_module.current_coordinates = new_coordinates

                # Update global coordinate variables
                NUMBER_4P_COORD = new_coordinates["NUMBER_4P_COORD"]
                NAMES_4P_COORD = new_coordinates["NAMES_4P_COORD"]
                BOSS_COORD = new_coordinates["BOSS_COORD"]
                LOCATION_COORD = new_coordinates["LOCATION_COORD"]
                MAP_LOC_COORD = new_coordinates["MAP_LOC_COORD"]
                ACTIVITY_COORD = new_coordinates["ACTIVITY_COORD"]
                DOMAIN_COORD = new_coordinates["DOMAIN_COORD"]
                PARTY_SETUP_COORD = new_coordinates["PARTY_SETUP_COORD"]

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
