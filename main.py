import os
import sys
import time

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTranslator, QLocale, Qt
from ui.main_window import PySideUI
from managers.server_manager import ServerManager

# Import specific core managers
from managers.singbox_manager import SingboxManager
from managers.xray_manager import XrayManager
import settings_manager
from utils.error_handler import get_global_error_handler, safe_execute, error_handler_decorator
from utils.performance_monitor import get_global_performance_monitor, PerformanceOptimizer
from constants import LogLevel


@error_handler_decorator(error_type="main_function", critical=True)
def main():
    """Main application entry point with comprehensive error handling."""
    # Initialize global error handler and performance monitor
    error_handler = get_global_error_handler()
    performance_monitor = get_global_performance_monitor()
    performance_optimizer = PerformanceOptimizer(error_handler.log)

    try:
        # Start performance monitoring
        safe_execute(
            lambda: performance_monitor.start_monitoring(),
            error_handler=error_handler,
            context="Starting performance monitoring",
            error_type="performance_monitor_start",
            default_return=False
        )
        # Load settings with error handling
        settings = safe_execute(
            settings_manager.load_settings,
            error_handler=error_handler,
            context="Loading application settings",
            error_type="settings_load",
            default_return={}
        )

        if not settings:
            error_handler.log(
                "Failed to load settings, using defaults", LogLevel.WARNING)
            settings = {}

        # Create the Qt Application and the UI instance
        app = QApplication([])

        # --- Language/Translator Setup ---
        # Default to system language if not set
        language = safe_execute(
            lambda: settings.get(
                "language", QLocale.system().name().split("_")[0]),
            error_handler=error_handler,
            context="Getting system language",
            error_type="language_detection",
            default_return="en"
        )

        # Save the determined language back to settings
        settings["language"] = language

        translator = QTranslator()

        # Construct the path to the translations directory
        translations_path = os.path.join(
            os.path.dirname(__file__), "translations")

        # Load the translation file from the 'translations' directory
        if language != "en":
            translation_loaded = safe_execute(
                lambda: translator.load(
                    f"onix_{language}.qm", translations_path),
                error_handler=error_handler,
                context=f"Loading translation for {language}",
                error_type="translation_load",
                default_return=False
            )
            if translation_loaded:
                app.installTranslator(translator)

        # --- RTL Support Setup ---
        from ui.rtl_styles import is_rtl_language, apply_rtl_styles, get_rtl_font_family

        # Check if language is RTL
        is_rtl = safe_execute(
            lambda: is_rtl_language(language),
            error_handler=error_handler,
            context="Checking RTL language support",
            error_type="rtl_check",
            default_return=False
        )

        if is_rtl:
            # Set RTL layout direction
            safe_execute(
                lambda: app.setLayoutDirection(Qt.RightToLeft),
                error_handler=error_handler,
                context="Setting RTL layout direction",
                error_type="rtl_layout",
                default_return=None
            )

            # Apply RTL styles
            safe_execute(
                lambda: apply_rtl_styles(app, is_dark_mode=False),
                error_handler=error_handler,
                context="Applying RTL styles",
                error_type="rtl_styles",
                default_return=None
            )

            error_handler.log(
                f"RTL support enabled for language: {language}", LogLevel.INFO)
        else:
            # Set LTR layout direction
            safe_execute(
                lambda: app.setLayoutDirection(Qt.LeftToRight),
                error_handler=error_handler,
                context="Setting LTR layout direction",
                error_type="ltr_layout",
                default_return=None
            )

            error_handler.log(
                f"LTR layout for language: {language}", LogLevel.INFO)
        # --- End RTL Support Setup ---

        # --- End Translator Setup ---

        # Initialize managers with error handling
        server_manager = safe_execute(
            lambda: ServerManager(settings, {}),
            error_handler=error_handler,
            context="Initializing server manager",
            error_type="server_manager_init",
            default_return=None
        )

        if not server_manager:
            error_handler.log(
                "Failed to initialize server manager", LogLevel.ERROR)
            return 1

        # Initialize connection manager
        active_core_name = settings.get("active_core", "sing-box")
        if active_core_name == "xray":
            connection_manager = safe_execute(
                lambda: XrayManager(settings, {}),
                error_handler=error_handler,
                context="Initializing Xray manager",
                error_type="xray_manager_init",
                default_return=None
            )
        else:  # Default to sing-box
            connection_manager = safe_execute(
                lambda: SingboxManager(settings, {}),
                error_handler=error_handler,
                context="Initializing Singbox manager",
                error_type="singbox_manager_init",
                default_return=None
            )

        if not connection_manager:
            error_handler.log(
                "Failed to initialize connection manager", LogLevel.ERROR)
            return 1

        # Create the UI with managers
        pyside_ui = safe_execute(
            lambda: PySideUI(server_manager, connection_manager),
            error_handler=error_handler,
            context="Creating main UI",
            error_type="ui_creation",
            default_return=None
        )

        if not pyside_ui:
            error_handler.log("Failed to create main UI", LogLevel.ERROR)
            return 1

        # Define and connect callbacks with error handling
        server_manager_callbacks = {
            "log": pyside_ui.log,
            "on_servers_loaded": pyside_ui.on_servers_loaded,
            "on_servers_updated": pyside_ui.on_servers_updated,
            "on_ping_result": lambda config, ping, test_type: pyside_ui.signals.ping_result.emit(
                config, ping, test_type
            ),
            "on_ping_started": lambda config: pyside_ui.signals.ping_started.emit(config),
            "on_health_check_progress": lambda current, total: pyside_ui.signals.health_check_progress.emit(
                current, total
            ),
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

        # Set callbacks with error handling
        safe_execute(
            lambda: setattr(server_manager, 'callbacks',
                            server_manager_callbacks),
            error_handler=error_handler,
            context="Setting server manager callbacks",
            error_type="callback_setup",
            default_return=None
        )

        safe_execute(
            lambda: setattr(connection_manager, 'callbacks',
                            connection_manager_callbacks),
            error_handler=error_handler,
            context="Setting connection manager callbacks",
            error_type="callback_setup",
            default_return=None
        )

        # Manually trigger initial data load for the UI
        safe_execute(
            lambda: server_manager.load_servers(),
            error_handler=error_handler,
            context="Loading initial server data",
            error_type="server_load",
            default_return=None
        )

        # Show the window and run the app
        app.setProperty("restart_requested", False)

        safe_execute(
            lambda: pyside_ui.show(),
            error_handler=error_handler,
            context="Showing main window",
            error_type="ui_show",
            default_return=None
        )

        exit_code = safe_execute(
            lambda: app.exec(),
            error_handler=error_handler,
            context="Running application event loop",
            error_type="app_exec",
            default_return=1
        )

        # Check if a restart was requested
        if app.property("restart_requested"):
            # Disconnect any active connection before restarting
            if connection_manager and hasattr(connection_manager, 'is_running') and connection_manager.is_running:
                safe_execute(
                    lambda: connection_manager.stop(),
                    error_handler=error_handler,
                    context="Stopping connection before restart",
                    error_type="connection_stop",
                    default_return=None
                )
                time.sleep(0.2)  # Give it a moment to stop

            safe_execute(
                lambda: pyside_ui.tray_icon.hide(),
                error_handler=error_handler,
                context="Hiding tray icon before restart",
                error_type="tray_hide",
                default_return=None
            )

            # Re-execute the application
            safe_execute(
                lambda: os.execv(sys.executable, ["python"] + sys.argv),
                error_handler=error_handler,
                context="Restarting application",
                error_type="app_restart",
                default_return=None
            )
        else:
            sys.exit(exit_code)

    except Exception as e:
        error_handler.handle_error(
            e, "Main application", "main_function", critical=True)
        return 1
    finally:
        # Cleanup resources
        try:
            # Stop performance monitoring
            safe_execute(
                lambda: performance_monitor.stop_monitoring(),
                error_handler=error_handler,
                context="Stopping performance monitoring",
                error_type="performance_monitor_stop",
                default_return=None
            )

            # Optimize memory before exit
            safe_execute(
                lambda: performance_optimizer.optimize_memory(),
                error_handler=error_handler,
                context="Optimizing memory before exit",
                error_type="memory_optimization",
                default_return=None
            )

        except Exception as cleanup_error:
            print(f"Cleanup error: {cleanup_error}")


if __name__ == "__main__":
    main()
