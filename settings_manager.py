import json
import os
from constants import (
    SETTINGS_FILE,
    DEFAULT_DNS_SERVERS,
    DEFAULT_BYPASS_DOMAINS,
    DEFAULT_BYPASS_IPS,
)

DEFAULT_SETTINGS = {
    "sub_link": "",
    "servers": {},
    "appearance_mode": "System",
    "color_theme": "green",
    "dns_servers": DEFAULT_DNS_SERVERS,
    "bypass_domains": DEFAULT_BYPASS_DOMAINS,
    "bypass_ips": DEFAULT_BYPASS_IPS,
    "connection_mode": "Rule-Based",
}


def save_settings(settings_to_save):
    """Saves settings to the settings file."""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings_to_save, f, indent=2)
    except Exception as e:
        print(f"Error saving settings: {e}")


def load_settings():
    """Loads settings from the settings file."""
    settings = DEFAULT_SETTINGS.copy()  # Start with a copy of default settings
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                loaded_settings = json.load(f)
                settings.update(loaded_settings)  # Merge loaded settings with defaults
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading settings: {e}")
    return settings
