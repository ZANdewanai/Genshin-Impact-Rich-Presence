"""
Utility functions and constants for the overlay system.
"""
from dataclasses import dataclass
from typing import Dict, Tuple, List, Optional, Any, Union
import re

# Constants for window styles (Windows API)
WINDOW_STYLES = {
    'GWL_EXSTYLE': -20,
    'WS_EX_LAYERED': 0x00080000,
    'WS_EX_TRANSPARENT': 0x00000020,
    'WS_EX_TOOLWINDOW': 0x00000080,
    'WS_EX_NOACTIVATE': 0x08000000,
}

# Default configuration values
DEFAULT_OPACITY = 0.8
DEFAULT_BORDER_WIDTH = 2
DEFAULT_BORDER_COLOR = 'yellow'
DEFAULT_TEXT_COLOR = '#00FFFF'  # Light cyan
DEFAULT_UPDATE_INTERVAL_MS = 250
DEFAULT_ERROR_RETRY_DELAY_MS = 2000

# Valid color names for quick lookup
VALID_COLORS = {
    'white', 'black', 'red', 'green', 'blue', 'cyan', 'yellow', 'magenta',
    'gray', 'grey', 'lightgray', 'lightgrey', 'darkgray', 'darkgrey',
    'orange', 'pink', 'purple', 'brown', 'violet', 'indigo'
}

# Pre-compiled regex patterns for color validation
HEX_COLOR_PATTERN = re.compile(r'^#(?:[0-9a-fA-F]{3}){1,2}$')
RGB_COLOR_PATTERN = re.compile(r'^rgb\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*\)$')

@dataclass
class OverlayConfig:
    """Configuration settings for the overlay."""
    enabled: bool = False
    debug_mode: bool = False
    opacity: float = DEFAULT_OPACITY
    border_color: str = DEFAULT_BORDER_COLOR
    text_color: str = DEFAULT_TEXT_COLOR
    background_color: str = 'black'  # Default background color for the overlay
    border_width: int = DEFAULT_BORDER_WIDTH
    update_interval_ms: int = DEFAULT_UPDATE_INTERVAL_MS
    error_retry_delay_ms: int = DEFAULT_ERROR_RETRY_DELAY_MS

class ColorValidationError(ValueError):
    """Raised when color validation fails."""
    pass

def validate_color(color: str, default: str = DEFAULT_BORDER_COLOR) -> str:
    """
    Validate and normalize a color string.
    
    Args:
        color: The color string to validate
        default: Default color to return if validation fails
        
    Returns:
        Normalized color string in lowercase for named colors, or the validated color string
        
    Raises:
        ColorValidationError: If the color format is invalid
    """
    if not color or not isinstance(color, str) or not color.strip():
        return default
        
    color = color.strip()
    
    # Check for named colors (case-insensitive)
    if color.lower() in VALID_COLORS:
        return color.lower()
        
    # Check for hex color
    if HEX_COLOR_PATTERN.match(color):
        return color.lower()
        
    # Check for rgb() format
    if RGB_COLOR_PATTERN.match(color):
        return color  # Keep original case for rgb() format
        
    return default

def load_config_from_module(config_module: Any) -> OverlayConfig:
    """
    Load overlay configuration from a module.
    
    Args:
        config_module: The module containing configuration values
        
    Returns:
        OverlayConfig: The loaded configuration
    """
    config = OverlayConfig()
    
    try:
        config.enabled = getattr(config_module, 'ENABLE_OCR_OVERLAY', False)
        config.debug_mode = getattr(config_module, 'DEBUG_MODE', False)
        
        # Load opacity with validation
        try:
            opacity = getattr(config_module, 'OVERLAY_OPACITY', DEFAULT_OPACITY)
            config.opacity = max(0.1, min(1.0, float(opacity)))
        except (ValueError, TypeError):
            pass
            
        # Load colors with validation
        config.border_color = validate_color(
            getattr(config_module, 'OVERLAY_BORDER_COLOR', DEFAULT_BORDER_COLOR),
            DEFAULT_BORDER_COLOR
        )
        config.text_color = validate_color(
            getattr(config_module, 'OVERLAY_TEXT_COLOR', DEFAULT_TEXT_COLOR),
            DEFAULT_TEXT_COLOR
        )
        
        # Load border width with validation
        try:
            border_width = getattr(config_module, 'OVERLAY_BORDER_WIDTH', DEFAULT_BORDER_WIDTH)
            config.border_width = max(1, min(10, int(border_width)))
        except (ValueError, TypeError):
            pass
            
    except Exception as e:
        if config.debug_mode:
            import traceback
            print(f"[ERROR] Error loading overlay config: {e}")
            traceback.print_exc()
    
    return config
