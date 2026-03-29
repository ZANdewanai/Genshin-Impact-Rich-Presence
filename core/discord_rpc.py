"""Discord Rich Presence integration."""
import threading
import time
from asyncio import new_event_loop, set_event_loop

import pypresence as discord

from core.datatypes import Activity, ActivityType, DEBUG_MODE
from CONFIG import DISC_APP_ID, USE_URL_ASSETS, ASSET_BASE_URL


# Event for clean shutdown
_shutdown_event = threading.Event()
_rpc_thread: threading.Thread = None


def get_asset_url(image_key: str) -> str:
    """
    Convert an image key to a URL if URL assets are enabled.
    
    When USE_URL_ASSETS is True, converts image keys like 'char_aether' or 
    'boss_anemo_hypostasis' to full URLs by prepending ASSET_BASE_URL.
    Automatically adds subfolder based on image key prefix (char_ → characters/, boss_ → bosses/, etc.)
    
    Args:
        image_key: The image key from CSV files (e.g., 'char_aether', 'icon_paimon')
        
    Returns:
        Full URL if USE_URL_ASSETS is enabled and base URL is set, 
        otherwise returns the original image_key for Discord asset lookup.
    """
    if not USE_URL_ASSETS or not ASSET_BASE_URL:
        return image_key
    
    # Don't convert special Discord-native assets or empty values
    if not image_key or image_key.startswith('http'):
        return image_key
    
    # Map image key prefixes to subfolders (only if key doesn't already contain a path)
    subfolder = ""
    filename = image_key
    if '/' not in image_key:
        if image_key.startswith('char_'):
            subfolder = "characters/"
        elif image_key.startswith('boss_'):
            subfolder = "bosses/"
        elif image_key.startswith('domain_'):
            # Domains have subfolders by type (forgery, blessing, mastery, trounce)
            if '_forgery_' in image_key or image_key.endswith('_forgery'):
                subfolder = "domains/forgery/"
            elif '_blessing_' in image_key or image_key.endswith('_blessing'):
                subfolder = "domains/blessing/"
            elif '_mastery_' in image_key or image_key.endswith('_mastery'):
                subfolder = "domains/mastery/"
            elif '_trounce_' in image_key or image_key.endswith('_trounce'):
                subfolder = "domains/trounce/"
            else:
                subfolder = "domains/"
        elif image_key.startswith('emblem_'):
            subfolder = "locations/"
        elif image_key.startswith('area_'):
            subfolder = "areas/"
        elif image_key.startswith('loc_'):
            subfolder = "locations/"
        elif image_key.startswith('menu_'):
            subfolder = "ui/menus/"
        elif image_key.startswith('ui_'):
            subfolder = "ui/ui/"
        elif image_key.startswith('tree_'):
            subfolder = "content/tree/"
        elif image_key.startswith('fountain_'):
            subfolder = "content/fountain/"
        elif image_key.startswith('spiral_abyss'):
            subfolder = "content/abyss/"
        elif image_key.startswith('tablet_'):
            subfolder = "content/"
        elif image_key.startswith('icon_'):
            subfolder = "ui/ui/"
        elif image_key.startswith('archive_'):
            subfolder = "ui/archive/"
    
    # Ensure base URL ends with / for proper concatenation
    base_url = ASSET_BASE_URL if ASSET_BASE_URL.endswith('/') else ASSET_BASE_URL + '/'
    
    # Construct full URL - add .png extension if no extension present
    if '.' not in filename:
        return f"{base_url}{subfolder}{filename}.png"
    else:
        return f"{base_url}{subfolder}{filename}"


def get_party_info_string(current_characters):
    """Generate party info string for Discord RPC."""
    party_members = []
    for i, char in enumerate(current_characters[:4], 1):  # Show first 4 characters
        if char is not None:
            party_members.append(char.character_display_name)
        else:
            party_members.append(f"Slot {i}")

    return " | ".join(party_members) if party_members else "No party detected"


