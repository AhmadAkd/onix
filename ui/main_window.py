import threading
import utils
import mss
import numpy as np
from pyzbar.pyzbar import decode
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QLabel,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QListWidget,
    QStackedWidget,
    QListWidgetItem,
    QPushButton,
    QSystemTrayIcon,
    QGraphicsOpacityEffect,
    QMenu,
    QMessageBox,
    QDialog,
    QFileDialog,
    QTableWidgetItem,
    QSizePolicy,
)
from PySide6.QtCore import (
    Qt,
    QSize,
    QPropertyAnimation,
    QPoint,
    QEasingCurve,
    QParallelAnimationGroup,
    QTimer,
    QByteArray,
    QRect,
)
from PySide6.QtGui import (
    QIcon,
    QAction,
    QPixmap,
    QPalette,
    QMovie,
    QPainter,
    QTextDocument,
    QTextCursor,
    QColor,
    QFont,
)
import resources_rc  # noqa: F401
from constants import TRAY_SHOW, TRAY_QUIT, LogLevel, PROXY_HOST, PROXY_PORT
from ui.signals import ManagerSignals
from ui.views.connection_view import create_connection_view
from ui.views.logs_view import create_logs_view
from ui.views.routing_view import create_routing_view
from ui.views.settings_view import create_settings_view
from ui.dialogs.about import AboutDialog
from ui.dialogs.qr_code import QRCodeDialog
from ui.dialogs.routing_rule import RoutingRuleDialog
from ui.dialogs.server_edit import ServerEditDialog
from ui.dialogs.chain_manager import ChainManagerDialog
from ui.dialogs.subscription import SubscriptionManagerDialog
from managers.subscription_manager import SubscriptionManager
from ui.dialogs.export_dialog import ExportDialog
from ui.widgets.server_card import ServerCardWidget
from ui.styles import THEMES, get_dark_stylesheet, get_light_stylesheet
from services.speed_test_service import SpeedTestService, AutoFailoverService


