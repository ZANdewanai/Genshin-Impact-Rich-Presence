"""
Activity renderer for Discord Rich Presence updates.
Converts Activity objects to Discord Presence update parameter dictionaries.
"""
from __future__ import annotations
from .models import Activity, ActivityType


def render_activity(activity: Activity) -> dict:
    """
    Creates a dictionary with parameters for `Presence.update`.

    Small image and timestamp not included and should be added later.
    """
    match activity.activity_type:
        case ActivityType.LOADING:
            if not activity.activity_data:
                return {
                    "state": "Loading",
                    "large_image": "menu_paimon",
                }
            else:
                return {
                    "details": "Somewhere in Teyvat",
                    "state": "PARTY_INFO_MARKER",
                    "large_image": "menu_paimon",
                }
        case ActivityType.PAUSED:
            return {
                "state": "Game paused",
                "large_image": "menu_paimon",
            }
        case ActivityType.PARTY_SETUP:
            return {
                "state": "Party Setup | PARTY_INFO_MARKER",
                "large_image": "menu_party_setup",
            }
        case ActivityType.DOMAIN:
            if activity.activity_data is None:
                return {
                    "state": "Clearing a domain",
                    "large_image": "menu_paimon",
                }
            return {
                "details": activity.activity_data.domain_name,
                "state": f"Clearing a {activity.activity_data.domain_type} | PARTY_INFO_MARKER",
                "large_image": activity.activity_data.image_key,
                "large_text": str(activity.activity_data.domain_type),
            }
        case ActivityType.GAMEMENU:
            if activity.activity_data is None:
                return {
                    "state": "In Menus",
                    "large_image": "menu_paimon",
                }
            return {
                "details": activity.activity_data.gamemenu_name,
                "state": f"{activity.activity_data.gamemenu_type}",
                "large_image": activity.activity_data.image_key,
                "large_text": str(activity.activity_data.gamemenu_type),
            }
        case ActivityType.LOCATION:
            if activity.activity_data is None:
                return {
                    "details": "Exploring Teyvat",
                    "state": "LOCATION_PARTY_INFO",
                    "large_image": "menu_paimon",
                }
            # Format location with subregion and region information
            location_parts = []
            if activity.activity_data.location_name:
                location_parts.append(activity.activity_data.location_name)
            if (
                hasattr(activity.activity_data, "subarea")
                and activity.activity_data.subarea
            ):
                location_parts.append(activity.activity_data.subarea)
            if (
                hasattr(activity.activity_data, "country")
                and activity.activity_data.country
            ):
                location_parts.append(activity.activity_data.country)

            full_location_name = (
                ", ".join(location_parts)
                if location_parts
                else activity.activity_data.location_name
            )

            return {
                "details": f"Exploring {full_location_name}",
                "state": "LOCATION_PARTY_INFO",  # Special marker for main loop to replace
                "large_image": activity.activity_data.image_key,
            }
        case ActivityType.MAP_LOCATION:
            if activity.activity_data is None:
                return {
                    "details": "Viewing map",
                    "state": "MAP_PARTY_INFO",
                    "large_image": "menu_paimon",
                }
            # Format location with subregion and region information
            location_parts = []
            if activity.activity_data.location_name:
                location_parts.append(activity.activity_data.location_name)
            if (
                hasattr(activity.activity_data, "subarea")
                and activity.activity_data.subarea
            ):
                location_parts.append(activity.activity_data.subarea)
            if (
                hasattr(activity.activity_data, "country")
                and activity.activity_data.country
            ):
                location_parts.append(activity.activity_data.country)

            full_location_name = (
                ", ".join(location_parts)
                if location_parts
                else activity.activity_data.location_name
            )

            return {
                "details": f"Thinking of traveling to {full_location_name}",
                "state": "MAP_PARTY_INFO",  # Special marker for main loop to replace
                "large_image": activity.activity_data.image_key,
            }
        case ActivityType.COMMISSION:
            return {
                "state": "Doing commissions",
                "details": f"In {activity.activity_data.location_name}, {activity.activity_data.country}"
                if activity.activity_data != None
                else "",
                "large_image": "menu_commissions",
            }
        case ActivityType.WORLD_BOSS:
            if activity.activity_data is None:
                return {
                    "state": "Fighting a boss | PARTY_INFO_MARKER",
                    "large_image": "menu_paimon",
                }
            return {
                "state": f"Fighting a boss | PARTY_INFO_MARKER",
                "details": activity.activity_data.boss_name,
                "large_image": activity.activity_data.image_key,
                "large_text": activity.activity_data.boss_name,
            }
        case _:
            # Fallback (should not happen)
            return {
                "state": "Unknown",
                "large_image": "menu_paimon",
            }


# Backward compatibility: add to_update_params_dict method to Activity class
# This is called by discord_rpc.py
def _to_update_params_dict(self) -> dict:
    return render_activity(self)

# Monkey-patch for backward compatibility
Activity.to_update_params_dict = _to_update_params_dict