from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QComboBox,
    QLineEdit,
    QPushButton,
    QListWidget,
    QTextEdit,
    QMenu,
    QLabel,
    QProgressBar,
    QSizePolicy,
)
from PySide6.QtGui import QIcon, QAction, QMovie
from PySide6.QtCore import QSize


def create_connection_view(main_window):
    widget = QWidget()
    main_layout = QHBoxLayout(widget)
    main_layout.setContentsMargins(0, 0, 0, 0)
    main_layout.setSpacing(0)

    top_bar = QWidget()
    top_bar.setObjectName("TopBar")
    top_bar_layout = QHBoxLayout(top_bar)
    top_bar_layout.setContentsMargins(16, 12, 16, 12)
    top_bar_layout.setSpacing(12)  # More spacing for better visibility
    main_window.current_view_mode = "servers"  # "servers" or "chains"

    main_window.group_dropdown = QComboBox()
    main_window.group_dropdown.setFixedWidth(140)
    main_window.group_dropdown.setSizePolicy(
        QSizePolicy.Fixed, QSizePolicy.Fixed)

    # Sort combo removed - auto-sort by best ping

    main_window.search_field = QLineEdit()
    main_window.search_field.setPlaceholderText(main_window.tr("Search..."))
    main_window.search_field.setFixedWidth(180)
    main_window.search_field.setSizePolicy(
        QSizePolicy.Fixed, QSizePolicy.Fixed)
    main_window.manage_subs_button = QPushButton(
        QIcon(":/icons/list.svg"), main_window.tr("Subscriptions")
    )
    main_window.manage_subs_button.setFixedWidth(140)
    main_window.manage_subs_button.setSizePolicy(
        QSizePolicy.Fixed, QSizePolicy.Fixed)

    # Update button moved to subscriptions menu

    main_window.health_check_tcp_button = QPushButton(
        QIcon(":/icons/zap.svg"), main_window.tr("TCP")
    )
    main_window.health_check_tcp_button.setFixedWidth(60)
    main_window.health_check_tcp_button.setSizePolicy(
        QSizePolicy.Fixed, QSizePolicy.Fixed
    )
    main_window.health_check_tcp_button.setToolTip(
        main_window.tr("Test TCP Ping"))
    main_window.health_check_tcp_button.setCheckable(True)

    main_window.health_check_url_button = QPushButton(
        QIcon(":/icons/activity.svg"), main_window.tr("URL")
    )
    main_window.health_check_url_button.setFixedWidth(60)
    main_window.health_check_url_button.setSizePolicy(
        QSizePolicy.Fixed, QSizePolicy.Fixed
    )
    main_window.health_check_url_button.setToolTip(
        main_window.tr("Test URL Ping"))
    main_window.health_check_url_button.setCheckable(True)

    # Speed Test Button
    main_window.speed_test_button = QPushButton(
        QIcon(":/icons/zap.svg"), main_window.tr("Speed")
    )
    main_window.speed_test_button.setFixedWidth(60)
    main_window.speed_test_button.setSizePolicy(
        QSizePolicy.Fixed, QSizePolicy.Fixed)
    main_window.speed_test_button.setToolTip(main_window.tr("Speed Test"))
    main_window.speed_test_button.setCheckable(True)

    # Smart Connect Button
    main_window.smart_connect_button = QPushButton(
        QIcon(":/icons/activity.svg"), main_window.tr("Smart Connect")
    )
    main_window.smart_connect_button.setFixedWidth(100)
    main_window.smart_connect_button.setSizePolicy(
        QSizePolicy.Fixed, QSizePolicy.Fixed)
    main_window.smart_connect_button.setToolTip(
        main_window.tr("Connect to best server automatically"))
    main_window.smart_connect_button.setStyleSheet("""
        QPushButton {
            background-color: #10b981;
            color: white;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            font-size: 12px;
        }
        QPushButton:hover {
            background-color: #059669;
        }
        QPushButton:pressed {
            background-color: #047857;
        }
    """)

    # Export button removed - now in more menu

    # Health Check Progress Bar with modern styling
    main_window.health_check_progress = QProgressBar()
    main_window.health_check_progress.setVisible(False)
    main_window.health_check_progress.setMaximum(100)
    main_window.health_check_progress.setValue(0)
    main_window.health_check_progress.setFixedHeight(8)
    main_window.health_check_progress.setStyleSheet(
        """
        QProgressBar {
            border: none;
            border-radius: 4px;
            text-align: center;
            background-color: #f3f4f6;
            font-size: 11px;
            font-weight: 600;
            color: #374151;
        }
        QProgressBar::chunk {
            background: linear-gradient(135deg, #10b981, #059669);
            border-radius: 4px;
        }
    """
    )

    # Loading animation for sorting
    main_window.sorting_spinner_label = QLabel()
    sorting_spinner_movie = QMovie(":/icons/spinner.gif")
    sorting_spinner_movie.setScaledSize(QSize(20, 20))
    main_window.sorting_spinner_label.setMovie(sorting_spinner_movie)
    main_window.sorting_spinner_label.hide()

    # Loading animation for subscription update
    main_window.update_spinner_label = QLabel()
    spinner_movie = QMovie(":/icons/spinner.gif")
    spinner_movie.setScaledSize(QSize(20, 20))
    main_window.update_spinner_label.setMovie(spinner_movie)
    main_window.update_spinner_label.hide()

    # --- More Actions Menu ---
    main_window.more_actions_button = QPushButton(
        QIcon(":/icons/more-horizontal.svg"), ""
    )
    main_window.more_actions_button.setMinimumWidth(30)
    main_window.more_actions_button.setMaximumWidth(40)
    main_window.more_actions_button.setSizePolicy(
        QSizePolicy.Fixed, QSizePolicy.Fixed)
    more_menu = QMenu(main_window)

    import_action = QAction(
        QIcon(":/icons/clipboard.svg"),
        main_window.tr("Import from Clipboard"),
        main_window,
    )
    import_action.triggered.connect(main_window.import_from_clipboard)
    more_menu.addAction(import_action)

    scan_qr_action = QAction(
        QIcon(":/icons/camera.svg"), main_window.tr("Scan QR from Screen"), main_window
    )
    scan_qr_action.triggered.connect(main_window.handle_scan_qr_from_screen)
    more_menu.addAction(scan_qr_action)

    import_wg_action = QAction(
        QIcon(":/icons/clipboard.svg"),
        main_window.tr("Import WireGuard from File"),
        main_window,
    )
    import_wg_action.triggered.connect(
        main_window.handle_import_wireguard_config)
    more_menu.addAction(import_wg_action)

    more_menu.addSeparator()

    # Add update subscriptions to menu
    update_subs_action = QAction(
        QIcon(":/icons/refresh-cw.svg"),
        main_window.tr("Update Subscriptions"),
        main_window,
    )
    update_subs_action.triggered.connect(
        main_window.handle_update_subscriptions)
    more_menu.addAction(update_subs_action)

    # Add export and manage chains to menu
    export_action = QAction(
        QIcon(":/icons/file-text.svg"), main_window.tr("Export Data"), main_window
    )
    export_action.triggered.connect(main_window.show_export_dialog)
    more_menu.addAction(export_action)

    manage_chains_action = QAction(
        QIcon(":/icons/git-merge.svg"), main_window.tr("Manage Chains"), main_window
    )
    manage_chains_action.triggered.connect(main_window.show_chain_manager)
    more_menu.addAction(manage_chains_action)

    more_menu.addSeparator()

    copy_links_action = QAction(
        QIcon(":/icons/copy.svg"), main_window.tr("Copy Group Links"), main_window
    )
    copy_links_action.triggered.connect(
        main_window.copy_group_links_to_clipboard)
    more_menu.addAction(copy_links_action)

    remove_duplicates_action = QAction(
        QIcon(":/icons/refresh-cw.svg"),
        main_window.tr("Remove Duplicates"),
        main_window,
    )
    remove_duplicates_action.triggered.connect(
        main_window.remove_duplicate_servers)
    more_menu.addAction(remove_duplicates_action)

    delete_group_action = QAction(
        QIcon(":/icons/trash-2.svg"),
        main_window.tr("Delete Current Group"),
        main_window,
    )
    delete_group_action.triggered.connect(main_window.delete_current_group)
    more_menu.addAction(delete_group_action)

    main_window.more_actions_button.setMenu(more_menu)

    # Simple and clean header layout
    top_bar_layout.addWidget(main_window.group_dropdown)
    top_bar_layout.addWidget(main_window.search_field)
    top_bar_layout.addStretch()
    top_bar_layout.addWidget(main_window.smart_connect_button)
    top_bar_layout.addWidget(main_window.health_check_tcp_button)
    top_bar_layout.addWidget(main_window.health_check_url_button)
    top_bar_layout.addWidget(main_window.speed_test_button)
    top_bar_layout.addWidget(main_window.manage_subs_button)
    top_bar_layout.addWidget(main_window.more_actions_button)

    # --- Left Panel (List) ---
    left_panel = QWidget()
    left_layout = QVBoxLayout(left_panel)
    left_layout.setContentsMargins(0, 0, 0, 0)
    left_layout.setSpacing(0)
    left_layout.addWidget(top_bar)

    main_window.server_list_widget = QListWidget()
    main_window.server_list_widget.setStyleSheet(
        "QListWidget::item { padding: 5px; }")
    main_window.server_list_widget.currentItemChanged.connect(
        main_window.on_server_selected
    )
    left_layout.addWidget(main_window.server_list_widget)

    # --- Right Panel (Details) ---
    main_window.server_details_panel = QWidget()
    main_window.server_details_panel.setObjectName("ServerDetailsPanel")
    main_window.server_details_panel.setMinimumWidth(250)
    main_window.server_details_panel.setMaximumWidth(350)
    main_window.server_details_panel.setSizePolicy(
        QSizePolicy.Preferred, QSizePolicy.Expanding
    )
    main_window.server_details_panel.setStyleSheet(
        "#ServerDetailsPanel { border-left: 1px solid #e9ecef; } [theme='dark'] #ServerDetailsPanel { border-left: 1px solid #495057; }"
    )
    details_layout = QVBoxLayout(main_window.server_details_panel)
    main_window.server_details_content = QTextEdit()
    main_window.server_details_content.setReadOnly(True)
    details_layout.addWidget(main_window.server_details_content)
    main_window.server_details_panel.hide()  # Initially hidden
    main_layout.addWidget(left_panel)
    main_layout.addWidget(main_window.server_details_panel)

    main_window.group_dropdown.currentTextChanged.connect(
        main_window.update_server_list
    )
    main_window.search_field.textChanged.connect(
        main_window.update_server_list)
    # Sort combo removed - auto-sort by best ping
    main_window.health_check_tcp_button.clicked.connect(
        main_window.toggle_health_check_tcp
    )
    main_window.health_check_url_button.clicked.connect(
        main_window.toggle_health_check_url
    )
    main_window.speed_test_button.clicked.connect(
        main_window.toggle_speed_test)
    main_window.manage_subs_button.clicked.connect(
        main_window.show_subscription_manager
    )
    # Update button moved to more menu

    return widget
