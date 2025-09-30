"""
Plugin System for Onix
Provides extensibility through third-party plugins and add-ons
"""

import os
import sys
import importlib
import inspect
import threading
import time
from typing import Dict, Any, List, Optional, Callable, Type
from dataclasses import dataclass
from constants import LogLevel


@dataclass
class PluginInfo:
    """Plugin information structure."""

    name: str
    version: str
    description: str
    author: str
    category: str
    dependencies: List[str]
    api_version: str
    enabled: bool = False
    path: str = ""


@dataclass
class PluginEvent:
    """Plugin event structure."""

    event_type: str
    data: Dict[str, Any]
    timestamp: float
    source: str


class PluginInterface:
    """Base interface for all plugins."""

    def __init__(self):
        self.plugin_info: Optional[PluginInfo] = None
        self.is_enabled = False
        self.event_handlers: Dict[str, List[Callable]] = {}

    def initialize(self, app_context: Dict[str, Any]) -> bool:
        """Initialize the plugin with app context."""
        raise NotImplementedError

    def cleanup(self) -> None:
        """Clean up plugin resources."""
        raise NotImplementedError

    def on_enable(self) -> None:
        """Called when plugin is enabled."""
        pass

    def on_disable(self) -> None:
        """Called when plugin is disabled."""
        pass

    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """Register an event handler."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    def emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Emit an event to the plugin system."""
        pass  # Will be implemented by PluginManager


