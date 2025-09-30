"""
Plugin Management View for Onix
Provides UI for managing plugins and extensions
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QTextEdit, QGroupBox,
    QSplitter, QScrollArea, QFrame, QSizePolicy, QMessageBox,
    QProgressBar, QCheckBox, QLineEdit, QComboBox
)
from PySide6.QtCore import Qt, QTimer, Signal, QThread
from PySide6.QtGui import QFont, QIcon, QPixmap
from services.plugin_system import PluginManager, PluginInfo, PluginInterface
from constants import LogLevel
import os


class PluginDiscoveryThread(QThread):
    """Thread for discovering plugins in background."""

    plugins_discovered = Signal(list)
    discovery_finished = Signal()

    def __init__(self, plugin_manager: PluginManager):
        super().__init__()
        self.plugin_manager = plugin_manager
        self._stop_requested = False

    def run(self):
        """Discover plugins in background thread."""
        try:
            if not self._stop_requested:
                discovered_plugins = self.plugin_manager.discover_plugins()
                if not self._stop_requested:
                    self.plugins_discovered.emit(discovered_plugins)
        except Exception as e:
            print(f"Error discovering plugins: {e}")
        finally:
            if not self._stop_requested:
                self.discovery_finished.emit()

    def stop(self):
        """Stop the thread gracefully."""
        self._stop_requested = True
        self.quit()
        self.wait(3000)  # Wait up to 3 seconds


class PluginItemWidget(QFrame):
    """Custom widget for displaying plugin information."""

    plugin_toggle_requested = Signal(str, bool)  # plugin_name, enabled
    plugin_remove_requested = Signal(str)  # plugin_name

    def __init__(self, plugin_info: PluginInfo, is_loaded: bool = False, parent=None):
        super().__init__(parent)
        self.plugin_info = plugin_info
        self.is_loaded = is_loaded

        self.setup_ui()
        self.setup_style()

    def setup_ui(self):
        """Setup the plugin item UI."""
        self.setFrameStyle(QFrame.StyledPanel)
        self.setLineWidth(1)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header with name and version
        header_layout = QHBoxLayout()

        self.name_label = QLabel(self.plugin_info.name)
        self.name_label.setObjectName("pluginName")
        header_layout.addWidget(self.name_label)

        self.version_label = QLabel(f"v{self.plugin_info.version}")
        self.version_label.setObjectName("pluginVersion")
        header_layout.addWidget(self.version_label)

        header_layout.addStretch()

        # Status indicator
        self.status_label = QLabel("Loaded" if self.is_loaded else "Available")
        self.status_label.setObjectName("pluginStatus")
        header_layout.addWidget(self.status_label)

        layout.addLayout(header_layout)

        # Description
        self.desc_label = QLabel(self.plugin_info.description)
        self.desc_label.setObjectName("pluginDescription")
        self.desc_label.setWordWrap(True)
        layout.addWidget(self.desc_label)

        # Author and category
        info_layout = QHBoxLayout()

        self.author_label = QLabel(f"by {self.plugin_info.author}")
        self.author_label.setObjectName("pluginAuthor")
        info_layout.addWidget(self.author_label)

        info_layout.addStretch()

        self.category_label = QLabel(self.plugin_info.category)
        self.category_label.setObjectName("pluginCategory")
        info_layout.addWidget(self.category_label)

        layout.addLayout(info_layout)

        # Dependencies
        if self.plugin_info.dependencies:
            deps_text = f"Dependencies: {', '.join(self.plugin_info.dependencies)}"
            self.deps_label = QLabel(deps_text)
            self.deps_label.setObjectName("pluginDependencies")
            self.deps_label.setWordWrap(True)
            layout.addWidget(self.deps_label)

        # Action buttons
        button_layout = QHBoxLayout()

        if self.is_loaded:
            self.toggle_button = QPushButton(
                "Disable" if self.plugin_info.enabled else "Enable")
            self.toggle_button.clicked.connect(self.toggle_plugin)
            button_layout.addWidget(self.toggle_button)

            self.remove_button = QPushButton("Remove")
            self.remove_button.clicked.connect(self.remove_plugin)
            button_layout.addWidget(self.remove_button)
        else:
            self.load_button = QPushButton("Load")
            self.load_button.clicked.connect(self.load_plugin)
            button_layout.addWidget(self.load_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

    def setup_style(self):
        """Setup the plugin item styling."""
        self.setStyleSheet("""
            PluginItemWidget {
                background-color: rgba(255, 255, 255, 0.8);
                border: 1px solid rgba(0, 0, 0, 0.1);
                border-radius: 8px;
                margin: 4px;
            }
            QLabel#pluginName {
                font-size: 16px;
                font-weight: 600;
                color: #1a1a1a;
            }
            QLabel#pluginVersion {
                font-size: 12px;
                color: #666666;
                background-color: #f3f4f6;
                padding: 2px 6px;
                border-radius: 4px;
            }
            QLabel#pluginStatus {
                font-size: 12px;
                color: #059669;
                font-weight: 500;
            }
            QLabel#pluginDescription {
                font-size: 14px;
                color: #4b5563;
                line-height: 1.4;
            }
            QLabel#pluginAuthor {
                font-size: 12px;
                color: #6b7280;
            }
            QLabel#pluginCategory {
                font-size: 12px;
                color: #3b82f6;
                background-color: #dbeafe;
                padding: 2px 6px;
                border-radius: 4px;
            }
            QLabel#pluginDependencies {
                font-size: 12px;
                color: #f59e0b;
                background-color: #fef3c7;
                padding: 4px 8px;
                border-radius: 4px;
            }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
        """)

    def toggle_plugin(self):
        """Toggle plugin enabled state."""
        self.plugin_toggle_requested.emit(
            self.plugin_info.name, not self.plugin_info.enabled)

    def remove_plugin(self):
        """Remove plugin."""
        reply = QMessageBox.question(
            self, "Remove Plugin",
            f"Are you sure you want to remove '{self.plugin_info.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.plugin_remove_requested.emit(self.plugin_info.name)

    def load_plugin(self):
        """Load plugin."""
        self.plugin_toggle_requested.emit(self.plugin_info.name, True)


def create_plugin_view(main_window) -> QWidget:
    """Create the plugin management view."""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(20, 20, 20, 20)
    layout.setSpacing(20)

    # Header
    header_layout = QHBoxLayout()

    title_label = QLabel("Plugin Manager")
    title_label.setObjectName("viewTitle")
    header_layout.addWidget(title_label)

    header_layout.addStretch()

    # Refresh button
    refresh_button = QPushButton("Refresh")
    refresh_button.clicked.connect(lambda: refresh_plugins(
        main_window, plugin_list, available_list))
    header_layout.addWidget(refresh_button)

    layout.addLayout(header_layout)

    # Main content splitter
    splitter = QSplitter(Qt.Horizontal)
    splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    # Loaded plugins section
    loaded_group = QGroupBox("Loaded Plugins")
    loaded_layout = QVBoxLayout(loaded_group)

    plugin_list = QListWidget()
    plugin_list.setObjectName("pluginList")
    loaded_layout.addWidget(plugin_list)

    splitter.addWidget(loaded_group)

    # Available plugins section
    available_group = QGroupBox("Available Plugins")
    available_layout = QVBoxLayout(available_group)

    available_list = QListWidget()
    available_list.setObjectName("availableList")
    available_layout.addWidget(available_list)

    splitter.addWidget(available_group)

    # Set splitter proportions
    splitter.setSizes([400, 400])
    layout.addWidget(splitter)

    # Plugin details section
    details_group = QGroupBox("Plugin Details")
    details_layout = QVBoxLayout(details_group)

    details_text = QTextEdit()
    details_text.setObjectName("pluginDetails")
    details_text.setMaximumHeight(150)
    details_text.setReadOnly(True)
    details_layout.addWidget(details_text)

    layout.addWidget(details_group)

    # Connect signals
    plugin_list.itemSelectionChanged.connect(
        lambda: on_plugin_selected(plugin_list, details_text, main_window))
    available_list.itemSelectionChanged.connect(
        lambda: on_available_selected(available_list, details_text))

    # Load initial plugins
    refresh_plugins(main_window, plugin_list, available_list)

    return widget


def refresh_plugins(main_window, plugin_list: QListWidget, available_list: QListWidget):
    """Refresh the plugin lists."""
    try:
        # Clear existing items
        plugin_list.clear()
        available_list.clear()

        # Load loaded plugins
        loaded_plugins = main_window.plugin_manager.list_plugins()
        for plugin_info in loaded_plugins:
            item = QListWidgetItem()
            widget = PluginItemWidget(plugin_info, is_loaded=True)
            widget.plugin_toggle_requested.connect(
                lambda name, enabled: toggle_plugin(main_window, name, enabled, plugin_list, available_list))
            widget.plugin_remove_requested.connect(
                lambda name: remove_plugin(main_window, name, plugin_list, available_list))

            item.setSizeHint(widget.sizeHint())
            plugin_list.addItem(item)
            plugin_list.setItemWidget(item, widget)

        # Discover available plugins in main thread to avoid thread issues
        try:
            discovered_plugins = main_window.plugin_manager.discover_plugins()
            load_available_plugins(
                discovered_plugins, available_list, loaded_plugins)
        except Exception as e:
            main_window.log(
                f"Error discovering plugins: {e}", LogLevel.WARNING)

    except Exception as e:
        main_window.log(f"Error refreshing plugins: {e}", LogLevel.ERROR)


def load_available_plugins(discovered_plugins, available_list: QListWidget, loaded_plugins):
    """Load available plugins into the list."""
    try:
        loaded_names = {p.name for p in loaded_plugins}

        for plugin_info in discovered_plugins:
            if plugin_info.name not in loaded_names:
                item = QListWidgetItem()
                widget = PluginItemWidget(plugin_info, is_loaded=False)
                widget.plugin_toggle_requested.connect(
                    lambda name, enabled: load_plugin(main_window, name, enabled, plugin_list, available_list))

                item.setSizeHint(widget.sizeHint())
                available_list.addItem(item)
                available_list.setItemWidget(item, widget)

    except Exception as e:
        print(f"Error loading available plugins: {e}")


def toggle_plugin(main_window, plugin_name: str, enabled: bool, plugin_list: QListWidget, available_list: QListWidget):
    """Toggle plugin enabled state."""
    try:
        if enabled:
            success = main_window.plugin_manager.enable_plugin(plugin_name)
        else:
            success = main_window.plugin_manager.disable_plugin(plugin_name)

        if success:
            main_window.log(
                f"Plugin {plugin_name} {'enabled' if enabled else 'disabled'}", LogLevel.INFO)
            refresh_plugins(main_window, plugin_list, available_list)
        else:
            main_window.log(
                f"Failed to {'enable' if enabled else 'disable'} plugin {plugin_name}", LogLevel.ERROR)

    except Exception as e:
        main_window.log(
            f"Error toggling plugin {plugin_name}: {e}", LogLevel.ERROR)


def remove_plugin(main_window, plugin_name: str, plugin_list: QListWidget, available_list: QListWidget):
    """Remove a plugin."""
    try:
        success = main_window.plugin_manager.unload_plugin(plugin_name)
        if success:
            main_window.log(f"Plugin {plugin_name} removed", LogLevel.INFO)
            refresh_plugins(main_window, plugin_list, available_list)
        else:
            main_window.log(
                f"Failed to remove plugin {plugin_name}", LogLevel.ERROR)

    except Exception as e:
        main_window.log(
            f"Error removing plugin {plugin_name}: {e}", LogLevel.ERROR)


def load_plugin(main_window, plugin_name: str, enabled: bool, plugin_list: QListWidget, available_list: QListWidget):
    """Load a plugin."""
    try:
        # Find plugin path
        plugin_path = None
        for plugin_info in main_window.plugin_manager.discover_plugins():
            if plugin_info.name == plugin_name:
                plugin_path = plugin_info.path
                break

        if not plugin_path:
            main_window.log(f"Plugin {plugin_name} not found", LogLevel.ERROR)
            return

        success = main_window.plugin_manager.load_plugin(plugin_path)
        if success:
            main_window.log(f"Plugin {plugin_name} loaded", LogLevel.INFO)
            refresh_plugins(main_window, plugin_list, available_list)
        else:
            main_window.log(
                f"Failed to load plugin {plugin_name}", LogLevel.ERROR)

    except Exception as e:
        main_window.log(
            f"Error loading plugin {plugin_name}: {e}", LogLevel.ERROR)


def on_plugin_selected(plugin_list: QListWidget, details_text: QTextEdit, main_window):
    """Handle plugin selection."""
    try:
        current_item = plugin_list.currentItem()
        if not current_item:
            return

        widget = plugin_list.itemWidget(current_item)
        if not widget or not hasattr(widget, 'plugin_info'):
            return

        plugin_info = widget.plugin_info
        details = f"""
