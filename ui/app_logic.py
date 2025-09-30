import threading
import mss
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import os

from PySide6.QtWidgets import QApplication, QMessageBox, QFileDialog, QDialog
from PySide6.QtCore import QTimer

from constants import LogLevel, SINGBOX_LOG_FILE
from ui.dialogs.about import AboutDialog
from ui.dialogs.server_edit import ServerEditDialog
from ui.dialogs.qr_code import QRCodeDialog
from ui.dialogs.subscription import SubscriptionManagerDialog
from ui.dialogs.chain_manager import ChainManagerDialog
import utils

class AppLogic:
    def __init__(self, main_window, server_manager, singbox_manager):
        self.main_window = main_window
        self.server_manager = server_manager
        self.singbox_manager = singbox_manager
        self.settings = self.server_manager.settings

    def log(self, message, level=LogLevel.INFO):
        """Helper to access the main window's logger."""
        self.main_window.log(message, level)

    # ... (existing methods) ...
    def handle_update_subscriptions(self):
        """Delegate to main window's subscription manager."""
        self.main_window.handle_update_subscriptions()

    def url_ping_all_servers(self):
        current_group = self.main_window.group_dropdown.currentText()
        if not current_group:
            return
        servers_to_test = self.server_manager.get_servers_by_group(current_group)
        if servers_to_test:
            self.server_manager.test_all_urls(servers_to_test)

    def ping_all_servers(self):
        current_group = self.main_window.group_dropdown.currentText()
        if not current_group:
            return
        servers_to_test = self.server_manager.get_servers_by_group(current_group)
        if servers_to_test:
            self.server_manager.test_all_tcp(servers_to_test)

    def cancel_all_tests(self):
        if self.server_manager:
            self.server_manager.cancel_tests()

    def start_stop_toggle(self):
        if self.singbox_manager.is_running:
            self.singbox_manager.stop()
        else:
            if self.main_window.selected_config:
                self.singbox_manager.start(self.main_window.selected_config)
            else:
                self.log(self.main_window.tr("No server selected!"))

    def handle_server_action(self, action, server_data):
        if action == "ping_url":
            self.log(self.main_window.tr("Latency testing server: {}").format(server_data.get('name')))
            self.server_manager.test_all_urls([server_data])
        elif action == "ping_tcp":
            self.log(self.main_window.tr("Latency testing server: {}").format(server_data.get('name')))
            self.server_manager.test_all_tcp([server_data])
        elif action == "delete":
            reply = QMessageBox.question(self.main_window, self.main_window.tr("Confirm Deletion"),
                                         self.main_window.tr("Are you sure you want to delete server\n'{}'?").format(server_data.get('name')))
            if reply == QMessageBox.Yes:
                self.server_manager.delete_server(server_data)
                self.main_window.update_server_list()
                if self.main_window.selected_config and self.main_window.selected_config.get("id") == server_data.get("id"):
                    self.main_window.selected_config = None
        elif action == "edit_server":
            dialog = ServerEditDialog(self.main_window, server_config=server_data)
            if dialog.exec() == QDialog.Accepted:
                updated_config = dialog.get_updated_config()
                self.server_manager.edit_server_config(server_data, updated_config)
                self.main_window.update_server_list()
        elif action == "copy_link":
            server_link = self.server_manager.get_server_link(server_data)
            if server_link:
                clipboard = QApplication.clipboard()
                clipboard.setText(server_link)
                self.log(self.main_window.tr("Copied link for '{}' to clipboard.").format(server_data.get('name')))
            else:
                self.log(self.main_window.tr("Could not generate a link for '{}'.").format(server_data.get('name')), LogLevel.WARNING)
        elif action == "qr_code":
            server_link = self.server_manager.get_server_link(server_data)
            if server_link:
                dialog = QRCodeDialog(server_link, server_data.get('name'), self.main_window)
                dialog.exec()
            else:
                QMessageBox.warning(self.main_window, self.main_window.tr("Error"), self.main_window.tr("Could not generate a link for this server."))

    def import_from_clipboard(self):
        clipboard = QApplication.clipboard()
        text = clipboard.text()
        if not text:
            self.log(self.main_window.tr("Clipboard is empty."), "warning")
            return
        links = text.strip().splitlines()
        added_count = 0
        for link in links:
            if self.server_manager.add_manual_server(link.strip()):
                added_count += 1
        self.log(self.main_window.tr("Imported {} server(s) from clipboard.").format(added_count))

    def handle_import_wireguard_config(self):
        file_path, _ = QFileDialog.getOpenFileName(self.main_window, self.main_window.tr("Import WireGuard Config"), "", self.main_window.tr("Config Files (*.conf)"))
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.server_manager.add_wireguard_config(content, file_path)
            except Exception as e:
                self.log(self.main_window.tr("Failed to read or parse WireGuard file: {}").format(e), LogLevel.ERROR)
                QMessageBox.critical(self.main_window, self.main_window.tr("Import Error"), self.main_window.tr("Could not import the WireGuard file:\n{}").format(e))

    def handle_scan_qr_from_screen(self):
        self.main_window._is_scanning_screen = True
        self.log(self.main_window.tr("Scanning screen for QR code..."))
        self.main_window.hide()
        QTimer.singleShot(300, self._start_scan_task)

    def _start_scan_task(self):
        threading.Thread(target=self._scan_and_add_task, daemon=True).start()

    def _scan_and_add_task(self):
        try:
            with mss.mss() as sct:
                monitor_info = sct.monitors[1]
                sct_img = sct.grab(monitor_info)
                img = np.frombuffer(sct_img.rgb, np.uint8).reshape((sct_img.height, sct_img.width, 3))
            decoded_objects = decode(img)
            if decoded_objects:
                link = decoded_objects[0].data.decode('utf-8')
                self.server_manager.add_manual_server(link)
            else:
                self.log(self.main_window.tr("No QR code found on the screen."), LogLevel.WARNING)
        finally:
            QTimer.singleShot(0, self.main_window.show_window)
            self.main_window._is_scanning_screen = False

    def copy_group_links_to_clipboard(self):
        if not self.server_manager:
            self.log("Server manager not initialized.", "error")
            return
        if self.main_window.server_list_widget.count() == 0:
            self.log(self.main_window.tr("No visible servers to copy."), LogLevel.WARNING)
            QMessageBox.warning(self.main_window, self.main_window.tr("Copy Links"), self.main_window.tr("There are no servers in the list to copy."))
            return
        visible_servers = []
        for i in range(self.main_window.server_list_widget.count()):
            item = self.main_window.server_list_widget.item(i)
            card = self.main_window.server_list_widget.itemWidget(item)
            if card:
                visible_servers.append(card.server_data)
        if not visible_servers:
            self.log(self.main_window.tr("Could not retrieve server data from the list."), LogLevel.ERROR)
            return
        links = [self.server_manager.get_server_link(s) for s in visible_servers if self.server_manager.get_server_link(s)]
        if links:
            clipboard = QApplication.clipboard()
            clipboard.setText("\n".join(links))
            QMessageBox.information(self.main_window, self.main_window.tr("Copy Successful"), self.main_window.tr("Copied {} server link(s) to clipboard.").format(len(links)))
        else:
            QMessageBox.warning(self.main_window, self.main_window.tr("Copy Failed"), self.main_window.tr("Could not generate links for the visible servers."))

    def delete_current_group(self):
        current_group = self.main_window.group_dropdown.currentText()
        if not current_group:
            self.log(self.main_window.tr("No group selected to delete."), LogLevel.WARNING)
            return
        reply = QMessageBox.question(self.main_window, self.main_window.tr("Confirm Group Deletion"),
                                     self.main_window.tr("Are you sure you want to delete the entire group '{}' and all its servers?").format(current_group),
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes and self.server_manager:
            self.server_manager.delete_group(current_group)

    def show_about_dialog(self):
        dialog = AboutDialog(self.main_window)
        dialog.exec()

    def handle_clear_core_log(self):
        log_file_path = SINGBOX_LOG_FILE
        if not os.path.exists(log_file_path):
            QMessageBox.information(self.main_window, self.main_window.tr("Log File"),
                                    self.main_window.tr("Core log file does not exist. Nothing to clear."))
            self.log(self.main_window.tr("Core log file not found, nothing to clear."), LogLevel.INFO)
            return

        reply = QMessageBox.question(
            self.main_window,
            self.main_window.tr("Confirm Clear"),
            self.main_window.tr("""Are you sure you want to delete the core log file?
({})

This action cannot be undone.""" ).format(log_file_path),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                os.remove(log_file_path)
                self.log(self.main_window.tr("Successfully deleted {}").format(log_file_path), LogLevel.SUCCESS)
            except OSError as e:
                self.log(self.main_window.tr("Failed to delete log file: {}").format(e), LogLevel.ERROR)

    def handle_import_profile(self):
        file_path, _ = QFileDialog.getOpenFileName(self.main_window, self.main_window.tr("Import Profile"), "", self.main_window.tr("JSON Files (*.json)"))
        if file_path:
            success = self.server_manager.import_settings(file_path)
            if success:
                QMessageBox.information(self.main_window, self.main_window.tr("Import Successful"), self.main_window.tr("Profile imported successfully. Please restart the application for the changes to take full effect."))
            else:
                QMessageBox.critical(self.main_window, self.main_window.tr("Import Failed"), self.main_window.tr("The selected file is not a valid Onix profile or is corrupted."))

    def handle_export_profile(self):
        file_path, _ = QFileDialog.getSaveFileName(self.main_window, self.main_window.tr("Export Profile"), "onix_profile.json", self.main_window.tr("JSON Files (*.json)"))
        if file_path:
            success = self.server_manager.export_settings(file_path)
            if success:
                QMessageBox.information(self.main_window, self.main_window.tr("Export Successful"), self.main_window.tr("Profile successfully exported to:\n{}").format(file_path))

    def handle_check_for_updates(self):
        self.log(self.main_window.tr("Checking for core updates..."))
        self.main_window.check_updates_button.setEnabled(False)
        self.main_window.check_updates_button.setText(self.main_window.tr("Checking..."))
        threading.Thread(target=self._run_update_check, daemon=True).start()

    def _run_update_check(self):
        update_callbacks = {
            'show_info': self.main_window.signals.show_info_message.emit,
            'show_warning': self.main_window.signals.show_warning_message.emit,
            'show_error': self.main_window.signals.show_error_message.emit,
            'ask_yes_no': self.main_window.ask_yes_no_from_thread,
        }
        active_core = self.settings.get("active_core", "sing-box")
        utils.download_core_if_needed(core_name=active_core, force_update=True, callbacks=update_callbacks)
        QTimer.singleShot(0, lambda: self._update_check_updates_button(True, self.main_window.tr("Check for Core Updates")))

    def _update_check_updates_button(self, enabled, text):
        self.main_window.check_updates_button.setEnabled(enabled)
        self.main_window.check_updates_button.setText(text)

    def show_subscription_manager(self):
        current_subs = self.settings.get("subscriptions", [])
        dialog = SubscriptionManagerDialog(self.main_window, subscriptions=[sub.copy() for sub in current_subs])
        if dialog.exec() == QDialog.Accepted:
            updated_subs = dialog.get_subscriptions()
            if updated_subs is not None:
                self.settings["subscriptions"] = updated_subs
                self.save_settings()
                self.log(self.main_window.tr("Subscription list updated."))
                reply = QMessageBox.question(self.main_window, self.main_window.tr("Update Subscriptions"),
                                             self.main_window.tr("Subscription list has changed. Do you want to update all enabled subscriptions now?"),
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
                if reply == QMessageBox.Yes:
                    self.handle_update_subscriptions()

    def show_chain_manager(self):
        current_chains = self.settings.get("outbound_chains", [])
        all_servers = self.server_manager.get_all_servers()
        dialog = ChainManagerDialog(self.main_window, chains=[c.copy() for c in current_chains], all_servers=all_servers)
        if dialog.exec() == QDialog.Accepted:
            updated_chains = dialog.get_subscriptions()  # Reusing method name
            if updated_chains != current_chains:
                self.settings["outbound_chains"] = updated_chains
                self.save_settings()
                self.log(self.main_window.tr("Outbound chains updated."))
                self.main_window.update_group_dropdown()  # Refresh groups to show/hide "Chains"

    # --- Settings Logic ---
    def _validate_and_save_setting(self, widget, setting_key, setting_name, validation_type="int"):
        value = widget.text().strip()
        try:
            if validation_type == "int":
                self.settings[setting_key] = int(value)
            elif validation_type == "range":
                parts = [int(x.strip()) for x in value.split('-')]
                if len(parts) != 2:
                    raise ValueError("Range must be in 'min-max' format.")
                self.settings[setting_key] = value
            else:
                self.settings[setting_key] = value
            return True
        except (ValueError, TypeError):
            QMessageBox.warning(
                self.main_window,
                self.main_window.tr("Invalid Input"),
                self.main_window.tr("The value for '{}' is invalid.\n" 
                                  "Please enter a valid {}").format(setting_name, self.main_window.tr('number') if validation_type == 'int' else self.main_window.tr('range (e.g., 10-100)'))
            )
            widget.setFocus()
            return False

    def save_settings(self):
        if not self.server_manager:
            return

        self.settings["connection_mode"] = self.main_window.connection_mode_combo.currentText()
        self.settings["dns_servers"] = self.main_window.dns_entry.text()
        self.settings["bypass_domains"] = self.main_window.bypass_domains_entry.text()
        self.settings["tun_enabled"] = self.main_window.tun_checkbox.isChecked()
        self.settings["appearance_mode"] = {self.main_window.tr("System"): "System", self.main_window.tr("Light"): "Light", self.main_window.tr("Dark"): "Dark"}.get(
            self.main_window.appearance_mode_combo.currentText(), "System")

        theme_name = self.main_window.theme_combo.currentText()
        for code, name in self.main_window.theme_names.items():
            if name == theme_name:
                self.settings["theme_color"] = code
        
        lang_name = self.main_window.language_combo.currentText()
        for code, name in self.main_window.languages.items():
            if name == lang_name:
                self.settings["language"] = code
                break

        self.settings["active_core"] = self.main_window.core_selector_combo.currentText()

        if not self._validate_and_save_setting(self.main_window.mux_max_streams_entry, "mux_max_streams", "Mux Max Streams", "int"):
            return
        if not self._validate_and_save_setting(self.main_window.tls_fragment_size_entry, "tls_fragment_size", "TLS Fragment Size", "range"):
            return
        if not self._validate_and_save_setting(self.main_window.tls_fragment_sleep_entry, "tls_fragment_sleep", "TLS Fragment Sleep", "range"):
            return
        if not self._validate_and_save_setting(self.main_window.hysteria_up_speed_entry, "hysteria_up_mbps", "Hysteria Upload Speed", "int"):
            return
        if not self._validate_and_save_setting(self.main_window.hysteria_down_speed_entry, "hysteria_down_mbps", "Hysteria Download Speed", "int"):
            return

        self.settings["tls_fragment_enabled"] = self.main_window.tls_fragment_checkbox.isChecked()
        self.settings["mux_enabled"] = self.main_window.mux_enabled_checkbox.isChecked()
        self.settings["mux_protocol"] = self.main_window.mux_protocol_combo.currentText()

        self.server_manager.save_settings()
        self.log(self.main_window.tr("Settings saved."))

    def on_language_change(self, lang_name):
        lang_code = "en"
        for code, name in self.main_window.languages.items():
            if name == lang_name:
                lang_code = code
                break
        if self.settings.get("language") != lang_code:
            self.settings["language"] = lang_code
            self.main_window.restart_button.show()

    def on_core_change(self, core_name):
        if self.settings.get("active_core") != core_name:
            self.settings["active_core"] = core_name
            self.main_window.restart_button.show()

    def on_theme_change(self, theme_name):
        theme_code = "blue"
        for code, name in self.main_window.theme_names.items():
            if name == theme_name:
                theme_code = code
                break
        if self.settings.get("theme_color") != theme_code:
            self.settings["theme_color"] = theme_code
            self.main_window.restart_button.show()

    def handle_restart(self):
        self.save_settings()
        self.log(self.main_window.tr("Restarting to apply changes..."))
        QApplication.instance().setProperty("restart_requested", True)
        QApplication.instance().quit()