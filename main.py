from ui_components import RightClickMenu, ServerContextMenu, handle_text_shortcut
from managers.singbox_manager import SingboxManager
from managers.server_manager import ServerManager
import settings_manager
import system_proxy
import utils
from constants import LogLevel, APP_FONT, ICON_BASE64, PROXY_SERVER_ADDRESS
import customtkinter
import threading
import base64
from PIL import Image
import io
import pystray
from pystray import MenuItem as item
from concurrent.futures import ThreadPoolExecutor
import webbrowser
from tkinter import messagebox, filedialog
import json
from message_utils import show_error_message, show_warning_message


# Local imports


class SingboxApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # --- Download sing-box if not exists ---
        utils.download_singbox_if_needed()

        # --- Load Settings ---
        self.settings = settings_manager.load_settings()

        # --- Initialize State Variables ---
        self.selected_config = None
        # self.server_groups = {} # This will be managed by ServerManager
        self.selected_server_button = None
        self.selected_group = None
        self.selected_group_button = None
        self.tray_icon = None
        self.ping_executor = ThreadPoolExecutor(max_workers=20)
        self.conn_status_label = None
        self.ip_label = None
        self.latency_label = None
        self.server_widgets = {}  # New: To store references to server widgets

        # --- Setup Managers ---
        self.singbox_manager = self._setup_singbox_manager()
        self.server_manager = self._setup_server_manager()

        self.setup_appearance()

        # --- Configure Window ---
        self.geometry("1024x600")
        self.app_version = self._get_app_version()
        self.title(f"Onix - {self.app_version}")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- Build UI ---
        self.create_widgets()
        self.bind_shortcuts()

        # --- Load Data ---
        self.load_data()

    def _get_app_version(self):
        """Reads the version from the version.txt file."""
        try:
            version_file_path = utils.get_resource_path("version.txt")
            with open(version_file_path, "r", encoding="utf-8") as f:
                version = f.read().strip()
                return version
        except FileNotFoundError:
            return "dev"  # Default version for local development

    def _setup_singbox_manager(self):
        callbacks = {
            "log": self.log,
            "schedule": self.after,
            "on_status_change": self._on_status_change,
            "on_connect": self._on_connect,
            "on_stop": self._on_stop,
            "on_ip_update": self._on_ip_update,
        }
        return SingboxManager(self.settings, callbacks)

    def _setup_server_manager(self):
        callbacks = {
            "log": self.log,
            "schedule": self.after,
            "on_update_start": self._on_update_start,
            "on_update_finish": self._on_update_finish,
            "on_servers_loaded": self.populate_group_dropdown,
            "on_servers_updated": self.refresh_server_list_ui,
            "on_ping_result": self._on_ping_result,
            "on_error": self._on_error,
            "on_testing_start": self._on_testing_start,
            "on_testing_finish": self._on_testing_finish,
        }
        return ServerManager(self.settings, callbacks)

    # --- Singbox Manager Callbacks ---
    def _on_status_change(self, status, color):
        self.status_label.configure(text=status, text_color=color)

    def _on_connect(self, latency):
        self.status_label.configure(
            text=f"Running: {self.selected_config['name']}", text_color="lightgreen"
        )
        self.conn_status_label.configure(text="Connected", text_color="lightgreen")
        self.latency_label.configure(text=f"{latency} ms")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.url_test_button.configure(state="normal")

    def _on_stop(self):
        status_text = f"Selected: {self.selected_config['name'] if self.selected_config else 'None'}"
        self.status_label.configure(text=status_text, text_color="orange")
        self.conn_status_label.configure(text="Disconnected", text_color="orange")
        self.ip_label.configure(text="N/A")
        self.latency_label.configure(text="N/A")
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.url_test_button.configure(state="disabled")

    def _on_ip_update(self, ip_address):
        self.ip_label.configure(text=ip_address)

    def _on_error(self, title, message):
        messagebox.showerror(title, message)

    def setup_appearance(self):
        customtkinter.set_appearance_mode(self.settings.get("appearance_mode"))
        customtkinter.set_default_color_theme(self.settings.get("color_theme"))

    def create_widgets(self):
        # --- Main Layout ---
        connection_tab, settings_tab, routing_tab = self._create_main_layout()

        # --- Connection Tab Layout ---
        connection_tab.grid_columnconfigure(
            0, weight=2, minsize=250
        )  # Server list column
        connection_tab.grid_columnconfigure(
            1, weight=1, minsize=300
        )  # Management column
        connection_tab.grid_rowconfigure(0, weight=1)
        connection_tab.grid_rowconfigure(1, weight=0)  # For status bar

        # --- Create and Place Widgets ---
        self._create_server_list_ui(connection_tab)
        self._create_management_ui(connection_tab)
        self._create_status_bar(connection_tab)
        self._create_settings_tab_widgets(settings_tab)
        self._create_routing_tab_widgets(routing_tab)

    def _create_main_layout(self):
        tab_view = customtkinter.CTkTabview(self, anchor="w")
        tab_view.pack(expand=True, fill="both", padx=10, pady=10)
        connection_tab = tab_view.add("Connection")
        settings_tab = tab_view.add("Settings")
        routing_tab = tab_view.add("Routing")
        return connection_tab, settings_tab, routing_tab

    def _create_server_list_ui(self, parent_tab):
        """Creates the UI for the left column (server list)."""
        server_list_container = customtkinter.CTkFrame(
            parent_tab, fg_color="transparent"
        )
        server_list_container.grid(
            row=0, column=0, sticky="nsew", padx=(10, 5), pady=10
        )
        # Make row 2 (server list) expandable
        server_list_container.grid_rowconfigure(2, weight=1)
        server_list_container.grid_columnconfigure(0, weight=1)

        # --- Group Dropdown (Row 0) ---
        self.group_dropdown = customtkinter.CTkOptionMenu(
            server_list_container,
            values=["No Groups"],
            command=self.filter_servers_by_group,
            font=APP_FONT,
        )
        self.group_dropdown.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # --- Connection Controls (Row 1) ---
        conn_frame = customtkinter.CTkFrame(server_list_container)
        conn_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        conn_frame.grid_columnconfigure(0, weight=1)  # Label
        conn_frame.grid_columnconfigure((1, 2), weight=0)  # Buttons

        self.status_label = customtkinter.CTkLabel(
            conn_frame,
            text="No Server Selected",
            font=(APP_FONT[0], 14),
            text_color="orange",
            wraplength=250,
            justify="left",
        )
        self.status_label.grid(row=0, column=0, padx=10, pady=(5, 5), sticky="w")

        self.start_button = customtkinter.CTkButton(
            conn_frame, text="Start", command=self.start_singbox, font=APP_FONT
        )
        self.start_button.grid(row=0, column=1, padx=(0, 5), pady=5, sticky="e")

        self.stop_button = customtkinter.CTkButton(
            conn_frame,
            text="Stop",
            command=self.stop_singbox,
            state="disabled",
            font=APP_FONT,
        )
        self.stop_button.grid(row=0, column=2, padx=(0, 10), pady=5, sticky="e")

        # --- Server List (Row 2) ---
        self.server_list_frame = customtkinter.CTkScrollableFrame(
            server_list_container, label_text="Servers", label_font=APP_FONT
        )
        self.server_list_frame.grid(row=2, column=0, sticky="nsew")
        self.server_list_frame.grid_columnconfigure(0, weight=1)

    def _create_management_ui(self, parent_tab):
        """Creates the UI for the right column (management panel)."""
        management_container = customtkinter.CTkScrollableFrame(
            parent_tab, fg_color="transparent"
        )
        management_container.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        management_container.grid_columnconfigure(0, weight=1)

        # --- Subscription Management ---
        sub_frame = customtkinter.CTkFrame(management_container)
        sub_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        sub_frame.grid_columnconfigure(0, weight=1)

        customtkinter.CTkLabel(
            sub_frame, text="Subscription Link:", font=APP_FONT
        ).grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        self.sub_link_entry = customtkinter.CTkEntry(
            sub_frame,
            placeholder_text="Paste your subscription link here",
            font=APP_FONT,
        )
        self.sub_link_entry.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="ew")

        customtkinter.CTkLabel(
            sub_frame, text="Group Name (Optional):", font=APP_FONT
        ).grid(row=2, column=0, padx=10, pady=(10, 0), sticky="w")
        self.group_name_entry = customtkinter.CTkEntry(
            sub_frame, placeholder_text="e.g., My Servers", font=APP_FONT
        )
        self.group_name_entry.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")

        self.group_sub_checkbox = customtkinter.CTkCheckBox(
            sub_frame, text="Create a group for this subscription", font=APP_FONT
        )
        self.group_sub_checkbox.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="w")

        self.update_button = customtkinter.CTkButton(
            sub_frame, text="Update", command=self.update_subscription, font=APP_FONT
        )
        self.update_button.grid(row=5, column=0, padx=10, pady=10, sticky="ew")

        self.progress_bar = customtkinter.CTkProgressBar(
            sub_frame, orientation="horizontal"
        )
        self.progress_bar.grid(row=6, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.progress_bar.grid_remove()  # Hide it initially

        # --- Group Actions ---
        actions_frame = customtkinter.CTkFrame(management_container)
        actions_frame.grid(row=1, column=0, sticky="ew", pady=10)
        actions_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.ping_button = customtkinter.CTkButton(
            actions_frame, text="Ping Group", command=self.test_all_pings, font=APP_FONT
        )
        self.ping_button.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")

        self.url_test_all_button = customtkinter.CTkButton(
            actions_frame,
            text="URL Test Group",
            command=self.test_all_urls,
            font=APP_FONT,
        )
        self.url_test_all_button.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

        self.cancel_tests_button = customtkinter.CTkButton(
            actions_frame,
            text="Cancel",
            command=self.cancel_all_tests,
            font=APP_FONT,
            state="disabled",
        )
        self.cancel_tests_button.grid(
            row=0, column=2, padx=(5, 10), pady=10, sticky="ew"
        )

        self.sort_button = customtkinter.CTkButton(
            actions_frame, text="Sort by Ping", command=self.sort_servers, font=APP_FONT
        )
        self.sort_button.grid(
            row=1, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="ew"
        )

        self.url_test_button = customtkinter.CTkButton(
            actions_frame,
            text="URL Test (Active)",
            command=self.run_url_test,
            font=APP_FONT,
            state="disabled",
        )
        self.url_test_button.grid(
            row=1, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="ew"
        )

        # --- Manual Add ---
        manual_frame = customtkinter.CTkFrame(management_container)
        manual_frame.grid(row=2, column=0, sticky="ew", pady=10)
        manual_frame.grid_columnconfigure(0, weight=1)

        customtkinter.CTkLabel(
            manual_frame, text="Add Single Server:", font=APP_FONT
        ).grid(row=0, column=0, padx=10, pady=(10, 0), sticky="w")
        self.manual_add_entry = customtkinter.CTkEntry(
            manual_frame,
            placeholder_text="Paste vmess://, vless://, etc.",
            font=APP_FONT,
        )
        self.manual_add_entry.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="ew")
        self.manual_add_button = customtkinter.CTkButton(
            manual_frame,
            text="Add Server",
            command=self.add_manual_server,
            font=APP_FONT,
        )
        self.manual_add_button.grid(row=2, column=0, padx=10, pady=10, sticky="ew")

        # --- Log Textbox ---
        log_frame = customtkinter.CTkFrame(management_container, fg_color="transparent")
        log_frame.grid(row=3, column=0, sticky="nsew", pady=(10, 0))
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        management_container.grid_rowconfigure(3, weight=1)

        self.log_textbox = customtkinter.CTkTextbox(log_frame, font=APP_FONT)
        self.log_textbox.grid(row=0, column=0, sticky="nsew")

    def _create_status_bar(self, parent_tab):
        status_bar_frame = customtkinter.CTkFrame(parent_tab, height=30)
        status_bar_frame.grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(5, 0)
        )
        status_bar_frame.grid_columnconfigure((1, 3, 5), weight=1)

        customtkinter.CTkLabel(
            status_bar_frame, text="Status:", font=APP_FONT, anchor="w"
        ).grid(row=0, column=0, padx=(10, 2), pady=5)
        self.conn_status_label = customtkinter.CTkLabel(
            status_bar_frame,
            text="Disconnected",
            text_color="orange",
            font=APP_FONT,
            anchor="w",
        )
        self.conn_status_label.grid(row=0, column=1, padx=(0, 10), pady=5, sticky="w")

        customtkinter.CTkLabel(
            status_bar_frame, text="IP Address:", font=APP_FONT, anchor="w"
        ).grid(row=0, column=2, padx=(10, 2), pady=5)
        self.ip_label = customtkinter.CTkLabel(
            status_bar_frame, text="N/A", font=APP_FONT, anchor="w"
        )
        self.ip_label.grid(row=0, column=3, padx=(0, 10), pady=5, sticky="w")

        customtkinter.CTkLabel(
            status_bar_frame, text="Latency:", font=APP_FONT, anchor="w"
        ).grid(row=0, column=4, padx=(10, 2), pady=5)
        self.latency_label = customtkinter.CTkLabel(
            status_bar_frame, text="N/A", font=APP_FONT, anchor="w"
        )
        self.latency_label.grid(row=0, column=5, padx=(0, 10), pady=5, sticky="w")

    def _create_settings_tab_widgets(self, parent_tab):
        parent_tab.grid_columnconfigure(0, weight=1)
        # Allow extra space to expand
        parent_tab.grid_rowconfigure(6, weight=1)

        # --- Appearance Settings ---
        customtkinter.CTkLabel(
            parent_tab, text="Appearance Settings", font=(APP_FONT[0], 16)
        ).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        theme_frame = customtkinter.CTkFrame(parent_tab)
        theme_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.appearance_mode_menu = customtkinter.CTkOptionMenu(
            theme_frame,
            values=["Light", "Dark", "System"],
            command=self.change_appearance_mode,
            font=APP_FONT,
        )
        self.appearance_mode_menu.pack(side="left", padx=10, pady=10)

        self.color_theme_menu = customtkinter.CTkOptionMenu(
            theme_frame,
            values=["green", "blue", "dark-blue"],
            command=self.change_color_theme,
            font=APP_FONT,
        )
        self.color_theme_menu.pack(side="right", padx=10, pady=10)

        self.appearance_mode_menu.set(self.settings.get("appearance_mode"))
        self.color_theme_menu.set(self.settings.get("color_theme"))

        # --- Network Settings ---
        customtkinter.CTkLabel(
            parent_tab, text="Network Settings", font=(APP_FONT[0], 16)
        ).grid(row=2, column=0, padx=20, pady=(20, 10), sticky="w")

        network_frame = customtkinter.CTkFrame(parent_tab)
        network_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        network_frame.grid_columnconfigure(1, weight=1)

        # Connection Mode
        customtkinter.CTkLabel(
            network_frame, text="Connection Mode:", font=APP_FONT
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.connection_mode_menu = customtkinter.CTkOptionMenu(
            network_frame, values=["Rule-Based", "Global"], font=APP_FONT
        )
        self.connection_mode_menu.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.connection_mode_menu.set(self.settings.get("connection_mode"))

        # DNS Servers
        customtkinter.CTkLabel(network_frame, text="DNS Servers:", font=APP_FONT).grid(
            row=1, column=0, padx=10, pady=5, sticky="w"
        )
        self.dns_entry = customtkinter.CTkEntry(network_frame, font=APP_FONT)
        self.dns_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.dns_entry.insert(0, self.settings.get("dns_servers"))

        # Bypass Domains
        customtkinter.CTkLabel(
            network_frame, text="Bypass Domains:", font=APP_FONT
        ).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.bypass_domains_entry = customtkinter.CTkEntry(network_frame, font=APP_FONT)
        self.bypass_domains_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.bypass_domains_entry.insert(0, self.settings.get("bypass_domains"))

        # Bypass IPs
        customtkinter.CTkLabel(network_frame, text="Bypass IPs:", font=APP_FONT).grid(
            row=3, column=0, padx=10, pady=5, sticky="w"
        )
        self.bypass_ips_entry = customtkinter.CTkEntry(network_frame, font=APP_FONT)
        self.bypass_ips_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        self.bypass_ips_entry.insert(0, self.settings.get("bypass_ips"))

        # --- Profile Management ---
        customtkinter.CTkLabel(
            parent_tab, text="Profile Management", font=(APP_FONT[0], 16)
        ).grid(row=4, column=0, padx=20, pady=(20, 10), sticky="w")

        profile_frame = customtkinter.CTkFrame(parent_tab)
        profile_frame.grid(row=5, column=0, padx=20, pady=10, sticky="ew")
        profile_frame.grid_columnconfigure((0, 1), weight=1)

        import_button = customtkinter.CTkButton(
            profile_frame,
            text="Import Profile",
            command=self.import_profile,
            font=APP_FONT,
        )
        import_button.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")

        export_button = customtkinter.CTkButton(
            profile_frame,
            text="Export Profile",
            command=self.export_profile,
            font=APP_FONT,
        )
        export_button.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="ew")

        # --- About Button ---
        about_button = customtkinter.CTkButton(
            parent_tab, text="About Onix", command=self.show_about_window
        )
        about_button.grid(row=7, column=0, padx=20, pady=20, sticky="s")

    def _create_routing_tab_widgets(self, parent_tab):
        parent_tab.grid_columnconfigure(0, weight=1)
        parent_tab.grid_rowconfigure(1, weight=1) # Make row for rules scrollable

        customtkinter.CTkLabel(
            parent_tab, text="Custom Routing Rules:", font=(APP_FONT[0], 16)
        ).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        self.routing_rules_frame = customtkinter.CTkScrollableFrame(parent_tab, fg_color="transparent")
        self.routing_rules_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 10))
        self.routing_rules_frame.grid_columnconfigure(0, weight=1)

        # Placeholder for rule entries
        customtkinter.CTkLabel(
            self.routing_rules_frame, text="No custom rules added yet.", font=APP_FONT
        ).grid(row=0, column=0, padx=10, pady=10, sticky="w")

        # Buttons for managing rules
        button_frame = customtkinter.CTkFrame(parent_tab, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        button_frame.grid_columnconfigure((0, 1, 2), weight=1)

        add_rule_button = customtkinter.CTkButton(
            button_frame, text="Add Rule", command=self._add_routing_rule_ui, font=APP_FONT
        )
        add_rule_button.grid(row=0, column=0, padx=(0, 5), pady=10, sticky="ew")

        save_rules_button = customtkinter.CTkButton(
            button_frame, text="Save Rules", command=self._save_routing_rules, font=APP_FONT
        )
        save_rules_button.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

        load_rules_button = customtkinter.CTkButton(
            button_frame, text="Load Rules", command=self._load_routing_rules, font=APP_FONT
        )
        load_rules_button.grid(row=0, column=2, padx=(5, 0), pady=10, sticky="ew")

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
            "<Control-x>", lambda e: handle_text_shortcut(self.focus_get(), "cut")
        )
        self.bind_all(
            "<Control-c>", lambda e: handle_text_shortcut(self.focus_get(), "copy")
        )
        self.bind_all(
            "<Control-v>", lambda e: handle_text_shortcut(self.focus_get(), "paste")
        )
        self.bind_all(
            "<Control-a>",
            lambda e: handle_text_shortcut(self.focus_get(), "select_all"),
        )

        self.bind_all("<Control-s>", self.start_stop_toggle)
        self.bind_all("<Control-u>", self.update_subscription)
        self.bind_all("<Control-q>", self.quit_application)

    # --- Data & Settings Management ---
    def save_all_settings(self):
        settings = {
            "sub_link": self.sub_link_entry.get(),
            "servers": self.server_manager.get_all_server_groups(),  # Get servers from the manager
            "appearance_mode": customtkinter.get_appearance_mode(),
            "color_theme": self.color_theme_menu.get(),
            "dns_servers": self.dns_entry.get(),
            "bypass_domains": self.bypass_domains_entry.get(),
            "bypass_ips": self.bypass_ips_entry.get(),
        }
        settings_manager.save_settings(settings)

    def load_data(self):
        try:
            self.sub_link_entry.insert(0, self.settings.get("sub_link"))
            self.server_manager.load_servers()
        except (FileNotFoundError, json.JSONDecodeError) as e:
            error_msg = f"Error loading application data. Settings file might be missing or corrupted: {e}"
            self.log(error_msg, LogLevel.ERROR)
            show_error_message("Error", error_msg)
        except Exception as e:
            error_msg = f"An unexpected error occurred while loading data: {e}"
            self.log(error_msg, LogLevel.ERROR)
            show_error_message("Error", error_msg)

    def import_profile(self):
        """Imports settings from a JSON file and overwrites the current settings."""
        file_path = filedialog.askopenfilename(
            title="Import Profile",
            filetypes=[("JSON files", "*.json"), ("All files", "*.* ")],
            defaultextension=".json",
        )
        if not file_path:
            return

        if not messagebox.askyesno(
            "Confirm Import",
            "This will overwrite all your current settings and servers. Are you sure you want to continue?",
        ):
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                new_settings = json.load(f)

            # Basic validation
            if "sub_link" not in new_settings or "servers" not in new_settings:
                raise ValueError("Invalid profile file.")

            settings_manager.save_settings(new_settings)
            messagebox.showinfo(
                "Import Successful",
                "Profile imported successfully. Please restart the application for the changes to take full effect.",
            )
            self.quit_application()  # Force restart
        except (IOError, json.JSONDecodeError, ValueError) as e:
            messagebox.showerror("Import Failed", f"Failed to import profile: {e}")

    def export_profile(self):
        """Exports all current settings to a JSON file."""
        file_path = filedialog.asksaveasfilename(
            title="Export Profile",
            filetypes=[("JSON files", "*.json"), ("All files", "*.* ")],
            defaultextension=".json",
            initialfile="onix_profile.json",
        )
        if not file_path:
            return

        try:
            # Ensure current settings are saved before exporting
            self.save_all_settings()

            # Read the saved settings and write to the new file
            current_settings = settings_manager.load_settings()
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(current_settings, f, indent=4)

            messagebox.showinfo(
                "Export Successful", f"Profile successfully exported to:\n{file_path}"
            )
        except (IOError, json.JSONDecodeError) as e:
            messagebox.showerror("Export Failed", f"Failed to export profile: {e}")

    # --- Server Manager Callbacks ---
    def _on_update_start(self):
        self.log_textbox.delete("1.0", "end")
        self.log("Updating from subscription link...", LogLevel.INFO)
        self.progress_bar.grid()
        self.progress_bar.start()
        self.update_button.configure(state="disabled")

    def _on_update_finish(self, error=False):
        self.progress_bar.stop()
        self.progress_bar.grid_remove()
        self.update_button.configure(state="normal")
        if not error:
            self.save_all_settings()
            self.populate_group_dropdown()
        else:
            self.log("Subscription update failed.", LogLevel.ERROR)

    def _on_ping_result(self, config, result, is_url_test):
        config_id = f"{config.get('server')}:{config.get('port')}"
        if config_id in self.server_widgets:
            widget_info = self.server_widgets[config_id]
            ping_label = widget_info["ping_label"]
            if ping_label.winfo_exists():
                if result != -1:
                    if is_url_test:
                        color = (
                            "lightgreen"
                            if result < 1000
                            else "orange"
                            if result < 3000
                            else "red"
                        )
                    else:
                        color = (
                            "lightgreen"
                            if result < 200
                            else "orange"
                            if result < 500
                            else "red"
                        )
                    ping_label.configure(text=f"{result} ms", text_color=color)
                else:
                    ping_label.configure(
                        text="Failed" if is_url_test else "Timeout", text_color="red"
                    )

    def _on_testing_start(self):
        """Disables test buttons and enables the cancel button."""
        self.ping_button.configure(state="disabled")
        self.url_test_all_button.configure(state="disabled")
        self.cancel_tests_button.configure(state="normal")
        self.update_button.configure(
            state="disabled"
        )  # Also disable updates during test

    def _on_testing_finish(self):
        """Enables test buttons and disables the cancel button."""
        self.ping_button.configure(state="normal")
        self.url_test_all_button.configure(state="normal")
        self.cancel_tests_button.configure(state="disabled")
        self.update_button.configure(state="normal")

    def refresh_server_list_ui(self):
        current_group = self.group_dropdown.get()
        self.filter_servers_by_group(current_group)

    # --- UI Update & Logging ---
    def log(self, message, level=LogLevel.INFO):
        log_colors = {
            LogLevel.INFO: "white",
            LogLevel.WARNING: "orange",
            LogLevel.ERROR: "red",
            LogLevel.SUCCESS: "lightgreen",
            LogLevel.DEBUG: "gray",
        }
        color = log_colors.get(level, "white")

        self.log_textbox.configure(state="normal")  # Enable editing
        self.log_textbox.insert("end", message + "\n", (level.value,))
        self.log_textbox.tag_config(level.value, foreground=color)
        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")  # Disable editing

    def populate_group_dropdown(self):
        groups = self.server_manager.get_groups()
        current_selection = self.group_dropdown.get()

        if not groups:
            self.group_dropdown.configure(values=["No Groups"])
            self.group_dropdown.set("No Groups")
            self.filter_servers_by_group("No Groups")
            return

        self.group_dropdown.configure(values=groups)
        if current_selection in groups:
            self.group_dropdown.set(current_selection)
        else:
            self.group_dropdown.set(groups[0])
        self.filter_servers_by_group(self.group_dropdown.get())

    def filter_servers_by_group(self, selected_group, sorted_configs=None):
        self.selected_server_button = None

        self.selected_group = selected_group
        configs = (
            sorted_configs
            if sorted_configs is not None
            else self.server_manager.get_servers_by_group(selected_group)
        )

        # Create a set of unique identifiers for the new configs
        new_config_ids = {f"{c.get('server')}:{c.get('port')}" for c in configs}

        # Identify widgets to remove
        widgets_to_destroy = []
        for config_id, widget_info in self.server_widgets.items():
            if config_id not in new_config_ids:
                widgets_to_destroy.append(widget_info["frame"])

        # Destroy old widgets
        for widget in widgets_to_destroy:
            widget.destroy()

        # Clear removed widgets from our tracking dictionary
        self.server_widgets = {
            config_id: widget_info
            for config_id, widget_info in self.server_widgets.items()
            if config_id in new_config_ids
        }

        # Update or create widgets
        for i, config in enumerate(configs):
            config_id = f"{config.get('server')}:{config.get('port')}"

            if config_id in self.server_widgets:
                # Update existing widget
                server_frame = self.server_widgets[config_id]["frame"]
                name_label = self.server_widgets[config_id]["name_label"]
                ping_label = self.server_widgets[config_id]["ping_label"]

                # Update text and color if changed
                if name_label.cget("text") != config["name"]:
                    name_label.configure(text=config["name"])

                ping_val = config.get("ping", "-")
                ping_text = (
                    f"{ping_val} ms"
                    if isinstance(ping_val, int) and ping_val != -1
                    else ("Timeout" if ping_val == -1 else "- ms")
                )
                if ping_label.cget("text") != ping_text:
                    ping_label.configure(text=ping_text)

                # Re-grid to ensure correct order
                server_frame.grid(row=i, column=0, sticky="ew", pady=1)

            else:
                # Create new widget
                server_frame = customtkinter.CTkFrame(
                    self.server_list_frame, fg_color="transparent"
                )
                server_frame.server_config = (
                    config  # Still attach for context menu and selection
                )
                server_frame.grid(row=i, column=0, sticky="ew", pady=1)
                server_frame.grid_columnconfigure(0, weight=1)

                name_label = customtkinter.CTkLabel(
                    server_frame, text=config["name"], font=APP_FONT, anchor="w"
                )
                name_label.grid(row=0, column=0, sticky="w", padx=5)

                ping_val = config.get("ping", "-")
                ping_text = (
                    f"{ping_val} ms"
                    if isinstance(ping_val, int) and ping_val != -1
                    else ("Timeout" if ping_val == -1 else "- ms")
                )
                ping_label = customtkinter.CTkLabel(
                    server_frame, text=ping_text, font=APP_FONT, anchor="e", width=80
                )
                ping_label.grid(row=0, column=1, sticky="e", padx=5)

                context_menu = ServerContextMenu(
                    self,
                    config,
                    ping_label,
                    lambda cfg, lbl: self.server_manager.test_all_pings([cfg]),
                    lambda cfg, lbl: self.server_manager.test_all_urls([cfg]),
                    self.delete_server,
                    self.edit_server,
                )

                server_frame.bind("<Button-3>", context_menu.popup)
                name_label.bind("<Button-3>", context_menu.popup)
                ping_label.bind("<Button-3>", context_menu.popup)

                server_frame.bind(
                    "<Button-1>",
                    lambda e, c=config, f=server_frame: self.select_server(c, f),
                )
                name_label.bind(
                    "<Button-1>",
                    lambda e, c=config, f=server_frame: self.select_server(c, f),
                )
                ping_label.bind(
                    "<Button-1>",
                    lambda e, c=config, f=server_frame: self.select_server(c, f),
                )

                # Store new widget references
                self.server_widgets[config_id] = {
                    "frame": server_frame,
                    "name_label": name_label,
                    "ping_label": ping_label,
                    "config": config,  # Store config for easy access
                }

        # Handle selection after updates
        if self.selected_config:
            selected_config_id = f"{self.selected_config.get('server')}:{self.selected_config.get('port')}"
            if selected_config_id in self.server_widgets:
                selected_frame = self.server_widgets[selected_config_id]["frame"]
                selected_frame.configure(fg_color=("gray85", "gray25"))
                self.selected_server_button = selected_frame
            else:
                self.selected_config = None  # Selected server no longer exists
                self.status_label.configure(
                    text="No Server Selected", text_color="orange"
                )

    def select_server(self, config, frame_widget):
        if self.selected_server_button is not None:
            self.selected_server_button.configure(fg_color="transparent")

        frame_widget.configure(fg_color=("gray85", "gray25"))
        self.selected_server_button = frame_widget
        self.selected_config = config
        self.log(f"Server selected: {config['name']}", LogLevel.INFO)
        self.status_label.configure(
            text=f"Selected: {config['name']}", text_color="orange"
        )

    def delete_server(self, config_to_delete):
        """Deletes a server from the list and saves the changes."""
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete server '{config_to_delete.get('name')}'?",
        ):
            return

        self.server_manager.delete_server(config_to_delete)

    def edit_server(self, config_to_edit):
        """Opens a dialog to edit the server's name."""
        dialog = customtkinter.CTkInputDialog(
            text="Enter new server name:", title="Edit Server Name"
        )
        dialog.after(10, dialog.lift)
        new_name = dialog.get_input()

        if new_name and new_name.strip():
            self.server_manager.edit_server(config_to_edit, new_name.strip())

    def add_manual_server(self):
        server_link = self.manual_add_entry.get()
        if not server_link:
            self.log("Please paste a server link to add.", LogLevel.WARNING)
            return

        self.server_manager.add_manual_server(server_link)
        self.manual_add_entry.delete(0, "end")

    # --- Core Functionality ---
    def update_subscription(self, event=None):
        sub_link = self.sub_link_entry.get()
        if not sub_link:
            self.log("Please enter a subscription link first.", LogLevel.WARNING)
            return

        custom_group_name = None
        if self.group_sub_checkbox.get():
            custom_group_name = self.group_name_entry.get().strip()
            if not custom_group_name:
                # Try to generate a group name from the subscription link
                try:
                    # A simple way to get a name from the url
                    custom_group_name = sub_link.split("/")[-1].split(".")[0]
                except IndexError:
                    warning_msg = "Could not automatically determine group name from subscription link. Using 'Subscription' as default."
                    self.log(warning_msg, LogLevel.WARNING)
                    show_warning_message("Warning", warning_msg)
                    custom_group_name = "Subscription"
                except Exception as e:
                    error_msg = f"An unexpected error occurred while generating group name: {e}. Using 'Subscription' as default."
                    self.log(error_msg, LogLevel.ERROR)
                    show_error_message("Error", error_msg)
                    custom_group_name = "Subscription"

        self.server_manager.update_subscription(sub_link, custom_group_name)

    def start_singbox(self):
        if not self.selected_config:
            self.log("Please select a server first!", LogLevel.WARNING)
            return
        self.log_textbox.delete("1.0", "end")
        self.singbox_manager.start(self.selected_config)

    def stop_singbox(self):
        self.singbox_manager.stop()

    def start_stop_toggle(self, event=None):
        if not self.singbox_manager.is_running:
            self.start_singbox()
        else:
            self.stop_singbox()

    # --- Ping & URL Tests ---
    def test_all_pings(self):
        current_group = self.group_dropdown.get()
        if not current_group or current_group == "No Groups":
            self.log("No servers to test.", LogLevel.INFO)
            return
        servers_to_test = self.server_manager.get_servers_by_group(current_group)
        self.server_manager.test_all_pings(servers_to_test)

    def test_all_urls(self):
        current_group = self.group_dropdown.get()
        if not current_group or current_group == "No Groups":
            self.log("No servers to test.")
            return
        servers_to_test = self.server_manager.get_servers_by_group(current_group)
        self.server_manager.test_all_urls(servers_to_test)

    def cancel_all_tests(self):
        self.log("Cancelling all tests...", LogLevel.INFO)
        self.server_manager.cancel_tests()

    def run_url_test(self):
        if not self.singbox_manager.is_running:
            self.log("URL Test failed: Not connected.", LogLevel.WARNING)
            return
        self.log("Running URL test on current connection...", LogLevel.INFO)
        self.url_test_button.configure(state="disabled", text="Testing...")

        def task():
            result = utils.url_test(PROXY_SERVER_ADDRESS)

            def update_ui():
                if result != -1:
                    self.log(
                        f"URL Test successful! Response time: {result} ms",
                        LogLevel.SUCCESS,
                    )
                else:
                    self.log(
                        "URL Test failed: Could not reach test URL via proxy.",
                        LogLevel.ERROR,
                    )
                if self.singbox_manager.is_running:
                    self.url_test_button.configure(
                        state="normal", text="URL Test (Active)"
                    )

            self.after(0, update_ui)

        threading.Thread(target=task, daemon=True).start()

    def sort_servers(self):
        current_group = self.group_dropdown.get()
        if not current_group or current_group == "No Groups":
            self.log("No servers to sort.")
            return
        self.server_manager.sort_servers_by_ping(current_group)

    # --- System & Window Management ---

    def change_appearance_mode(self, new_mode):
        customtkinter.set_appearance_mode(new_mode)
        self.save_all_settings()

    def change_color_theme(self, new_theme):
        self.log(
            "Color theme changed. Please restart the app to see full effect.",
            LogLevel.INFO,
        )
        self.color_theme_menu.set(new_theme)
        self.save_all_settings()

    def on_closing(self):
        self.save_all_settings()
        if self.singbox_manager.is_running:
            # Reset proxy in a separate thread to avoid blocking UI
            threading.Thread(
                target=self._reset_proxy_and_then_hide, daemon=True
            ).start()
        else:
            self.quit_application()

    def _reset_proxy_and_then_hide(self):
        system_proxy.set_system_proxy(False, self.settings, self.log)
        # After resetting proxy, hide the window (which will then start the tray icon in its own thread)
        self.after(0, self.hide_window)

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
        self.withdraw()  # UI operation, must be on main thread
        # Start the tray icon in a new thread, as it's blocking
        threading.Thread(target=self._run_tray_icon, daemon=True).start()

    def _run_tray_icon(self):
        image_data = base64.b64decode(ICON_BASE64)
        image = Image.open(io.BytesIO(image_data))
        menu = (item("Show", self.show_window), item("Quit", self.quit_application))
        self.tray_icon = pystray.Icon("Sing-box Client", image, "Sing-box Client", menu)
        self.tray_icon.run()

    def show_about_window(self):
        """Displays the About window."""
        # Prevent multiple about windows
        if hasattr(self, "about_win") and self.about_win.winfo_exists():
            self.about_win.lift()
            return

        self.about_win = customtkinter.CTkToplevel(self)
        self.about_win.title("About Onix")
        self.about_win.geometry("350x220")
        self.about_win.resizable(False, False)
        self.about_win.transient(self)  # Keep on top of the main window

        self.about_win.grid_columnconfigure(0, weight=1)

        title_label = customtkinter.CTkLabel(
            self.about_win,
            text="Onix",
            font=customtkinter.CTkFont(size=24, weight="bold"),
        )
        title_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        version_label = customtkinter.CTkLabel(
            self.about_win, text=f"Version: {self.app_version}", font=APP_FONT
        )
        version_label.grid(row=1, column=0, padx=20, pady=0)

        def open_releases_page(e):
            webbrowser.open_new("https://github.com/AhmadAkd/onix/releases")

        link_label = customtkinter.CTkLabel(
            self.about_win,
            text="GitHub Releases Page",
            text_color=("blue", "cyan"),
            cursor="hand2",
            font=customtkinter.CTkFont(underline=True),
        )
        link_label.grid(row=2, column=0, padx=20, pady=10)
        link_label.bind("<Button-1>", open_releases_page)

        ok_button = customtkinter.CTkButton(
            self.about_win, text="OK", command=self.about_win.destroy, width=100
        )
        ok_button.grid(row=3, column=0, padx=20, pady=20)


    def _add_routing_rule_ui(self):
        self.log("Add Routing Rule UI (Not yet implemented)", LogLevel.INFO)

    def _save_routing_rules(self):
        self.log("Save Routing Rules (Not yet implemented)", LogLevel.INFO)

    def _load_routing_rules(self):
        self.log("Load Routing Rules (Not yet implemented)", LogLevel.INFO)


if __name__ == "__main__":
    app = SingboxApp()
    app.mainloop()