Plugin: {plugin_info.name}
Version: {plugin_info.version}
Author: {plugin_info.author}
Category: {plugin_info.category}
Description: {plugin_info.description}
Dependencies: {', '.join(plugin_info.dependencies) if plugin_info.dependencies else 'None'}
API Version: {plugin_info.api_version}
Status: {'Enabled' if plugin_info.enabled else 'Disabled'}
Path: {plugin_info.path}
        """.strip()

        details_text.setPlainText(details)

    except Exception as e:
        main_window.log(f"Error showing plugin details: {e}", LogLevel.ERROR)


def on_available_selected(available_list: QListWidget, details_text: QTextEdit):
    """Handle available plugin selection."""
    try:
        current_item = available_list.currentItem()
        if not current_item:
            return

        widget = available_list.itemWidget(current_item)
        if not widget or not hasattr(widget, 'plugin_info'):
            return

        plugin_info = widget.plugin_info
        details = f"""
Plugin: {plugin_info.name}
Version: {plugin_info.version}
Author: {plugin_info.author}
Category: {plugin_info.category}
Description: {plugin_info.description}
Dependencies: {', '.join(plugin_info.dependencies) if plugin_info.dependencies else 'None'}
API Version: {plugin_info.api_version}
Status: Available
Path: {plugin_info.path}
        """.strip()

        details_text.setPlainText(details)

    except Exception as e:
        print(f"Error showing available plugin details: {e}")