class PluginManager:
    """Manages plugins and their lifecycle."""

    def __init__(self, log_callback: Optional[Callable[[str, LogLevel], None]] = None):
        self.log = log_callback or (lambda msg, level: print(f"[{level}] {msg}"))
        self.plugins: Dict[str, PluginInterface] = {}
        self.plugin_info: Dict[str, PluginInfo] = {}
        self.event_handlers: Dict[str, List[Callable]] = {}
        self.plugin_directories: List[str] = []
        self.app_context: Dict[str, Any] = {}
        self._plugin_lock = threading.Lock()
        self._event_queue = []
        self._event_thread = None
        self._stop_events = threading.Event()

    def add_plugin_directory(self, directory: str) -> None:
        """Add a directory to search for plugins."""
        if os.path.exists(directory) and directory not in self.plugin_directories:
            self.plugin_directories.append(directory)
            self.log(f"Added plugin directory: {directory}", LogLevel.INFO)

    def set_app_context(self, context: Dict[str, Any]) -> None:
        """Set application context for plugins."""
        self.app_context = context

    def discover_plugins(self) -> List[PluginInfo]:
        """Discover all available plugins."""
        discovered_plugins = []

        for plugin_dir in self.plugin_directories:
            try:
                for root, dirs, files in os.walk(plugin_dir):
                    for file in files:
                        if file.endswith(".py") and file != "__init__.py":
                            plugin_path = os.path.join(root, file)
                            plugin_info = self._load_plugin_info(plugin_path)
                            if plugin_info:
                                discovered_plugins.append(plugin_info)
            except Exception as e:
                self.log(
                    f"Error discovering plugins in {plugin_dir}: {e}", LogLevel.ERROR
                )

        return discovered_plugins

    def _load_plugin_info(self, plugin_path: str) -> Optional[PluginInfo]:
        """Load plugin information from a file."""
        try:
            # Read the file to extract plugin metadata
            with open(plugin_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Look for plugin metadata in comments
            lines = content.split("\n")
            metadata = {}

            for line in lines:
                if line.strip().startswith("# PLUGIN_"):
                    key_value = line.strip()[2:].split(":", 1)
                    if len(key_value) == 2:
                        key = key_value[0].strip().lower()
                        value = key_value[1].strip()
                        metadata[key] = value

            if "name" not in metadata:
                return None

            plugin_info = PluginInfo(
                name=metadata.get("name", "Unknown"),
                version=metadata.get("version", "1.0.0"),
                description=metadata.get("description", "No description"),
                author=metadata.get("author", "Unknown"),
                category=metadata.get("category", "General"),
                dependencies=(
                    metadata.get("dependencies", "").split(",")
                    if metadata.get("dependencies")
                    else []
                ),
                api_version=metadata.get("api_version", "1.0"),
                path=plugin_path,
            )

            return plugin_info

        except Exception as e:
            self.log(
                f"Error loading plugin info from {plugin_path}: {e}", LogLevel.WARNING
            )
            return None

    def load_plugin(self, plugin_path: str) -> bool:
        """Load a plugin from file."""
        try:
            with self._plugin_lock:
                # Get plugin info
                plugin_info = self._load_plugin_info(plugin_path)
                if not plugin_info:
                    return False

                # Check if already loaded
                if plugin_info.name in self.plugins:
                    self.log(
                        f"Plugin {plugin_info.name} already loaded", LogLevel.WARNING
                    )
                    return False

                # Import the plugin module
                module_name = f"plugin_{plugin_info.name.lower().replace(' ', '_')}"
                spec = importlib.util.spec_from_file_location(module_name, plugin_path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)

                # Find the plugin class
                plugin_class = None
                for name, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, PluginInterface)
                        and obj != PluginInterface
                    ):
                        plugin_class = obj
                        break

                if not plugin_class:
                    self.log(
                        f"No valid plugin class found in {plugin_path}", LogLevel.ERROR
                    )
                    return False

                # Create plugin instance
                plugin_instance = plugin_class()
                plugin_instance.plugin_info = plugin_info

                # Initialize plugin
                if plugin_instance.initialize(self.app_context):
                    self.plugins[plugin_info.name] = plugin_instance
                    self.plugin_info[plugin_info.name] = plugin_info
                    plugin_instance.is_enabled = True
                    plugin_instance.on_enable()

                    self.log(
                        f"Loaded plugin: {plugin_info.name} v{plugin_info.version}",
                        LogLevel.INFO,
                    )
                    return True
                else:
                    self.log(
                        f"Failed to initialize plugin: {plugin_info.name}",
                        LogLevel.ERROR,
                    )
                    return False

        except Exception as e:
            self.log(f"Error loading plugin {plugin_path}: {e}", LogLevel.ERROR)
            return False

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin."""
        try:
            with self._plugin_lock:
                if plugin_name not in self.plugins:
                    self.log(f"Plugin {plugin_name} not loaded", LogLevel.WARNING)
                    return False

                plugin = self.plugins[plugin_name]
                plugin.on_disable()
                plugin.cleanup()
                plugin.is_enabled = False

                del self.plugins[plugin_name]
                del self.plugin_info[plugin_name]

                self.log(f"Unloaded plugin: {plugin_name}", LogLevel.INFO)
                return True

        except Exception as e:
            self.log(f"Error unloading plugin {plugin_name}: {e}", LogLevel.ERROR)
            return False

    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin."""
        try:
            with self._plugin_lock:
                if plugin_name not in self.plugins:
                    self.log(f"Plugin {plugin_name} not loaded", LogLevel.WARNING)
                    return False

                plugin = self.plugins[plugin_name]
                if plugin.is_enabled:
                    return True

                plugin.on_enable()
                plugin.is_enabled = True
                self.plugin_info[plugin_name].enabled = True

                self.log(f"Enabled plugin: {plugin_name}", LogLevel.INFO)
                return True

        except Exception as e:
            self.log(f"Error enabling plugin {plugin_name}: {e}", LogLevel.ERROR)
            return False

    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin."""
        try:
            with self._plugin_lock:
                if plugin_name not in self.plugins:
                    self.log(f"Plugin {plugin_name} not loaded", LogLevel.WARNING)
                    return False

                plugin = self.plugins[plugin_name]
                if not plugin.is_enabled:
                    return True

                plugin.on_disable()
                plugin.is_enabled = False
                self.plugin_info[plugin_name].enabled = False

                self.log(f"Disabled plugin: {plugin_name}", LogLevel.INFO)
                return True

        except Exception as e:
            self.log(f"Error disabling plugin {plugin_name}: {e}", LogLevel.ERROR)
            return False

    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """Register a global event handler."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    def emit_event(
        self, event_type: str, data: Dict[str, Any], source: str = "system"
    ) -> None:
        """Emit an event to all registered handlers."""
        try:
            event = PluginEvent(
                event_type=event_type, data=data, timestamp=time.time(), source=source
            )

            # Add to event queue for processing
            self._event_queue.append(event)

        except Exception as e:
            self.log(f"Error emitting event {event_type}: {e}", LogLevel.ERROR)

    def start_event_processing(self) -> None:
        """Start the event processing thread."""
        if self._event_thread and self._event_thread.is_alive():
            return

        self._stop_events.clear()
        self._event_thread = threading.Thread(
            target=self._event_processing_loop, daemon=True
        )
        self._event_thread.start()

        self.log("Started plugin event processing", LogLevel.INFO)

    def stop_event_processing(self) -> None:
        """Stop the event processing thread."""
        self._stop_events.set()
        if self._event_thread and self._event_thread.is_alive():
            self._event_thread.join(timeout=2)

        self.log("Stopped plugin event processing", LogLevel.INFO)

    def _event_processing_loop(self) -> None:
        """Main event processing loop."""
        while not self._stop_events.is_set():
            try:
                if self._event_queue:
                    event = self._event_queue.pop(0)
                    self._process_event(event)
                else:
                    time.sleep(0.1)  # Small delay when no events

            except Exception as e:
                self.log(f"Error in event processing loop: {e}", LogLevel.ERROR)
                time.sleep(1)

    def _process_event(self, event: PluginEvent) -> None:
        """Process a single event."""
        try:
            # Process global event handlers
            if event.event_type in self.event_handlers:
                for handler in self.event_handlers[event.event_type]:
                    try:
                        handler(event)
                    except Exception as e:
                        self.log(f"Error in global event handler: {e}", LogLevel.ERROR)

            # Process plugin event handlers
            for plugin_name, plugin in self.plugins.items():
                if plugin.is_enabled and event.event_type in plugin.event_handlers:
                    for handler in plugin.event_handlers[event.event_type]:
                        try:
                            handler(event)
                        except Exception as e:
                            self.log(
                                f"Error in plugin {plugin_name} event handler: {e}",
                                LogLevel.ERROR,
                            )

        except Exception as e:
            self.log(f"Error processing event {event.event_type}: {e}", LogLevel.ERROR)

    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """Get information about a plugin."""
        return self.plugin_info.get(plugin_name)

    def list_plugins(self) -> List[PluginInfo]:
        """List all loaded plugins."""
        return list(self.plugin_info.values())

    def get_plugin(self, plugin_name: str) -> Optional[PluginInterface]:
        """Get a plugin instance."""
        return self.plugins.get(plugin_name)

    def cleanup_all(self) -> None:
        """Clean up all plugins and resources."""
        try:
            # Stop event processing
            self.stop_event_processing()

            # Disable and unload all plugins
            with self._plugin_lock:
                for plugin_name in list(self.plugins.keys()):
                    try:
                        self.unload_plugin(plugin_name)
                    except Exception as e:
                        self.log(
                            f"Error unloading plugin {plugin_name}: {e}",
                            LogLevel.WARNING,
                        )

            # Clear all data structures
            self.plugins.clear()
            self.plugin_info.clear()
            self.event_handlers.clear()
            self._event_queue.clear()

            self.log("Cleaned up all plugins", LogLevel.INFO)

        except Exception as e:
            self.log(f"Error during plugin cleanup: {e}", LogLevel.ERROR)


