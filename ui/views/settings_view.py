from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QListWidget,
    QStackedWidget,
    QListWidgetItem,
    QScrollArea,
    QGroupBox,
    QFormLayout,
    QComboBox,
    QPushButton,
    QLineEdit,
    QCheckBox,
    QSizePolicy,
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize
from constants import (
    LBL_THEME_COLOR,
    LogLevel,
)


def create_settings_view(main_window):
    widget = QWidget()
    widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    main_layout = QHBoxLayout(widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    # Navigation on the left
    nav_container = QWidget()
    nav_container.setMaximumWidth(200)  # Limit container width
    nav_container.setMinimumWidth(140)  # Ensure minimum width
    nav_container.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
    nav_layout = QVBoxLayout(nav_container)
    nav_layout.setContentsMargins(0, 0, 0, 0)
    nav_layout.setSpacing(0)  # Remove spacing

    # Search field
    search_field = QLineEdit()
    search_field.setPlaceholderText(main_window.tr("Search settings..."))
    search_field.setObjectName("SettingsSearch")
    search_field.setMaximumHeight(35)  # Limit height
    search_field.setStyleSheet("""
        QLineEdit#SettingsSearch {
            padding: 6px 10px;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            background-color: #ffffff;
            margin: 4px 8px;
            font-size: 12px;
        }
        QLineEdit#SettingsSearch:focus {
            border-color: #007bff;
            outline: none;
        }
    """)
    nav_layout.addWidget(search_field)

    settings_nav = QListWidget()
    settings_nav.setMinimumWidth(140)
    settings_nav.setMaximumWidth(200)
    settings_nav.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
    settings_nav.setObjectName("SettingsNav")
    settings_nav.setSpacing(2)  # Reduce spacing between items
    settings_nav.setAlternatingRowColors(False)  # Disable alternating colors
    settings_nav.setStyleSheet(
        """
        QListWidget#SettingsNav {
            background-color: #e9ecef;
            border-right: 1px solid #dee2e6;
        }
        QListWidget#SettingsNav::item {
            padding: 8px 12px;
            border-bottom: 1px solid #dee2e6;
            font-size: 13px;
        }
        QListWidget#SettingsNav::item:selected {
            background-color: #007bff;
            color: #ffffff;
            border-left: 4px solid #0056b3;
            font-weight: bold;
        }
        /* Dark theme adjustments */
        [theme="dark"] QListWidget#SettingsNav {
            background-color: #343a40;
            border-right: 1px solid #495057;
        }
        [theme="dark"] QListWidget#SettingsNav::item {
            border-bottom: 1px solid #495057;
        }
        [theme="dark"] QListWidget#SettingsNav::item:selected {
            background-color: #3daee9;
            color: #ffffff;
            border-left-color: #2a8bc7;
        }
    """
    )
    nav_layout.addWidget(settings_nav)  # Add navigation list to container

    # Pages on the right
    main_window.settings_pages = QStackedWidget()
    main_window.settings_pages.setSizePolicy(
        QSizePolicy.Expanding, QSizePolicy.Expanding)

    # Connect search functionality
    search_field.textChanged.connect(
        lambda text: _filter_settings_pages(main_window, text))

    # Create and add pages
    main_window.settings_pages.addWidget(
        _create_general_settings_page(main_window))
    main_window.settings_pages.addWidget(
        _create_network_settings_page(main_window))
    main_window.settings_pages.addWidget(
        _create_protocols_settings_page(main_window))
    main_window.settings_pages.addWidget(
        _create_security_settings_page(main_window))
    main_window.settings_pages.addWidget(
        _create_performance_settings_page(main_window))
    main_window.settings_pages.addWidget(
        _create_privacy_settings_page(main_window))

    # Add items to navigation
    general_item = QListWidgetItem(
        QIcon(":/icons/sliders.svg"), main_window.tr("General")
    )
    network_item = QListWidgetItem(
        QIcon(":/icons/globe.svg"), main_window.tr("Network")
    )
    protocols_item = QListWidgetItem(
        QIcon(":/icons/shield.svg"), main_window.tr("Protocols")
    )
    security_item = QListWidgetItem(
        QIcon(":/icons/shield.svg"), main_window.tr("Security")
    )
    performance_item = QListWidgetItem(
        QIcon(":/icons/zap.svg"), main_window.tr("Performance")
    )
    privacy_item = QListWidgetItem(
        QIcon(":/icons/shield.svg"), main_window.tr("Privacy")
    )

    # Set size hints and add items
    items = [general_item, network_item, protocols_item,
             security_item, performance_item, privacy_item]
    for item in items:
        item.setSizeHint(QSize(item.sizeHint().width(), 35))  # Reduced height
        settings_nav.addItem(item)

    # Ensure navigation is visible
    settings_nav.setVisible(True)

    main_layout.addWidget(nav_container, 0)  # Fixed size for navigation
    main_layout.addWidget(main_window.settings_pages, 1)  # Stretch for content

    # Set layout properties
    main_layout.setStretchFactor(nav_container, 0)  # Don't stretch navigation
    main_layout.setStretchFactor(
        main_window.settings_pages, 1)  # Stretch content

    settings_nav.currentRowChanged.connect(
        main_window.settings_pages.setCurrentIndex)
    settings_nav.setCurrentRow(0)

    return widget


def _create_settings_page_container(main_window):
    """Helper to create a standard container for a settings page."""
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    scroll_area.setStyleSheet("QScrollArea { border: none; }")
    page_widget = QWidget()
    page_layout = QVBoxLayout(page_widget)
    page_layout.setContentsMargins(25, 20, 25, 20)
    page_layout.setSpacing(15)
    page_layout.setAlignment(Qt.AlignTop)
    scroll_area.setWidget(page_widget)
    return scroll_area, page_layout


def _create_general_settings_page(main_window):
    """Creates the 'General' settings page."""
    container, layout = _create_settings_page_container(main_window)

    # --- Appearance Group ---
    appearance_group = QGroupBox(main_window.tr("Appearance"))
    appearance_layout = QFormLayout(appearance_group)

    main_window.appearance_mode_combo = QComboBox()
    main_window.appearance_mode_combo.addItems(
        [main_window.tr("System"), main_window.tr(
            "Light"), main_window.tr("Dark")]
    )
    main_window.appearance_mode_combo.setCurrentText(
        main_window.tr(main_window.settings.get("appearance_mode", "System"))
    )
    main_window.appearance_mode_combo.currentTextChanged.connect(
        main_window.apply_theme)

    main_window.theme_combo = QComboBox()
    main_window.theme_names = {
        "blue": main_window.tr("Indigo"),
        "green": main_window.tr("Emerald"),
        "purple": main_window.tr("Violet"),
        "rose": main_window.tr("Rose"),
    }
    main_window.theme_combo.addItems(main_window.theme_names.values())
    current_theme_code = main_window.settings.get("theme_color", "blue")
    main_window.theme_combo.setCurrentText(
        main_window.theme_names.get(
            current_theme_code, main_window.tr("Indigo"))
    )
    main_window.theme_combo.currentTextChanged.connect(
        main_window.on_theme_change)

    appearance_layout.addRow(
        main_window.tr("Appearance Mode:"), main_window.appearance_mode_combo
    )

    main_window.language_combo = QComboBox()
    main_window.languages = {
        "en": "English",
        "fa": "فارسی (Persian)",
        "ru": "Русский (Russian)",
        "ar": "العربية (Arabic)",
        "zh": "简体中文 (Chinese)",
    }
    main_window.language_combo.addItems(main_window.languages.values())
    current_lang_code = main_window.settings.get("language", "en")
    current_lang_name = main_window.languages.get(current_lang_code, "English")
    main_window.language_combo.setCurrentText(current_lang_name)
    main_window.language_combo.currentTextChanged.connect(
        main_window.on_language_change)

    # Add a restart button for language and core changes
    main_window.restart_button = QPushButton(main_window.tr("Apply & Restart"))
    main_window.restart_button.clicked.connect(main_window.handle_restart)
    main_window.restart_button.hide()  # Initially hidden
    appearance_layout.addRow(main_window.tr(
        "Language:"), main_window.language_combo)
    appearance_layout.addRow(main_window.tr(
        LBL_THEME_COLOR), main_window.theme_combo)

    layout.addWidget(appearance_group)

    # --- Profile Management Group ---
    profile_group = QGroupBox(main_window.tr("Profile Management"))
    profile_layout = QHBoxLayout(profile_group)

    import_button = QPushButton(main_window.tr("Import Profile"))
    import_button.clicked.connect(main_window.handle_import_profile)
    profile_layout.addWidget(import_button)

    export_button = QPushButton(main_window.tr("Export Profile"))
    export_button.clicked.connect(main_window.handle_export_profile)
    profile_layout.addWidget(export_button)

    layout.addWidget(profile_group)

    # --- Log File Management Group ---
    log_group = QGroupBox(main_window.tr("Log File Management"))
    log_layout = QFormLayout(log_group)

    # Add Log Level setting
    main_window.log_level_combo = QComboBox()
    main_window.log_level_combo.addItems([
        main_window.tr("Debug"),
        main_window.tr("Info"),
        main_window.tr("Warning"),
        main_window.tr("Error")
    ])
    current_log_level = main_window.settings.get("log_level", "Info")
    main_window.log_level_combo.setCurrentText(
        main_window.tr(current_log_level))
    main_window.log_level_combo.currentTextChanged.connect(
        main_window.save_settings)
    log_layout.addRow(main_window.tr("Log Level:"),
                      main_window.log_level_combo)

    clear_core_log_button = QPushButton(
        QIcon(":/icons/trash-2.svg"), main_window.tr("Clear Core Log File")
    )
    clear_core_log_button.clicked.connect(main_window.handle_clear_core_log)
    log_layout.addRow(clear_core_log_button)

    layout.addWidget(log_group)

    # --- Core Management Group ---
    core_management_group = QGroupBox(main_window.tr("Core Management"))
    core_management_layout = QFormLayout(core_management_group)

    main_window.core_selector_combo = QComboBox()
    # Add other supported cores here in the future
    main_window.core_selector_combo.addItems(["sing-box", "xray"])
    main_window.core_selector_combo.setCurrentText(
        main_window.settings.get("active_core", "sing-box")
    )
    main_window.core_selector_combo.currentTextChanged.connect(
        main_window.on_core_change)
    core_management_layout.addRow(
        main_window.tr("Active Core:"), main_window.core_selector_combo
    )

    main_window.check_updates_button = QPushButton(
        main_window.tr("Check for Core Updates")
    )
    main_window.check_updates_button.clicked.connect(
        main_window.handle_check_for_updates)
    core_management_layout.addRow(main_window.check_updates_button)
    core_management_layout.addRow(main_window.restart_button)

    layout.addWidget(core_management_group)

    # --- Settings Presets Group ---
    presets_group = QGroupBox(main_window.tr("Settings Presets"))
    presets_layout = QFormLayout(presets_group)

    # Preset selection
    main_window.settings_preset_combo = QComboBox()
    main_window.settings_preset_combo.addItems([
        main_window.tr("Custom"),
        main_window.tr("Balanced"),
        main_window.tr("Performance"),
        main_window.tr("Security"),
        main_window.tr("Privacy")
    ])
    main_window.settings_preset_combo.currentTextChanged.connect(
        lambda preset: _apply_settings_preset(main_window, preset))
    presets_layout.addRow(main_window.tr("Preset:"),
                          main_window.settings_preset_combo)

    # Reset to defaults button
    reset_defaults_button = QPushButton(
        QIcon(":/icons/refresh-cw.svg"), main_window.tr("Reset to Defaults"))
    reset_defaults_button.clicked.connect(
        lambda: _reset_settings_to_defaults(main_window))
    presets_layout.addRow(reset_defaults_button)

    layout.addWidget(presets_group)

    # --- About Button ---
    about_button = QPushButton(main_window.tr("About Onix"))
    about_button.clicked.connect(main_window.show_about_dialog)
    layout.addWidget(about_button, alignment=Qt.AlignLeft)

    return container


def _create_network_settings_page(main_window):
    """Creates the 'Network' settings page."""
    container, layout = _create_settings_page_container(main_window)

    # --- Network Settings Group ---
    network_group = QGroupBox(main_window.tr("Connection & DNS"))
    network_layout = QFormLayout(network_group)

    # --- Health Check Settings Group ---
    health_group = QGroupBox(main_window.tr("Health Check Settings"))
    health_layout = QFormLayout(health_group)

    # Health Check Interval
    main_window.health_check_interval_combo = QComboBox()
    main_window.health_check_interval_combo.addItems(
        ["30 seconds", "60 seconds", "120 seconds", "300 seconds"])
    current_interval = main_window.settings.get("health_check_interval", 30)
    main_window.health_check_interval_combo.setCurrentText(
        f"{current_interval} seconds")
    health_layout.addRow(main_window.tr("Check Interval:"),
                         main_window.health_check_interval_combo)

    # EMA Alpha
    main_window.health_check_ema_combo = QComboBox()
    main_window.health_check_ema_combo.addItems(
        ["0.1 (Fast)", "0.3 (Balanced)", "0.5 (Slow)"])
    current_ema = main_window.settings.get("health_check_ema_alpha", 0.3)
    main_window.health_check_ema_combo.setCurrentText(
        f"{current_ema} (Balanced)" if current_ema == 0.3 else f"{current_ema} (Fast)" if current_ema == 0.1 else f"{current_ema} (Slow)")
    health_layout.addRow(main_window.tr("Smoothing:"),
                         main_window.health_check_ema_combo)

    # Backoff Base
    main_window.health_check_backoff_combo = QComboBox()
    main_window.health_check_backoff_combo.addItems(
        ["1 second", "2 seconds", "5 seconds"])
    current_backoff = main_window.settings.get("health_check_backoff_base", 1)
    main_window.health_check_backoff_combo.setCurrentText(
        f"{current_backoff} second" if current_backoff == 1 else f"{current_backoff} seconds")
    health_layout.addRow(main_window.tr("Backoff Base:"),
                         main_window.health_check_backoff_combo)

    # Auto-start for groups
    main_window.health_check_auto_start = QCheckBox(
        main_window.tr("Auto-start Health Check for new groups"))
    main_window.health_check_auto_start.setChecked(
        main_window.settings.get("health_check_auto_start", False))
    health_layout.addRow(main_window.health_check_auto_start)

    # Auto-failover
    main_window.auto_failover_checkbox = QCheckBox(
        main_window.tr("Enable Auto-failover"))
    main_window.auto_failover_checkbox.setChecked(
        main_window.settings.get("auto_failover_enabled", False))
    main_window.auto_failover_checkbox.stateChanged.connect(
        main_window.save_settings)
    health_layout.addRow(main_window.auto_failover_checkbox)

    main_window.connection_mode_combo = QComboBox()
    main_window.connection_mode_combo.addItems(
        [main_window.tr("Rule-Based"), main_window.tr("Global")]
    )
    main_window.connection_mode_combo.setCurrentText(
        main_window.settings.get("connection_mode", "Rule-Based")
    )
    network_layout.addRow(
        main_window.tr("Connection Mode:"), main_window.connection_mode_combo
    )

    main_window.dns_entry = QLineEdit()
    main_window.dns_entry.setText(main_window.settings.get("dns_servers", ""))
    main_window.dns_entry.setPlaceholderText(
        main_window.tr("e.g., 1.1.1.1,8.8.8.8"))
    network_layout.addRow(main_window.tr(
        "DNS Servers:"), main_window.dns_entry)

    main_window.tun_checkbox = QCheckBox(
        main_window.tr("Enable TUN Mode (System-wide Proxy)")
    )
    main_window.tun_checkbox.setChecked(
        main_window.settings.get("tun_enabled", False))
    main_window.tun_checkbox.stateChanged.connect(main_window.save_settings)
    network_layout.addRow(main_window.tun_checkbox)
    layout.addWidget(network_group)
    layout.addWidget(health_group)

    # --- Bypass Rules Group ---
    bypass_group = QGroupBox(main_window.tr("Bypass Rules"))
    bypass_layout = QFormLayout(bypass_group)

    main_window.bypass_domains_entry = QLineEdit()
    main_window.bypass_domains_entry.setText(
        main_window.settings.get("bypass_domains", "")
    )
    main_window.bypass_domains_entry.setPlaceholderText(
        main_window.tr("Comma-separated domains")
    )
    bypass_layout.addRow(
        main_window.tr("Bypass Domains:"), main_window.bypass_domains_entry
    )

    # Add Bypass IPs field
    main_window.bypass_ips_entry = QLineEdit()
    main_window.bypass_ips_entry.setText(
        main_window.settings.get("bypass_ips", "")
    )
    main_window.bypass_ips_entry.setPlaceholderText(
        main_window.tr("Comma-separated IPs (e.g., 192.168.0.0/16,127.0.0.1)")
    )
    bypass_layout.addRow(
        main_window.tr("Bypass IPs:"), main_window.bypass_ips_entry
    )

    layout.addWidget(bypass_group)

    return container


def _create_protocols_settings_page(main_window):
    """Creates the 'Protocols' settings page."""
    container, layout = _create_settings_page_container(main_window)

    # --- Muxing Settings Group ---
    mux_group = QGroupBox(main_window.tr("Muxing Settings"))
    mux_layout = QFormLayout(mux_group)
    main_window.mux_enabled_checkbox = QCheckBox(
        main_window.tr("Enable Muxing"))
    main_window.mux_enabled_checkbox.setChecked(
        main_window.settings.get("mux_enabled", False)
    )
    main_window.mux_enabled_checkbox.stateChanged.connect(
        main_window.save_settings)
    mux_layout.addRow(main_window.mux_enabled_checkbox)
    main_window.mux_protocol_combo = QComboBox()
    main_window.mux_protocol_combo.addItems(["smux", "h2mux", "yamux"])
    main_window.mux_protocol_combo.setCurrentText(
        main_window.settings.get("mux_protocol", "smux")
    )
    mux_layout.addRow(main_window.tr("Protocol:"),
                      main_window.mux_protocol_combo)
    main_window.mux_max_streams_entry = QLineEdit()
    main_window.mux_max_streams_entry.setText(
        str(main_window.settings.get("mux_max_streams", 8))
    )
    mux_layout.addRow(main_window.tr("Max Streams:"),
                      main_window.mux_max_streams_entry)

    # Add Mux Padding checkbox
    main_window.mux_padding_checkbox = QCheckBox(
        main_window.tr("Enable Mux Padding"))
    main_window.mux_padding_checkbox.setChecked(
        main_window.settings.get("mux_padding", False))
    main_window.mux_padding_checkbox.stateChanged.connect(
        main_window.save_settings)
    mux_layout.addRow(main_window.mux_padding_checkbox)

    layout.addWidget(mux_group)

    # --- Advanced TLS Settings Group ---
    tls_group = QGroupBox(main_window.tr("Advanced TLS Settings"))
    tls_layout = QFormLayout(tls_group)
    main_window.tls_fragment_checkbox = QCheckBox(
        main_window.tr("Enable TLS Fragment"))
    main_window.tls_fragment_checkbox.setChecked(
        main_window.settings.get("tls_fragment_enabled", False)
    )
    main_window.tls_fragment_checkbox.stateChanged.connect(
        main_window.save_settings)
    tls_layout.addRow(main_window.tls_fragment_checkbox)
    main_window.tls_fragment_size_entry = QLineEdit()
    main_window.tls_fragment_size_entry.setText(
        main_window.settings.get("tls_fragment_size", "10-100")
    )
    tls_layout.addRow(
        main_window.tr("Fragment Size:"), main_window.tls_fragment_size_entry
    )
    main_window.tls_fragment_sleep_entry = QLineEdit()
    main_window.tls_fragment_sleep_entry.setText(
        main_window.settings.get("tls_fragment_sleep", "10-100")
    )
    tls_layout.addRow(
        main_window.tr("Fragment Sleep:"), main_window.tls_fragment_sleep_entry
    )
    layout.addWidget(tls_group)

    # --- Hysteria2 Settings Group ---
    hysteria_group = QGroupBox(main_window.tr("Hysteria2 Settings"))
    hysteria_layout = QFormLayout(hysteria_group)
    main_window.hysteria_up_speed_entry = QLineEdit()
    main_window.hysteria_up_speed_entry.setText(
        str(main_window.settings.get("hysteria_up_mbps", 50))
    )
    hysteria_layout.addRow(
        main_window.tr(
            "Default Upload (Mbps):"), main_window.hysteria_up_speed_entry
    )
    main_window.hysteria_down_speed_entry = QLineEdit()
    main_window.hysteria_down_speed_entry.setText(
        str(main_window.settings.get("hysteria_down_mbps", 200))
    )
    hysteria_layout.addRow(
        main_window.tr("Default Download (Mbps):"),
        main_window.hysteria_down_speed_entry,
    )
    layout.addWidget(hysteria_group)

    # Connect all settings widgets to the save_settings method
    main_window.appearance_mode_combo.currentTextChanged.connect(
        main_window.save_settings)
    main_window.connection_mode_combo.currentTextChanged.connect(
        main_window.save_settings)
    main_window.dns_entry.editingFinished.connect(main_window.save_settings)
    main_window.bypass_domains_entry.editingFinished.connect(
        main_window.save_settings)
    main_window.bypass_ips_entry.editingFinished.connect(
        main_window.save_settings)
    main_window.tun_checkbox.stateChanged.connect(main_window.save_settings)
    main_window.mux_enabled_checkbox.stateChanged.connect(
        main_window.save_settings)
    main_window.mux_protocol_combo.currentTextChanged.connect(
        main_window.save_settings)
    main_window.mux_max_streams_entry.editingFinished.connect(
        main_window.save_settings)
    main_window.mux_padding_checkbox.stateChanged.connect(
        main_window.save_settings)
    main_window.tls_fragment_checkbox.stateChanged.connect(
        main_window.save_settings)
    main_window.tls_fragment_size_entry.editingFinished.connect(
        main_window.save_settings)
    main_window.tls_fragment_sleep_entry.editingFinished.connect(
        main_window.save_settings)
    main_window.hysteria_up_speed_entry.editingFinished.connect(
        main_window.save_settings)
    main_window.hysteria_down_speed_entry.editingFinished.connect(
        main_window.save_settings)

    return container


def _create_security_settings_page(main_window):
    """Creates the 'Security' settings page."""
    container, layout = _create_settings_page_container(main_window)

    # --- Connection Security Group ---
    connection_security_group = QGroupBox(
        main_window.tr("Connection Security"))
    connection_security_layout = QFormLayout(connection_security_group)

    # Enable IPv6
    main_window.enable_ipv6_checkbox = QCheckBox(
        main_window.tr("Enable IPv6 Support"))
    main_window.enable_ipv6_checkbox.setChecked(
        main_window.settings.get("enable_ipv6", True))
    main_window.enable_ipv6_checkbox.stateChanged.connect(
        main_window.save_settings)
    connection_security_layout.addRow(main_window.enable_ipv6_checkbox)

    # Allow Insecure
    main_window.allow_insecure_checkbox = QCheckBox(
        main_window.tr("Allow Insecure Connections"))
    main_window.allow_insecure_checkbox.setChecked(
        main_window.settings.get("allow_insecure", False))
    main_window.allow_insecure_checkbox.stateChanged.connect(
        main_window.save_settings)
    connection_security_layout.addRow(main_window.allow_insecure_checkbox)

    # Certificate Verification
    main_window.cert_verification_checkbox = QCheckBox(
        main_window.tr("Verify SSL Certificates"))
    main_window.cert_verification_checkbox.setChecked(
        main_window.settings.get("cert_verification", True))
    main_window.cert_verification_checkbox.stateChanged.connect(
        main_window.save_settings)
    connection_security_layout.addRow(main_window.cert_verification_checkbox)

    layout.addWidget(connection_security_group)

    # --- Advanced Security Group ---
    advanced_security_group = QGroupBox(main_window.tr("Advanced Security"))
    advanced_security_layout = QFormLayout(advanced_security_group)

    # Custom CA Certificate
    main_window.custom_ca_entry = QLineEdit()
    main_window.custom_ca_entry.setText(
        main_window.settings.get("custom_ca_cert", ""))
    main_window.custom_ca_entry.setPlaceholderText(
        main_window.tr("Path to custom CA certificate file"))
    advanced_security_layout.addRow(
        main_window.tr("Custom CA Certificate:"), main_window.custom_ca_entry)

    # Cipher Suites
    main_window.cipher_suites_entry = QLineEdit()
    main_window.cipher_suites_entry.setText(
        main_window.settings.get("cipher_suites", ""))
    main_window.cipher_suites_entry.setPlaceholderText(
        main_window.tr("Comma-separated cipher suites"))
    advanced_security_layout.addRow(
        main_window.tr("Cipher Suites:"), main_window.cipher_suites_entry)

    # Security Level
    main_window.security_level_combo = QComboBox()
    main_window.security_level_combo.addItems([
        main_window.tr("High"),
        main_window.tr("Medium"),
        main_window.tr("Low")
    ])
    current_security_level = main_window.settings.get("security_level", "High")
    main_window.security_level_combo.setCurrentText(
        main_window.tr(current_security_level))
    main_window.security_level_combo.currentTextChanged.connect(
        main_window.save_settings)
    advanced_security_layout.addRow(
        main_window.tr("Security Level:"), main_window.security_level_combo)

    layout.addWidget(advanced_security_group)

    # --- Connection Settings Group ---
    connection_settings_group = QGroupBox(
        main_window.tr("Connection Settings"))
    connection_settings_layout = QFormLayout(connection_settings_group)

    # Connection Timeout
    main_window.connection_timeout_entry = QLineEdit()
    main_window.connection_timeout_entry.setText(
        str(main_window.settings.get("connection_timeout", 30)))
    main_window.connection_timeout_entry.setPlaceholderText(
        main_window.tr("Connection timeout in seconds"))
    connection_settings_layout.addRow(
        main_window.tr("Connection Timeout:"), main_window.connection_timeout_entry)

    # Retry Attempts
    main_window.retry_attempts_entry = QLineEdit()
    main_window.retry_attempts_entry.setText(
        str(main_window.settings.get("retry_attempts", 3)))
    main_window.retry_attempts_entry.setPlaceholderText(
        main_window.tr("Number of retry attempts"))
    connection_settings_layout.addRow(
        main_window.tr("Retry Attempts:"), main_window.retry_attempts_entry)

    # Keep Alive
    main_window.keep_alive_checkbox = QCheckBox(
        main_window.tr("Enable Keep-Alive"))
    main_window.keep_alive_checkbox.setChecked(
        main_window.settings.get("keep_alive", True))
    main_window.keep_alive_checkbox.stateChanged.connect(
        main_window.save_settings)
    connection_settings_layout.addRow(main_window.keep_alive_checkbox)

    layout.addWidget(connection_settings_group)

    # Connect all settings widgets to the save_settings method
    main_window.custom_ca_entry.editingFinished.connect(
        main_window.save_settings)
    main_window.cipher_suites_entry.editingFinished.connect(
        main_window.save_settings)
    main_window.connection_timeout_entry.editingFinished.connect(
        main_window.save_settings)
    main_window.retry_attempts_entry.editingFinished.connect(
        main_window.save_settings)

    return container


def _create_performance_settings_page(main_window):
    """Creates the 'Performance' settings page."""
    container, layout = _create_settings_page_container(main_window)

    # --- Connection Performance Group ---
    connection_performance_group = QGroupBox(
        main_window.tr("Connection Performance"))
    connection_performance_layout = QFormLayout(connection_performance_group)

    # Connection Pool Size
    main_window.connection_pool_size_entry = QLineEdit()
    main_window.connection_pool_size_entry.setText(
        str(main_window.settings.get("connection_pool_size", 10)))
    main_window.connection_pool_size_entry.setPlaceholderText(
        main_window.tr("Number of connections in pool"))
    connection_performance_layout.addRow(
        main_window.tr("Connection Pool Size:"), main_window.connection_pool_size_entry)

    # Thread Pool Size
    main_window.thread_pool_size_entry = QLineEdit()
    main_window.thread_pool_size_entry.setText(
        str(main_window.settings.get("thread_pool_size", 5)))
    main_window.thread_pool_size_entry.setPlaceholderText(
        main_window.tr("Number of worker threads"))
    connection_performance_layout.addRow(
        main_window.tr("Thread Pool Size:"), main_window.thread_pool_size_entry)

    # Buffer Size
    main_window.buffer_size_entry = QLineEdit()
    main_window.buffer_size_entry.setText(
        str(main_window.settings.get("buffer_size", 8192)))
    main_window.buffer_size_entry.setPlaceholderText(
        main_window.tr("Buffer size in bytes"))
    connection_performance_layout.addRow(
        main_window.tr("Buffer Size:"), main_window.buffer_size_entry)

    layout.addWidget(connection_performance_group)

    # --- Network Performance Group ---
    network_performance_group = QGroupBox(
        main_window.tr("Network Performance"))
    network_performance_layout = QFormLayout(network_performance_group)

    # Bandwidth Limiting
    main_window.bandwidth_limit_checkbox = QCheckBox(
        main_window.tr("Enable Bandwidth Limiting"))
    main_window.bandwidth_limit_checkbox.setChecked(
        main_window.settings.get("bandwidth_limit_enabled", False))
    main_window.bandwidth_limit_checkbox.stateChanged.connect(
        main_window.save_settings)
    network_performance_layout.addRow(main_window.bandwidth_limit_checkbox)

    # Upload Speed Limit
    main_window.upload_speed_limit_entry = QLineEdit()
    main_window.upload_speed_limit_entry.setText(
        str(main_window.settings.get("upload_speed_limit", 0)))
    main_window.upload_speed_limit_entry.setPlaceholderText(
        main_window.tr("Upload speed limit in KB/s (0 = unlimited)"))
    network_performance_layout.addRow(
        main_window.tr("Upload Speed Limit:"), main_window.upload_speed_limit_entry)

    # Download Speed Limit
    main_window.download_speed_limit_entry = QLineEdit()
    main_window.download_speed_limit_entry.setText(
        str(main_window.settings.get("download_speed_limit", 0)))
    main_window.download_speed_limit_entry.setPlaceholderText(
        main_window.tr("Download speed limit in KB/s (0 = unlimited)"))
    network_performance_layout.addRow(
        main_window.tr("Download Speed Limit:"), main_window.download_speed_limit_entry)

    layout.addWidget(network_performance_group)

    # --- Advanced Performance Group ---
    advanced_performance_group = QGroupBox(
        main_window.tr("Advanced Performance"))
    advanced_performance_layout = QFormLayout(advanced_performance_group)

    # Connection Multiplexing
    main_window.connection_multiplexing_checkbox = QCheckBox(
        main_window.tr("Enable Connection Multiplexing"))
    main_window.connection_multiplexing_checkbox.setChecked(
        main_window.settings.get("connection_multiplexing", True))
    main_window.connection_multiplexing_checkbox.stateChanged.connect(
        main_window.save_settings)
    advanced_performance_layout.addRow(
        main_window.connection_multiplexing_checkbox)

    # Compression
    main_window.compression_checkbox = QCheckBox(
        main_window.tr("Enable Compression"))
    main_window.compression_checkbox.setChecked(
        main_window.settings.get("compression_enabled", False))
    main_window.compression_checkbox.stateChanged.connect(
        main_window.save_settings)
    advanced_performance_layout.addRow(main_window.compression_checkbox)

    # Fast Open
    main_window.fast_open_checkbox = QCheckBox(
        main_window.tr("Enable TCP Fast Open"))
    main_window.fast_open_checkbox.setChecked(
        main_window.settings.get("tcp_fast_open", False))
    main_window.fast_open_checkbox.stateChanged.connect(
        main_window.save_settings)
    advanced_performance_layout.addRow(main_window.fast_open_checkbox)

    # Congestion Control
    main_window.congestion_control_combo = QComboBox()
    main_window.congestion_control_combo.addItems([
        main_window.tr("Cubic"),
        main_window.tr("BBR"),
        main_window.tr("BBR2"),
        main_window.tr("Reno")
    ])
    current_congestion = main_window.settings.get(
        "congestion_control", "Cubic")
    main_window.congestion_control_combo.setCurrentText(
        main_window.tr(current_congestion))
    main_window.congestion_control_combo.currentTextChanged.connect(
        main_window.save_settings)
    advanced_performance_layout.addRow(
        main_window.tr("Congestion Control:"), main_window.congestion_control_combo)

    layout.addWidget(advanced_performance_group)

    # --- Monitoring Group ---
    monitoring_group = QGroupBox(main_window.tr("Performance Monitoring"))
    monitoring_layout = QFormLayout(monitoring_group)

    # Enable Statistics
    main_window.enable_statistics_checkbox = QCheckBox(
        main_window.tr("Enable Performance Statistics"))
    main_window.enable_statistics_checkbox.setChecked(
        main_window.settings.get("enable_statistics", True))
    main_window.enable_statistics_checkbox.stateChanged.connect(
        main_window.save_settings)
    monitoring_layout.addRow(main_window.enable_statistics_checkbox)

    # Statistics Interval
    main_window.statistics_interval_entry = QLineEdit()
    main_window.statistics_interval_entry.setText(
        str(main_window.settings.get("statistics_interval", 5)))
    main_window.statistics_interval_entry.setPlaceholderText(
        main_window.tr("Statistics update interval in seconds"))
    monitoring_layout.addRow(
        main_window.tr("Statistics Interval:"), main_window.statistics_interval_entry)

    layout.addWidget(monitoring_group)

    # Connect all settings widgets to the save_settings method
    main_window.connection_pool_size_entry.editingFinished.connect(
        main_window.save_settings)
    main_window.thread_pool_size_entry.editingFinished.connect(
        main_window.save_settings)
    main_window.buffer_size_entry.editingFinished.connect(
        main_window.save_settings)
    main_window.upload_speed_limit_entry.editingFinished.connect(
        main_window.save_settings)
    main_window.download_speed_limit_entry.editingFinished.connect(
        main_window.save_settings)
    main_window.statistics_interval_entry.editingFinished.connect(
        main_window.save_settings)

    return container


def _filter_settings_pages(main_window, search_text):
    """Filter settings pages based on search text."""
    if not search_text.strip():
        # Show all pages
        for i in range(main_window.settings_pages.count()):
            main_window.settings_pages.widget(i).setVisible(True)
        return

    search_text = search_text.lower()

    # Define keywords for each page
    page_keywords = {
        # General
        0: ["general", "appearance", "theme", "language", "profile", "log", "core"],
        1: ["network", "dns", "bypass", "connection", "mode", "tun"],  # Network
        2: ["protocol", "tls", "mux", "hysteria", "fragment"],  # Protocols
        # Security
        3: ["security", "ipv6", "insecure", "cert", "cipher", "timeout", "retry"],
        # Performance
        4: ["performance", "pool", "thread", "buffer", "bandwidth", "multiplexing", "compression"],
        # Privacy
        5: ["privacy", "telemetry", "crash", "usage", "logging", "dns", "traffic", "ip", "auto", "update"]
    }

    # Show/hide pages based on search
    for page_index, keywords in page_keywords.items():
        if page_index < main_window.settings_pages.count():
            page_widget = main_window.settings_pages.widget(page_index)
            if any(keyword in search_text for keyword in keywords):
                page_widget.setVisible(True)
            else:
                page_widget.setVisible(False)


def _apply_settings_preset(main_window, preset_name):
    """Apply a settings preset."""
    if preset_name == main_window.tr("Custom"):
        return  # Don't change anything for custom

    presets = {
        main_window.tr("Balanced"): {
            "connection_mode": "Rule-Based",
            "dns_servers": "1.1.1.1,8.8.8.8",
            "bypass_domains": "*.ir,*.local",
            "tun_enabled": False,
            "mux_enabled": True,
            "mux_protocol": "smux",
            "tls_fragment_enabled": False,
            "enable_ipv6": True,
            "allow_insecure": False,
            "cert_verification": True,
            "connection_timeout": 30,
            "retry_attempts": 3,
            "connection_pool_size": 10,
            "thread_pool_size": 5,
            "buffer_size": 8192,
            "bandwidth_limit_enabled": False,
            "connection_multiplexing": True,
            "compression_enabled": False,
            "tcp_fast_open": False,
            "congestion_control": "Cubic",
            "enable_statistics": True,
            "statistics_interval": 5,
            "auto_failover_enabled": False,
        },
        main_window.tr("Performance"): {
            "connection_mode": "Global",
            "dns_servers": "1.1.1.1,1.0.0.1",
            "bypass_domains": "",
            "tun_enabled": True,
            "mux_enabled": True,
            "mux_protocol": "smux",
            "tls_fragment_enabled": True,
            "enable_ipv6": True,
            "allow_insecure": False,
            "cert_verification": True,
            "connection_timeout": 15,
            "retry_attempts": 5,
            "connection_pool_size": 20,
            "thread_pool_size": 10,
            "buffer_size": 16384,
            "bandwidth_limit_enabled": False,
            "connection_multiplexing": True,
            "compression_enabled": True,
            "tcp_fast_open": True,
            "congestion_control": "BBR",
            "enable_statistics": True,
            "statistics_interval": 3,
            "auto_failover_enabled": True,
        },
        main_window.tr("Security"): {
            "connection_mode": "Rule-Based",
            "dns_servers": "1.1.1.1,8.8.8.8",
            "bypass_domains": "*.ir,*.local",
            "tun_enabled": False,
            "mux_enabled": False,
            "mux_protocol": "smux",
            "tls_fragment_enabled": False,
            "enable_ipv6": False,
            "allow_insecure": False,
            "cert_verification": True,
            "connection_timeout": 60,
            "retry_attempts": 2,
            "connection_pool_size": 5,
            "thread_pool_size": 3,
            "buffer_size": 4096,
            "bandwidth_limit_enabled": False,
            "connection_multiplexing": False,
            "compression_enabled": False,
            "tcp_fast_open": False,
            "congestion_control": "Cubic",
            "enable_statistics": True,
            "statistics_interval": 10,
            "auto_failover_enabled": False,
        },
        main_window.tr("Privacy"): {
            "connection_mode": "Rule-Based",
            "dns_servers": "1.1.1.1,1.0.0.1",
            "bypass_domains": "*.ir,*.local",
            "tun_enabled": True,
            "mux_enabled": True,
            "mux_protocol": "smux",
            "tls_fragment_enabled": True,
            "enable_ipv6": False,
            "allow_insecure": False,
            "cert_verification": True,
            "connection_timeout": 45,
            "retry_attempts": 3,
            "connection_pool_size": 8,
            "thread_pool_size": 4,
            "buffer_size": 6144,
            "bandwidth_limit_enabled": False,
            "connection_multiplexing": True,
            "compression_enabled": True,
            "tcp_fast_open": False,
            "congestion_control": "Cubic",
            "enable_statistics": False,
            "statistics_interval": 15,
            "auto_failover_enabled": True,
        }
    }

    if preset_name in presets:
        preset_settings = presets[preset_name]

        # Apply settings
        for key, value in preset_settings.items():
            main_window.settings[key] = value

        # Update UI widgets
        _update_settings_ui(main_window, preset_settings)

        # Save settings
        main_window.save_settings()

        main_window.log(f"Applied {preset_name} preset", LogLevel.SUCCESS)


def _update_settings_ui(main_window, settings):
    """Update UI widgets with new settings."""
    # Update widgets if they exist
    if hasattr(main_window, 'connection_mode_combo'):
        mode_map = {
            "Rule-Based": main_window.tr("Rule-Based"), "Global": main_window.tr("Global")}
        for key, value in mode_map.items():
            if settings.get("connection_mode") == key:
                main_window.connection_mode_combo.setCurrentText(value)
                break

    if hasattr(main_window, 'dns_entry'):
        main_window.dns_entry.setText(settings.get("dns_servers", ""))

    if hasattr(main_window, 'bypass_domains_entry'):
        main_window.bypass_domains_entry.setText(
            settings.get("bypass_domains", ""))

    if hasattr(main_window, 'tun_checkbox'):
        main_window.tun_checkbox.setChecked(settings.get("tun_enabled", False))

    if hasattr(main_window, 'mux_enabled_checkbox'):
        main_window.mux_enabled_checkbox.setChecked(
            settings.get("mux_enabled", False))

    if hasattr(main_window, 'mux_protocol_combo'):
        protocol_map = {"smux": main_window.tr(
            "smux"), "yamux": main_window.tr("yamux")}
        for key, value in protocol_map.items():
            if settings.get("mux_protocol") == key:
                main_window.mux_protocol_combo.setCurrentText(value)
                break

    if hasattr(main_window, 'tls_fragment_checkbox'):
        main_window.tls_fragment_checkbox.setChecked(
            settings.get("tls_fragment_enabled", False))

    if hasattr(main_window, 'enable_ipv6_checkbox'):
        main_window.enable_ipv6_checkbox.setChecked(
            settings.get("enable_ipv6", True))

    if hasattr(main_window, 'allow_insecure_checkbox'):
        main_window.allow_insecure_checkbox.setChecked(
            settings.get("allow_insecure", False))

    if hasattr(main_window, 'cert_verification_checkbox'):
        main_window.cert_verification_checkbox.setChecked(
            settings.get("cert_verification", True))

    if hasattr(main_window, 'connection_timeout_entry'):
        main_window.connection_timeout_entry.setText(
            str(settings.get("connection_timeout", 30)))

    if hasattr(main_window, 'retry_attempts_entry'):
        main_window.retry_attempts_entry.setText(
            str(settings.get("retry_attempts", 3)))

    if hasattr(main_window, 'connection_pool_size_entry'):
        main_window.connection_pool_size_entry.setText(
            str(settings.get("connection_pool_size", 10)))

    if hasattr(main_window, 'thread_pool_size_entry'):
        main_window.thread_pool_size_entry.setText(
            str(settings.get("thread_pool_size", 5)))

    if hasattr(main_window, 'buffer_size_entry'):
        main_window.buffer_size_entry.setText(
            str(settings.get("buffer_size", 8192)))

    if hasattr(main_window, 'bandwidth_limit_checkbox'):
        main_window.bandwidth_limit_checkbox.setChecked(
            settings.get("bandwidth_limit_enabled", False))

    if hasattr(main_window, 'connection_multiplexing_checkbox'):
        main_window.connection_multiplexing_checkbox.setChecked(
            settings.get("connection_multiplexing", True))

    if hasattr(main_window, 'compression_checkbox'):
        main_window.compression_checkbox.setChecked(
            settings.get("compression_enabled", False))

    if hasattr(main_window, 'tcp_fast_open_checkbox'):
        main_window.tcp_fast_open_checkbox.setChecked(
            settings.get("tcp_fast_open", False))

    if hasattr(main_window, 'congestion_control_combo'):
        control_map = {"Cubic": main_window.tr(
            "Cubic"), "BBR": main_window.tr("BBR")}
        for key, value in control_map.items():
            if settings.get("congestion_control") == key:
                main_window.congestion_control_combo.setCurrentText(value)
                break

    if hasattr(main_window, 'enable_statistics_checkbox'):
        main_window.enable_statistics_checkbox.setChecked(
            settings.get("enable_statistics", True))

    if hasattr(main_window, 'statistics_interval_entry'):
        main_window.statistics_interval_entry.setText(
            str(settings.get("statistics_interval", 5)))

    if hasattr(main_window, 'auto_failover_checkbox'):
        main_window.auto_failover_checkbox.setChecked(
            settings.get("auto_failover_enabled", False))


def _reset_settings_to_defaults(main_window):
    """Reset all settings to defaults."""
    from settings_manager import DEFAULT_SETTINGS

    # Apply default settings
    for key, value in DEFAULT_SETTINGS.items():
        if key not in ["app_version", "subscriptions", "servers", "window_geometry", "window_maximized"]:
            main_window.settings[key] = value

    # Update UI
    _update_settings_ui(main_window, DEFAULT_SETTINGS)

    # Save settings
    main_window.save_settings()

    main_window.log("Reset all settings to defaults", LogLevel.SUCCESS)


def _create_privacy_settings_page(main_window):
    """Creates the 'Privacy' settings page."""
    container, layout = _create_settings_page_container(main_window)

    # --- Data Collection Group ---
    data_collection_group = QGroupBox(main_window.tr("Data Collection"))
    data_collection_layout = QFormLayout(data_collection_group)

    # Disable telemetry
    main_window.disable_telemetry_checkbox = QCheckBox(
        main_window.tr("Disable Telemetry"))
    main_window.disable_telemetry_checkbox.setChecked(
        main_window.settings.get("disable_telemetry", True))
    main_window.disable_telemetry_checkbox.stateChanged.connect(
        main_window.save_settings)
    data_collection_layout.addRow(main_window.disable_telemetry_checkbox)

    # Disable crash reports
    main_window.disable_crash_reports_checkbox = QCheckBox(
        main_window.tr("Disable Crash Reports"))
    main_window.disable_crash_reports_checkbox.setChecked(
        main_window.settings.get("disable_crash_reports", True))
    main_window.disable_crash_reports_checkbox.stateChanged.connect(
        main_window.save_settings)
    data_collection_layout.addRow(main_window.disable_crash_reports_checkbox)

    # Disable usage statistics
    main_window.disable_usage_stats_checkbox = QCheckBox(
        main_window.tr("Disable Usage Statistics"))
    main_window.disable_usage_stats_checkbox.setChecked(
        main_window.settings.get("disable_usage_stats", True))
    main_window.disable_usage_stats_checkbox.stateChanged.connect(
        main_window.save_settings)
    data_collection_layout.addRow(main_window.disable_usage_stats_checkbox)

    layout.addWidget(data_collection_group)

    # --- Logging Privacy Group ---
    logging_privacy_group = QGroupBox(main_window.tr("Logging Privacy"))
    logging_privacy_layout = QFormLayout(logging_privacy_group)

    # Disable detailed logging
    main_window.disable_detailed_logging_checkbox = QCheckBox(
        main_window.tr("Disable Detailed Logging"))
    main_window.disable_detailed_logging_checkbox.setChecked(
        main_window.settings.get("disable_detailed_logging", False))
    main_window.disable_detailed_logging_checkbox.stateChanged.connect(
        main_window.save_settings)
    logging_privacy_layout.addRow(
        main_window.disable_detailed_logging_checkbox)

    # Clear logs on exit
    main_window.clear_logs_on_exit_checkbox = QCheckBox(
        main_window.tr("Clear Logs on Exit"))
    main_window.clear_logs_on_exit_checkbox.setChecked(
        main_window.settings.get("clear_logs_on_exit", False))
    main_window.clear_logs_on_exit_checkbox.stateChanged.connect(
        main_window.save_settings)
    logging_privacy_layout.addRow(main_window.clear_logs_on_exit_checkbox)

    # Disable connection logging
    main_window.disable_connection_logging_checkbox = QCheckBox(
        main_window.tr("Disable Connection Logging"))
    main_window.disable_connection_logging_checkbox.setChecked(
        main_window.settings.get("disable_connection_logging", False))
    main_window.disable_connection_logging_checkbox.stateChanged.connect(
        main_window.save_settings)
    logging_privacy_layout.addRow(
        main_window.disable_connection_logging_checkbox)

    layout.addWidget(logging_privacy_group)

    # --- Network Privacy Group ---
    network_privacy_group = QGroupBox(main_window.tr("Network Privacy"))
    network_privacy_layout = QFormLayout(network_privacy_group)

    # Disable DNS logging
    main_window.disable_dns_logging_checkbox = QCheckBox(
        main_window.tr("Disable DNS Query Logging"))
    main_window.disable_dns_logging_checkbox.setChecked(
        main_window.settings.get("disable_dns_logging", True))
    main_window.disable_dns_logging_checkbox.stateChanged.connect(
        main_window.save_settings)
    network_privacy_layout.addRow(main_window.disable_dns_logging_checkbox)

    # Disable traffic statistics
    main_window.disable_traffic_stats_checkbox = QCheckBox(
        main_window.tr("Disable Traffic Statistics"))
    main_window.disable_traffic_stats_checkbox.setChecked(
        main_window.settings.get("disable_traffic_stats", False))
    main_window.disable_traffic_stats_checkbox.stateChanged.connect(
        main_window.save_settings)
    network_privacy_layout.addRow(main_window.disable_traffic_stats_checkbox)

    # Disable IP logging
    main_window.disable_ip_logging_checkbox = QCheckBox(
        main_window.tr("Disable IP Address Logging"))
    main_window.disable_ip_logging_checkbox.setChecked(
        main_window.settings.get("disable_ip_logging", True))
    main_window.disable_ip_logging_checkbox.stateChanged.connect(
        main_window.save_settings)
    network_privacy_layout.addRow(main_window.disable_ip_logging_checkbox)

    layout.addWidget(network_privacy_group)

    # --- Application Privacy Group ---
    app_privacy_group = QGroupBox(main_window.tr("Application Privacy"))
    app_privacy_layout = QFormLayout(app_privacy_group)

    # Disable auto-updates
    main_window.disable_auto_updates_checkbox = QCheckBox(
        main_window.tr("Disable Auto-Updates"))
    main_window.disable_auto_updates_checkbox.setChecked(
        main_window.settings.get("disable_auto_updates", False))
    main_window.disable_auto_updates_checkbox.stateChanged.connect(
        main_window.save_settings)
    app_privacy_layout.addRow(main_window.disable_auto_updates_checkbox)

    # Disable core auto-updates
    main_window.disable_core_auto_updates_checkbox = QCheckBox(
        main_window.tr("Disable Core Auto-Updates"))
    main_window.disable_core_auto_updates_checkbox.setChecked(
        main_window.settings.get("disable_core_auto_updates", False))
    main_window.disable_core_auto_updates_checkbox.stateChanged.connect(
        main_window.save_settings)
    app_privacy_layout.addRow(main_window.disable_core_auto_updates_checkbox)

    # Disable subscription auto-updates
    main_window.disable_sub_auto_updates_checkbox = QCheckBox(
        main_window.tr("Disable Subscription Auto-Updates"))
    main_window.disable_sub_auto_updates_checkbox.setChecked(
        main_window.settings.get("disable_sub_auto_updates", False))
    main_window.disable_sub_auto_updates_checkbox.stateChanged.connect(
        main_window.save_settings)
    app_privacy_layout.addRow(main_window.disable_sub_auto_updates_checkbox)

    layout.addWidget(app_privacy_group)

    # --- Privacy Actions Group ---
    privacy_actions_group = QGroupBox(main_window.tr("Privacy Actions"))
    privacy_actions_layout = QFormLayout(privacy_actions_group)

    # Clear all data button
    clear_data_button = QPushButton(
        QIcon(":/icons/trash-2.svg"), main_window.tr("Clear All Data"))
    clear_data_button.clicked.connect(
        lambda: _clear_all_privacy_data(main_window))
    privacy_actions_layout.addRow(clear_data_button)

    # Export privacy settings button
    export_privacy_button = QPushButton(
        QIcon(":/icons/file-text.svg"), main_window.tr("Export Privacy Settings"))
    export_privacy_button.clicked.connect(
        lambda: _export_privacy_settings(main_window))
    privacy_actions_layout.addRow(export_privacy_button)

    layout.addWidget(privacy_actions_group)

    return container


def _clear_all_privacy_data(main_window):
    """Clear all privacy-sensitive data."""
    from PySide6.QtWidgets import QMessageBox

    reply = QMessageBox.question(
        main_window,
        main_window.tr("Clear All Data"),
        main_window.tr(
            "This will clear all logs, cache, and temporary data. Continue?"),
        QMessageBox.Yes | QMessageBox.No,
        QMessageBox.No
    )

    if reply == QMessageBox.Yes:
        try:
            # Clear logs
            import os
            log_files = ["xray_core.log", "singbox_core.log"]
            for log_file in log_files:
                if os.path.exists(log_file):
                    os.remove(log_file)

            # Clear cache
            if os.path.exists("cache.db"):
                os.remove("cache.db")

            # Clear temp directory
            import shutil
            if os.path.exists("storage/temp"):
                shutil.rmtree("storage/temp")
                os.makedirs("storage/temp", exist_ok=True)

            main_window.log(
                "Cleared all privacy-sensitive data", LogLevel.SUCCESS)

        except Exception as e:
            main_window.log(f"Error clearing data: {e}", LogLevel.ERROR)


def _export_privacy_settings(main_window):
    """Export privacy settings to a file."""
    try:
        privacy_settings = {
            "disable_telemetry": main_window.settings.get("disable_telemetry", True),
            "disable_crash_reports": main_window.settings.get("disable_crash_reports", True),
            "disable_usage_stats": main_window.settings.get("disable_usage_stats", True),
            "disable_detailed_logging": main_window.settings.get("disable_detailed_logging", False),
            "clear_logs_on_exit": main_window.settings.get("clear_logs_on_exit", False),
            "disable_connection_logging": main_window.settings.get("disable_connection_logging", False),
            "disable_dns_logging": main_window.settings.get("disable_dns_logging", True),
            "disable_traffic_stats": main_window.settings.get("disable_traffic_stats", False),
            "disable_ip_logging": main_window.settings.get("disable_ip_logging", True),
            "disable_auto_updates": main_window.settings.get("disable_auto_updates", False),
            "disable_core_auto_updates": main_window.settings.get("disable_core_auto_updates", False),
            "disable_sub_auto_updates": main_window.settings.get("disable_sub_auto_updates", False),
        }

        import json
        with open("privacy_settings.json", "w", encoding="utf-8") as f:
            json.dump(privacy_settings, f, indent=2, ensure_ascii=False)

        main_window.log(
            "Exported privacy settings to privacy_settings.json", LogLevel.SUCCESS)

    except Exception as e:
        main_window.log(
            f"Error exporting privacy settings: {e}", LogLevel.ERROR)
