
import sys
import threading
import os
import time

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QTranslator, QLocale
from ui.main_window import PySideUI
from managers.server_manager import ServerManager
# Import specific core managers
from managers.singbox_manager import SingboxManager
from managers.xray_manager import XrayManager
import settings_manager


def main():
    app_instance = None
    # Load settings
    settings = settings_manager.load_settings()

    # Create the Qt Application and the UI instance
    app = QApplication(sys.argv)

    # --- Language/Translator Setup ---
    # Default to system language if not set
    language = settings.get("language", QLocale.system().name().split('_')[
                            0])  # Default to system language
    # Save the determined language back to settings
    settings["language"] = language

    translator = QTranslator()

    # Construct the path to the translations directory
    translations_path = os.path.join(os.path.dirname(__file__), "translations")

    # Load the translation file from the 'translations' directory
    if language != "en" and translator.load(f"onix_{language}.qm", translations_path):
        app.installTranslator(translator)

    # --- End Translator Setup ---

    # Initialize managers
    server_manager = ServerManager(settings, {})
    active_core_name = settings.get("active_core", "sing-box")
    if active_core_name == "xray":
        connection_manager = XrayManager(settings, {})
    else:  # Default to sing-box
        connection_manager = SingboxManager(settings, {})

    # Create the UI with managers
    pyside_ui = PySideUI(server_manager, connection_manager)

    # Define and connect callbacks
    server_manager_callbacks = {
        "log": pyside_ui.log,
        "on_servers_loaded": pyside_ui.on_servers_loaded,
        "on_servers_updated": pyside_ui.on_servers_updated,
        "on_ping_result": lambda config, ping, test_type: pyside_ui.signals.ping_result.emit(config, ping, test_type),
        "on_ping_started": lambda config: pyside_ui.signals.ping_started.emit(config),
        "on_health_check_progress": lambda current, total: pyside_ui.signals.health_check_progress.emit(current, total),
        "on_update_start": pyside_ui.signals.update_started.emit,
        "on_update_finish": pyside_ui.signals.update_finished.emit,
        "on_update_progress": lambda sub_name: pyside_ui.log(f"Updating {sub_name}..."),
        "request_save": pyside_ui.signals.save_requested.emit,
    }
    connection_manager_callbacks = {
        "log": pyside_ui.log,
        "on_status_change": pyside_ui.signals.status_changed.emit,
        "on_connect": pyside_ui.signals.connected.emit,
        "on_stop": pyside_ui.signals.stopped.emit,
        "on_ip_update": pyside_ui.signals.ip_updated.emit,
    }

    server_manager.callbacks = server_manager_callbacks
    connection_manager.callbacks = connection_manager_callbacks

    # Manually trigger initial data load for the UI
    # The load_servers call will trigger the on_servers_loaded callback
    server_manager.load_servers()

    # Show the window and run the app
    app.setProperty("restart_requested", False)
    pyside_ui.show()
    exit_code = app.exec()

    # Check if a restart was requested
    if app.property("restart_requested"):
        # Disconnect any active connection before restarting
        if connection_manager and connection_manager.is_running:
            connection_manager.stop()
            time.sleep(0.2)  # Give it a moment to stop
        pyside_ui.tray_icon.hide()  # Hide tray icon before restart
        # Re-execute the application
        os.execv(sys.executable, ['python'] + sys.argv)
    else:
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