# Example plugin implementations
class ExamplePlugin(PluginInterface):
    """Example plugin for demonstration."""

    def initialize(self, app_context: Dict[str, Any]) -> bool:
        """Initialize the example plugin."""
        try:
            self.log = app_context.get(
                "log_callback", lambda msg, level: print(f"[{level}] {msg}")
            )
            self.log("Example plugin initialized", LogLevel.INFO)
            return True
        except Exception as e:
            self.log(f"Error initializing example plugin: {e}", LogLevel.ERROR)
            return False

    def cleanup(self) -> None:
        """Clean up example plugin."""
        self.log("Example plugin cleaned up", LogLevel.INFO)

    def on_enable(self) -> None:
        """Called when plugin is enabled."""
        self.log("Example plugin enabled", LogLevel.INFO)

    def on_disable(self) -> None:
        """Called when plugin is disabled."""
        self.log("Example plugin disabled", LogLevel.INFO)


# Plugin API utilities
class PluginAPI:
    """API utilities for plugins."""

    @staticmethod
    def create_plugin_info(
        name: str,
        version: str,
        description: str,
        author: str,
        category: str = "General",
        dependencies: List[str] = None,
        api_version: str = "1.0",
    ) -> PluginInfo:
        """Create a plugin info object."""
        return PluginInfo(
            name=name,
            version=version,
            description=description,
            author=author,
            category=category,
            dependencies=dependencies or [],
            api_version=api_version,
        )

    @staticmethod
    def validate_plugin(plugin_class: Type[PluginInterface]) -> bool:
        """Validate a plugin class."""
        try:
            # Check if it's a subclass of PluginInterface
            if not issubclass(plugin_class, PluginInterface):
                return False

            # Check required methods
            required_methods = ["initialize", "cleanup"]
            for method in required_methods:
                if not hasattr(plugin_class, method):
                    return False
                if not callable(getattr(plugin_class, method)):
                    return False

            return True

        except Exception:
            return False
