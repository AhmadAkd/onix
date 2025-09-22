import json
import os
from constants import SETTINGS_FILE

def save_settings(settings_to_save):
    """Saves settings to the settings file."""
    try:
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(settings_to_save, f, indent=2)
    except Exception as e:
        print(f"Error saving settings: {e}")

def load_settings():
    """Loads settings from the settings file."""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error loading settings: {e}")
    return {}
