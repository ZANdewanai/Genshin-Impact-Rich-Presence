"""Core modules for Genshin Impact Rich Presence."""
from core.state import (
    current_active_character, last_active_character,
    current_characters, current_activity, prev_non_idle_activity,
    game_start_time, current_timer_type, ingame_pause_ocr,
    gui_callback, shutdown_event, state_lock, ocr_lock,
    update_activity, set_active_character, update_character,
    get_current_activity, get_current_characters, get_game_start_time,
    get_current_timer_type, get_last_active_character,
    reset_game_start_time, write_gui_shared_data,
    shutdown_ocr_executor,
)
from core.ocr_utils import capture_and_process_ocr, calculate_keyword_match_score, calculate_location_confidence, process_map_text
from core.discord_rpc import (
    start_rpc_thread, stop_rpc_thread, is_rpc_alive, join_rpc_thread,
    get_party_info_string
)
from core.detection import (
    update_coordinates_if_needed,
    RESOLUTION_CHECK_INTERVAL
)

__all__ = [
    # State
    'current_active_character', 'last_active_character',
    'current_characters', 'current_activity', 'prev_non_idle_activity',
    'game_start_time', 'current_timer_type', 'ingame_pause_ocr',
    'gui_callback', 'shutdown_event', 'state_lock', 'ocr_lock',
    'update_activity', 'set_active_character', 'update_character',
    'get_current_activity', 'get_current_characters', 'get_game_start_time',
    'get_current_timer_type', 'get_last_active_character',
    'reset_game_start_time', 'write_gui_shared_data',
    'shutdown_ocr_executor',
    # OCR
    'capture_and_process_ocr', 'calculate_keyword_match_score', 'calculate_location_confidence', 'process_map_text',
    # Discord RPC
    'start_rpc_thread', 'stop_rpc_thread', 'is_rpc_alive', 'join_rpc_thread',
    'get_party_info_string',
    # Detection
    'update_coordinates_if_needed',
    'RESOLUTION_CHECK_INTERVAL',
]