class PySideUI(QMainWindow):
    def __init__(self, server_manager, singbox_manager):
        super().__init__()
        self.server_manager = server_manager
        self.singbox_manager = singbox_manager
        self.signals = ManagerSignals()
        self.selected_config = None

        self.log_level_colors = {
            # ... (existing colors)
            LogLevel.INFO: self.palette().color(QPalette.WindowText).name(),
            LogLevel.WARNING: "#FFC107",  # Amber
            LogLevel.ERROR: "#F44336",  # Red
            LogLevel.DEBUG: "#888888",  # Gray
            LogLevel.SUCCESS: "#4CAF50",  # Green
        }

        self.all_logs = []  # Store all log messages
        # For handling synchronous questions from other threads
        self._is_scanning_screen = False
        self._question_response = None

        self.settings = self.server_manager.settings if self.server_manager else {}
        self.server_widgets = {}  # Map server name to its card widget

        # Initialize subscription manager
        subscription_callbacks = {
            "log": self.log,
            "on_update_start": self.signals.update_started.emit,
            "on_update_finish": self.signals.update_finished.emit,
            "show_info": lambda title, msg: self.log(msg, LogLevel.INFO),
            "show_warning": lambda title, msg: self.log(msg, LogLevel.WARNING),
            "show_error": self.signals.show_error_message.emit,
        }
        self.subscription_manager = SubscriptionManager(
            server_manager, self.settings, subscription_callbacks
        )

        # Initialize speed test and auto-failover services
        self.speed_test_service = SpeedTestService(self.log)
        self.auto_failover_service = AutoFailoverService(self.log)
        # Connect signals to slots
        self.signals.ping_result.connect(
            self.on_ping_result, Qt.QueuedConnection)
        self.signals.ping_started.connect(
            self.on_ping_started, Qt.QueuedConnection)
        self.signals.health_check_progress.connect(
            self.on_health_check_progress, Qt.QueuedConnection
        )
        self.signals.update_started.connect(self.on_update_started)
        self.signals.log_message.connect(self._log_to_widget)
        self.signals.status_changed.connect(self.on_status_change)
        self.signals.connected.connect(self.on_connect)
        self.signals.stopped.connect(self.on_stop)
        self.signals.ip_updated.connect(self.on_ip_update)
        self.signals.speed_updated.connect(self.on_speed_update)
        self.signals.update_finished.connect(self.on_update_finished)
        self.signals.servers_updated.connect(self.on_servers_updated)
        self.signals.save_requested.connect(self._request_save_settings)
        # Connect message box signals
        self.signals.show_info_message.connect(self.show_info_message_box)
        self.signals.show_warning_message.connect(
            self.show_warning_message_box)
        self.signals.show_error_message.connect(self.show_error_message_box)
        self.signals.ask_yes_no_question.connect(self.handle_ask_yes_no)
        self.signals.schedule_task_signal.connect(self._handle_schedule_task)

        # Title is a brand name, no need to translate
        self.setWindowTitle("Onix")
        self.resize(1200, 800)  # Better initial size
        self.setMinimumSize(900, 600)  # Set minimum size
        self.setMaximumSize(2000, 1500)  # Set maximum size

        # Enable responsive behavior
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Main layout setup...
        self.setup_main_layout()
        self.setup_views()

        # Connect navigation
        self.nav_rail.currentRowChanged.connect(self.animate_tab_transition)
        self.nav_rail.setCurrentRow(0)

        # Apply initial theme
        self.apply_theme(self.settings.get("appearance_mode", "System"))

        # Apply RTL support based on language
        self.apply_rtl_support()
        # Also apply RTL to the entire application
        app = QApplication.instance()
        if app:
            rtl_languages = ["fa", "ar", "he", "ur"]
            if self.settings.get("language") in rtl_languages:
                app.setLayoutDirection(Qt.RightToLeft)
                app.setAttribute(Qt.WA_RightToLeft, True)
                # Apply RTL-specific styling to the entire application
                app.setStyleSheet(app.styleSheet() + """
                    QWidget {
                        direction: rtl;
                    }
                    QMainWindow {
                        direction: rtl;
                    }
                    QLabel {
                        direction: rtl;
                    }
                    QPushButton {
                        direction: rtl;
                    }
                    QComboBox {
                        direction: rtl;
                    }
                    QLineEdit {
                        direction: rtl;
                    }
                    QTextEdit {
                        direction: rtl;
                    }
                    QListWidget {
                        direction: rtl;
                    }
                    QTableWidget {
                        direction: rtl;
                    }
                """)
            else:
                app.setLayoutDirection(Qt.LeftToRight)
                app.setAttribute(Qt.WA_RightToLeft, False)
                # Apply LTR-specific styling to the entire application
                app.setStyleSheet(app.styleSheet() + """
                    QWidget {
                        direction: ltr;
                    }
                    QMainWindow {
                        direction: ltr;
                    }
                    QLabel {
                        direction: ltr;
                    }
                    QPushButton {
                        direction: ltr;
                    }
                    QComboBox {
                        direction: ltr;
                    }
                    QLineEdit {
                        direction: ltr;
                    }
                    QTextEdit {
                        direction: ltr;
                    }
                    QListWidget {
                        direction: ltr;
                    }
                    QTableWidget {
                        direction: ltr;
                    }
                """)

        # Setup System Tray Icon
        self.create_tray_icon()

        # Restore window geometry from last session
        self.restore_window_geometry()

        # Setup a debounced save timer, managed by the UI thread
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(1000)  # 1-second debounce
        self._save_timer.timeout.connect(self._save_settings_to_disk)

    def setup_main_layout(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.nav_rail = QListWidget()
        self.nav_rail.setObjectName("NavRail")
        self.nav_rail.setFixedWidth(160)  # Fixed width for stability
        self.nav_rail.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        main_layout.addWidget(self.nav_rail)

        content_container = QWidget()
        content_container.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.stacked_widget = QStackedWidget()
        content_layout.addWidget(self.stacked_widget)
        content_layout.addWidget(self.create_status_bar())

        main_layout.addWidget(content_container)

    def create_status_bar(self):
        status_bar = QWidget()
        status_bar.setObjectName("StatusBar")
        status_bar.setFixedHeight(60)  # Fixed height
        layout = QHBoxLayout(status_bar)
        # Smaller margins for responsiveness
        layout.setContentsMargins(8, 4, 8, 4)

        # Connection status section
        status_section = QHBoxLayout()
        status_section.setSpacing(8)  # Better spacing

        # Status icon with modern styling
        self.connection_status_icon = QLabel("●")
        self.connection_status_icon.setStyleSheet(
            """
            color: #f59e0b; 
            font-size: 14px;
            font-weight: bold;
            background-color: #fef3c7;
            padding: 3px 6px;
            border-radius: 4px;
        """
        )

        # Status text with modern styling
        self.connection_status_text = QLabel(self.tr("Disconnected"))
        self.connection_status_text.setStyleSheet(
            """
            font-weight: 600; 
            font-size: 12px;
            color: #374151;
        """
        )

        # Connecting animation
        self.connecting_spinner_label = QLabel()
        spinner_movie = QMovie(":/icons/spinner.gif")
        # Reduced from 20x20 to 16x16
        spinner_movie.setScaledSize(QSize(16, 16))
        self.connecting_spinner_label.setMovie(spinner_movie)
        self.connecting_spinner_label.hide()

        status_section.addWidget(self.connecting_spinner_label)
        status_section.addWidget(self.connection_status_icon)
        status_section.addWidget(self.connection_status_text)

        # Network info section
        network_section = QHBoxLayout()
        network_section.setSpacing(10)  # Better spacing

        # IP label with responsive styling
        self.ip_label = QLabel(self.tr("IP: N/A"))
        self.ip_label.setStyleSheet(
            """
            font-size: 10px;
            color: #6b7280;
            background-color: #f3f4f6;
            padding: 3px 6px;
            border-radius: 4px;
        """
        )
        self.ip_label.setMinimumWidth(80)  # Minimum width for responsiveness

        # Latency label with responsive styling
        self.latency_label = QLabel(self.tr("Latency: N/A"))
        self.latency_label.setStyleSheet(
            """
            font-size: 10px;
            color: #6b7280;
            background-color: #f3f4f6;
            padding: 3px 6px;
            border-radius: 4px;
        """
        )
        # Minimum width for responsiveness
        self.latency_label.setMinimumWidth(100)

        # Speed labels with responsive styling
        self.down_speed_label = QLabel("↓ 0 KB/s")
        self.down_speed_label.setStyleSheet(
            """
            font-size: 10px;
            color: #10b981;
            background-color: #d1fae5;
            padding: 3px 6px;
            border-radius: 4px;
            font-weight: 500;
        """
        )
        self.down_speed_label.setMinimumWidth(
            80)  # Minimum width for responsiveness

        self.up_speed_label = QLabel("↑ 0 KB/s")
        self.up_speed_label.setStyleSheet(
            """
            font-size: 10px;
            color: #3b82f6;
            background-color: #dbeafe;
            padding: 3px 6px;
            border-radius: 4px;
            font-weight: 500;
        """
        )
        # Minimum width for responsiveness
        self.up_speed_label.setMinimumWidth(80)

        network_section.addWidget(self.down_speed_label)
        network_section.addWidget(self.up_speed_label)
        network_section.addWidget(self.ip_label)
        network_section.addWidget(self.latency_label)

        # Start/Stop button with responsive styling
        self.start_stop_button = QPushButton(self.tr("Start"))
        self.start_stop_button.setStyleSheet(
            """
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: 500;
                font-size: 12px;
                min-width: 70px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
        """
        )
        self.start_stop_button.setMaximumWidth(
            120)  # Maximum width for responsiveness
        self.start_stop_button.clicked.connect(self.start_stop_toggle)

        # Add sections to main layout with responsive behavior
        layout.addLayout(status_section)
        layout.addStretch()

        # Create a container for network section and button
        right_container = QWidget()
        right_layout = QHBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        right_layout.addLayout(network_section)
        right_layout.addWidget(self.start_stop_button)

        layout.addWidget(right_container)

        return status_bar

    def setup_views(self):
        nav_items = [
            (self.tr("Connection"), ":/icons/link.svg"),
            (self.tr("Routing"), ":/icons/git-merge.svg"),
            (self.tr("Logs"), ":/icons/file-text.svg"),
            (self.tr("Settings"), ":/icons/settings.svg"),
        ]
        for name, icon_name in nav_items:
            item = QListWidgetItem(QIcon(icon_name), name)
            item.setTextAlignment(Qt.AlignCenter)
            item.setSizeHint(QSize(item.sizeHint().width(), 50))
            self.nav_rail.addItem(item)

        self.stacked_widget.addWidget(create_connection_view(self))
        self.stacked_widget.addWidget(create_routing_view(self))
        self.stacked_widget.addWidget(create_logs_view(self))
        self.stacked_widget.addWidget(create_settings_view(self))

    def show_about_dialog(self):
        """Shows the About dialog."""
        dialog = AboutDialog(self)
        dialog.exec()

    def handle_clear_core_log(self):
        """Handles the clearing of the singbox_core.log file."""
        from constants import SINGBOX_LOG_FILE
        import os

        log_file_path = SINGBOX_LOG_FILE

        if not os.path.exists(log_file_path):
            QMessageBox.information(
                self,
                self.tr("Log File"),
                self.tr("Core log file does not exist. Nothing to clear."),
            )
            self.log(
                self.tr("Core log file not found, nothing to clear."), LogLevel.INFO
            )
            return

        reply = QMessageBox.question(
            self,
            self.tr("Confirm Clear"),
            self.tr(
                """Are you sure you want to delete the core log file?\n({})

This action cannot be undone."""
            ).format(log_file_path),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                os.remove(log_file_path)
                self.log(
                    self.tr("Successfully deleted {}").format(log_file_path),
                    LogLevel.SUCCESS,
                )
            except OSError as e:
                self.log(
                    self.tr("Failed to delete log file: {}").format(
                        e), LogLevel.ERROR
                )

    def _validate_and_save_setting(
        self, widget, setting_key, setting_name, validation_type="int"
    ):
        """
        Validates the input from a widget, saves it to settings, and shows an error if invalid.
        Returns True on success, False on failure.
        """
        value = widget.text().strip()
        try:
            if validation_type == "int":
                self.settings[setting_key] = int(value)
            elif validation_type == "range":
                parts = [int(x.strip()) for x in value.split("-")]
                if len(parts) != 2:
                    raise ValueError("Range must be in 'min-max' format.")
                self.settings[setting_key] = value
            else:  # Default to string
                self.settings[setting_key] = value
            return True
        except (ValueError, TypeError):
            QMessageBox.warning(
                self,
                self.tr("Invalid Input"),
                self.tr(
                    "The value for '{}' is invalid.\n" "Please enter a valid {}"
                ).format(
                    setting_name,
                    (
                        self.tr("number")
                        if validation_type == "int"
                        else self.tr("range (e.g., 10-100)")
                    ),
                ),
            )
            widget.setFocus()  # Focus the problematic field
            return False

    def on_language_change(self, lang_name):
        """Handles language change from the settings dropdown."""
        # Find the language code from the display name
        lang_code = "en"  # Default
        for code, name in self.languages.items():
            if name == lang_name:
                lang_code = code
                break

        if self.settings.get("language") != lang_code:
            self.settings["language"] = lang_code
            # Apply RTL support immediately for the new language
            self.apply_rtl_support()
            # Also apply RTL to the entire application
            app = QApplication.instance()
            if app:
                rtl_languages = ["fa", "ar", "he", "ur"]
                if lang_code in rtl_languages:
                    app.setLayoutDirection(Qt.RightToLeft)
                    app.setAttribute(Qt.WA_RightToLeft, True)
                    # Apply RTL-specific styling to the entire application
                    rtl_styles = """
                        QWidget {
                            direction: rtl;
                        }
                        QMainWindow {
                            direction: rtl;
                        }
                        QLabel {
                            direction: rtl;
                        }
                        QPushButton {
                            direction: rtl;
                        }
                        QComboBox {
                            direction: rtl;
                        }
                        QLineEdit {
                            direction: rtl;
                        }
                        QTextEdit {
                            direction: rtl;
                        }
                        QListWidget {
                            direction: rtl;
                        }
                        QTableWidget {
                            direction: rtl;
                        }
                    """
                    app.setStyleSheet(app.styleSheet() + rtl_styles)
                else:
                    app.setLayoutDirection(Qt.LeftToRight)
                    app.setAttribute(Qt.WA_RightToLeft, False)
                    # Apply LTR-specific styling to the entire application
                    ltr_styles = """
                        QWidget {
                            direction: ltr;
                        }
                        QMainWindow {
                            direction: ltr;
                        }
                        QLabel {
                            direction: ltr;
                        }
                        QPushButton {
                            direction: ltr;
                        }
                        QComboBox {
                            direction: ltr;
                        }
                        QLineEdit {
                            direction: ltr;
                        }
                        QTextEdit {
                            direction: ltr;
                        }
                        QListWidget {
                            direction: ltr;
                        }
                        QTableWidget {
                            direction: ltr;
                        }
                    """
                    app.setStyleSheet(app.styleSheet() + ltr_styles)
            self.restart_button.show()

    def on_core_change(self, core_name):
        """Handles core change from the settings dropdown."""
        if self.settings.get("active_core") != core_name:
            self.settings["active_core"] = core_name
            self.restart_button.show()

    def on_theme_change(self, theme_name):
        """Handles theme color change from the settings dropdown."""
        theme_code = "blue"  # Default
        for code, name in self.theme_names.items():
            if name == theme_name:
                theme_code = code
                break
        if self.settings.get("theme_color") != theme_code:
            self.settings["theme_color"] = theme_code
            self.restart_button.show()

    def handle_restart(self):
        """Saves settings and signals the main application to restart."""
        self.save_settings()
        self.log(self.tr("Restarting to apply changes..."))
        QApplication.instance().setProperty("restart_requested", True)
        QApplication.instance().quit()

    def save_settings(self):
        if not self.server_manager:
            return

        self.settings["connection_mode"] = self.connection_mode_combo.currentText()
        self.settings["dns_servers"] = self.dns_entry.text()
        self.settings["bypass_domains"] = self.bypass_domains_entry.text()
        self.settings["bypass_ips"] = self.bypass_ips_entry.text()
        self.settings["tun_enabled"] = self.tun_checkbox.isChecked()

        # Health Check Settings
        if hasattr(self, "health_check_interval_combo"):
            interval_text = self.health_check_interval_combo.currentText()
            self.settings["health_check_interval"] = int(
                interval_text.split()[0])
        if hasattr(self, "health_check_ema_combo"):
            ema_text = self.health_check_ema_combo.currentText()
            self.settings["health_check_ema_alpha"] = float(
                ema_text.split()[0])
        if hasattr(self, "health_check_backoff_combo"):
            backoff_text = self.health_check_backoff_combo.currentText()
            self.settings["health_check_backoff_base"] = int(
                backoff_text.split()[0])
        if hasattr(self, "health_check_auto_start"):
            self.settings["health_check_auto_start"] = (
                self.health_check_auto_start.isChecked()
            )
        if hasattr(self, "auto_failover_checkbox"):
            self.settings["auto_failover_enabled"] = (
                self.auto_failover_checkbox.isChecked()
            )
        self.settings["appearance_mode"] = {
            self.tr("System"): "System",
            self.tr("Light"): "Light",
            self.tr("Dark"): "Dark",
        }.get(self.appearance_mode_combo.currentText(), "System")

        theme_name = self.theme_combo.currentText()
        for code, name in self.theme_names.items():
            if name == theme_name:
                self.settings["theme_color"] = code
        # Add language and core settings to be saved
        lang_name = self.language_combo.currentText()
        for code, name in self.languages.items():
            if name == lang_name:
                self.settings["language"] = code
                break

        self.settings["active_core"] = self.core_selector_combo.currentText()

        # Apply RTL support based on the new language setting
        self.apply_rtl_support()
        # Also apply RTL to the entire application
        app = QApplication.instance()
        if app:
            rtl_languages = ["fa", "ar", "he", "ur"]
            if self.settings.get("language") in rtl_languages:
                app.setLayoutDirection(Qt.RightToLeft)
                app.setAttribute(Qt.WA_RightToLeft, True)
                # Apply RTL-specific styling to the entire application
                app.setStyleSheet(app.styleSheet() + """
                    QWidget {
                        direction: rtl;
                    }
                    QMainWindow {
                        direction: rtl;
                    }
                    QLabel {
                        direction: rtl;
                    }
                    QPushButton {
                        direction: rtl;
                    }
                    QComboBox {
                        direction: rtl;
                    }
                    QLineEdit {
                        direction: rtl;
                    }
                    QTextEdit {
                        direction: rtl;
                    }
                    QListWidget {
                        direction: rtl;
                    }
                    QTableWidget {
                        direction: rtl;
                    }
                """)
            else:
                app.setLayoutDirection(Qt.LeftToRight)
                app.setAttribute(Qt.WA_RightToLeft, False)
                # Apply LTR-specific styling to the entire application
                app.setStyleSheet(app.styleSheet() + """
                    QWidget {
                        direction: ltr;
                    }
                    QMainWindow {
                        direction: ltr;
                    }
                    QLabel {
                        direction: ltr;
                    }
                    QPushButton {
                        direction: ltr;
                    }
                    QComboBox {
                        direction: ltr;
                    }
                    QLineEdit {
                        direction: ltr;
                    }
                    QTextEdit {
                        direction: ltr;
                    }
                    QListWidget {
                        direction: ltr;
                    }
                    QTableWidget {
                        direction: ltr;
                    }
                """)

        # Validate and save numeric/range settings
        if not self._validate_and_save_setting(
            self.mux_max_streams_entry, "mux_max_streams", "Mux Max Streams", "int"
        ):
            return
        if not self._validate_and_save_setting(
            self.tls_fragment_size_entry,
            "tls_fragment_size",
            "TLS Fragment Size",
            "range",
        ):
            return
        if not self._validate_and_save_setting(
            self.tls_fragment_sleep_entry,
            "tls_fragment_sleep",
            "TLS Fragment Sleep",
            "range",
        ):
            return
        if not self._validate_and_save_setting(
            self.hysteria_up_speed_entry,
            "hysteria_up_mbps",
            "Hysteria Upload Speed",
            "int",
        ):
            return
        if not self._validate_and_save_setting(
            self.hysteria_down_speed_entry,
            "hysteria_down_mbps",
            "Hysteria Download Speed",
            "int",
        ):
            return

        # Save other settings that don't need complex validation
        self.settings["tls_fragment_enabled"] = self.tls_fragment_checkbox.isChecked()
        self.settings["mux_enabled"] = self.mux_enabled_checkbox.isChecked()
        self.settings["mux_protocol"] = self.mux_protocol_combo.currentText()
        self.settings["mux_padding"] = self.mux_padding_checkbox.isChecked()

        # Save log level
        if hasattr(self, "log_level_combo"):
            log_level_map = {
                self.tr("Debug"): "Debug",
                self.tr("Info"): "Info",
                self.tr("Warning"): "Warning",
                self.tr("Error"): "Error",
            }
            self.settings["log_level"] = log_level_map.get(
                self.log_level_combo.currentText(), "Info"
            )

        # Save security settings
        if hasattr(self, "enable_ipv6_checkbox"):
            self.settings["enable_ipv6"] = self.enable_ipv6_checkbox.isChecked()
        if hasattr(self, "allow_insecure_checkbox"):
            self.settings["allow_insecure"] = self.allow_insecure_checkbox.isChecked()
        if hasattr(self, "cert_verification_checkbox"):
            self.settings["cert_verification"] = (
                self.cert_verification_checkbox.isChecked()
            )
        if hasattr(self, "custom_ca_entry"):
            self.settings["custom_ca_cert"] = self.custom_ca_entry.text()
        if hasattr(self, "cipher_suites_entry"):
            self.settings["cipher_suites"] = self.cipher_suites_entry.text()
        if hasattr(self, "security_level_combo"):
            security_level_map = {
                self.tr("High"): "High",
                self.tr("Medium"): "Medium",
                self.tr("Low"): "Low",
            }
            self.settings["security_level"] = security_level_map.get(
                self.security_level_combo.currentText(), "High"
            )
        if hasattr(self, "connection_timeout_entry"):
            self.settings["connection_timeout"] = int(
                self.connection_timeout_entry.text()
            )
        if hasattr(self, "retry_attempts_entry"):
            self.settings["retry_attempts"] = int(
                self.retry_attempts_entry.text())
        if hasattr(self, "keep_alive_checkbox"):
            self.settings["keep_alive"] = self.keep_alive_checkbox.isChecked()

        # Save performance settings
        if hasattr(self, "connection_pool_size_entry"):
            self.settings["connection_pool_size"] = int(
                self.connection_pool_size_entry.text()
            )
        if hasattr(self, "thread_pool_size_entry"):
            self.settings["thread_pool_size"] = int(
                self.thread_pool_size_entry.text())
        if hasattr(self, "buffer_size_entry"):
            self.settings["buffer_size"] = int(self.buffer_size_entry.text())
        if hasattr(self, "bandwidth_limit_checkbox"):
            self.settings["bandwidth_limit_enabled"] = (
                self.bandwidth_limit_checkbox.isChecked()
            )
        if hasattr(self, "upload_speed_limit_entry"):
            self.settings["upload_speed_limit"] = int(
                self.upload_speed_limit_entry.text()
            )
        if hasattr(self, "download_speed_limit_entry"):
            self.settings["download_speed_limit"] = int(
                self.download_speed_limit_entry.text()
            )
        if hasattr(self, "connection_multiplexing_checkbox"):
            self.settings["connection_multiplexing"] = (
                self.connection_multiplexing_checkbox.isChecked()
            )
        if hasattr(self, "compression_checkbox"):
            self.settings["compression_enabled"] = self.compression_checkbox.isChecked()
        if hasattr(self, "fast_open_checkbox"):
            self.settings["tcp_fast_open"] = self.fast_open_checkbox.isChecked()
        if hasattr(self, "congestion_control_combo"):
            congestion_map = {
                self.tr("Cubic"): "Cubic",
                self.tr("BBR"): "BBR",
                self.tr("BBR2"): "BBR2",
                self.tr("Reno"): "Reno",
            }
            self.settings["congestion_control"] = congestion_map.get(
                self.congestion_control_combo.currentText(), "Cubic"
            )
        if hasattr(self, "enable_statistics_checkbox"):
            self.settings["enable_statistics"] = (
                self.enable_statistics_checkbox.isChecked()
            )
        if hasattr(self, "statistics_interval_entry"):
            self.settings["statistics_interval"] = int(
                self.statistics_interval_entry.text()
            )

        # Save privacy settings
        if hasattr(self, "disable_telemetry_checkbox"):
            self.settings["disable_telemetry"] = (
                self.disable_telemetry_checkbox.isChecked()
            )
        if hasattr(self, "disable_crash_reports_checkbox"):
            self.settings["disable_crash_reports"] = (
                self.disable_crash_reports_checkbox.isChecked()
            )
        if hasattr(self, "disable_usage_stats_checkbox"):
            self.settings["disable_usage_stats"] = (
                self.disable_usage_stats_checkbox.isChecked()
            )
        if hasattr(self, "disable_detailed_logging_checkbox"):
            self.settings["disable_detailed_logging"] = (
                self.disable_detailed_logging_checkbox.isChecked()
            )
        if hasattr(self, "clear_logs_on_exit_checkbox"):
            self.settings["clear_logs_on_exit"] = (
                self.clear_logs_on_exit_checkbox.isChecked()
            )
        if hasattr(self, "disable_connection_logging_checkbox"):
            self.settings["disable_connection_logging"] = (
                self.disable_connection_logging_checkbox.isChecked()
            )
        if hasattr(self, "disable_dns_logging_checkbox"):
            self.settings["disable_dns_logging"] = (
                self.disable_dns_logging_checkbox.isChecked()
            )
        if hasattr(self, "disable_traffic_stats_checkbox"):
            self.settings["disable_traffic_stats"] = (
                self.disable_traffic_stats_checkbox.isChecked()
            )
        if hasattr(self, "disable_ip_logging_checkbox"):
            self.settings["disable_ip_logging"] = (
                self.disable_ip_logging_checkbox.isChecked()
            )
        if hasattr(self, "disable_auto_updates_checkbox"):
            self.settings["disable_auto_updates"] = (
                self.disable_auto_updates_checkbox.isChecked()
            )
        if hasattr(self, "disable_core_auto_updates_checkbox"):
            self.settings["disable_core_auto_updates"] = (
                self.disable_core_auto_updates_checkbox.isChecked()
            )
        if hasattr(self, "disable_sub_auto_updates_checkbox"):
            self.settings["disable_sub_auto_updates"] = (
                self.disable_sub_auto_updates_checkbox.isChecked()
            )

        self.server_manager.save_settings()
        self.log(self.tr("Settings saved."))

    def _request_save_settings(self):
        """Starts the debounced timer to save settings."""
        self._save_timer.start()

    def _save_settings_to_disk(self):
        """The actual slot that saves settings to disk."""
        self.server_manager.save_settings_to_disk()

    def apply_theme(self, theme_name):
        app = QApplication.instance()
        theme_color_code = self.settings.get("theme_color", "blue")
        theme_palette = THEMES.get(theme_color_code, THEMES["blue"])
        if theme_name == self.tr("Dark"):
            app.setStyleSheet(get_dark_stylesheet(theme_palette))
        elif theme_name == self.tr("Light"):
            app.setStyleSheet(get_light_stylesheet(theme_palette))
        else:  # System
            # Detect system theme based on the palette's base color
            palette = app.palette()
            window_color = palette.color(QPalette.Window)
        if window_color.lightness() < 128:
            app.setStyleSheet(get_dark_stylesheet(theme_palette))
        else:
            app.setStyleSheet(get_light_stylesheet(theme_palette))

        # Reapply RTL support after theme change
        self.apply_rtl_support()
        # Also reapply RTL to the entire application
        app = QApplication.instance()
        if app:
            rtl_languages = ["fa", "ar", "he", "ur"]
            if self.settings.get("language") in rtl_languages:
                app.setLayoutDirection(Qt.RightToLeft)
                app.setAttribute(Qt.WA_RightToLeft, True)
                # Apply RTL-specific styling to the entire application
                app.setStyleSheet(app.styleSheet() + """
                    QWidget {
                        direction: rtl;
                    }
                    QMainWindow {
                        direction: rtl;
                    }
                    QLabel {
                        direction: rtl;
                    }
                    QPushButton {
                        direction: rtl;
                    }
                    QComboBox {
                        direction: rtl;
                    }
                    QLineEdit {
                        direction: rtl;
                    }
                    QTextEdit {
                        direction: rtl;
                    }
                    QListWidget {
                        direction: rtl;
                    }
                    QTableWidget {
                        direction: rtl;
                    }
                """)
            else:
                app.setLayoutDirection(Qt.LeftToRight)
                app.setAttribute(Qt.WA_RightToLeft, False)
                # Apply LTR-specific styling to the entire application
                app.setStyleSheet(app.styleSheet() + """
                    QWidget {
                        direction: ltr;
                    }
                    QMainWindow {
                        direction: ltr;
                    }
                    QLabel {
                        direction: ltr;
                    }
                    QPushButton {
                        direction: ltr;
                    }
                    QComboBox {
                        direction: ltr;
                    }
                    QLineEdit {
                        direction: ltr;
                    }
                    QTextEdit {
                        direction: ltr;
                    }
                    QListWidget {
                        direction: ltr;
                    }
                    QTableWidget {
                        direction: ltr;
                    }
                """)

    def apply_rtl_support(self):
        """Apply RTL support based on current language setting."""
        current_lang = self.settings.get("language", "en")
        # Persian, Arabic, Hebrew, Urdu
        rtl_languages = ["fa", "ar", "he", "ur"]

        if current_lang in rtl_languages:
            self.setLayoutDirection(Qt.RightToLeft)
            self.setAttribute(Qt.WA_RightToLeft, True)
            # Apply RTL-specific styling
            rtl_styles = """
                QWidget[dir="rtl"] {
                    direction: rtl;
                }
                QMainWindow {
                    direction: rtl;
                }
                QWidget {
                    direction: rtl;
                }
                QLabel {
                    direction: rtl;
                }
                QPushButton {
                    direction: rtl;
                }
                QComboBox {
                    direction: rtl;
                }
                QLineEdit {
                    direction: rtl;
                }
                QTextEdit {
                    direction: rtl;
                }
                QListWidget {
                    direction: rtl;
                }
                QTableWidget {
                    direction: rtl;
                }
            """
            # Get current stylesheet and add RTL styles
            current_style = self.styleSheet()
            self.setStyleSheet(current_style + rtl_styles)
        else:
            self.setLayoutDirection(Qt.LeftToRight)
            self.setAttribute(Qt.WA_RightToLeft, False)
            # Reset to LTR styling
            ltr_styles = """
                QWidget[dir="rtl"] {
                    direction: ltr;
                }
                QMainWindow {
                    direction: ltr;
                }
                QWidget {
                    direction: ltr;
                }
                QLabel {
                    direction: ltr;
                }
                QPushButton {
                    direction: ltr;
                }
                QComboBox {
                    direction: ltr;
                }
                QLineEdit {
                    direction: ltr;
                }
                QTextEdit {
                    direction: ltr;
                }
                QListWidget {
                    direction: ltr;
                }
                QTableWidget {
                    direction: ltr;
                }
            """
            # Get current stylesheet and add LTR styles
            current_style = self.styleSheet()
            self.setStyleSheet(current_style + ltr_styles)

    def handle_check_for_updates(self):
        self.log(self.tr("Checking for core updates..."))
        self.check_updates_button.setEnabled(False)
        self.check_updates_button.setText(self.tr("Checking..."))

        # Run the update check in a separate thread to not freeze the UI
        threading.Thread(target=self._run_update_check, daemon=True).start()

    def _update_check_updates_button(self, enabled, text):
        self.check_updates_button.setEnabled(enabled)
        self.check_updates_button.setText(self.tr(text))

    def handle_import_profile(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, self.tr("Import Profile"), "", self.tr("JSON Files (*.json)")
        )

        if file_path:
            success = self.server_manager.import_settings(file_path)
            if success:
                QMessageBox.information(
                    self,
                    self.tr("Import Successful"),
                    self.tr(
                        "Profile imported successfully. Please restart the application for the changes to take full effect."
                    ),
                )
                # Optionally, you can try to reload the UI dynamically here,
                # but a restart is safer and simpler.
            else:
                QMessageBox.critical(
                    self,
                    self.tr("Import Failed"),
                    self.tr(
                        "The selected file is not a valid Onix profile or is corrupted."
                    ),
                )

    def handle_export_profile(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            self.tr("Export Profile"),
            "onix_profile.json",
            self.tr("JSON Files (*.json)"),
        )

        if file_path:
            success = self.server_manager.export_settings(file_path)
            if success:
                QMessageBox.information(
                    self,
                    self.tr("Export Successful"),
                    self.tr("Profile successfully exported to:\n{}").format(
                        file_path),
                )

    def _run_update_check(self):
        # Define callbacks that emit signals to the UI thread
        update_callbacks = {
            "show_info": self.signals.show_info_message.emit,
            "show_warning": self.signals.show_warning_message.emit,
            "show_error": self.signals.show_error_message.emit,
            "ask_yes_no": self.ask_yes_no_from_thread,
        }
        active_core = self.settings.get("active_core", "sing-box")
        utils.download_core_if_needed(
            core_name=active_core, force_update=True, callbacks=update_callbacks
        )
        # Re-enable the button on the main thread
        QTimer.singleShot(
            0,
            lambda: self._update_check_updates_button(
                True, self.tr("Check for Core Updates")
            ),
        )

    def show_subscription_manager(self):
        current_subs = self.settings.get("subscriptions", [])
        # Pass a copy of the list to the dialog, so we can compare it later.
        dialog = SubscriptionManagerDialog(
            self, subscriptions=[sub.copy() for sub in current_subs]
        )
        if dialog.exec() == QDialog.Accepted:
            updated_subs = dialog.get_subscriptions()
            if updated_subs is not None:
                self.settings["subscriptions"] = updated_subs
                self.save_settings()
                self.log(self.tr("Subscription list updated."))
                # Ask user to update subscriptions now that the list has changed.
                reply = QMessageBox.question(
                    self,
                    self.tr("Update Subscriptions"),
                    self.tr(
                        "Subscription list has changed. Do you want to update all enabled subscriptions now?"
                    ),
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes,
                )
                if reply == QMessageBox.Yes:
                    self.handle_update_subscriptions()

    def import_from_clipboard(self):
        """Imports server configurations from the clipboard."""
        clipboard = QApplication.clipboard()
        text = clipboard.text()

        if not text:
            self.log(self.tr("Clipboard is empty."), "warning")
            return

        links = text.strip().splitlines()
        added_count = 0
        for link in links:
            if self.server_manager.add_manual_server(link.strip()):
                added_count += 1

        self.log(self.tr("Imported {} server(s) from clipboard.").format(added_count))

    def handle_import_wireguard_config(self):
        """Opens a file dialog to import a WireGuard .conf file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Import WireGuard Config"),
            "",
            self.tr("Config Files (*.conf)"),
        )

        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                # The server manager will parse and add the config
                self.server_manager.add_wireguard_config(content, file_path)
            except Exception as e:
                self.log(
                    self.tr("Failed to read or parse WireGuard file: {}").format(e),
                    LogLevel.ERROR,
                )
                QMessageBox.critical(
                    self,
                    self.tr("Import Error"),
                    self.tr("Could not import the WireGuard file:\n{}").format(e),
                )

    def handle_scan_qr_from_screen(self):
        """Hides the window, takes a screenshot, and scans for a QR code."""
        self._is_scanning_screen = True
        self.log(self.tr("Scanning screen for QR code..."))
        # self.scan_qr_button.setEnabled(False) # This button does not exist in the pyside UI

        # Hide the window to scan the screen
        self.hide()
        # Give a small delay for the window to hide completely
        QTimer.singleShot(300, self._start_scan_task)

    def _start_scan_task(self):
        threading.Thread(target=self._scan_and_add_task, daemon=True).start()

    def _scan_and_add_task(self):
        """The actual scanning logic that runs in a background thread."""
        try:
            with mss.mss() as sct:
                # Get information of monitor 1
                monitor_info = sct.monitors[1]
                sct_img = sct.grab(monitor_info)
                img = np.frombuffer(sct_img.rgb, np.uint8).reshape(
                    (sct_img.height, sct_img.width, 3)
                )

            decoded_objects = decode(img)
            if decoded_objects:
                link = decoded_objects[0].data.decode("utf-8")
                self.server_manager.add_manual_server(link)
            else:
                self.log(self.tr("No QR code found on the screen."),
                         LogLevel.WARNING)
        finally:
            # Ensure the window is shown again and the button is re-enabled
            QTimer.singleShot(0, self.show_window)
            self._is_scanning_screen = False
            # self.scan_qr_button.setEnabled(True)

    def copy_group_links_to_clipboard(self):
        """Copies the links of all VISIBLE servers in the list to the clipboard."""
        if not self.server_manager:
            self.log("Server manager not initialized.", "error")
            return

        if self.server_list_widget.count() == 0:
            self.log(self.tr("No visible servers to copy."), LogLevel.WARNING)
            QMessageBox.warning(
                self,
                self.tr("Copy Links"),
                self.tr("There are no servers in the list to copy."),
            )
            return

        visible_servers = []
        for i in range(self.server_list_widget.count()):
            item = self.server_list_widget.item(i)
            card = self.server_list_widget.itemWidget(item)
            if card:
                visible_servers.append(card.server_data)

        if not visible_servers:
            self.log(
                self.tr(
                    "Could not retrieve server data from the list."), LogLevel.ERROR
            )
            return

        links = [
            self.server_manager.get_server_link(s)
            for s in visible_servers
            if self.server_manager.get_server_link(s)
        ]

        if links:
            clipboard = QApplication.clipboard()
            clipboard.setText("\n".join(links))
            QMessageBox.information(
                self,
                self.tr("Copy Successful"),
                self.tr("Copied {} server link(s) to clipboard.").format(
                    len(links)),
            )
        else:
            QMessageBox.warning(
                self,
                self.tr("Copy Failed"),
                self.tr("Could not generate links for the visible servers."),
            )

    def delete_current_group(self):
        """Deletes the currently selected server group after confirmation."""
        current_group = self.group_dropdown.currentText()
        if not current_group:
            self.log(self.tr("No group selected to delete."), LogLevel.WARNING)
            return

        reply = QMessageBox.question(
            self,
            self.tr("Confirm Group Deletion"),
            self.tr(
                "Are you sure you want to delete the entire group '{}' and all its servers?"
            ).format(current_group),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes and self.server_manager:
            self.server_manager.delete_group(current_group)

    def handle_update_subscriptions(self):
        """Handle subscription update using the new subscription manager."""
        if self.subscription_manager.is_update_in_progress():
            self.log(
                "Subscription update is already in progress. Please wait...",
                LogLevel.WARNING,
            )
            return

        current_group = self.group_dropdown.currentText()
        all_subs = self.settings.get("subscriptions", [])

        # Try to find a subscription matching the current group
        sub_to_update = None
        for sub in all_subs:
            if sub.get("name") == current_group:
                sub_to_update = sub
                break

        subs_to_process = []
        if sub_to_update:
            # User is in a subscription group, update just this one
            if sub_to_update.get("enabled", True):
                subs_to_process = [sub_to_update]
                self.log(
                    f"Updating current subscription group: {current_group}...")
            else:
                self.log(
                    f"Subscription '{current_group}' is disabled. Please enable it in the Subscription Manager.",
                    LogLevel.WARNING,
                )
                return
        else:
            # User is not in a subscription group, or group name doesn't match.
            # Fallback to original behavior: update all enabled subs.
            subs_to_process = [
                sub for sub in all_subs if sub.get("enabled", True)]
            self.log("Updating all enabled subscriptions...")

        if not subs_to_process:
            self.log(self.tr("No enabled subscriptions to update."),
                     LogLevel.WARNING)
            return

        # Use the new subscription manager
        self.subscription_manager.update_subscriptions(subs_to_process)

    # --- Message Box Handlers (Slots) ---
    def show_info_message_box(self, title, message):
        QMessageBox.information(self, title, message)

    def show_warning_message_box(self, title, message):
        QMessageBox.warning(self, title, message)

    def show_error_message_box(self, title, message):
        QMessageBox.critical(self, title, message)

    def handle_ask_yes_no(self, title, question):
        reply = QMessageBox.question(
            self, title, question, QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        self._question_response = reply == QMessageBox.Yes

    def ask_yes_no_from_thread(self, title, question):
        """Synchronously ask a question from a non-GUI thread."""
        self._question_response = None
        self.signals.ask_yes_no_question.emit(title, question)
        # Wait until the main thread has processed the question
        while self._question_response is None:
            QApplication.processEvents()  # Allow UI to respond
        return self._question_response

    def update_routing_table(self):
        # Save current sort order
        header = self.routing_table.horizontalHeader()
        sort_column = header.sortIndicatorSection()
        sort_order = header.sortIndicatorOrder()

        # Disable sorting while updating to prevent issues
        self.routing_table.setSortingEnabled(False)

        rules = self.settings.get("custom_routing_rules", [])
        self.routing_table.setRowCount(len(rules))

        for row_index, rule in enumerate(rules):
            self.routing_table.setItem(
                row_index, 0, QTableWidgetItem(rule.get("type")))
            self.routing_table.setItem(
                row_index, 1, QTableWidgetItem(rule.get("value"))
            )
            self.routing_table.setItem(
                row_index, 2, QTableWidgetItem(rule.get("action"))
            )

            # Actions buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 0, 5, 0)
            actions_layout.setSpacing(5)

            edit_button = QPushButton("Edit")
            edit_button.clicked.connect(
                lambda _, r=row_index: self.show_rule_dialog(
                    rule_to_edit=self.settings["custom_routing_rules"][r], index=r
                )
            )

            delete_button = QPushButton("Delete")
            delete_button.setStyleSheet("background-color: #F44336;")
            delete_button.clicked.connect(
                lambda _, r=row_index: self.delete_rule(r))

            actions_layout.addWidget(edit_button)
            actions_layout.addWidget(delete_button)
            actions_layout.addStretch()

            self.routing_table.setCellWidget(row_index, 3, actions_widget)

        # Re-enable sorting after the table is populated
        self.routing_table.setSortingEnabled(True)
        # Restore the sort order
        if sort_column is not None:
            self.routing_table.sortByColumn(sort_column, sort_order)

    def show_rule_dialog(self, _, rule_to_edit=None, index=None):
        dialog = RoutingRuleDialog(self, rule=rule_to_edit)
        if dialog.exec() == QDialog.Accepted:
            new_rule_data = dialog.get_rule_data()
            if not new_rule_data["value"]:
                QMessageBox.warning(
                    self,
                    self.tr("Input Error"),
                    self.tr("The 'Value' field cannot be empty."),
                )
                return

            rules = self.settings.get("custom_routing_rules", [])
            if rule_to_edit is not None and index is not None:
                # Editing existing rule
                rules[index] = new_rule_data
                self.log(self.tr("Rule updated: {}").format(
                    new_rule_data["value"]))
            else:
                # Adding new rule
                rules.append(new_rule_data)
                self.log(self.tr("Rule added: {}").format(
                    new_rule_data["value"]))

            self.settings["custom_routing_rules"] = rules
            self.save_settings()
            self.update_routing_table()

    def delete_rule(self, index):
        rules = self.settings.get("custom_routing_rules", [])
        if 0 <= index < len(rules):
            rule_to_delete = rules[index]
            reply = QMessageBox.question(
                self,
                self.tr("Confirm Deletion"),
                self.tr("Are you sure you want to delete the rule for '{}'?").format(
                    rule_to_delete.get("value")
                ),
            )
            if reply == QMessageBox.Yes:
                deleted_rule = rules.pop(index)
                self.log(self.tr("Rule deleted: {}").format(
                    deleted_rule["value"]))
                self.save_settings()
                self.update_routing_table()

    def toggle_health_check_tcp(self):
        """Toggle TCP health checking on/off."""
        if self.health_check_tcp_button.isChecked():
            # Start TCP health checking
            current_group = self.group_dropdown.currentText()
            if not current_group:
                self.health_check_tcp_button.setChecked(False)
                self.log("No group selected for TCP health checking",
                         LogLevel.WARNING)
                return

            self.server_manager.start_health_check(current_group, ["tcp"])
            self.health_check_tcp_button.setText(
                self.tr("Stop TCP Health Check"))
            self.health_check_tcp_button.setStyleSheet(
                "background-color: #F44336;")
            self.health_check_progress.setVisible(True)
            self.health_check_progress.setValue(0)
            self.log(
                f"Started TCP health checking for group: {current_group}", LogLevel.INFO
            )
        else:
            # Stop health checking
            self.server_manager.stop_health_check()
            self.health_check_tcp_button.setText(self.tr("Health Check TCP"))
            self.health_check_tcp_button.setStyleSheet("")
            self.health_check_progress.setVisible(False)
            self.log("Stopped TCP health checking", LogLevel.INFO)

    def toggle_health_check_url(self):
        """Toggle URL health checking on/off."""
        if self.health_check_url_button.isChecked():
            # Start URL health checking
            current_group = self.group_dropdown.currentText()
            if not current_group:
                self.health_check_url_button.setChecked(False)
                self.log("No group selected for URL health checking",
                         LogLevel.WARNING)
                return

            self.server_manager.start_health_check(current_group, ["url"])
            self.health_check_url_button.setText(
                self.tr("Stop URL Health Check"))
            self.health_check_url_button.setStyleSheet(
                "background-color: #F44336;")
            self.health_check_progress.setVisible(True)
            self.health_check_progress.setValue(0)
            self.log(
                f"Started URL health checking for group: {current_group}", LogLevel.INFO
            )
        else:
            # Stop health checking
            self.server_manager.stop_health_check()
            self.health_check_url_button.setText(self.tr("Health Check URL"))
            self.health_check_url_button.setStyleSheet("")
            self.health_check_progress.setVisible(False)
            self.log("Stopped URL health checking", LogLevel.INFO)

    def toggle_speed_test(self):
        """Toggle speed test on/off."""
        if self.speed_test_button.isChecked():
            # Start speed test
            if not self.selected_config:
                self.speed_test_button.setChecked(False)
                self.log("No server selected for speed test", LogLevel.WARNING)
                return

            if not self.singbox_manager.is_running:
                self.speed_test_button.setChecked(False)
                self.log("Please connect to a server first", LogLevel.WARNING)
                return

            self.speed_test_button.setText(self.tr("Stop Speed Test"))
            self.speed_test_button.setStyleSheet("background-color: #F44336;")

            # Start speed test
            proxy_address = f"{PROXY_HOST}:{PROXY_PORT}"
            self.speed_test_service.start_speed_test(
                proxy_address, duration=10, callback=self.on_speed_test_result
            )
            self.log(
                f"Started speed test for server: {self.selected_config.get('name')}",
                LogLevel.INFO,
            )
        else:
            # Stop speed test
            self.speed_test_service.stop_speed_test()
            self.speed_test_button.setText(self.tr("Speed Test"))
            self.speed_test_button.setStyleSheet("")
            self.log("Stopped speed test", LogLevel.INFO)

    def on_speed_test_result(self, download_speed: float, upload_speed: float):
        """Handle speed test results."""
        # Update speed labels in status bar
        self.on_speed_update(upload_speed, download_speed)

        # Log the results
        self.log(
            f"Speed test: {download_speed/1024/1024:.2f} MB/s download, "
            f"{upload_speed/1024/1024:.2f} MB/s upload",
            LogLevel.SUCCESS,
        )

    def show_export_dialog(self):
        """Show export dialog for current group."""
        current_group = self.group_dropdown.currentText()
        if not current_group:
            self.log("No group selected for export", LogLevel.WARNING)
            return

        servers = self.server_manager.get_servers_by_group(current_group)
        if not servers:
            self.log("No servers to export", LogLevel.WARNING)
            return

        # Get health stats from health checker
        health_stats = {}
        if hasattr(self.server_manager, "_health_checker"):
            for server in servers:
                server_id = server.get("id")
                if server_id:
                    health_stats[server_id] = (
                        self.server_manager._health_checker.get_server_stats(
                            server_id)
                    )

        dialog = ExportDialog(self, servers, health_stats)
        dialog.exec()

    def on_health_check_progress(self, current: int, total: int):
        """Handle health check progress updates."""
        if hasattr(self, "health_check_progress"):
            percentage = int((current / total) * 100) if total > 0 else 0
            self.health_check_progress.setValue(percentage)
            self.health_check_progress.setFormat(
                f"{current}/{total} ({percentage}%)")

    def start_stop_toggle(self):
        if self.singbox_manager.is_running:
            # Stop health check when manually disconnecting
            self.server_manager.stop_health_check()
            # Reset health check button states
            if hasattr(self, "health_check_tcp_button"):
                self.health_check_tcp_button.setChecked(False)
                self.health_check_tcp_button.setText(
                    self.tr("Health Check TCP"))
                self.health_check_tcp_button.setStyleSheet("")
            if hasattr(self, "health_check_url_button"):
                self.health_check_url_button.setChecked(False)
                self.health_check_url_button.setText(
                    self.tr("Health Check URL"))
                self.health_check_url_button.setStyleSheet("")
            if hasattr(self, "health_check_progress"):
                self.health_check_progress.setVisible(False)
            threading.Thread(target=self.singbox_manager.stop,
                             daemon=True).start()
        else:
            if self.selected_config:
                # The start method already runs in a background thread.
                self.singbox_manager.start(self.selected_config)
            else:
                self.log(self.tr("No server selected!"))

    # --- Slots for Server Card Actions ---
    def handle_server_action(self, action, server_data):
        if action == "ping_url":
            self.log(
                self.tr("Latency testing server: {}").format(
                    server_data.get("name"))
            )
            threading.Thread(
                target=self.server_manager.test_all_urls,
                args=([server_data],),
                daemon=True,
            ).start()
        elif action == "ping_tcp":
            self.log(
                self.tr("Latency testing server: {}").format(
                    server_data.get("name"))
            )
            threading.Thread(
                target=self.server_manager.test_all_tcp,
                args=([server_data],),
                daemon=True,
            ).start()
        elif action == "delete":
            reply = QMessageBox.question(
                self,
                self.tr("Confirm Deletion"),
                self.tr("Are you sure you want to delete server\n'{}'?").format(
                    server_data.get("name")
                ),
            )
            if reply == QMessageBox.Yes:
                self.server_manager.delete_server(server_data)
                self.update_server_list()
                if self.selected_config and self.selected_config.get(
                    "id"
                ) == server_data.get("id"):
                    self.selected_config = None
        elif action == "edit_server":
            dialog = ServerEditDialog(self, server_config=server_data)
            if dialog.exec() == QDialog.Accepted:
                updated_config = dialog.get_updated_config()
                self.server_manager.edit_server_config(
                    server_data, updated_config)
                self.update_server_list()
        elif action == "copy_link":
            server_link = self.server_manager.get_server_link(server_data)
            if server_link:
                clipboard = QApplication.clipboard()
                clipboard.setText(server_link)
                self.log(
                    self.tr("Copied link for '{}' to clipboard.").format(
                        server_data.get("name")
                    )
                )
            else:
                self.log(
                    self.tr("Could not generate a link for '{}'.").format(
                        server_data.get("name")
                    ),
                    LogLevel.WARNING,
                )
        elif action == "qr_code":
            server_link = self.server_manager.get_server_link(server_data)
            if server_link:
                dialog = QRCodeDialog(
                    server_link, server_data.get("name"), self)
                dialog.exec()
            else:
                QMessageBox.warning(
                    self,
                    self.tr("Error"),
                    self.tr("Could not generate a link for this server."),
                )

    # --- Log Search Methods ---
    def find_next_log(self):
        """Finds the next occurrence of the search query in the log view."""
        query = self.log_search_input.text()
        if not query:
            return

        # Using find with default options (forward search)
        found = self.log_view.find(query)

        if not found:
            # If not found, wrap around to the beginning of the document
            cursor = self.log_view.textCursor()
            cursor.movePosition(QTextCursor.Start)
            self.log_view.setTextCursor(cursor)
            self.log_view.find(query)

    def find_prev_log(self):
        """Finds the previous occurrence of the search query in the log view."""
        query = self.log_search_input.text()
        if not query:
            return

        # Using find with the FindBackward flag
        self.log_view.find(query, QTextDocument.FindBackward)

    def show_log_context_menu(self, position):
        """Creates and shows a context menu for the log view."""
        menu = QMenu()

        # Standard "Copy" action for selected text
        copy_action = menu.addAction(
            QIcon(":/icons/copy.svg"), self.tr("Copy"))
        copy_action.triggered.connect(self.log_view.copy)
        # Disable if no text is selected
        copy_action.setEnabled(self.log_view.textCursor().hasSelection())

        # Action to copy the entire line under the cursor
        copy_line_action = menu.addAction(self.tr("Copy Line"))

        def copy_current_line():
            cursor = self.log_view.cursorForPosition(position)
            cursor.select(QTextCursor.LineUnderCursor)
            self.log_view.setTextCursor(cursor)
            self.log_view.copy()
            # Optional: clear selection after copy
            cursor.clearSelection()
            self.log_view.setTextCursor(cursor)

        copy_line_action.triggered.connect(copy_current_line)
        menu.exec(self.log_view.viewport().mapToGlobal(position))

    def clear_logs(self):
        """Clears all logs from the view and internal storage."""
        self.all_logs.clear()
        self.log_view.clear()
        self.log(self.tr("Logs cleared."))

    # --- Data Loading and UI Updates (Slots) ---
    def log(self, message, level=None):
        # Always emit a signal to ensure logging is thread-safe and handled on the main thread.
        if level is None:
            level = LogLevel.INFO
        self.signals.log_message.emit(message, level)

    def _log_to_widget(self, message, level):
        """This method is a slot and should only be called from the main UI thread via a signal."""
        if level is None:
            level = LogLevel.INFO

        if self.log_view:
            color = self.log_level_colors.get(
                level, self.log_level_colors[LogLevel.INFO]
            )

            # Check if the current level is enabled in filters
            level_enabled = False
            if level == LogLevel.INFO and self.log_filter_info.isChecked():
                level_enabled = True
            elif level == LogLevel.WARNING and self.log_filter_warning.isChecked():
                level_enabled = True
            elif level == LogLevel.ERROR and self.log_filter_error.isChecked():
                level_enabled = True
            elif level == LogLevel.DEBUG and self.log_filter_debug.isChecked():
                level_enabled = True

            if level_enabled:
                # Use HTML to set the color of the appended text
                self.log_view.append(
                    f'<span style="color:{color};">{message}</span>')

        self.all_logs.append((message, level))

    def refresh_log_display(self):
        """Clears and re-populates the log view based on current filters."""
        self.log_view.clear()
        active_levels = set()
        if self.log_filter_info.isChecked():
            active_levels.add(LogLevel.INFO)
        if self.log_filter_warning.isChecked():
            active_levels.add(LogLevel.WARNING)
        if self.log_filter_error.isChecked():
            active_levels.add(LogLevel.ERROR)
        if self.log_filter_debug.isChecked():
            active_levels.add(LogLevel.DEBUG)

        for message, level in self.all_logs:
            if level in active_levels:
                color = self.log_level_colors.get(
                    level, self.log_level_colors[LogLevel.INFO]
                )
                self.log_view.append(
                    f'<span style="color:{color};">{message}</span>')

    def _get_available_groups(self):
        """Returns a list of available groups, including a special one for chains."""
        server_groups = self.server_manager.get_groups()
        # Add the chains group if any chains exist
        if self.settings.get("outbound_chains"):
            return ["⛓️ Chains"] + server_groups
        return server_groups

    def update_group_dropdown(self):
        groups = self._get_available_groups()
        self.group_dropdown.blockSignals(True)
        self.group_dropdown.clear()
        if groups:
            self.group_dropdown.addItems(groups)
        self.group_dropdown.blockSignals(False)
        if groups:
            self.group_dropdown.setCurrentIndex(0)
            self.update_server_list()

    def update_server_list(self):
        self.server_list_widget.clear()
        self.server_widgets.clear()
        selected_group = self.group_dropdown.currentText()
        search_term = self.search_field.text().lower()
        if not selected_group:
            return

        if selected_group == "⛓️ Chains":
            self.current_view_mode = "chains"
            items_to_display = self.settings.get("outbound_chains", [])
            # Chains don't need sorting
        else:
            self.current_view_mode = "servers"
            items_to_display = self.server_manager.get_servers_by_group(
                selected_group)

        # --- Manual Sorting ---
        if self.current_view_mode == "servers":
            # Auto-sort by best ping (lowest first), with N/A at the end
            def ping_sort_key(server):
                tcp_ping = server.get("tcp_ping")
                if tcp_ping is None or tcp_ping == -1:
                    return 9999  # Put N/A at the end
                return tcp_ping

            items_to_display.sort(key=ping_sort_key)

        # --- Filtering and Display ---
        for item_data in items_to_display:
            # is_chain = self.current_view_mode == "chains" # This variable is not used
            if not search_term or search_term in item_data.get("name", "").lower():
                card = ServerCardWidget(item_data)
                card.action_requested.connect(self.handle_server_action)
                item = QListWidgetItem(self.server_list_widget)
                item.setSizeHint(card.sizeHint())
                self.server_list_widget.addItem(item)
                self.server_list_widget.setItemWidget(item, card)
                self.server_widgets[item_data.get("id")] = card

    def on_server_selected(self, current_item, previous_item):
        if not current_item:
            self.selected_config = None
            self.server_details_panel.hide()
            return
        card = self.server_list_widget.itemWidget(current_item)
        if card:
            self.selected_config = card.server_data
            self.log(
                self.tr("Selected server: {}").format(
                    self.selected_config.get("name"))
            )
            # self._update_details_panel(self.selected_config)

    def _update_details_panel(self, config):
        """Populates the right-side panel with server details."""
        if not config:
            self.server_details_panel.hide()
            return

        details_html = "<h3>{}</h3><hr>".format(config.get("name", "N/A"))
        details_html += "<table>"

        # Define which keys to show and their display names
        key_map = {
            "protocol": "Protocol",
            "server": "Server",
            "port": "Port",
            "uuid": "UUID",
            "password": "Password",
            "sni": "SNI",
            "transport": "Transport",
            "ws_path": "Path",
        }

        for key, label in key_map.items():
            if value := config.get(key):
                details_html += (
                    f"<tr><td width='80'><b>{label}:</b></td><td>{value}</td></tr>"
                )

        details_html += "</table>"
        self.server_details_content.setHtml(details_html)
        self.server_details_panel.show()

    def on_ping_result(self, config, ping, test_type):
        server_id = config.get("id")
        self.log(
            self.tr(
                "Ping result for '{}' (ID: {}, Type: {}): {} ms. Emitting signal."
            ).format(config.get("name"), server_id, test_type, ping),
            LogLevel.DEBUG,
        )
        if not server_id:
            self.log(
                self.tr("Server ID is missing in ping result. Cannot update UI."),
                LogLevel.WARNING,
            )
            return

        # This should be server_card_widgets
        card = self.server_widgets.get(server_id)
        if card:
            self.log(
                self.tr("Found card for server ID {}. Updating {} ping value.").format(
                    server_id, test_type
                ),
                LogLevel.DEBUG,
            )
            card.update_ping(test_type, ping)

            # Update health stats if this is from health checker
            if hasattr(self.server_manager, "_health_checker"):
                health_stats = self.server_manager._health_checker.get_server_stats(
                    server_id
                )
                if health_stats:
                    card.update_health_stats(health_stats)
        else:
            self.log(
                self.tr("Could not find card widget for server ID {}").format(
                    server_id
                ),
                LogLevel.WARNING,
            )

    def on_ping_started(self, config):
        server_id = config.get("id")
        if not server_id:
            return
        card = self.server_widgets.get(server_id)
        if card:
            # Reset both labels to '...'
            card.update_ping("direct_tcp", -2)
            card.update_ping("url", -2)

    def on_update_started(self):
        self.manage_subs_button.setEnabled(False)
        self.manage_subs_button.hide()
        self.update_spinner_label.show()
        self.update_spinner_label.movie().start()

    def on_update_finished(self, error):
        self.manage_subs_button.setEnabled(True)
        self.update_spinner_label.hide()
        self.manage_subs_button.show()
        self.update_spinner_label.movie().stop()
        self.log(self.tr("Subscription update finished."))
        self.update_group_dropdown()
        self.update_server_list()

    def on_servers_loaded(self):
        """Called when servers are initially loaded."""
        self.update_group_dropdown()
        self.update_server_list()

    def on_servers_updated(self):
        """Called when servers are updated (e.g., after subscription update)."""
        self.update_group_dropdown()
        self.update_server_list()

    def update_single_subscription(self, sub):
        """Update a single subscription."""
        if self.subscription_manager.is_update_in_progress():
            self.log(
                "Subscription update is already in progress. Please wait...",
                LogLevel.WARNING,
            )
            return

        if not sub.get("enabled", True):
            self.log(
                f"Subscription '{sub.get('name', 'Unknown')}' is disabled. Please enable it first.",
                LogLevel.WARNING,
            )
            return

        self.log(f"Updating subscription: {sub.get('name', 'Unknown')}...")
        self.subscription_manager.update_subscriptions([sub])

    def update_all_subscriptions(self):
        """Update all enabled subscriptions."""
        if self.subscription_manager.is_update_in_progress():
            self.log(
                "Subscription update is already in progress. Please wait...",
                LogLevel.WARNING,
            )
            return

        all_subs = self.settings.get("subscriptions", [])
        enabled_subs = [sub for sub in all_subs if sub.get("enabled", True)]

        if not enabled_subs:
            self.log("No enabled subscriptions to update.", LogLevel.WARNING)
            return

        self.log(f"Updating {len(enabled_subs)} subscription(s)...")
        self.subscription_manager.update_subscriptions(enabled_subs)

    def remove_duplicate_servers(self):
        """Remove duplicate servers from all groups."""
        reply = QMessageBox.question(
            self,
            self.tr("Remove Duplicates"),
            self.tr(
                "This will remove all duplicate servers based on their configuration. Continue?"
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self.log("Scanning for duplicate servers...", LogLevel.INFO)
            removed_count = self.server_manager.remove_duplicate_servers()

            if removed_count > 0:
                QMessageBox.information(
                    self,
                    self.tr("Duplicates Removed"),
                    self.tr("Removed {} duplicate server(s).").format(
                        removed_count),
                )
            else:
                QMessageBox.information(
                    self,
                    self.tr("No Duplicates"),
                    self.tr("No duplicate servers found."),
                )

    def show_chain_manager(self):
        """Shows the dialog to manage outbound chains."""
        current_chains = self.settings.get("outbound_chains", [])
        all_servers = self.server_manager.get_all_servers()

        dialog = ChainManagerDialog(
            self, chains=[c.copy() for c in current_chains], all_servers=all_servers
        )

        if dialog.exec() == QDialog.Accepted:
            updated_chains = dialog.get_subscriptions()  # Reusing method name
            if updated_chains != current_chains:
                self.settings["outbound_chains"] = updated_chains
                self.save_settings()
                self.log(self.tr("Outbound chains updated."))
                self.update_group_dropdown()  # Refresh groups to show/hide "Chains"

    def on_status_change(self, status, color):
        self.connection_status_text.setText(status)

        # Modern status styling based on status
        if status == self.tr("Connected"):
            self.connection_status_icon.setStyleSheet(
                """
                color: #10b981; 
                font-size: 16px;
                font-weight: bold;
                background-color: #d1fae5;
                padding: 4px 8px;
                border-radius: 6px;
            """
            )
        elif status == self.tr("Connecting..."):
            self.connecting_spinner_label.show()
            self.connecting_spinner_label.movie().start()
            self.connection_status_icon.hide()
            return
        else:  # Disconnected
            self.connection_status_icon.setStyleSheet(
                """
                color: #f59e0b; 
                font-size: 16px;
                font-weight: bold;
                background-color: #fef3c7;
                padding: 4px 8px;
                border-radius: 6px;
            """
            )

        self.connecting_spinner_label.hide()
        self.connecting_spinner_label.movie().stop()
        self.connection_status_icon.show()

    def on_connect(self, latency):
        self.on_status_change(self.tr("Connected"), "#10b981")
        self.latency_label.setText(self.tr("Latency: {} ms").format(latency))
        self.latency_label.setStyleSheet(
            """
            font-size: 12px;
            color: #10b981;
            background-color: #d1fae5;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 500;
        """
        )
        self.start_stop_button.setText(self.tr("Disconnect"))
        self.start_stop_button.setStyleSheet(
            """
            QPushButton {
                background-color: #ef4444;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: 500;
                font-size: 12px;
                min-width: 70px;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
            QPushButton:pressed {
                background-color: #b91c1c;
            }
        """
        )

    def on_stop(self):
        self.on_status_change(self.tr("Disconnected"), "#f59e0b")
        self.latency_label.setText(self.tr("Latency: N/A"))
        self.latency_label.setStyleSheet(
            """
            font-size: 12px;
            color: #6b7280;
            background-color: #f3f4f6;
            padding: 4px 8px;
            border-radius: 4px;
        """
        )
        self.ip_label.setText(self.tr("IP: N/A"))
        self.up_speed_label.setText("↑ 0 KB/s")
        self.down_speed_label.setText("↓ 0 KB/s")
        self.start_stop_button.setText(self.tr("Start"))
        self.start_stop_button.setStyleSheet(
            """
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                font-weight: 500;
                font-size: 12px;
                min-width: 70px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
        """
        )

    def on_ip_update(self, ip_address):
        self.ip_label.setText(self.tr("IP: {}").format(ip_address))
        self.ip_label.setStyleSheet(
            """
            font-size: 12px;
            color: #10b981;
            background-color: #d1fae5;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 500;
        """
        )

    def on_speed_update(self, up_speed, down_speed):
        self.up_speed_label.setText(f"↑ {self.format_speed(up_speed)}")
        self.down_speed_label.setText(f"↓ {self.format_speed(down_speed)}")

        # Update speed label colors based on speed
        if up_speed > 1024 * 1024:  # > 1MB/s
            up_color = "#10b981"
            up_bg = "#d1fae5"
        elif up_speed > 100 * 1024:  # > 100KB/s
            up_color = "#f59e0b"
            up_bg = "#fef3c7"
        else:
            up_color = "#6b7280"
            up_bg = "#f3f4f6"

        if down_speed > 1024 * 1024:  # > 1MB/s
            down_color = "#10b981"
            down_bg = "#d1fae5"
        elif down_speed > 100 * 1024:  # > 100KB/s
            down_color = "#f59e0b"
            down_bg = "#fef3c7"
        else:
            down_color = "#6b7280"
            down_bg = "#f3f4f6"

        self.up_speed_label.setStyleSheet(
            f"""
            font-size: 12px;
            color: {up_color};
            background-color: {up_bg};
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 500;
        """
        )

        self.down_speed_label.setStyleSheet(
            f"""
            font-size: 12px;
            color: {down_color};
            background-color: {down_bg};
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: 500;
        """
        )

        # Update the tray icon with the new speeds
        self.update_tray_icon(up_speed, down_speed)

    def update_tray_icon(self, up_speed, down_speed):
        """
        Dynamically creates an icon with speed information and updates the system tray.
        """
        # Use a slightly larger pixmap for better text rendering
        pixmap_size = 64
        pixmap = QPixmap(pixmap_size, pixmap_size)
        pixmap.fill(Qt.transparent)  # Transparent background

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw the base application icon
        base_icon = QIcon(":/icons/app-icon.svg")
        base_pixmap = base_icon.pixmap(QSize(pixmap_size, pixmap_size))
        painter.drawPixmap(0, 0, base_pixmap)

        # --- Text Drawing ---
        # Set a clear, small font
        font = QFont("Segoe UI", 16, QFont.Bold)
        painter.setFont(font)

        # Set text color with a slight outline for better visibility
        text_color = QColor("white")
        outline_color = QColor("black")

        # Format speed text to be compact
        up_text = self.format_speed(up_speed, compact=True)
        down_text = self.format_speed(down_speed, compact=True)

        # Define positions for text (top for upload, bottom for download)
        up_rect = QRect(0, 0, pixmap_size, pixmap_size // 2)
        down_rect = QRect(0, pixmap_size // 2, pixmap_size, pixmap_size // 2)

        # Draw outline (by drawing text slightly offset in black)
        painter.setPen(outline_color)
        painter.drawText(up_rect.translated(1, 1), Qt.AlignCenter, up_text)
        painter.drawText(down_rect.translated(1, 1), Qt.AlignCenter, down_text)

        # Draw main text
        painter.setPen(text_color)
        painter.drawText(up_rect, Qt.AlignCenter, up_text)
        painter.drawText(down_rect, Qt.AlignCenter, down_text)

        painter.end()
        self.tray_icon.setIcon(QIcon(pixmap))

    @staticmethod
    def format_speed(speed_bytes_per_sec, compact=False):
        if not compact:
            if speed_bytes_per_sec < 1024:
                return f"{speed_bytes_per_sec:.0f} B/s"
            if speed_bytes_per_sec < 1024 * 1024:
                return f"{speed_bytes_per_sec / 1024:.1f} KB/s"
            if speed_bytes_per_sec < 1024 * 1024 * 1024:
                return f"{speed_bytes_per_sec / (1024 * 1024):.2f} MB/s"
            return f"{speed_bytes_per_sec / (1024 * 1024 * 1024):.2f} GB/s"
        else:
            # Compact format for the tray icon
            if speed_bytes_per_sec < 1024 * 1024:
                return f"{speed_bytes_per_sec / 1024:.0f}K"
            if speed_bytes_per_sec < 1024 * 1024 * 1024:
                return f"{speed_bytes_per_sec / (1024 * 1024):.1f}M"
            return f"{speed_bytes_per_sec / (1024 * 1024 * 1024):.1f}G"

    # --- System Tray Icon ---

    def create_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)

        # Set Icon from resource file
        icon = QIcon(":/icons/app-icon.svg")
        self.setWindowIcon(icon)
        self.tray_icon.setIcon(icon)

        # Create Menu
        tray_menu = QMenu()
        show_action = QAction(TRAY_SHOW, self)
        show_action.triggered.connect(self.show_window)
        quit_action = QAction(TRAY_QUIT, self)
        quit_action.triggered.connect(QApplication.instance().quit)

        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_icon_activated)
        self.tray_icon.show()

    def on_tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()

    def show_window(self):
        self.show()
        self.activateWindow()

    def closeEvent(self, event):
        """Saves window state and hides to tray on close."""
        # If we are in the middle of a screen scan, show the window first
        # to prevent it from being permanently hidden if the app is quit from tray.
        if self._is_scanning_screen:
            self.show_window()
            self._is_scanning_screen = False

        # If the singbox manager is running, stop it before quitting.
        if self.singbox_manager and self.singbox_manager.is_running:
            self.singbox_manager.stop()

        if self.server_manager:
            self.server_manager.force_save_settings()

        self.save_window_geometry()
        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            "Onix is running",
            self.tr("The application is still running in the background."),
            QSystemTrayIcon.Information,
            2000,
        )

    def _handle_schedule_task(self, delay_ms, func, args):
        """Slot to handle scheduled tasks safely in the main UI thread."""
        if args:
            QTimer.singleShot(delay_ms, lambda: func(*args))
        else:
            QTimer.singleShot(delay_ms, func)

    def save_window_geometry(self):
        """Saves the window's current size, position, and maximized state."""
        if not self.server_manager:
            return
        self.settings["window_maximized"] = self.isMaximized()
        # Use saveGeometry() which returns a QByteArray
        self.settings["window_geometry"] = (
            self.saveGeometry().toBase64().data().decode("ascii")
        )
        self.server_manager.save_settings()

    def restore_window_geometry(self):
        """Restores the window's size, position, and state from settings."""
        geometry_b64 = self.settings.get("window_geometry")
        if geometry_b64:
            # Convert base64 string back to QByteArray
            self.restoreGeometry(QByteArray.fromBase64(
                geometry_b64.encode("ascii")))

        if self.settings.get("window_maximized", False):
            self.showMaximized()

    # --- Tab Animation ---
    def animate_tab_transition(self, next_index):
        """
        Animates the transition between tabs in the main stacked widget
        using a combination of slide and fade effects for a smoother experience.
        """
        current_index = self.stacked_widget.currentIndex()
        if next_index == current_index:
            return

        current_widget = self.stacked_widget.widget(current_index)
        next_widget = self.stacked_widget.widget(next_index)

        width = self.stacked_widget.width()
        slide_direction = 1

        # --- Prepare Widgets for Animation ---
        next_widget.setGeometry(0, 0, width, self.stacked_widget.height())
        next_widget.move(slide_direction * width, 0)
        next_widget.show()
        next_widget.raise_()

        # --- Opacity Effect ---
        # Get or create opacity effect for the current widget
        current_opacity_effect = current_widget.graphicsEffect()
        if not isinstance(current_opacity_effect, QGraphicsOpacityEffect):
            current_opacity_effect = QGraphicsOpacityEffect(current_widget)
            current_widget.setGraphicsEffect(current_opacity_effect)

        # Get or create opacity effect for the next widget
        next_opacity_effect = next_widget.graphicsEffect()
        if not isinstance(next_opacity_effect, QGraphicsOpacityEffect):
            next_opacity_effect = QGraphicsOpacityEffect(next_widget)
            next_widget.setGraphicsEffect(next_opacity_effect)

        # --- Create Animations ---
        # Slide animations
        anim_current = QPropertyAnimation(current_widget, b"pos")
        anim_current.setDuration(300)
        anim_current.setEndValue(QPoint(-slide_direction * width, 0))
        anim_current.setEasingCurve(QEasingCurve.InOutCubic)  # Smoother curve

        anim_next = QPropertyAnimation(next_widget, b"pos")
        anim_next.setDuration(300)
        anim_next.setEndValue(QPoint(0, 0))
        anim_next.setEasingCurve(QEasingCurve.InOutCubic)

        # Fade animations
        anim_fade_out = QPropertyAnimation(current_opacity_effect, b"opacity")
        anim_fade_out.setDuration(300)
        anim_fade_out.setStartValue(1.0)
        anim_fade_out.setEndValue(0.0)

        anim_fade_in = QPropertyAnimation(next_opacity_effect, b"opacity")
        anim_fade_in.setDuration(300)
        anim_fade_in.setStartValue(0.0)
        anim_fade_in.setEndValue(1.0)

        # --- Group and Run Animations ---
        self.animation_group = QParallelAnimationGroup(self)
        self.animation_group.addAnimation(anim_current)
        self.animation_group.addAnimation(anim_next)
        self.animation_group.addAnimation(anim_fade_out)
        self.animation_group.addAnimation(anim_fade_in)

        self.animation_group.finished.connect(
            lambda: self.stacked_widget.setCurrentIndex(next_index)
        )
        self.animation_group.start()
