"""Sensor workers package (split from core/sensors.py)."""
from .base import BaseSensor, _looks_same
from .char_sensor import CharSensor
from .location_sensor import LocationSensor
from .menu_sensor import MenuSensor
__all__ = [
    "BaseSensor", "_looks_same",
    "CharSensor", "LocationSensor", "MenuSensor",
]