def discord_rpc_loop(current_activity_ref, current_characters_ref, game_start_time_ref,
                     current_timer_type_ref, last_active_character_ref):
    """
    Main Discord RPC loop - runs in separate thread.
    
    :param current_activity_ref: Callable that returns current Activity
    :param current_characters_ref: Callable that returns list of Characters
    :param game_start_time_ref: Callable that returns game start time
    :param current_timer_type_ref: Callable that returns timer type string
    :param last_active_character_ref: Callable that returns last active character index
    """
    set_event_loop(new_event_loop())
    rpc: discord.Presence = None

    def init_discord_rpc():
        nonlocal rpc

        printed_wait = False
        while not _shutdown_event.is_set():
            try:
                rpc = discord.Presence(DISC_APP_ID)
                rpc.connect()
                print("Connected to Discord Client!")
                if USE_URL_ASSETS and ASSET_BASE_URL:
                    print(f"URL Asset Mode enabled - images will be loaded from: {ASSET_BASE_URL}")
                break
            except discord.exceptions.DiscordNotFound:
                if not printed_wait:
                    printed_wait = True
                    print("Waiting for discord to start...")
                _shutdown_event.wait(2.5)
            except Exception as e:
                print("Unknown error while attempting to initialize discord RPC:")
                print(e)
                _shutdown_event.wait(2.5)

    while not _shutdown_event.is_set():
        if _shutdown_event.is_set():
            break
        if rpc is None:
            init_discord_rpc()  # Waits for discord to open (Blocking)
            if _shutdown_event.is_set():
                break

        try:
            current_activity = current_activity_ref()
            current_characters = current_characters_ref()
            game_start_time = game_start_time_ref()
            current_timer_type = current_timer_type_ref()
            last_active_character = last_active_character_ref()

            params = current_activity.to_update_params_dict()

            # Handle special markers for dynamic content
            if params.get("state") == "LOCATION_PARTY_INFO":
                # Replace with current party information
                params["state"] = f"Party: {get_party_info_string(current_characters)}"
            elif params.get("state") == "MAP_PARTY_INFO":
                # Handle map location party info
                params["state"] = f"Party: {get_party_info_string(current_characters)}"
            elif "PARTY_INFO_MARKER" in params.get("state", ""):
                # Handle party info marker in other activity types
                if params.get("state") == "PARTY_INFO_MARKER":
                    params["state"] = f"Party: {get_party_info_string(current_characters)}"
                else:
                    params["state"] = params["state"].replace(" | PARTY_INFO_MARKER", f" | Party: {get_party_info_string(current_characters)}")

            # Special handling for LOADING state with character data
            # Swap images: large = character, small = paimon, and show "Playing as [character]"
            if params.get("state") == "Loading" and last_active_character != 0:
                c = current_characters[last_active_character - 1]
                if c is not None:
                    params["large_image"] = c.image_key
                    params["large_text"] = f"Playing as {c.character_display_name}"
                    params["small_image"] = "icon_paimon"
                    params["small_text"] = "Loading..."
                    # Show "Playing as [character]" until we get location/boss/domain data
                    params["state"] = f"Playing as {c.character_display_name}"

            if DEBUG_MODE:
                print(f"DEBUG Discord RPC: params={params}")
                print(f"DEBUG Discord RPC: current_activity={current_activity}")
                print(f"DEBUG Discord RPC: current_characters={current_characters}")

            # Smart timer selection based on activity type
            if current_timer_type == "global" and game_start_time is not None:
                params["start"] = game_start_time
            elif current_timer_type == "activity":
                params["start"] = current_activity.start_time
            elif current_timer_type == "menu":
                # Menu timer is handled separately via menu_start_time
                pass
            elif game_start_time is not None:
                params["start"] = game_start_time  # fallback to global

            if last_active_character != 0:
                c = current_characters[last_active_character - 1]
                if c is not None:
                    params["small_image"] = c.image_key
                    params["small_text"] = f"playing {c.character_display_name}"

            # Convert image keys to URLs if URL assets are enabled
            if USE_URL_ASSETS and ASSET_BASE_URL:
                if "large_image" in params and params["large_image"]:
                    params["large_image"] = get_asset_url(params["large_image"])
                if "small_image" in params and params["small_image"]:
                    params["small_image"] = get_asset_url(params["small_image"])
                
                if DEBUG_MODE:
                    print(f"DEBUG Discord RPC (URL mode): large_image={params.get('large_image')}, small_image={params.get('small_image')}")

            # Always update Discord - remove caching to prevent stale data
            try:
                rpc.update(**params)
            except discord.exceptions.InvalidID:
                # Discord closed mid game. Need to create a new Presence client connection instance.
                rpc.close()
                rpc = None
                continue
            except Exception as e:
                print("Error updating Discord RPC:")
                print(e)

        except Exception as e:
            print(f"ERROR in Discord RPC loop: {e}")
            import traceback
            traceback.print_exc()

        # Rate limit for UpdateActivity RPC is 5 updates / 20 seconds.
        _shutdown_event.wait(5)

    # Cleanup on shutdown
    if rpc:
        try:
            rpc.clear()  # Explicitly clear Discord presence
            rpc.close()
        except Exception:
            pass


def start_rpc_thread(current_activity_ref, current_characters_ref, game_start_time_ref,
                     current_timer_type_ref, last_active_character_ref):
    """Start the Discord RPC thread."""
    global _rpc_thread
    
    # Clear shutdown event and previous_update cache for fresh start
    _shutdown_event.clear()
    discord_rpc_loop.__globals__['previous_update'] = None
    
    _rpc_thread = threading.Thread(
        daemon=True,
        target=discord_rpc_loop,
        args=(current_activity_ref, current_characters_ref, game_start_time_ref,
              current_timer_type_ref, last_active_character_ref)
    )
    _rpc_thread.start()
    return _rpc_thread


def stop_rpc_thread():
    """Signal the RPC thread to stop."""
    _shutdown_event.set()


def is_rpc_alive():
    """Check if RPC thread is still running."""
    return _rpc_thread is not None and _rpc_thread.is_alive()


def join_rpc_thread(timeout=2.0):
    """Wait for RPC thread to finish."""
    if _rpc_thread and _rpc_thread.is_alive():
        _rpc_thread.join(timeout=timeout)
