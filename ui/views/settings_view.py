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
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt, QSize
from constants import (
    LBL_THEME_COLOR,
    THEME_NAME_GREEN,
    THEME_NAME_BLUE,
    THEME_NAME_DARK_BLUE,
)


def create_settings_view(main_window):
    widget = QWidget()
    main_layout = QHBoxLayout(widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    # Navigation on the left
    settings_nav = QListWidget()
    settings_nav.setFixedWidth(180)
    settings_nav.setObjectName("SettingsNav")
    settings_nav.setStyleSheet(
        """
        QListWidget#SettingsNav {
            background-color: #e9ecef;
            border-right: 1px solid #dee2e6;
        }
        QListWidget#SettingsNav::item {
            padding: 12px 15px;
            border-bottom: 1px solid #dee2e6;
        }
        QListWidget#SettingsNav::item:selected {
            background-color: #ffffff;
            border-left: 4px solid #007bff;
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
            background-color: #212529;
            border-left-color: #3daee9;
        }
    """
    )

    # Pages on the right
    main_window.settings_pages = QStackedWidget()

    # Create and add pages
    main_window.settings_pages.addWidget(
        _create_general_settings_page(main_window))
    main_window.settings_pages.addWidget(
        _create_network_settings_page(main_window))
    main_window.settings_pages.addWidget(
        _create_protocols_settings_page(main_window))

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

    for item in [general_item, network_item, protocols_item]:
        item.setSizeHint(QSize(item.sizeHint().width(), 40))
        settings_nav.addItem(item)

    main_layout.addWidget(settings_nav)
    main_layout.addWidget(main_window.settings_pages)

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
        "blue": main_window.tr(THEME_NAME_BLUE),
        "green": main_window.tr(THEME_NAME_GREEN),
        "dark-blue": main_window.tr(THEME_NAME_DARK_BLUE),
    }
    main_window.theme_combo.addItems(main_window.theme_names.values())
    current_theme_code = main_window.settings.get("theme_color", "blue")
    main_window.theme_combo.setCurrentText(
        main_window.theme_names.get(
            current_theme_code, main_window.tr(THEME_NAME_BLUE))
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
    log_layout = QHBoxLayout(log_group)

    clear_core_log_button = QPushButton(
        QIcon(":/icons/trash-2.svg"), main_window.tr("Clear Core Log File")
    )
    clear_core_log_button.clicked.connect(main_window.handle_clear_core_log)
    log_layout.addWidget(
        clear_core_log_button, alignment=Qt.AlignLeft
    )  # Align to left

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
    main_window.tun_checkbox.stateChanged.connect(main_window.save_settings)
    main_window.mux_enabled_checkbox.stateChanged.connect(
        main_window.save_settings)
    main_window.mux_protocol_combo.currentTextChanged.connect(
        main_window.save_settings)
    main_window.mux_max_streams_entry.editingFinished.connect(
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
