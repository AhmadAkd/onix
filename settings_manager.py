import json
import os
from constants import (
    APP_VERSION,
    SETTINGS_FILE,
    DEFAULT_DNS_SERVERS,
    DEFAULT_BYPASS_DOMAINS,
    DEFAULT_BYPASS_IPS,
    DEFAULT_LOG_LEVEL,
    LogLevel,
)

DEFAULT_SETTINGS = {
    "app_version": APP_VERSION,
    "subscriptions": [],
    "servers": {},
    "appearance_mode": "System",
    "theme_color": "blue",
    "dns_servers": DEFAULT_DNS_SERVERS,
    "bypass_domains": DEFAULT_BYPASS_DOMAINS,
    "bypass_ips": DEFAULT_BYPASS_IPS,
    "connection_mode": "Rule-Based",
    "custom_routing_rules": [],
    "outbound_chains": [],  # Added for outbound chaining
    "tls_fragment_enabled": False,
    "tls_fragment_size": "10-100",
    "tls_fragment_sleep": "10-100",
    "window_geometry": None,  # To store window position and size
    "window_maximized": False,  # To store if the window was maximized
    "log_level": DEFAULT_LOG_LEVEL,
    "mux_padding": False,
    # Security settings
    "enable_ipv6": True,
    "allow_insecure": False,
    "cert_verification": True,
    "custom_ca_cert": "",
    "cipher_suites": "",
    "security_level": "High",
    "connection_timeout": 30,
    "retry_attempts": 3,
    "keep_alive": True,
    # Performance settings
    "connection_pool_size": 10,
    "thread_pool_size": 5,
    "buffer_size": 8192,
    "bandwidth_limit_enabled": False,
    "upload_speed_limit": 0,
    "download_speed_limit": 0,
    "connection_multiplexing": True,
    "compression_enabled": False,
    "tcp_fast_open": False,
    "congestion_control": "Cubic",
    "enable_statistics": True,
    "statistics_interval": 5,
    # Advanced features
    "auto_failover_enabled": False,
    # Privacy settings
    "disable_telemetry": True,
    "disable_crash_reports": True,
    "disable_usage_stats": True,
    "disable_detailed_logging": False,
    "clear_logs_on_exit": False,
    "disable_connection_logging": False,
    "disable_dns_logging": True,
    "disable_traffic_stats": False,
    "disable_ip_logging": True,
    "disable_auto_updates": False,
    "disable_core_auto_updates": False,
    "disable_sub_auto_updates": False,
}


def save_settings(settings_to_save, log_callback=None):
    """Saves settings to the settings file."""
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings_to_save, f, indent=2)
    except Exception as e:
        if log_callback:
            log_callback(f"Error saving settings: {e}", LogLevel.ERROR)


def load_settings(log_callback=None):
    """Loads settings from the settings file and handles migration from old format."""
    settings = DEFAULT_SETTINGS.copy()  # Start with a copy of default settings
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                loaded_settings = json.load(f)

                # Merge loaded settings into defaults to ensure all keys exist
                settings.update(loaded_settings)

                # --- Migration Logic ---
                if (
                    "sub_link" in loaded_settings
                    and "subscriptions" not in loaded_settings
                ):
                    sub_link = loaded_settings.get("sub_link")
                    if sub_link:
                        loaded_settings["subscriptions"] = [
                            {"name": "Default", "url": sub_link, "enabled": True}
                        ]
                    del loaded_settings["sub_link"]

                # You can add more complex migration logic based on version here
                # if version.parse(settings_version) < version.parse("1.1.0"):
                #     # Do something for versions older than 1.1.0
                #     pass

    except (IOError, json.JSONDecodeError) as e:
        if log_callback:
            log_callback(f"Error loading settings: {e}", LogLevel.ERROR)
    return settings


def export_settings(file_path, log_callback=None):
    """Exports current settings to a specified file."""
    try:
        settings_to_export = load_settings(log_callback)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(settings_to_export, f, indent=2)
        if log_callback:
            log_callback(
                f"Settings successfully exported to {file_path}", LogLevel.SUCCESS
            )
        return True
    except Exception as e:
        if log_callback:
            log_callback(f"Error exporting settings: {e}", LogLevel.ERROR)
        return False


def import_settings(file_path, log_callback=None):
    """Imports settings from a specified file and saves them."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            imported_settings = json.load(f)

        # Basic validation: check if it's a dictionary and contains 'servers' key
        if (
            not isinstance(imported_settings, dict)
            or "servers" not in imported_settings
        ):
            if log_callback:
                log_callback(
                    "Error: Invalid settings file format. Missing 'servers' key or not a dictionary.",
                    LogLevel.ERROR,
                )
            return False

        save_settings(imported_settings, log_callback)
        if log_callback:
            log_callback(
                f"Settings successfully imported from {file_path}", LogLevel.SUCCESS
            )
        return True
    except FileNotFoundError:
        if log_callback:
            log_callback(f"Error: File not found at {file_path}", LogLevel.ERROR)
        return False
    except json.JSONDecodeError:
        if log_callback:
            log_callback(f"Error: Invalid JSON format in {file_path}", LogLevel.ERROR)
        return False
    except Exception as e:
        if log_callback:
            log_callback(f"Error importing settings: {e}", LogLevel.ERROR)
        return False
