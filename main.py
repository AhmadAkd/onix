from ui_components import (
    RightClickMenu,
    ServerContextMenu,
    handle_text_shortcut,
    AddRoutingRuleDialog,
    SubscriptionManagerDialog,
)
from managers.singbox_manager import SingboxManager
from managers.server_manager import ServerManager
import settings_manager
import system_proxy
import utils
from constants import (
    LogLevel,
    APP_FONT,
    ICON_BASE64,
    PROXY_SERVER_ADDRESS,
    TAB_CONNECTION,
    TAB_SETTINGS,
    TAB_ROUTING,
    NO_GROUPS,
    STATUS_NO_SERVER_SELECTED,
    BTN_START,
    BTN_STOP,
    LBL_SERVERS,
    BTN_MANAGE_SUBSCRIPTIONS,
    BTN_UPDATE_ALL_SUBSCRIPTIONS,
    BTN_PING_GROUP,
    BTN_URL_TEST_GROUP,
    BTN_CANCEL,
    BTN_SORT_BY_PING,
    BTN_URL_TEST_ACTIVE,
    LBL_ADD_SERVER,
    PLACEHOLDER_MANUAL_ADD,
    BTN_ADD_SERVER,
    BTN_SCAN_QR,
    LBL_STATUS,
    STATUS_DISCONNECTED,
    LBL_IP_ADDRESS,
    NA,
    LBL_LATENCY,
    LBL_APPEARANCE_SETTINGS,
    APPEARANCE_MODE_LIGHT,
    APPEARANCE_MODE_DARK,
    APPEARANCE_MODE_SYSTEM,
    THEME_GREEN,
    THEME_BLUE,
    THEME_DARK_BLUE,
    LBL_NETWORK_SETTINGS,
    LBL_CONNECTION_MODE,
    MODE_RULE_BASED,
    MODE_GLOBAL,
    LBL_DNS_SERVERS,
    LBL_BYPASS_DOMAINS,
    LBL_BYPASS_IPS,
    LBL_ENABLE_TUN,
    LBL_PROFILE_MANAGEMENT,
    BTN_IMPORT_PROFILE,
    BTN_EXPORT_PROFILE,
    LBL_UPDATES,
    BTN_CHECK_FOR_UPDATES,
    BTN_ABOUT,
    TITLE_EDIT_SERVER,
    PROMPT_NEW_SERVER_NAME,
    TITLE_CONFIRM_DELETE,
    MSG_CONFIRM_DELETE_SERVER,
    MSG_CONFIRM_DELETE_RULE,
    TITLE_QR_CODE,
    BTN_ADD_RULE,
    BTN_EDIT,
    BTN_DELETE,
    TITLE_ABOUT,
    LBL_VERSION,
    LBL_GITHUB_RELEASES,
    BTN_OK,
    STATUS_CONNECTED,
    STATUS_SELECTED,
)
import constants
import customtkinter
import threading
import base64
import PIL
import numpy as np
import io
import pystray
from pystray import MenuItem as item
from concurrent.futures import ThreadPoolExecutor
import webbrowser
from tkinter import messagebox, filedialog
import json
from message_utils import show_error_message


# Local imports


class SingboxApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # --- Check for sing-box updates in a separate thread ---
        threading.Thread(target=utils.download_singbox_if_needed, daemon=True).start()

        # --- Load Settings ---
        self.settings = settings_manager.load_settings()

        # --- Initialize State Variables ---
        self.selected_config = None
        self.selected_server_button = None
        self.selected_group = None
        self.selected_group_button = None
        self.tray_icon = None
        self.ping_executor = ThreadPoolExecutor(max_workers=20)
        self.conn_status_label = None
        self.ip_label = None
        self.latency_label = None
        self.server_widgets = {}  # New: To store references to server widgets
        self.custom_routing_rules = []  # New: To store custom routing rules
        self.subscriptions = []  # New: To store subscriptions
        self.all_logs = []  # For log filtering
        self.log_filter_checkboxes = {}  # For log filtering
        self.sort_column = "name"  # For sorting
        self.sort_ascending = True  # For sorting
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
            text=STATUS_CONNECTED.format(self.selected_config["name"]),
            text_color="lightgreen",
        )
        self.conn_status_label.configure(text="Connected", text_color="lightgreen")
        self.latency_label.configure(text=f"{latency} ms")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.url_test_button.configure(state="normal")

    def _on_stop(self):
        status_text = (
            STATUS_SELECTED.format(self.selected_config["name"])
            if self.selected_config
            else STATUS_NO_SERVER_SELECTED
        )
        self.status_label.configure(text=status_text, text_color="orange")
        self.conn_status_label.configure(text=STATUS_DISCONNECTED, text_color="orange")
        self.ip_label.configure(text=NA)
        self.latency_label.configure(text=NA)
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
        connection_tab = tab_view.add(TAB_CONNECTION)
        settings_tab = tab_view.add(TAB_SETTINGS)
        routing_tab = tab_view.add(TAB_ROUTING)
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
            values=[NO_GROUPS],
            command=self.update_server_display,
            font=APP_FONT,
        )
        self.group_dropdown.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        # --- Search Bar (Row 1) ---
        self.search_entry = customtkinter.CTkEntry(
            server_list_container, placeholder_text="Search servers...", font=APP_FONT
        )
        self.search_entry.grid(row=1, column=0, sticky="ew", pady=(0, 5))
        self.search_entry.bind("<KeyRelease>", self.update_server_display)

        # --- Connection Controls (Row 2) ---
        conn_frame = customtkinter.CTkFrame(server_list_container)
        conn_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        conn_frame.grid_columnconfigure(0, weight=1)  # Label
        conn_frame.grid_columnconfigure((1, 2), weight=0)  # Buttons

        # --- Server List Header (Row 3) ---
        header_frame = customtkinter.CTkFrame(server_list_container, fg_color="transparent")
        header_frame.grid(row=3, column=0, sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)

        self.name_sort_button = customtkinter.CTkButton(
            header_frame, text="Name", font=APP_FONT, fg_color="gray20", text_color="cyan",
            command=self._sort_by_name
        )
        self.name_sort_button.grid(row=0, column=0, sticky="ew", padx=(5,0))

        self.ping_sort_button = customtkinter.CTkButton(
            header_frame, text="Ping", font=APP_FONT, width=80, fg_color="gray20",
            command=self._sort_by_ping
        )
        self.ping_sort_button.grid(row=0, column=1, sticky="e", padx=(0,5))


        # --- Server List (Row 4) ---
        self.server_list_frame = customtkinter.CTkScrollableFrame(
            server_list_container #, label_text=LBL_SERVERS, label_font=APP_FONT
        )
        self.server_list_frame.grid(row=4, column=0, sticky="nsew")
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

        self.manage_subs_button = customtkinter.CTkButton(
            sub_frame,
            text=BTN_MANAGE_SUBSCRIPTIONS,
            command=self.manage_subscriptions,
            font=APP_FONT,
        )
        self.manage_subs_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        self.update_button = customtkinter.CTkButton(
            sub_frame,
            text=BTN_UPDATE_ALL_SUBSCRIPTIONS,
            command=self.update_all_subscriptions,
            font=APP_FONT,
        )
        self.update_button.grid(row=1, column=0, padx=10, pady=10, sticky="ew")

        self.progress_bar = customtkinter.CTkProgressBar(
            sub_frame, orientation="horizontal"
        )
        self.progress_bar.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="ew")
        self.progress_bar.grid_remove()  # Hide it initially

        # --- Group Actions ---
        actions_frame = customtkinter.CTkFrame(management_container)
        actions_frame.grid(row=1, column=0, sticky="ew", pady=10)
        actions_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.ping_button = customtkinter.CTkButton(
            actions_frame,
            text=BTN_PING_GROUP,
            command=self.test_all_pings,
            font=APP_FONT,
        )
        self.ping_button.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")

        self.url_test_all_button = customtkinter.CTkButton(
            actions_frame,
            text=BTN_URL_TEST_GROUP,
            command=self.test_all_urls,
            font=APP_FONT,
        )
        self.url_test_all_button.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

        self.cancel_tests_button = customtkinter.CTkButton(
            actions_frame,
            text=BTN_CANCEL,
            command=self.cancel_all_tests,
            font=APP_FONT,
            state="disabled",
        )
        self.cancel_tests_button.grid(
            row=0, column=2, padx=(5, 10), pady=10, sticky="ew"
        )

        self.sort_button = customtkinter.CTkButton(
            actions_frame,
            text=BTN_SORT_BY_PING,
            command=self.sort_servers,
            font=APP_FONT,
        )
        self.sort_button.grid(
            row=1, column=0, columnspan=3, padx=10, pady=(0, 10), sticky="ew"
        )

        self.url_test_button = customtkinter.CTkButton(
            actions_frame,
            text=BTN_URL_TEST_ACTIVE,
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

        customtkinter.CTkLabel(manual_frame, text=LBL_ADD_SERVER, font=APP_FONT).grid(
            row=0, column=0, padx=10, pady=(10, 0), sticky="w"
        )
        self.manual_add_entry = customtkinter.CTkEntry(
            manual_frame,
            placeholder_text=PLACEHOLDER_MANUAL_ADD,
            font=APP_FONT,
        )
        self.manual_add_entry.grid(row=1, column=0, padx=10, pady=(0, 5), sticky="ew")
        self.manual_add_button = customtkinter.CTkButton(
            manual_frame,
            text=BTN_ADD_SERVER,
            command=self.add_manual_server,
            font=APP_FONT,
        )
        self.manual_add_button.grid(row=2, column=0, padx=10, pady=(10, 0), sticky="ew")

        self.scan_qr_button = customtkinter.CTkButton(
            manual_frame,
            text=BTN_SCAN_QR,
            command=self.scan_qr_from_screen,
            font=APP_FONT,
        )
        self.scan_qr_button.grid(row=3, column=0, padx=10, pady=(10, 10), sticky="ew")

        self.import_wg_button = customtkinter.CTkButton(
            manual_frame,
            text="Import WireGuard Config",
            command=self.import_wireguard_config,
            font=APP_FONT,
        )
        self.import_wg_button.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="ew")


        # --- Log Filters ---
        log_filter_frame = customtkinter.CTkFrame(management_container)
        log_filter_frame.grid(row=3, column=0, sticky="ew", pady=(0, 5))
        log_filter_frame.grid_columnconfigure(0, weight=1)

        customtkinter.CTkLabel(log_filter_frame, text="Log Filters:", font=APP_FONT).pack(side="left", padx=(10, 5), pady=5)

        for level in LogLevel:
            checkbox = customtkinter.CTkCheckBox(
                log_filter_frame,
                text=level.name.capitalize(),
                font=APP_FONT,
                command=self._rerender_logs,
                checkbox_width=20,
                checkbox_height=20,
            )
            checkbox.pack(side="left", padx=5, pady=5)
            checkbox.select() # Select all by default
            self.log_filter_checkboxes[level] = checkbox

        # --- Log Textbox ---
        log_frame = customtkinter.CTkFrame(management_container, fg_color="transparent")
        log_frame.grid(row=4, column=0, sticky="nsew", pady=(0, 0))
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        management_container.grid_rowconfigure(4, weight=1)

        self.log_textbox = customtkinter.CTkTextbox(log_frame, font=APP_FONT)
        self.log_textbox.grid(row=0, column=0, sticky="nsew")

    def _create_status_bar(self, parent_tab):
        status_bar_frame = customtkinter.CTkFrame(parent_tab, height=30)
        status_bar_frame.grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(5, 0)
        )
        status_bar_frame.grid_columnconfigure((1, 3, 5), weight=1)

        customtkinter.CTkLabel(
            status_bar_frame, text=LBL_STATUS, font=APP_FONT, anchor="w"
        ).grid(row=0, column=0, padx=(10, 2), pady=5)
        self.conn_status_label = customtkinter.CTkLabel(
            status_bar_frame,
            text=STATUS_DISCONNECTED,
            text_color="orange",
            font=APP_FONT,
            anchor="w",
        )
        self.conn_status_label.grid(row=0, column=1, padx=(0, 10), pady=5, sticky="w")

        customtkinter.CTkLabel(
            status_bar_frame, text=LBL_IP_ADDRESS, font=APP_FONT, anchor="w"
        ).grid(row=0, column=2, padx=(10, 2), pady=5)
        self.ip_label = customtkinter.CTkLabel(
            status_bar_frame, text=NA, font=APP_FONT, anchor="w"
        )
        self.ip_label.grid(row=0, column=3, padx=(0, 10), pady=5, sticky="w")

        customtkinter.CTkLabel(
            status_bar_frame, text=LBL_LATENCY, font=APP_FONT, anchor="w"
        ).grid(row=0, column=4, padx=(10, 2), pady=5)
        self.latency_label = customtkinter.CTkLabel(
            status_bar_frame, text=NA, font=APP_FONT, anchor="w"
        )
        self.latency_label.grid(row=0, column=5, padx=(0, 10), pady=5, sticky="w")

    def _create_settings_tab_widgets(self, parent_tab):
        parent_tab.grid_columnconfigure(0, weight=1)
        # Allow extra space to expand
        parent_tab.grid_rowconfigure(6, weight=1)

        # --- Appearance Settings ---
        customtkinter.CTkLabel(
            parent_tab, text=LBL_APPEARANCE_SETTINGS, font=(APP_FONT[0], 16)
        ).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        theme_frame = customtkinter.CTkFrame(parent_tab)
        theme_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")

        self.appearance_mode_menu = customtkinter.CTkOptionMenu(
            theme_frame,
            values=[
                APPEARANCE_MODE_LIGHT,
                APPEARANCE_MODE_DARK,
                APPEARANCE_MODE_SYSTEM,
            ],
            command=self.change_appearance_mode,
            font=APP_FONT,
        )
        self.appearance_mode_menu.pack(side="left", padx=10, pady=10)

        self.color_theme_menu = customtkinter.CTkOptionMenu(
            theme_frame,
            values=[THEME_GREEN, THEME_BLUE, THEME_DARK_BLUE],
            command=self.change_color_theme,
            font=APP_FONT,
        )
        self.color_theme_menu.pack(side="right", padx=10, pady=10)

        self.appearance_mode_menu.set(self.settings.get("appearance_mode"))
        self.color_theme_menu.set(self.settings.get("color_theme"))

        # --- Network Settings ---
        customtkinter.CTkLabel(
            parent_tab, text=LBL_NETWORK_SETTINGS, font=(APP_FONT[0], 16)
        ).grid(row=2, column=0, padx=20, pady=(20, 10), sticky="w")

        network_frame = customtkinter.CTkFrame(parent_tab)
        network_frame.grid(row=3, column=0, padx=20, pady=10, sticky="nsew")
        network_frame.grid_columnconfigure(1, weight=1)

        # Connection Mode
        customtkinter.CTkLabel(
            network_frame, text=LBL_CONNECTION_MODE, font=APP_FONT
        ).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.connection_mode_menu = customtkinter.CTkOptionMenu(
            network_frame, values=[MODE_RULE_BASED, MODE_GLOBAL], font=APP_FONT
        )
        self.connection_mode_menu.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.connection_mode_menu.set(self.settings.get("connection_mode"))

        # DNS Servers
        customtkinter.CTkLabel(network_frame, text=LBL_DNS_SERVERS, font=APP_FONT).grid(
            row=1, column=0, padx=10, pady=5, sticky="w"
        )
        self.dns_entry = customtkinter.CTkEntry(network_frame, font=APP_FONT)
        self.dns_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.dns_entry.insert(0, self.settings.get("dns_servers"))

        # Bypass Domains
        customtkinter.CTkLabel(
            network_frame, text=LBL_BYPASS_DOMAINS, font=APP_FONT
        ).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.bypass_domains_entry = customtkinter.CTkEntry(network_frame, font=APP_FONT)
        self.bypass_domains_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.bypass_domains_entry.insert(0, self.settings.get("bypass_domains"))

        # Bypass IPs
        customtkinter.CTkLabel(network_frame, text=LBL_BYPASS_IPS, font=APP_FONT).grid(
            row=3, column=0, padx=10, pady=5, sticky="w"
        )
        self.bypass_ips_entry = customtkinter.CTkEntry(network_frame, font=APP_FONT)
        self.bypass_ips_entry.grid(row=3, column=1, padx=10, pady=5, sticky="ew")
        self.bypass_ips_entry.insert(0, self.settings.get("bypass_ips"))

        # TUN Mode
        self.tun_mode_checkbox = customtkinter.CTkCheckBox(
            network_frame,
            text=LBL_ENABLE_TUN,
            font=APP_FONT,
            command=self.change_tun_mode,
        )
        self.tun_mode_checkbox.grid(
            row=4, column=0, columnspan=2, padx=10, pady=10, sticky="w"
        )
        if self.settings.get("tun_enabled", False):
            self.tun_mode_checkbox.select()
        else:
            self.tun_mode_checkbox.deselect()

        # --- TLS Fragment Settings ---
        tls_fragment_frame = customtkinter.CTkFrame(network_frame)
        tls_fragment_frame.grid(
            row=5, column=0, columnspan=2, padx=10, pady=10, sticky="ew"
        )
        tls_fragment_frame.grid_columnconfigure(1, weight=1)

        self.tls_fragment_checkbox = customtkinter.CTkCheckBox(
            tls_fragment_frame,
            text="Enable TLS Fragment",
            font=APP_FONT,
            command=self.save_all_settings,
        )
        self.tls_fragment_checkbox.grid(
            row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w"
        )
        if self.settings.get("tls_fragment_enabled", False):
            self.tls_fragment_checkbox.select()

        customtkinter.CTkLabel(
            tls_fragment_frame, text="Fragment Size:", font=APP_FONT
        ).grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.tls_fragment_size_entry = customtkinter.CTkEntry(
            tls_fragment_frame, font=APP_FONT
        )
        self.tls_fragment_size_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.tls_fragment_size_entry.insert(0, self.settings.get("tls_fragment_size"))

        customtkinter.CTkLabel(
            tls_fragment_frame, text="Fragment Sleep:", font=APP_FONT
        ).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.tls_fragment_sleep_entry = customtkinter.CTkEntry(
            tls_fragment_frame, font=APP_FONT
        )
        self.tls_fragment_sleep_entry.grid(
            row=2, column=1, padx=10, pady=5, sticky="ew"
        )
        self.tls_fragment_sleep_entry.insert(0, self.settings.get("tls_fragment_sleep"))

        # --- Mux Settings ---
        mux_frame = customtkinter.CTkFrame(network_frame)
        mux_frame.grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        mux_frame.grid_columnconfigure(1, weight=1)

        self.mux_enabled_checkbox = customtkinter.CTkCheckBox(
            mux_frame,
            text="Enable Mux",
            font=APP_FONT,
            command=self.save_all_settings,
        )
        self.mux_enabled_checkbox.grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        if self.settings.get("mux_enabled", False):
            self.mux_enabled_checkbox.select()

        customtkinter.CTkLabel(mux_frame, text="Mux Protocol:", font=APP_FONT).grid(
            row=1, column=0, padx=10, pady=5, sticky="w"
        )
        self.mux_protocol_menu = customtkinter.CTkOptionMenu(
            mux_frame, values=["h2mux", "smux", "yamux"], font=APP_FONT
        )
        self.mux_protocol_menu.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.mux_protocol_menu.set(self.settings.get("mux_protocol", "h2mux"))

        customtkinter.CTkLabel(mux_frame, text="Max Streams:", font=APP_FONT).grid(
            row=2, column=0, padx=10, pady=5, sticky="w"
        )
        self.mux_max_streams_entry = customtkinter.CTkEntry(mux_frame, font=APP_FONT)
        self.mux_max_streams_entry.grid(row=2, column=1, padx=10, pady=5, sticky="ew")
        self.mux_max_streams_entry.insert(0, self.settings.get("mux_max_streams", "0"))

        self.mux_padding_checkbox = customtkinter.CTkCheckBox(
            mux_frame,
            text="Enable Padding",
            font=APP_FONT,
            command=self.save_all_settings,
        )
        self.mux_padding_checkbox.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="w")
        if self.settings.get("mux_padding", False):
            self.mux_padding_checkbox.select()

        # --- Hysteria2 Settings ---
        hy2_frame = customtkinter.CTkFrame(network_frame)
        hy2_frame.grid(row=7, column=0, columnspan=2, padx=10, pady=10, sticky="ew")
        hy2_frame.grid_columnconfigure(1, weight=1)

        customtkinter.CTkLabel(hy2_frame, text="Hysteria2 Up Mbps:", font=APP_FONT).grid(
            row=0, column=0, padx=10, pady=5, sticky="w"
        )
        self.hy2_up_mbps_entry = customtkinter.CTkEntry(hy2_frame, font=APP_FONT)
        self.hy2_up_mbps_entry.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.hy2_up_mbps_entry.insert(0, self.settings.get("hy2_up_mbps", "50"))

        customtkinter.CTkLabel(hy2_frame, text="Hysteria2 Down Mbps:", font=APP_FONT).grid(
            row=1, column=0, padx=10, pady=5, sticky="w"
        )
        self.hy2_down_mbps_entry = customtkinter.CTkEntry(hy2_frame, font=APP_FONT)
        self.hy2_down_mbps_entry.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
        self.hy2_down_mbps_entry.insert(0, self.settings.get("hy2_down_mbps", "100"))

        # --- Profile Management ---
        customtkinter.CTkLabel(
            parent_tab, text=LBL_PROFILE_MANAGEMENT, font=(APP_FONT[0], 16)
        ).grid(row=8, column=0, padx=20, pady=(20, 10), sticky="w")

        profile_frame = customtkinter.CTkFrame(parent_tab)
        profile_frame.grid(row=6, column=0, padx=20, pady=10, sticky="ew")
        profile_frame.grid_columnconfigure((0, 1), weight=1)

        import_button = customtkinter.CTkButton(
            profile_frame,
            text=BTN_IMPORT_PROFILE,
            command=self.import_profile,
            font=APP_FONT,
        )
        import_button.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")

        export_button = customtkinter.CTkButton(
            profile_frame,
            text=BTN_EXPORT_PROFILE,
            command=self.export_profile,
            font=APP_FONT,
        )
        export_button.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="ew")

        # --- Update Section ---
        customtkinter.CTkLabel(
            parent_tab, text=LBL_UPDATES, font=(APP_FONT[0], 16)
        ).grid(row=7, column=0, padx=20, pady=(20, 10), sticky="w")

        update_frame = customtkinter.CTkFrame(parent_tab)
        update_frame.grid(row=8, column=0, padx=20, pady=10, sticky="ew")
        update_frame.grid_columnconfigure(0, weight=1)

        update_singbox_button = customtkinter.CTkButton(
            update_frame,
            text=BTN_CHECK_FOR_UPDATES,
            command=self.check_for_singbox_updates,
            font=APP_FONT,
        )
        update_singbox_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # --- About Button ---
        about_button = customtkinter.CTkButton(
            parent_tab, text=BTN_ABOUT, command=self.show_about_window
        )
        about_button.grid(row=9, column=0, padx=20, pady=20, sticky="s")

    def check_for_singbox_updates(self):
        """Checks for sing-box updates in a separate thread."""
        threading.Thread(
            target=utils.download_singbox_if_needed,
            kwargs={"force_update": True},
            daemon=True,
        ).start()

    def _create_routing_tab_widgets(self, parent_tab):
        parent_tab.grid_columnconfigure(0, weight=1)
        parent_tab.grid_rowconfigure(1, weight=1)  # Make row for rules scrollable

        customtkinter.CTkLabel(
            parent_tab, text="Custom Routing Rules:", font=(APP_FONT[0], 16)
        ).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        self.routing_rules_frame = customtkinter.CTkScrollableFrame(
            parent_tab, fg_color="transparent"
        )
        self.routing_rules_frame.grid(
            row=1, column=0, sticky="nsew", padx=20, pady=(0, 10)
        )
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
            button_frame,
            text=BTN_ADD_RULE,
            command=self._add_routing_rule_ui,
            font=APP_FONT,
        )
        add_rule_button.grid(row=0, column=0, padx=(0, 5), pady=10, sticky="ew")

        save_rules_button = customtkinter.CTkButton(
            button_frame,
            text="Save Rules",
            command=self._save_routing_rules,
            font=APP_FONT,
        )
        save_rules_button.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

        load_rules_button = customtkinter.CTkButton(
            button_frame,
            text="Load Rules",
            command=self._load_routing_rules,
            font=APP_FONT,
        )
        load_rules_button.grid(row=0, column=2, padx=(5, 0), pady=10, sticky="ew")

    def bind_shortcuts(self):
        right_click_menu = RightClickMenu(self)
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
        self.bind_all("<Control-u>", self.update_all_subscriptions)
        self.bind_all("<Control-q>", self.quit_application)

    # --- Data & Settings Management ---
    def save_all_settings(self):
        settings = {
            "subscriptions": self.subscriptions,
            "servers": self.server_manager.get_all_server_groups(),  # Get servers from the manager
            "appearance_mode": customtkinter.get_appearance_mode(),
            "color_theme": self.color_theme_menu.get(),
            "dns_servers": self.dns_entry.get(),
            "bypass_domains": self.bypass_domains_entry.get(),
            "bypass_ips": self.bypass_ips_entry.get(),
            "custom_routing_rules": self.custom_routing_rules,
            "tun_enabled": self.tun_mode_checkbox.get() == 1,
            "tls_fragment_enabled": self.tls_fragment_checkbox.get() == 1,
            "tls_fragment_size": self.tls_fragment_size_entry.get(),
            "tls_fragment_sleep": self.tls_fragment_sleep_entry.get(),
            "mux_enabled": self.mux_enabled_checkbox.get() == 1,
            "mux_protocol": self.mux_protocol_menu.get(),
            "mux_max_streams": self.mux_max_streams_entry.get(),
            "mux_padding": self.mux_padding_checkbox.get() == 1,
            "hy2_up_mbps": self.hy2_up_mbps_entry.get(),
            "hy2_down_mbps": self.hy2_down_mbps_entry.get(),
        }
        settings_manager.save_settings(settings)

    def load_data(self):
        try:
            self.subscriptions = self.settings.get("subscriptions", [])
            self.server_manager.load_servers()
            self.custom_routing_rules = self.settings.get("custom_routing_rules", [])
            self._display_routing_rules()
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
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            defaultextension=".json",
        )
        if not file_path:
            return

        if not messagebox.askyesno(
            "Confirm Import",
            "This will overwrite all your current settings and servers. Are you sure you want to continue? All unsaved changes will be lost.",
        ):
            return

        if settings_manager.import_settings(file_path):
            messagebox.showinfo(
                "Import Successful",
                "Profile imported successfully. Please restart the application for the changes to take full effect.",
            )
            self.quit_application()  # Force restart
        else:
            messagebox.showerror(
                "Import Failed",
                "Failed to import profile. Please check the file format.",
            )

    def export_profile(self):
        """Exports all current settings to a JSON file."""
        file_path = filedialog.asksaveasfilename(
            title="Export Profile",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            defaultextension=".json",
            initialfile="onix_profile.json",
        )
        if not file_path:
            return

        # Ensure current settings are saved before exporting
        self.save_all_settings()

        if settings_manager.export_settings(file_path):
            messagebox.showinfo(
                "Export Successful", f"Profile successfully exported to:\n{file_path}"
            )
        else:
            messagebox.showerror("Export Failed", "Failed to export profile.")

    # --- Server Manager Callbacks ---
    def _on_update_start(self):
        self.log_textbox.delete("1.0", "end")
        self.log("Updating subscriptions...", LogLevel.INFO)
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
        self.update_server_display()

    # --- UI Update & Logging ---
    def log(self, message, level=LogLevel.INFO):
        """Adds a log message to the internal list and re-renders the log view."""
        self.all_logs.append((level, message))
        # Limit stored logs to avoid memory issues
        if len(self.all_logs) > 500:
            self.all_logs.pop(0)
        self._rerender_logs()

    def _rerender_logs(self):
        """Clears and re-populates the log textbox based on active filters."""
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")

        active_levels = {
            level
            for level, checkbox in self.log_filter_checkboxes.items()
            if checkbox.get() == 1
        }

        log_colors = {
            LogLevel.INFO: "white",
            LogLevel.WARNING: "orange",
            LogLevel.ERROR: "red",
            LogLevel.SUCCESS: "lightgreen",
            LogLevel.DEBUG: "gray",
        }

        for level, message in self.all_logs:
            if level in active_levels:
                color = log_colors.get(level, "white")
                self.log_textbox.insert("end", message + "\n", (level.value,))
                self.log_textbox.tag_config(level.value, foreground=color)

        self.log_textbox.see("end")
        self.log_textbox.configure(state="disabled")

    def populate_group_dropdown(self):
        groups = self.server_manager.get_groups()
        current_selection = self.group_dropdown.get()

        if not groups:
            self.group_dropdown.configure(values=["No Groups"])
            self.group_dropdown.set("No Groups")
            self.update_server_display()
            return

        self.group_dropdown.configure(values=groups)
        if current_selection in groups:
            self.group_dropdown.set(current_selection)
        else:
            self.group_dropdown.set(groups[0])
        self.update_server_display()

    def update_server_display(self, event=None):
        """Central function to filter and display servers based on group and search term."""
        search_term = self.search_entry.get().lower() if self.search_entry else ""
        selected_group = self.group_dropdown.get()

        all_configs = self.server_manager.get_servers_by_group(selected_group)

        if not search_term:
            filtered_configs = all_configs
        else:
            filtered_configs = [
                config
                for config in all_configs
                if search_term in config.get("name", "").lower()
            ]
        
        # --- Sorting ---
        if self.sort_column == "name":
            sort_key = lambda c: c.get("name", "").lower()
            filtered_configs.sort(key=sort_key, reverse=not self.sort_ascending)
        elif self.sort_column == "ping":
            # Handle non-existent, timeout (-1), and valid pings
            def ping_sort_key(c):
                ping = c.get("ping", 9999)
                if ping == -1: return 99999 # Timeouts last
                if not isinstance(ping, int): return 99998 # Not tested yet
                return ping
            filtered_configs.sort(key=ping_sort_key, reverse=not self.sort_ascending)

        self._update_sort_indicators()
        self._render_server_list(filtered_configs)

    def _render_server_list(self, configs):
        self.selected_server_button = None

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
                    self._show_qr_code_for_server,
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
            TITLE_CONFIRM_DELETE,
            MSG_CONFIRM_DELETE_SERVER.format(config_to_delete.get("name")),
        ):
            return

        self.server_manager.delete_server(config_to_delete)

    def edit_server(self, config_to_edit):
        """Opens a dialog to edit the server's name."""
        dialog = customtkinter.CTkInputDialog(
            text=PROMPT_NEW_SERVER_NAME, title=TITLE_EDIT_SERVER
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

    def import_wireguard_config(self):
        file_path = filedialog.askopenfilename(
            title="Import WireGuard Config",
            filetypes=[("WireGuard Config", "*.conf"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config_content = f.read()

            # We will use the server_manager to handle the parsing and adding
            self.server_manager.add_wireguard_config(config_content, file_path)

        except Exception as e:
            error_msg = f"Failed to read or parse WireGuard config: {e}"
            self.log(error_msg, LogLevel.ERROR)
            show_error_message("Import Error", error_msg)

    def scan_qr_from_screen(self):
        """Scans the screen for QR codes and adds any found server links."""
        try:
            import pyscreenshot as ImageGrab
            import cv2
            from pyzbar import pyzbar

            self.log("Scanning screen for QR codes...", LogLevel.INFO)
            # Grab the entire screen
            screen = ImageGrab.grab()
            screen_np = cv2.cvtColor(
                np.array(screen),
                cv2.COLOR_RGB2BGR,
            )

            decoded_objects = pyzbar.decode(screen_np)

            found_qrs = 0
            for obj in decoded_objects:
                if obj.type == "QRCODE":
                    qr_data = obj.data.decode("utf-8")
                    self.log(f"Found QR Code: {qr_data}", LogLevel.INFO)
                    self.server_manager.add_manual_server(qr_data)
                    found_qrs += 1

            if found_qrs == 0:
                self.log("No QR codes found on screen.", LogLevel.WARNING)
            else:
                self.log(
                    f"Successfully added {found_qrs} server(s) from QR codes.",
                    LogLevel.SUCCESS,
                )

        except ImportError as e:
            show_error_message(
                "Missing Library",
                f"Required library for QR scan not found: {e}. Please install 'pyscreenshot', 'opencv-python', and 'pyzbar' using pip.",
            )
            self.log(f"Missing library for QR scan: {e}", LogLevel.ERROR)
        except Exception as e:
            show_error_message(
                "QR Scan Error", f"An unexpected error occurred during QR scan: {e}"
            )
            self.log(f"Error during QR scan: {e}", LogLevel.ERROR)

    # --- Core Functionality ---
    def update_all_subscriptions(self, event=None):
        enabled_subs = [sub for sub in self.subscriptions if sub.get("enabled", True)]
        if not enabled_subs:
            self.log("No enabled subscriptions to update.", LogLevel.WARNING)
            return

        self.log(
            f"Starting update for {len(enabled_subs)} subscription(s)...", LogLevel.INFO
        )
        self.server_manager.update_subscriptions(enabled_subs)

    def manage_subscriptions(self):
        dialog = SubscriptionManagerDialog(self, self.subscriptions, self.log)
        self.wait_window(dialog)
        # After the dialog is closed, save the potentially modified subscriptions
        self.save_all_settings()

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

        # Update UI to show testing indicator
        for config in servers_to_test:
            config_id = f"{config.get('server')}:{config.get('port')}"
            if config_id in self.server_widgets:
                widget_info = self.server_widgets[config_id]
                ping_label = widget_info["ping_label"]
                if ping_label.winfo_exists():
                    ping_label.configure(text="...", text_color="gray")

        self.server_manager.test_all_pings(servers_to_test)

    def test_all_urls(self):
        current_group = self.group_dropdown.get()
        if not current_group or current_group == "No Groups":
            self.log("No servers to test.")
            return
        servers_to_test = self.server_manager.get_servers_by_group(current_group)

        # Update UI to show testing indicator
        for config in servers_to_test:
            config_id = f"{config.get('server')}:{config.get('port')}"
            if config_id in self.server_widgets:
                widget_info = self.server_widgets[config_id]
                ping_label = widget_info["ping_label"]
                if ping_label.winfo_exists():
                    ping_label.configure(text="...", text_color="gray")

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

    def _sort_by_name(self):
        if self.sort_column == "name":
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = "name"
            self.sort_ascending = True
        self.update_server_display()

    def _sort_by_ping(self):
        if self.sort_column == "ping":
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = "ping"
            self.sort_ascending = True
        self.update_server_display()

    def _update_sort_indicators(self):
        name_text = "Name"
        ping_text = "Ping"
        arrow_up = " ▲"
        arrow_down = " ▼"

        # Reset colors
        self.name_sort_button.configure(fg_color="gray20", text_color="white")
        self.ping_sort_button.configure(fg_color="gray20", text_color="white")

        if self.sort_column == "name":
            name_text += arrow_up if self.sort_ascending else arrow_down
            self.name_sort_button.configure(fg_color="#246ba3", text_color="white") # Highlight color
        elif self.sort_column == "ping":
            ping_text += arrow_up if self.sort_ascending else arrow_down
            self.ping_sort_button.configure(fg_color="#246ba3", text_color="white") # Highlight color
        
        self.name_sort_button.configure(text=name_text)
        self.ping_sort_button.configure(text=ping_text)

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

    def change_tun_mode(self):
        self.settings["tun_enabled"] = self.tun_mode_checkbox.get()
        self.save_all_settings()
        self.log(
            f"TUN Mode {('enabled' if self.settings['tun_enabled'] else 'disabled')}. Please restart the app for changes to take full effect.",
            LogLevel.INFO,
        )

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
        img = PIL.Image.open(io.BytesIO(image_data))
        menu = (item("Show", self.show_window), item("Quit", self.quit_application))
        self.tray_icon = pystray.Icon("Sing-box Client", img, "Sing-box Client", menu)
        self.tray_icon.run()

    def show_about_window(self):
        """Displays the About window."""
        # Prevent multiple about windows
        if hasattr(self, "about_win") and self.about_win.winfo_exists():
            self.about_win.lift()
            return

        self.about_win = customtkinter.CTkToplevel(self)
        self.about_win.title(TITLE_ABOUT)
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
            self.about_win, text=LBL_VERSION.format(self.app_version), font=APP_FONT
        )
        version_label.grid(row=1, column=0, padx=20, pady=0)

        def open_releases_page(e):
            webbrowser.open_new(constants.GITHUB_RELEASES_URL)

        link_label = customtkinter.CTkLabel(
            self.about_win,
            text=LBL_GITHUB_RELEASES,
            text_color=("blue", "cyan"),
            cursor="hand2",
            font=customtkinter.CTkFont(underline=True),
        )
        link_label.grid(row=2, column=0, padx=20, pady=10)
        link_label.bind("<Button-1>", open_releases_page)

        ok_button = customtkinter.CTkButton(
            self.about_win, text=BTN_OK, command=self.about_win.destroy, width=100
        )
        ok_button.grid(row=3, column=0, padx=20, pady=20)

    def _show_qr_code_for_server(self, config):
        try:
            import qrcode
            from PIL import ImageTk

            server_link = self.server_manager.get_server_link(
                config
            )  # Assuming ServerManager has a method to get the full link
            if not server_link:
                show_error_message(
                    "QR Code Error", "Could not generate QR code: Server link is empty."
                )
                return

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(server_link)
            qr.make(fit=True)

            img = qr.make_image(fill_color="black", back_color="white")

            # Create a new Toplevel window to display the QR code
            qr_window = customtkinter.CTkToplevel(self)
            qr_window.title(TITLE_QR_CODE.format(config.get("name", "Server")))
            qr_window.transient(self)  # Make it appear on top of the main window
            qr_window.grab_set()  # Make it modal

            # Convert PIL Image to PhotoImage for Tkinter
            img_tk = ImageTk.PhotoImage(img)

            qr_label = customtkinter.CTkLabel(qr_window, image=img_tk, text="")
            qr_label.image = img_tk  # Keep a reference!
            qr_label.pack(padx=20, pady=20)

            # Center the new window
            qr_window.update_idletasks()
            x = (
                self.winfo_x()
                + (self.winfo_width() // 2)
                - (qr_window.winfo_width() // 2)
            )
            y = (
                self.winfo_y()
                + (self.winfo_height() // 2)
                - (qr_window.winfo_height() // 2)
            )
            qr_window.geometry(f"+{x}+{y}")

        except ImportError:
            show_error_message(
                "Missing Library",
                "The 'qrcode' or 'Pillow' library is not installed. Please install it using 'pip install qrcode Pillow'.",
            )
        except Exception as e:
            show_error_message(
                "QR Code Error", f"An error occurred while generating QR code: {e}"
            )

    def _add_routing_rule_ui(self):
        AddRoutingRuleDialog(self, self._on_rule_added)

    def _on_rule_added(self, rule_data):
        if rule_data and rule_data["value"]:
            self.custom_routing_rules.append(rule_data)
            self.log(f"Added routing rule: {rule_data}", LogLevel.INFO)
            self._display_routing_rules()

    def _display_routing_rules(self):
        # Clear existing rules
        for widget in self.routing_rules_frame.winfo_children():
            widget.destroy()

        if not self.custom_routing_rules:
            customtkinter.CTkLabel(
                self.routing_rules_frame,
                text="No custom rules added yet.",
                font=APP_FONT,
            ).grid(row=0, column=0, padx=10, pady=10, sticky="w")
            return

        for i, rule in enumerate(self.custom_routing_rules):
            rule_text = f"{rule['type']}: {rule['value']} -> {rule['action']}"
            rule_label = customtkinter.CTkLabel(
                self.routing_rules_frame, text=rule_text, font=APP_FONT, anchor="w"
            )
            rule_label.grid(row=i, column=0, padx=10, pady=5, sticky="ew")

            # Add Edit/Delete buttons
            edit_button = customtkinter.CTkButton(
                self.routing_rules_frame,
                text=BTN_EDIT,
                width=60,
                font=APP_FONT,
                command=lambda r=rule: self._edit_routing_rule_ui(r),
            )
            edit_button.grid(row=i, column=1, padx=(0, 5), pady=5, sticky="e")

            delete_button = customtkinter.CTkButton(
                self.routing_rules_frame,
                text=BTN_DELETE,
                width=60,
                font=APP_FONT,
                command=lambda r=rule: self._delete_routing_rule(r),
            )
            delete_button.grid(row=i, column=2, padx=(0, 10), pady=5, sticky="e")

    def _save_routing_rules(self):
        self.save_all_settings()
        self.log("Routing rules saved.", LogLevel.SUCCESS)

    def _load_routing_rules(self):
        self.settings = settings_manager.load_settings()
        self.custom_routing_rules = self.settings.get("custom_routing_rules", [])
        self._display_routing_rules()
        self.log("Routing rules loaded.", LogLevel.INFO)

    def _delete_routing_rule(self, rule_to_delete):
        if messagebox.askyesno(TITLE_CONFIRM_DELETE, MSG_CONFIRM_DELETE_RULE):
            self.custom_routing_rules.remove(rule_to_delete)
            self._display_routing_rules()
            self.save_all_settings()
            self.log("Routing rule deleted.", LogLevel.INFO)

    def _edit_routing_rule_ui(self, rule_to_edit):
        # Store the original rule to find and update it later
        self._current_edit_rule = rule_to_edit
        AddRoutingRuleDialog(self, self._on_rule_edited, initial_rule=rule_to_edit)

    def _on_rule_edited(self, new_rule_data):
        if new_rule_data and new_rule_data["value"]:
            # Find the index of the original rule and update it
            try:
                index = self.custom_routing_rules.index(self._current_edit_rule)
                self.custom_routing_rules[index] = new_rule_data
                self.log(f"Edited routing rule: {new_rule_data}", LogLevel.INFO)
                self._display_routing_rules()
                self.save_all_settings()
            except ValueError:
                self.log("Error: Original rule not found for editing.", LogLevel.ERROR)
        # Clear the stored rule after editing
        self._current_edit_rule = None


if __name__ == "__main__":
    app = SingboxApp()
    app.mainloop()
