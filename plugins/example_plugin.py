# PLUGIN_NAME: Example Plugin
# PLUGIN_VERSION: 1.0.0
# PLUGIN_DESCRIPTION: A simple example plugin for Onix
# PLUGIN_AUTHOR: Onix Team
# PLUGIN_CATEGORY: Examples
# PLUGIN_DEPENDENCIES:
# PLUGIN_API_VERSION: 1.0

"""
Example Plugin for Onix
Demonstrates basic plugin functionality
"""

import sys
import os
from typing import Dict, Any

# Add the parent directory to the path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.plugin_system import PluginInterface
from constants import LogLevel


class ExamplePlugin(PluginInterface):
    """Example plugin implementation."""

    def __init__(self):
        super().__init__()
        self.log = None
        self.server_manager = None
        self.singbox_manager = None
        self.main_window = None

    def initialize(self, app_context: Dict[str, Any]) -> bool:
        """Initialize the plugin with app context."""
        try:
            self.log = app_context.get("log_callback")
            self.server_manager = app_context.get("server_manager")
            self.singbox_manager = app_context.get("singbox_manager")
            self.main_window = app_context.get("main_window")

            if self.log:
                self.log("Example plugin initialized successfully", LogLevel.INFO)

            # Register event handlers
            self.register_event_handler("server_connected", self.on_server_connected)
            self.register_event_handler(
                "server_disconnected", self.on_server_disconnected
            )

            return True

        except Exception as e:
            if self.log:
                self.log(f"Error initializing example plugin: {e}", LogLevel.ERROR)
            return False

    def cleanup(self) -> None:
        """Clean up plugin resources."""
        try:
            if self.log:
                self.log("Example plugin cleaned up", LogLevel.INFO)
        except Exception as e:
            if self.log:
                self.log(f"Error cleaning up example plugin: {e}", LogLevel.ERROR)

    def on_enable(self) -> None:
        """Called when plugin is enabled."""
        if self.log:
            self.log("Example plugin enabled", LogLevel.INFO)

    def on_disable(self) -> None:
        """Called when plugin is disabled."""
        if self.log:
            self.log("Example plugin disabled", LogLevel.INFO)

    def on_server_connected(self, event):
        """Handle server connected event."""
        if self.log:
            self.log(
                f"Example plugin: Server connected - {event.data.get('server_name', 'Unknown')}",
                LogLevel.INFO,
            )

    def on_server_disconnected(self, event):
        """Handle server disconnected event."""
        if self.log:
            self.log(
                f"Example plugin: Server disconnected - {event.data.get('server_name', 'Unknown')}",
                LogLevel.INFO,
            )
