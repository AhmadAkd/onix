from ui_components import RightClickMenu, ServerContextMenu, handle_text_shortcut
import settings_manager
import utils
from constants import *
import customtkinter
import subprocess
import threading
import os
import sys  # Added for PyInstaller path handling
import winreg
import ctypes
import requests
import base64
import json
import time
import glob
from PIL import Image
import io
import pystray
from pystray import MenuItem as item
from concurrent.futures import ThreadPoolExecutor
import webbrowser
from tkinter import messagebox


def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.getcwd(), relative_path)


def get_app_version():
    """Reads the version from the version.txt file."""
    try:
        version_file_path = get_resource_path('version.txt')
        with open(version_file_path, 'r', encoding='utf-8') as f:
            version = f.read().strip()
            return version
    except FileNotFoundError:
        return "dev"  # Default version for local development


# Local imports


class SingboxApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # --- Load Settings ---
        self.settings = settings_manager.load_settings()

        # --- Initialize State Variables ---
        self.singbox_process = None
        self.singbox_pid = None
        self.selected_config = None
        self.server_groups = {}
        self.selected_server_button = None
        self.selected_group = None
        self.selected_group_button = None
        self.tray_icon = None
        self.ping_executor = ThreadPoolExecutor(max_workers=20)
        self.current_config_file = None
        self.conn_status_label = None
        self.ip_label = None
        self.latency_label = None

        self.setup_appearance()

        # --- Configure Window ---
        self.geometry("1024x600")
        self.app_version = get_app_version()
        self.title(f"Onix - {self.app_version}")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- Build UI ---
        self.create_widgets()
        self.bind_shortcuts()

        # --- Cleanup ---
        self._cleanup_temp_files()

        # --- Load Data ---
        self.load_data()

    def setup_appearance(self):
        customtkinter.set_appearance_mode(
            self.settings.get("appearance_mode", "System"))
        customtkinter.set_default_color_theme(
            self.settings.get("color_theme", "green"))

    def create_widgets(self):
        # --- Main Layout ---
        connection_tab, settings_tab = self._create_main_layout()

        # --- Connection Tab Layout ---
        connection_tab.grid_columnconfigure(
            0, weight=2, minsize=250)  # Server list column
        connection_tab.grid_columnconfigure(
            1, weight=1, minsize=300)  # Management column
        connection_tab.grid_rowconfigure(0, weight=1)
        connection_tab.grid_rowconfigure(1, weight=0)  # For status bar

        # --- Create and Place Widgets ---
        self._create_server_list_ui(connection_tab)
        self._create_management_ui(connection_tab)
        self._create_status_bar(connection_tab)
        self._create_settings_tab_widgets(settings_tab)

    def _create_main_layout(self):
        tab_view = customtkinter.CTkTabview(self, anchor="w")
        tab_view.pack(expand=True, fill="both", padx=10, pady=10)
        connection_tab = tab_view.add("Connection")
        settings_tab = tab_view.add("Settings")
        return connection_tab, settings_tab

    def _create_server_list_ui(self, parent_tab):
        """Creates the UI for the left column (server list)."""
        server_list_container = customtkinter.CTkFrame(
            parent_tab, fg_color="transparent")
        server_list_container.grid(
            row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        # Make row 2 (server list) expandable
        server_list_container.grid_rowconfigure(2, weight=1)
        server_list_container.grid_columnconfigure(0, weight=1)

        # --- Group Dropdown (Row 0) ---
        self.group_dropdown = customtkinter.CTkOptionMenu(server_list_container, values=[
                                                          "No Groups"], command=self.filter_servers_by_group, font=APP_FONT)
        self.group_dropdown.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # --- Connection Controls (Row 1) ---
        conn_frame = customtkinter.CTkFrame(server_list_container)
        conn_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        conn_frame.grid_columnconfigure(0, weight=1)  # Label
        conn_frame.grid_columnconfigure((1, 2), weight=0)  # Buttons

        self.status_label = customtkinter.CTkLabel(
            conn_frame, text="No Server Selected", font=(APP_FONT[0], 14), text_color="orange", wraplength=250, justify="left")
        self.status_label.grid(row=0, column=0, padx=10,
                               pady=(5, 5), sticky="w")

        self.start_button = customtkinter.CTkButton(
            conn_frame, text="Start", command=self.start_singbox, font=APP_FONT)
        self.start_button.grid(
            row=0, column=1, padx=(0, 5), pady=5, sticky="e")

        self.stop_button = customtkinter.CTkButton(
            conn_frame, text="Stop", command=self.stop_singbox, state="disabled", font=APP_FONT)
        self.stop_button.grid(
            row=0, column=2, padx=(0, 10), pady=5, sticky="e")

        # --- Server List (Row 2) ---
        self.server_list_frame = customtkinter.CTkScrollableFrame(
            server_list_container, label_text="Servers", label_font=APP_FONT)
        self.server_list_frame.grid(row=2, column=0, sticky="nsew")
        self.server_list_frame.grid_columnconfigure(0, weight=1)

    def _create_management_ui(self, parent_tab):
        """Creates the UI for the right column (management panel)."""
        management_container = customtkinter.CTkScrollableFrame(
            parent_tab, fg_color="transparent")
        management_container.grid(
            row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        management_container.grid_columnconfigure(0, weight=1)

        # --- Subscription Management ---
        sub_frame = customtkinter.CTkFrame(management_container)
        sub_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        sub_frame.grid_columnconfigure(0, weight=1)

        customtkinter.CTkLabel(sub_frame, text="Subscription Link:", font=APP_FONT).grid(
            row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        self.sub_link_entry = customtkinter.CTkEntry(
            sub_frame, placeholder_text="Paste your subscription link here", font=APP_FONT)
        self.sub_link_entry.grid(
            row=1, column=0, padx=10, pady=(0, 5), sticky="ew")

        customtkinter.CTkLabel(sub_frame, text="Group Name (Optional):", font=APP_FONT).grid(
            row=2, column=0, padx=10, pady=(10, 0), sticky="w")
        self.group_name_entry = customtkinter.CTkEntry(
            sub_frame, placeholder_text="e.g., My Servers", font=APP_FONT)
        self.group_name_entry.grid(
            row=3, column=0, padx=10, pady=(0, 10), sticky="ew")

        self.update_button = customtkinter.CTkButton(
            sub_frame, text="Update", command=self.update_subscription, font=APP_FONT)
        self.update_button.grid(row=4, column=0, padx=10, pady=10, sticky="ew")

        self.progress_bar = customtkinter.CTkProgressBar(
            sub_frame, mode="indeterminate")
        self.progress_bar.grid(row=5, column=0, padx=10, pady=5, sticky="ew")
        self.progress_bar.grid_remove()

        # --- Group Actions ---
        actions_frame = customtkinter.CTkFrame(management_container)
        actions_frame.grid(row=1, column=0, sticky="ew", pady=10)
        actions_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.ping_button = customtkinter.CTkButton(
            actions_frame, text="Ping Group", command=self.test_all_pings, font=APP_FONT)
        self.ping_button.grid(row=0, column=0, padx=(
            10, 5), pady=10, sticky="ew")

        self.url_test_all_button = customtkinter.CTkButton(
            actions_frame, text="URL Test Group", command=self.test_all_urls, font=APP_FONT)
        self.url_test_all_button.grid(
            row=0, column=1, padx=5, pady=10, sticky="ew")

        self.sort_button = customtkinter.CTkButton(
            actions_frame, text="Sort by Ping", command=self.sort_servers, font=APP_FONT)
        self.sort_button.grid(row=0, column=2, padx=(
            5, 10), pady=10, sticky="ew")

        self.url_test_button = customtkinter.CTkButton(
            actions_frame, text="URL Test (Active)", command=self.run_url_test, font=APP_FONT, state="disabled")
        self.url_test_button.grid(
            row=1, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="ew")

        # --- Manual Add ---
        manual_frame = customtkinter.CTkFrame(management_container)
        manual_frame.grid(row=2, column=0, sticky="ew", pady=10)
        manual_frame.grid_columnconfigure(0, weight=1)

        customtkinter.CTkLabel(manual_frame, text="Add Single Server:", font=APP_FONT).grid(
            row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        self.manual_add_entry = customtkinter.CTkEntry(
            manual_frame, placeholder_text="Paste vmess://, vless://, etc.", font=APP_FONT)
        self.manual_add_entry.grid(
            row=1, column=0, padx=10, pady=(0, 5), sticky="ew")
        self.manual_add_button = customtkinter.CTkButton(
            manual_frame, text="Add Server", command=self.add_manual_server, font=APP_FONT)
        self.manual_add_button.grid(
            row=2, column=0, padx=10, pady=10, sticky="ew")

        # --- Log Textbox ---
        log_frame = customtkinter.CTkFrame(
            management_container, fg_color="transparent")
        log_frame.grid(row=3, column=0, sticky="nsew", pady=(10, 0))
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        management_container.grid_rowconfigure(3, weight=1)

        self.log_textbox = customtkinter.CTkTextbox(log_frame, font=APP_FONT)
        self.log_textbox.grid(row=0, column=0, sticky="nsew")

    def _create_status_bar(self, parent_tab):
        status_bar_frame = customtkinter.CTkFrame(parent_tab, height=30)
        status_bar_frame.grid(row=1, column=0, columnspan=2,
                              sticky="ew", padx=10, pady=(5, 0))
        status_bar_frame.grid_columnconfigure((1, 3, 5), weight=1)

        customtkinter.CTkLabel(status_bar_frame, text="Status:", font=APP_FONT, anchor="w").grid(
            row=0, column=0, padx=(10, 2), pady=5)
        self.conn_status_label = customtkinter.CTkLabel(
            status_bar_frame, text="Disconnected", text_color="orange", font=APP_FONT, anchor="w")
        self.conn_status_label.grid(
            row=0, column=1, padx=(0, 10), pady=5, sticky="w")

        customtkinter.CTkLabel(status_bar_frame, text="IP Address:", font=APP_FONT, anchor="w").grid(
            row=0, column=2, padx=(10, 2), pady=5)
        self.ip_label = customtkinter.CTkLabel(
            status_bar_frame, text="N/A", font=APP_FONT, anchor="w")
        self.ip_label.grid(row=0, column=3, padx=(0, 10), pady=5, sticky="w")

        customtkinter.CTkLabel(status_bar_frame, text="Latency:", font=APP_FONT, anchor="w").grid(
            row=0, column=4, padx=(10, 2), pady=5)
        self.latency_label = customtkinter.CTkLabel(
            status_bar_frame, text="N/A", font=APP_FONT, anchor="w")
        self.latency_label.grid(
            row=0, column=5, padx=(0, 10), pady=5, sticky="w")

    def _create_settings_tab_widgets(self, parent_tab):
        parent_tab.grid_columnconfigure(0, weight=1)
        # Allow extra space to expand
        parent_tab.grid_rowconfigure(4, weight=1)

        # --- Appearance Settings ---
        customtkinter.CTkLabel(parent_tab, text="Appearance Settings", font=(
            APP_FONT[0], 16)).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        theme_frame = customtkinter.CTkFrame(parent_tab)
        theme_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.appearance_mode_menu = customtkinter.CTkOptionMenu(theme_frame, values=[
                                                                "Light", "Dark", "System"], command=self.change_appearance_mode, font=APP_FONT)
        self.appearance_mode_menu.pack(side="left", padx=10, pady=10)

        self.color_theme_menu = customtkinter.CTkOptionMenu(theme_frame, values=[
                                                            "green", "blue", "dark-blue"], command=self.change_color_theme, font=APP_FONT)
        self.color_theme_menu.pack(side="right", padx=10, pady=10)

        self.appearance_mode_menu.set(
            self.settings.get("appearance_mode", "System"))
        self.color_theme_menu.set(self.settings.get("color_theme", "green"))

        # --- Network Settings ---
        customtkinter.CTkLabel(parent_tab, text="Network Settings", font=(
            APP_FONT[0], 16)).grid(row=2, column=0, padx=20, pady=(20, 10), sticky="w")

        network_frame = customtkinter.CTkFrame(parent_tab)
        network_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        network_frame.grid_columnconfigure(1, weight=1)

        # Connection Mode
        customtkinter.CTkLabel(network_frame, text="Connection Mode:", font=APP_FONT).grid(
            row=0, column=0, padx=10, pady=5, sticky="w")
        self.connection_mode_menu = customtkinter.CTkOptionMenu(
            network_frame, values=["Rule-Based", "Global"], font=APP_FONT)
        self.connection_mode_menu.grid(
            row=0, column=1, padx=10, pady=5, sticky="ew")
        self.connection_mode_menu.set(
            self.settings.get("connection_mode", "Rule-Based"))

        # DNS Servers
        customtkinter.CTkLabel(network_frame, text="DNS Servers:", font=APP_FONT).grid(
            row=1, column=0, padx=10, pady=5, sticky="w")
        self.dns_entry = customtkinter.CTkEntry(network_frame, font=APP_FONT)
        self.dns_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.dns_entry.insert(0, self.settings.get(
            "dns_servers", "1.1.1.1,8.8.8.8"))

        # Bypass Domains
        customtkinter.CTkLabel(network_frame, text="Bypass Domains:", font=APP_FONT).grid(
            row=2, column=0, padx=10, pady=5, sticky="w")
        self.bypass_domains_entry = customtkinter.CTkEntry(
            network_frame, font=APP_FONT)
        self.bypass_domains_entry.grid(
            row=2, column=1, padx=10, pady=5, sticky="ew")
        self.bypass_domains_entry.insert(0, self.settings.get(
            "bypass_domains", "domain:geosite:tld-ir,*.ir,*.local"))

        # Bypass IPs
        customtkinter.CTkLabel(network_frame, text="Bypass IPs:", font=APP_FONT).grid(
            row=3, column=0, padx=10, pady=5, sticky="w")
        self.bypass_ips_entry = customtkinter.CTkEntry(
            network_frame, font=APP_FONT)
        self.bypass_ips_entry.grid(
            row=3, column=1, padx=10, pady=5, sticky="ew")
        self.bypass_ips_entry.insert(0, self.settings.get(
            "bypass_ips", "geoip:ir,192.168.0.0/16,127.0.0.1,10.0.0.0/8"))

        # --- About Button ---
        about_button = customtkinter.CTkButton(
            parent_tab,
            text="About Onix",
            command=self.show_about_window
        )
        about_button.grid(row=5, column=0, padx=20, pady=20, sticky="s")

    def bind_shortcuts(self):
        right_click_menu = RightClickMenu(self)
        self.sub_link_entry.bind("<Button-3>", right_click_menu.popup)
        self.group_name_entry.bind("<Button-3>", right_click_menu.popup)
        self.log_textbox.bind("<Button-3>", right_click_menu.popup)

        self.manual_add_entry.bind("<Button-3>", right_click_menu.popup)
        self.dns_entry.bind("<Button-3>", right_click_menu.popup)
        self.bypass_domains_entry.bind("<Button-3>", right_click_menu.popup)
        self.bypass_ips_entry.bind("<Button-3>", right_click_menu.popup)

        self.bind_all(
            "<Control-x>", lambda e: handle_text_shortcut(self.focus_get(), 'cut'))
        self.bind_all(
            "<Control-c>", lambda e: handle_text_shortcut(self.focus_get(), 'copy'))
        self.bind_all(
            "<Control-v>", lambda e: handle_text_shortcut(self.focus_get(), 'paste'))
        self.bind_all(
            "<Control-a>", lambda e: handle_text_shortcut(self.focus_get(), 'select_all'))

        self.bind_all("<Control-s>", self.start_stop_toggle)
        self.bind_all("<Control-u>", self.update_subscription)
        self.bind_all("<Control-q>", self.quit_application)

    def _cleanup_temp_files(self):
        """Removes leftover temporary config files from previous sessions."""
        try:
            # Use glob to find all temp config files
            temp_files = glob.glob("temp_config_*.json")
            temp_files.extend(glob.glob("temp_url_test_config.json"))

            if not temp_files:
                return

            count = 0
            for f in temp_files:
                try:
                    os.remove(f)
                    count += 1
                except OSError as e:
                    self.log(f"Error removing temp file {f}: {e}")
            if count > 0:
                self.log(f"Removed {count} old temporary file(s).")
        except Exception as e:
            self.log(f"An error occurred during temp file cleanup: {e}")

    # --- Data & Settings Management ---
    def save_all_settings(self):
        settings = {
            "sub_link": self.sub_link_entry.get(),
            "servers": self.server_groups,
            "appearance_mode": customtkinter.get_appearance_mode(),
            "color_theme": self.color_theme_menu.get(),
            "dns_servers": self.dns_entry.get(),
            "bypass_domains": self.bypass_domains_entry.get(),
            "bypass_ips": self.bypass_ips_entry.get(),
        }
        settings_manager.save_settings(settings)

    def load_data(self):
        try:
            self.sub_link_entry.insert(0, self.settings.get("sub_link", ""))
            self.server_groups = self.settings.get("servers", {})
            if self.server_groups:
                self.populate_group_dropdown()
                self.log("Saved servers loaded successfully.")
        except Exception as e:
            self.log(f"Error loading data: {e}")

    # --- UI Update & Logging ---
    def log(self, message):
        self.log_textbox.insert("end", message + "\n")
        self.log_textbox.see("end")

    def populate_group_dropdown(self):
        groups = list(self.server_groups.keys())
        self.group_dropdown.configure(
            values=groups if groups else ["No Groups"])
        if groups:
            self.group_dropdown.set(groups[0])
            self.filter_servers_by_group(groups[0])

    def filter_servers_by_group(self, selected_group, sorted_configs=None):
        self.selected_server_button = None
        for widget in self.server_list_frame.winfo_children():
            widget.destroy()

        configs = sorted_configs if sorted_configs is not None else self.server_groups.get(
            selected_group, [])
        for i, config in enumerate(configs):
            server_frame = customtkinter.CTkFrame(
                self.server_list_frame, fg_color="transparent")
            server_frame.server_config = config
            server_frame.grid(row=i, column=0, sticky="ew", pady=1)
            server_frame.grid_columnconfigure(0, weight=1)

            name_label = customtkinter.CTkLabel(
                server_frame, text=config["name"], font=APP_FONT, anchor="w")
            name_label.grid(row=0, column=0, sticky="w", padx=5)

            ping_val = config.get("ping", "-")
            ping_text = f"{ping_val} ms" if isinstance(
                ping_val, int) and ping_val != -1 else ("Timeout" if ping_val == -1 else "- ms")
            ping_label = customtkinter.CTkLabel(
                server_frame, text=ping_text, font=APP_FONT, anchor="e", width=80)
            ping_label.grid(row=0, column=1, sticky="e", padx=5)

            context_menu = ServerContextMenu(
                self, config, ping_label, self._ping_thread_task, self._url_test_thread_task, self.delete_server, self.edit_server)

            server_frame.bind("<Button-3>", context_menu.popup)
            name_label.bind("<Button-3>", context_menu.popup)
            ping_label.bind("<Button-3>", context_menu.popup)

            server_frame.bind("<Button-1>", lambda e, c=config,
                              f=server_frame: self.select_server(c, f))
            name_label.bind("<Button-1>", lambda e, c=config,
                            f=server_frame: self.select_server(c, f))
            ping_label.bind("<Button-1>", lambda e, c=config,
                            f=server_frame: self.select_server(c, f))

    def select_server(self, config, frame_widget):
        if self.selected_server_button is not None:
            self.selected_server_button.configure(fg_color="transparent")

        frame_widget.configure(fg_color=("gray85", "gray25"))
        self.selected_server_button = frame_widget
        self.selected_config = config
        self.log(f"Server selected: {config['name']}")
        self.status_label.configure(
            text=f"Selected: {config['name']}", text_color="orange")

    def delete_server(self, config_to_delete):
        """Deletes a server from the list and saves the changes."""
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete server '{config_to_delete.get('name')}'?"):
            return

        group_name = config_to_delete.get("group")
        if not group_name or group_name not in self.server_groups:
            self.log(
                f"Error: Could not find group for server {config_to_delete.get('name')}.")
            return

        # Find and remove the server
        initial_len = len(self.server_groups[group_name])
        self.server_groups[group_name] = [
            s for s in self.server_groups[group_name] if s != config_to_delete
        ]
        final_len = len(self.server_groups[group_name])

        if final_len < initial_len:
            self.log(f"Deleted server: {config_to_delete.get('name')}")

            # If the group is now empty, remove it
            if not self.server_groups[group_name]:
                del self.server_groups[group_name]
                self.log(f"Removed empty group: {group_name}")
                # Refresh dropdown if a group was removed
                self.populate_group_dropdown()

            # Refresh the currently displayed list
            current_group = self.group_dropdown.get()
            if current_group == group_name:
                self.filter_servers_by_group(current_group)
            elif not self.server_groups:  # If all groups are gone
                self.filter_servers_by_group("No Groups")

            # If the deleted server was the selected one, clear selection
            if self.selected_config == config_to_delete:
                self.selected_config = None
                self.selected_server_button = None
                self.status_label.configure(
                    text="No Server Selected", text_color="orange")

            self.save_all_settings()
        else:
            self.log(
                f"Error: Could not find server {config_to_delete.get('name')} to delete.")

    def edit_server(self, config_to_edit):
        """Opens a dialog to edit the server's name."""
        dialog = customtkinter.CTkInputDialog(
            text="Enter new server name:",
            title="Edit Server Name"
        )
        # To make the dialog appear on top of the main window
        dialog.after(10, dialog.lift)
        new_name = dialog.get_input()

        if new_name and new_name.strip():
            old_name = config_to_edit['name']
            config_to_edit['name'] = new_name.strip()
            self.log(f"Renamed server '{old_name}' to '{new_name.strip()}'.")

            # Refresh the UI
            current_group = self.group_dropdown.get()
            self.filter_servers_by_group(current_group)

            # Save changes
            self.save_all_settings()

    def add_manual_server(self):
        server_link = self.manual_add_entry.get()
        if not server_link:
            self.log("Please paste a server link to add.")
            return

        config = utils.parse_server_link(server_link)
        if not config:
            self.log(f"Failed to parse server link: {server_link}")
            return

        # --- Duplicate Check ---
        server_id = f"{config.get('server')}:{config.get('port')}"
        for group in self.server_groups.values():
            for s_config in group:
                if f"{s_config.get('server')}:{s_config.get('port')}" == server_id:
                    self.log(
                        f"Server {config.get('name')} already exists. Skipping.")
                    return
        # --- End Duplicate Check ---

        group_name = config.get("group", "Manual Servers")
        if group_name not in self.server_groups:
            self.server_groups[group_name] = []

        self.server_groups[group_name].append(config)
        self.log(
            f"Added server '{config.get('name')}' to group '{group_name}'.")

        # Refresh UI and save
        self.populate_group_dropdown()
        self.filter_servers_by_group(self.group_dropdown.get())  # Refresh list
        self.save_all_settings()
        self.manual_add_entry.delete(0, "end")  # Clear entry

    # --- Core Functionality ---
    def update_subscription(self, event=None):
        sub_link = self.sub_link_entry.get()
        if not sub_link:
            self.log("Please enter a subscription link first.")
            return

        self.log_textbox.delete("1.0", "end")
        self.log("Updating from subscription link...")
        self.progress_bar.grid()
        self.progress_bar.start()

        threading.Thread(target=self._update_subscription_task,
                         daemon=True).start()

    def _update_subscription_task(self):
        sub_link = self.sub_link_entry.get()
        custom_group_name = self.group_name_entry.get().strip()
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(sub_link, headers=headers, timeout=10)
            response.raise_for_status()

            base64_text = response.text.strip()
            decoded_content = base64.b64decode(base64_text).decode('utf-8')
            server_links = decoded_content.splitlines()

            # --- Duplicate Check Setup ---
            existing_server_ids = set()
            for group in self.server_groups.values():
                for s_config in group:
                    s_id = f"{s_config.get('server')}:{s_config.get('port')}"
                    existing_server_ids.add(s_id)
            # --- End Duplicate Check Setup ---

            temp_groups = {}
            server_count = 0
            skipped_count = 0

            for link in server_links:
                config = utils.parse_server_link(link)
                if config:
                    # --- Duplicate Check ---
                    server_id = f"{config.get('server')}:{config.get('port')}"
                    if server_id in existing_server_ids:
                        skipped_count += 1
                        continue
                    # --- End Duplicate Check ---

                    # Add to set to check against others in the same subscription
                    existing_server_ids.add(server_id)
                    server_count += 1
                    group_name = custom_group_name if custom_group_name else config["group"]
                    if group_name not in temp_groups:
                        temp_groups[group_name] = []
                    config["group"] = group_name
                    temp_groups[group_name].append(config)

            self.server_groups.update(temp_groups)
            self.after(0, self.populate_group_dropdown)

            log_message = f"Successfully loaded {server_count} new servers."
            if skipped_count > 0:
                log_message += f" Skipped {skipped_count} duplicate(s)."
            self.after(0, self.log, log_message)

            self.save_all_settings()

        except Exception as e:
            self.after(0, self.log, f"Failed to update subscription: {e}")
        finally:
            self.after(0, self.progress_bar.stop)
            self.after(0, self.progress_bar.grid_remove)

    def start_singbox(self):
        if not self.selected_config:
            self.log("Please select a server first!")
            return

        if self.singbox_process and self.singbox_process.poll() is None:
            self.log("Switching servers... Stopping previous connection first.")
            self.stop_singbox()
            time.sleep(0.5)

        self.current_config_file = f"temp_config_{int(time.time()*1000)}.json"

        self.log_textbox.delete("1.0", "end")
        self.log("Starting connection...")
        self.status_label.configure(text="Connecting...", text_color="yellow")

        threading.Thread(target=self._run_singbox_and_log_output, args=(
            self.selected_config, self.current_config_file), daemon=True).start()
        self.after(2000, self.check_connection_status)

    def _run_singbox_and_log_output(self, config_to_run, config_filename):
        try:
            # 1. Generate config
            full_config = utils.generate_config_json(
                config_to_run, self.settings)
            with open(config_filename, 'w', encoding='utf-8') as f:
                json.dump(full_config, f, indent=2)

            # 2. Validate config
            self.after(0, self.log, "Validating configuration...")
            check_command = [get_resource_path(
                'sing-box.exe'), 'check', '-c', config_filename]
            result = subprocess.run(check_command, capture_output=True, text=True,
                                    encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW)

            if result.returncode != 0:
                error_message = result.stdout.strip() or result.stderr.strip()
                self.after(0, self.log, "Configuration check failed!")
                self.after(0, self.log, f"Error: {error_message}")
                self.after(0, self.stop_singbox)  # Clean up
                return

            self.after(
                0, self.log, "Configuration is valid. Starting process...")

            # 3. Run process
            command = [get_resource_path(
                'sing-box.exe'), 'run', '-c', config_filename]
            self.singbox_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                                    text=True, encoding='utf-8', creationflags=subprocess.CREATE_NO_WINDOW)
            self.singbox_pid = self.singbox_process.pid  # Store PID

            for line in iter(self.singbox_process.stdout.readline, ''):
                self.after(0, self.log, line.strip())

        except FileNotFoundError:
            singbox_path = get_resource_path(
                'sing-box.exe')  # Get path again for logging
            self.after(
                0, self.log, f"Error: sing-box.exe not found at '{singbox_path}'!")
        except Exception as e:
            self.after(
                0, self.log, f"An unexpected error occurred: {type(e).__name__}: {e}")

    def stop_singbox(self):
        pid_to_kill = self.singbox_pid
        process_to_kill = self.singbox_process

        # Reset state immediately
        self.singbox_process = None
        self.singbox_pid = None

        if process_to_kill and process_to_kill.poll() is None:
            try:
                process_to_kill.kill()
                self.log("Sing-box process terminated.")
            except Exception as e:
                self.log(
                    f"Failed to terminate process object: {e}. Falling back to PID kill.")
                if pid_to_kill:
                    try:
                        subprocess.run(["taskkill", "/F", "/PID", str(pid_to_kill)], check=False,
                                       capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                        self.log(
                            f"Killed process with PID {pid_to_kill} as a fallback.")
                    except Exception as kill_e:
                        self.log(f"Fallback PID kill failed: {kill_e}")
        elif pid_to_kill:
            self.log(
                f"Process object not active, attempting to clean up PID {pid_to_kill}.")
            try:
                # Use timeout to prevent hanging, capture output to hide it
                result = subprocess.run(["taskkill", "/F", "/PID", str(pid_to_kill)], check=False,
                                        capture_output=True, timeout=5, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
                # taskkill exit code is 0 on success, 128 if process not found.
                if result.returncode == 0:
                    self.log(
                        f"Cleaned up lingering process with PID {pid_to_kill}.")
            except Exception as e:
                self.log(f"Error during lingering process cleanup: {e}")

        try:
            if self.current_config_file and os.path.exists(self.current_config_file):
                os.remove(self.current_config_file)
        except OSError as e:
            self.log(f"Error removing config file: {e}")

        self.set_system_proxy(False)
        status_text = f"Selected: {self.selected_config['name'] if self.selected_config else 'None'}"
        self.status_label.configure(text=status_text, text_color="orange")
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.url_test_button.configure(state="disabled")
        self.conn_status_label.configure(
            text="Disconnected", text_color="orange")
        self.ip_label.configure(text="N/A")
        self.latency_label.configure(text="N/A")

    def _fetch_ip_and_update_statusbar(self):
        ip_address = utils.get_external_ip(PROXY_SERVER_ADDRESS)

        def update_ui():
            self.ip_label.configure(text=ip_address)
        self.after(0, update_ui)

    def check_connection_status(self):
        result = utils.url_test(PROXY_SERVER_ADDRESS)
        if result != -1:
            self.status_label.configure(
                text=f"Running: {self.selected_config['name']}", text_color="lightgreen")
            self.log(f"Connection successful! Latency: {result} ms.")
            self.set_system_proxy(True)
            self.start_button.configure(state="disabled")
            self.stop_button.configure(state="normal")
            self.url_test_button.configure(state="normal")
            self.conn_status_label.configure(
                text="Connected", text_color="lightgreen")
            self.latency_label.configure(text=f"{result} ms")
            threading.Thread(
                target=self._fetch_ip_and_update_statusbar, daemon=True).start()
        else:
            self.status_label.configure(
                text="Connection Failed", text_color="red")
            self.log("Error: Connection test failed. Check server config.")
            self.stop_singbox()

    def start_stop_toggle(self, event=None):
        if (self.singbox_process is None) or (self.singbox_process.poll() is not None):
            self.start_singbox()
        else:
            self.stop_singbox()

    # --- Ping & URL Tests ---
    def _ping_thread_task(self, config, ping_label):
        ping_label.configure(text="...", text_color="gray")
        ping_result = utils.tcp_ping(config["server"], config["port"])
        config["ping"] = ping_result

        def update_ui():
            if ping_label.winfo_exists():
                if ping_result != -1:
                    color = "lightgreen" if ping_result < 200 else "orange" if ping_result < 500 else "red"
                    ping_label.configure(
                        text=f"{ping_result} ms", text_color=color)
                else:
                    ping_label.configure(text="Timeout", text_color="red")
        self.after(0, update_ui)

    def _url_test_thread_task(self, config, ping_label):
        ping_label.configure(text="...", text_color="gray")
        result = utils.run_single_url_test(config, self.settings)
        config["ping"] = result

        def update_ui():
            if ping_label.winfo_exists():
                if result != -1:
                    color = "lightgreen" if result < 1000 else "orange" if result < 3000 else "red"
                    ping_label.configure(text=f"{result} ms", text_color=color)
                else:
                    ping_label.configure(text="Failed", text_color="red")
        self.after(0, update_ui)

    def test_all_pings(self):
        self.log("Starting TCP ping for all visible servers...")
        for server_frame in self.server_list_frame.winfo_children():
            config = server_frame.server_config
            ping_label = server_frame.grid_slaves(row=0, column=1)[0]
            self.ping_executor.submit(
                self._ping_thread_task, config, ping_label)

    def test_all_urls(self):
        self.log(
            "Starting URL test. This process is SLOW and may take several minutes.")
        all_frames = list(self.server_list_frame.winfo_children())

        def sequential_test_task():
            for server_frame in all_frames:
                if server_frame.winfo_exists():
                    config = server_frame.server_config
                    ping_label = server_frame.grid_slaves(row=0, column=1)[0]
                    self._url_test_thread_task(config, ping_label)
                    time.sleep(0.5)  # Avoid overwhelming the system
        threading.Thread(target=sequential_test_task, daemon=True).start()

    def run_url_test(self):
        if self.singbox_process is None or self.singbox_process.poll() is not None:
            self.log("URL Test failed: Not connected.")
            return
        self.log("Running URL test on current connection...")
        self.url_test_button.configure(state="disabled", text="Testing...")

        def task():
            result = utils.url_test(PROXY_SERVER_ADDRESS)

            def update_ui():
                if result != -1:
                    self.log(
                        f"URL Test successful! Response time: {result} ms")
                else:
                    self.log(
                        "URL Test failed: Could not reach test URL via proxy.")
                if self.singbox_process is not None and self.singbox_process.poll() is None:
                    self.url_test_button.configure(
                        state="normal", text="URL Test")
            self.after(0, update_ui)
        threading.Thread(target=task, daemon=True).start()

    def sort_servers(self):
        current_group = self.group_dropdown.get()
        if not current_group or current_group == "No Groups":
            self.log("No servers to sort.")
            return

        configs = self.server_groups.get(current_group, [])
        configs.sort(key=lambda c: c.get("ping", 9999)
                     if c.get("ping", 9999) != -1 else 99999)

        self.filter_servers_by_group(current_group, sorted_configs=configs)
        self.log("Servers sorted by ping (fastest first).")

    # --- System & Window Management ---
    def set_system_proxy(self, enable):
        try:
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Internet Settings"
            internet_settings = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
            if enable:
                # Combine default bypass with user-defined domains for the system setting
                user_domains = self.settings.get("bypass_domains", "")
                bypass_list = PROXY_BYPASS
                if user_domains:
                    # System proxy bypass list is semicolon-separated
                    user_domains_semicolon = ";".join(
                        d.strip() for d in user_domains.split(','))
                    bypass_list = f"{PROXY_BYPASS};{user_domains_semicolon}"

                winreg.SetValueEx(internet_settings,
                                  "ProxyEnable", 0, winreg.REG_DWORD, 1)
                winreg.SetValueEx(internet_settings, "ProxyServer",
                                  0, winreg.REG_SZ, PROXY_SERVER_ADDRESS)
                winreg.SetValueEx(
                    internet_settings,
                    "ProxyOverride", 0, winreg.REG_SZ, bypass_list)
            else:
                winreg.SetValueEx(internet_settings,
                                  "ProxyEnable", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(internet_settings)

            ctypes.windll.Wininet.InternetSetOptionW(
                0, 39, 0, 0)  # INTERNET_OPTION_SETTINGS_CHANGED
            ctypes.windll.Wininet.InternetSetOptionW(
                0, 37, 0, 0)  # INTERNET_OPTION_REFRESH
        except Exception as e:
            self.log(f"Failed to set system proxy: {e}")

    def change_appearance_mode(self, new_mode):
        customtkinter.set_appearance_mode(new_mode)
        self.save_all_settings()

    def change_color_theme(self, new_theme):
        self.log("Color theme changed. Please restart the app to see full effect.")
        self.color_theme_menu.set(new_theme)
        self.save_all_settings()

    def on_closing(self):
        self.save_all_settings()
        if self.singbox_process is not None and self.singbox_process.poll() is None:
            threading.Thread(target=self.hide_window, daemon=True).start()
        else:
            self.quit_application()

    def quit_application(self, event=None):
        self.ping_executor.shutdown(wait=False, cancel_futures=True)
        self.stop_singbox()  # Stop sing-box process before quitting
        if self.tray_icon and self.tray_icon.visible:
            self.tray_icon.stop()
        self.quit()

    def show_window(self, icon, item):
        if self.tray_icon:
            self.tray_icon.stop()
        self.after(0, self.deiconify)

    def hide_window(self):
        self.withdraw()
        image_data = base64.b64decode(ICON_BASE64)
        image = Image.open(io.BytesIO(image_data))
        menu = (item('Show', self.show_window),
                item('Quit', self.quit_application))
        self.tray_icon = pystray.Icon(
            "Sing-box Client", image, "Sing-box Client", menu)
        self.tray_icon.run()

    def show_about_window(self):
        """Displays the About window."""
        # Prevent multiple about windows
        if hasattr(self, 'about_win') and self.about_win.winfo_exists():
            self.about_win.lift()
            return

        self.about_win = customtkinter.CTkToplevel(self)
        self.about_win.title("About Onix")
        self.about_win.geometry("350x220")
        self.about_win.resizable(False, False)
        self.about_win.transient(self)  # Keep on top of the main window

        self.about_win.grid_columnconfigure(0, weight=1)

        title_label = customtkinter.CTkLabel(
            self.about_win, text="Onix", font=customtkinter.CTkFont(size=24, weight="bold"))
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        version_label = customtkinter.CTkLabel(
            self.about_win, text=f"Version: {self.app_version}", font=APP_FONT)
        version_label.grid(row=1, column=0, padx=20, pady=0)

        def open_releases_page(e):
            webbrowser.open_new("https://github.com/AhmadAkd/onix/releases")

        link_label = customtkinter.CTkLabel(
            self.about_win, text="GitHub Releases Page", text_color=("blue", "cyan"), cursor="hand2", font=customtkinter.CTkFont(underline=True))
        link_label.grid(row=2, column=0, padx=20, pady=10)
        link_label.bind("<Button-1>", open_releases_page)

        ok_button = customtkinter.CTkButton(
            self.about_win, text="OK", command=self.about_win.destroy, width=100)
        ok_button.grid(row=3, column=0, padx=20, pady=20)


if __name__ == "__main__":
    app = SingboxApp()
    app.mainloop()
